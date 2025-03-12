import streamlit as st
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
from utils.file_operations import (
    normalizar_dataframe,
    guardar_dataframe_por_hojas,
    crear_archivo_descargable,
    consolidar_hojas_excel
)

# Archivos de salida
PERSISTENT_EXPENSES_FILE = "data/control_de_gasto_de_licitaciones.xlsx"
PERSISTENT_ORDERS_FILE = "data/control_de_ordenes_de_compra.xlsx"
CONTROL_SUMMARY_FILE = "data/resumen_control_licitaciones.json"

# Función para convertir objetos no serializables a formato JSON
def json_serial(obj):
    """Función para convertir objetos especiales a un formato serializable en JSON."""
    if isinstance(obj, (datetime, pd.Timestamp)):
        return obj.strftime('%Y-%m-%d')
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if pd.isna(obj):
        return None
    raise TypeError(f"Tipo no serializable: {type(obj)}")

def control_avanzado_de_gastos(licitaciones_df, ordenes_df):
    """
    Sistema avanzado de control de gastos para licitaciones.
    
    Args:
        licitaciones_df: DataFrame con información de licitaciones
        ordenes_df: DataFrame con órdenes de compra
        
    Returns:
        dict: Diccionario con DataFrames de control para cada licitación
    """
    # Asegurar que las columnas están normalizadas
    licitaciones_df.columns = [col.lower().strip().replace(" ", "_") for col in licitaciones_df.columns]
    ordenes_df.columns = [col.lower().strip().replace(" ", "_") for col in ordenes_df.columns]
    
    # Verificar si existe la columna numero_licitacion
    if 'numero_licitacion' not in licitaciones_df.columns:
        st.error("Error: No se encontró la columna 'numero_licitacion' en el archivo de licitaciones.")
        st.write("Columnas disponibles:", list(licitaciones_df.columns))
        return {}
        
    if 'numero_licitacion' not in ordenes_df.columns:
        st.error("Error: No se encontró la columna 'numero_licitacion' en el archivo de órdenes.")
        st.write("Columnas disponibles:", list(ordenes_df.columns))
        return {}
    
    # Diccionario para almacenar los DataFrames de control
    controles = {}
    
    # Procesar cada licitación
    for _, licitacion in licitaciones_df.iterrows():
        numero_licitacion = licitacion["numero_licitacion"]
        
        # Convertir valores de pandas a Python nativos para evitar problemas de serialización
        fecha_inicio = licitacion.get("fecha_inicio")
        if isinstance(fecha_inicio, (pd.Timestamp, datetime)):
            fecha_inicio = fecha_inicio.strftime('%Y-%m-%d')
            
        fecha_final = licitacion.get("fecha_final")
        if isinstance(fecha_final, (pd.Timestamp, datetime)):
            fecha_final = fecha_final.strftime('%Y-%m-%d')
            
        presupuesto_total = float(licitacion.get("presupuesto_total", 0))
        
        # Crear estructura base de control
        control = {
            "resumen": {
                "numero_licitacion": str(numero_licitacion),
                "nombre": str(licitacion.get("nombre_licitaciones", "Sin nombre")),
                "fecha_inicio": fecha_inicio,
                "fecha_final": fecha_final,
                "presupuesto_total": presupuesto_total,
                "presupuesto_ejecutado": 0,
                "presupuesto_comprometido": 0,  # Órdenes enviadas pero sin certificado
                "presupuesto_certificado": 0,   # Órdenes con certificado
                "presupuesto_disponible": presupuesto_total,
                "porcentaje_ejecucion": 0,
                "porcentaje_certificacion": 0,  # Nuevo indicador
                "estado": "Activa"
            },
            "historial": []
        }
        
        # Filtrar órdenes de esta licitación
        ordenes_licitacion = ordenes_df[ordenes_df["numero_licitacion"] == numero_licitacion]
        
        if not ordenes_licitacion.empty:
            # Ordenar por fecha si existe la columna fecha_envio_oc
            if "fecha_envio_oc" in ordenes_licitacion.columns:
                ordenes_licitacion = ordenes_licitacion.sort_values(by="fecha_envio_oc")
            
            # Asegurar que existe la columna estado
            if "estado" not in ordenes_licitacion.columns:
                st.warning(f"La columna 'estado' no existe en las órdenes. Se asumirá que todas están aceptadas.")
                ordenes_licitacion["estado"] = "Recepcion Conforme"
            
            # Asegurar que existe la columna certificado
            if "certificado" not in ordenes_licitacion.columns:
                ordenes_licitacion["certificado"] = "NO"
            
            # Calcular montos por estado (con manejo seguro de valores)
            try:
                # Normalizar valores de estado
                ordenes_licitacion["estado"] = ordenes_licitacion["estado"].astype(str).str.lower()
                
                # Normalizar valores de certificado
                ordenes_licitacion["certificado"] = ordenes_licitacion["certificado"].astype(str).str.upper()
                
                # Filtrar órdenes aceptadas
                ordenes_aceptadas = ordenes_licitacion[
                    ordenes_licitacion["estado"].str.contains("aceptada|conforme|recepcion", case=False, na=False)
                ]
                
                # Calcular montos
                presupuesto_comprometido = float(ordenes_aceptadas[
                    ordenes_aceptadas["certificado"] != "SÍ"
                ]["total"].sum())
                
                presupuesto_certificado = float(ordenes_aceptadas[
                    ordenes_aceptadas["certificado"] == "SÍ"
                ]["total"].sum())
                
                # Actualizar resumen
                control["resumen"]["presupuesto_comprometido"] = presupuesto_comprometido
                control["resumen"]["presupuesto_certificado"] = presupuesto_certificado
                control["resumen"]["presupuesto_ejecutado"] = presupuesto_comprometido + presupuesto_certificado
                control["resumen"]["presupuesto_disponible"] = control["resumen"]["presupuesto_total"] - control["resumen"]["presupuesto_ejecutado"]
                
                # Calcular porcentajes con manejo de divisiones por cero
                if control["resumen"]["presupuesto_total"] > 0:
                    control["resumen"]["porcentaje_ejecucion"] = float((control["resumen"]["presupuesto_ejecutado"] / control["resumen"]["presupuesto_total"]) * 100)
                    if control["resumen"]["presupuesto_ejecutado"] > 0:
                        control["resumen"]["porcentaje_certificacion"] = float((presupuesto_certificado / control["resumen"]["presupuesto_ejecutado"]) * 100)
            except Exception as e:
                st.warning(f"Error al calcular montos para la licitación {numero_licitacion}: {e}")
            
            # Determinar estado
            if control["resumen"]["presupuesto_disponible"] <= 0:
                control["resumen"]["estado"] = "Completada"
            else:
                try:
                    fecha_final_dt = pd.to_datetime(fecha_final, errors='coerce')
                    if fecha_final_dt is not pd.NaT and fecha_final_dt < datetime.now():
                        control["resumen"]["estado"] = "Vencida"
                except:
                    pass
            
            # Generar historial de movimientos
            try:
                saldo = control["resumen"]["presupuesto_total"]
                for _, orden in ordenes_aceptadas.iterrows():
                    # Convertir valores a tipos Python nativos
                    fecha_orden = orden.get("fecha_envio_oc")
                    if isinstance(fecha_orden, (pd.Timestamp, datetime)):
                        fecha_orden = fecha_orden.strftime('%Y-%m-%d')
                    
                    monto = float(orden.get("total", 0))
                    saldo_anterior = float(saldo)
                    saldo -= monto
                    
                    # Calcular porcentaje acumulado
                    porcentaje_acumulado = 0
                    if control["resumen"]["presupuesto_total"] > 0:
                        porcentaje_acumulado = float(((control["resumen"]["presupuesto_total"] - saldo) / control["resumen"]["presupuesto_total"]) * 100)
                    
                    # Agregar al historial
                    control["historial"].append({
                        "fecha": fecha_orden,
                        "orden_compra": str(orden.get("orden_de_compra", "")),
                        "proveedor": str(orden.get("proveedor", "")),
                        "descripcion": str(orden.get("nombre_orden", "")),
                        "monto": monto,
                        "saldo_anterior": saldo_anterior,
                        "saldo_disponible": float(saldo),
                        "certificado": str(orden.get("certificado", "NO")),
                        "porcentaje_acumulado": porcentaje_acumulado
                    })
            except Exception as e:
                st.warning(f"Error al generar historial para la licitación {numero_licitacion}: {e}")
        
        controles[str(numero_licitacion)] = control
    
    return controles

def generar_control_de_ordenes(ordenes_df):
    """
    Genera el archivo `control_de_ordenes_de_compra.xlsx` con las órdenes separadas en hojas,
    cada una nombrada por el número de licitación.
    """
    # Asegurar que la carpeta data existe
    os.makedirs("data", exist_ok=True)
    
    # Asegurar que la columna 'numero_licitacion' existe
    if 'numero_licitacion' not in ordenes_df.columns:
        st.error("Error: La columna 'numero_licitacion' no existe en el DataFrame de órdenes.")
        st.write("Columnas disponibles:", list(ordenes_df.columns))
        return False
    
    # Agrupar las órdenes por número de licitación
    return guardar_dataframe_por_hojas(
        ordenes_df, 
        PERSISTENT_ORDERS_FILE, 
        "numero_licitacion",
        "xlsxwriter"
    )

def generar_control_de_gasto(controles):
    """
    Genera el archivo `control_de_gasto_de_licitaciones.xlsx` y el resumen en JSON
    basado en el control avanzado de gastos.
    """
    # Asegurar que la carpeta data existe
    os.makedirs("data", exist_ok=True)
    
    # Verificar si hay controles
    if not controles:
        st.error("No hay datos de control para generar el archivo.")
        return False
    
    # Crear un DataFrame para cada licitación
    hojas = {}
    resumenes = []
    
    for numero_licitacion, control in controles.items():
        # Extraer el resumen para guardarlo en JSON
        resumenes.append(control["resumen"])
        
        # Crear DataFrame con el historial
        historial_df = pd.DataFrame(control["historial"]) if control["historial"] else pd.DataFrame()
        
        # Crear DataFrame con el resumen
        resumen_df = pd.DataFrame([control["resumen"]])
        
        # Si hay historial, combinarlo con el resumen
        if not historial_df.empty:
            # Asegurar que todas las columnas del resumen estén presentes
            for col in resumen_df.columns:
                if col not in historial_df.columns:
                    historial_df[col] = None
            
            # Combinar resumen con historial
            hoja_df = pd.concat([resumen_df, historial_df], ignore_index=True)
        else:
            hoja_df = resumen_df
        
        # Guardar en el diccionario de hojas
        hojas[numero_licitacion] = hoja_df
    
    # Guardar el archivo Excel con múltiples hojas
    try:
        with pd.ExcelWriter(PERSISTENT_EXPENSES_FILE, engine="xlsxwriter") as writer:
            for sheet_name, df in hojas.items():
                # Limitar nombre de hoja a 31 caracteres (límite de Excel)
                sheet_name_clean = str(sheet_name)[:31]
                df.to_excel(writer, index=False, sheet_name=sheet_name_clean)
    except Exception as e:
        st.error(f"Error al guardar el archivo Excel: {e}")
        return False
    
    # Guardar el resumen en formato JSON con el manejador personalizado
    try:
        with open(CONTROL_SUMMARY_FILE, 'w', encoding='utf-8') as f:
            json.dump(resumenes, f, default=json_serial, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Error al guardar el archivo JSON: {e}")
        return False
    
    return True

def pagina_2():
    st.title("Página 2: Control de Órdenes y Gasto de Licitaciones")
    
    # Crear contenedores para organizar la interfaz
    upload_container = st.container()
    processing_container = st.container()
    results_container = st.container()
    
    with upload_container:
        st.header("Subir Archivos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Archivo de Licitaciones")
            licitaciones_file = st.file_uploader(
                "Sube el archivo de licitaciones (Excel)",
                type=["xlsx"],
                key="licitaciones_file"
            )
            
            if licitaciones_file:
                st.success(f"Archivo subido: {licitaciones_file.name}")
        
        with col2:
            st.subheader("Archivo de Órdenes de Compra")
            ordenes_file = st.file_uploader(
                "Sube el archivo de órdenes de compra (Excel generado en Página 1)",
                type=["xlsx"],
                key="ordenes_file"
            )
            
            if ordenes_file:
                st.success(f"Archivo subido: {ordenes_file.name}")
    
    # Solo mostrar el resto si se han subido ambos archivos
    if licitaciones_file and ordenes_file:
        with processing_container:
            st.header("Procesar Datos")
            
            # Mostrar opciones de configuración
            with st.expander("Opciones de configuración"):
                col1, col2 = st.columns(2)
                with col1:
                    licitaciones_sheet = st.text_input("Hoja de licitaciones", "Hoja1")
                with col2:
                    ordenes_sheet = st.text_input("Hoja de órdenes", "Sheet1")
            
            # Botón para procesar
            if st.button("Procesar Archivos y Generar Control de Gastos", type="primary"):
                with st.spinner("Procesando archivos..."):
                    try:
                        # Leer el archivo de licitaciones
                        try:
                            licitaciones_df = pd.read_excel(licitaciones_file, sheet_name=licitaciones_sheet, engine="openpyxl")
                            st.info(f"Licitaciones: Se encontraron {len(licitaciones_df)} registros")
                        except Exception as e:
                            st.error(f"Error al leer el archivo de licitaciones: {e}")
                            # Intentar leer la primera hoja disponible
                            excel = pd.ExcelFile(licitaciones_file, engine="openpyxl")
                            st.warning(f"Intentando con la primera hoja disponible: {excel.sheet_names[0]}")
                            licitaciones_df = pd.read_excel(licitaciones_file, sheet_name=excel.sheet_names[0], engine="openpyxl")
                        
                        # Mostrar primeras filas de licitaciones
                        st.write("Vista previa de licitaciones:")
                        st.dataframe(licitaciones_df.head())
                        
                        # Mapear columnas de licitaciones
                        mapeo_licitaciones = {
                            "número licitación": "numero_licitacion",
                            "número_licitación": "numero_licitacion",
                            "numero licitación": "numero_licitacion",
                            "numero licitacion": "numero_licitacion",
                            "nombre licitaciones": "nombre_licitaciones",
                            "nombre_licitaciones": "nombre_licitaciones",
                            "nombre licitacion": "nombre_licitaciones",
                            "fecha inicio": "fecha_inicio",
                            "fecha_inicio": "fecha_inicio",
                            "fecha final": "fecha_final",
                            "fecha_final": "fecha_final",
                            "presupuesto total": "presupuesto_total",
                            "presupuesto_total": "presupuesto_total"
                        }
                        licitaciones_df = normalizar_dataframe(licitaciones_df, mapeo_licitaciones)
                        
                        # Leer el archivo de órdenes
                        try:
                            ordenes_df = pd.read_excel(ordenes_file, sheet_name=ordenes_sheet, engine="openpyxl")
                            st.info(f"Órdenes: Se encontraron {len(ordenes_df)} registros")
                        except Exception as e:
                            st.error(f"Error al leer el archivo de órdenes: {e}")
                            # Intentar leer la primera hoja disponible
                            excel = pd.ExcelFile(ordenes_file, engine="openpyxl")
                            st.warning(f"Intentando con la primera hoja disponible: {excel.sheet_names[0]}")
                            ordenes_df = pd.read_excel(ordenes_file, sheet_name=excel.sheet_names[0], engine="openpyxl")
                        
                        # Mostrar primeras filas de órdenes
                        st.write("Vista previa de órdenes:")
                        st.dataframe(ordenes_df.head())
                        
                        # Mapear columnas de órdenes
                        mapeo_ordenes = {
                            "número licitación": "numero_licitacion",
                            "número_licitación": "numero_licitacion",
                            "numero licitación": "numero_licitacion",
                            "numero licitacion": "numero_licitacion",
                            "número licitacion": "numero_licitacion",
                            "orden de compra": "orden_de_compra",
                            "orden_de_compra": "orden_de_compra",
                            "estado": "estado",
                            "proveedor": "proveedor",
                            "rut proveedor": "rut_proveedor",
                            "rut_proveedor": "rut_proveedor",
                            "nombre orden": "nombre_orden",
                            "nombre_orden": "nombre_orden",
                            "fecha envío oc": "fecha_envio_oc",
                            "fecha_envío_oc": "fecha_envio_oc",
                            "fecha envio oc": "fecha_envio_oc",
                            "fecha_envio_oc": "fecha_envio_oc",
                            "total": "total"
                        }
                        ordenes_df = normalizar_dataframe(ordenes_df, mapeo_ordenes)
                        
                        # Mostrar las columnas normalizadas
                        st.write("Columnas normalizadas de licitaciones:", list(licitaciones_df.columns))
                        st.write("Columnas normalizadas de órdenes:", list(ordenes_df.columns))
                        
                        # Asegurar que existe la columna certificado
                        if "certificado" not in ordenes_df.columns:
                            ordenes_df["certificado"] = "NO"
                        
                        # Generar control avanzado de gastos
                        controles = control_avanzado_de_gastos(licitaciones_df, ordenes_df)
                        
                        # Verificar si se generaron controles
                        if not controles:
                            st.error("No se pudieron generar controles de gastos.")
                            return
                        
                        # Generar archivo de control de órdenes
                        exito_ordenes = generar_control_de_ordenes(ordenes_df)
                        
                        # Generar archivo de control de gastos
                        exito_gastos = generar_control_de_gasto(controles)
                        
                        if exito_ordenes and exito_gastos:
                            st.success("✅ Archivos de control generados correctamente.")
                            
                            # Mostrar resumen
                            with results_container:
                                mostrar_resultados_control(controles)
                        else:
                            st.error("❌ Error al generar los archivos de control.")
                    
                    except Exception as e:
                        st.error(f"❌ Error al procesar los archivos: {e}")
                        import traceback
                        st.error(f"Detalles: {traceback.format_exc()}")

def mostrar_resultados_control(controles):
    """
    Muestra los resultados del control de gastos en la interfaz.
    """
    st.header("Resultados del Control de Gastos")
    
    # Crear pestañas para cada licitación
    if controles:
        tabs = st.tabs([f"Licitación {num}" for num in controles.keys()])
        
        for i, (numero_licitacion, control) in enumerate(controles.items()):
            with tabs[i]:
                # Mostrar resumen
                resumen = control["resumen"]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Información de la Licitación")
                    st.markdown(f"**Número:** {resumen['numero_licitacion']}")
                    st.markdown(f"**Nombre:** {resumen['nombre']}")
                    st.markdown(f"**Periodo:** {resumen['fecha_inicio']} al {resumen['fecha_final']}")
                    st.markdown(f"**Estado:** {resumen['estado']}")
                
                with col2:
                    st.subheader("Resumen Financiero")
                    st.markdown(f"**Presupuesto Total:** ${resumen['presupuesto_total']:,.0f}")
                    st.markdown(f"**Ejecutado:** ${resumen['presupuesto_ejecutado']:,.0f} ({resumen['porcentaje_ejecucion']:.2f}%)")
                    st.markdown(f"**Con Certificado:** ${resumen['presupuesto_certificado']:,.0f} ({resumen['porcentaje_certificacion']:.2f}%)")
                    st.markdown(f"**Comprometido sin Certificado:** ${resumen['presupuesto_comprometido']:,.0f}")
                    st.markdown(f"**Disponible:** ${resumen['presupuesto_disponible']:,.0f}")
                
                # Mostrar historial
                st.subheader("Historial de Movimientos")
                
                if control["historial"]:
                    historial_df = pd.DataFrame(control["historial"])
                    
                    # Añadir formato a las columnas numéricas
                    for col in ["monto", "saldo_anterior", "saldo_disponible"]:
                        if col in historial_df.columns:
                            historial_df[col] = historial_df[col].apply(lambda x: f"${x:,.0f}" if pd.notnull(x) else "-")
                    
                    if "porcentaje_acumulado" in historial_df.columns:
                        historial_df["porcentaje_acumulado"] = historial_df["porcentaje_acumulado"].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else "-")
                    
                    st.dataframe(historial_df)
                else:
                    st.info("No hay movimientos registrados para esta licitación.")
    
    # Botones para descargar los archivos generados
    col1, col2 = st.columns(2)
    
    with col1:
        if os.path.exists(PERSISTENT_EXPENSES_FILE):
            with open(PERSISTENT_EXPENSES_FILE, "rb") as f:
                st.download_button(
                    label="📥 Descargar Control de Gasto de Licitaciones",
                    data=f,
                    file_name="control_de_gasto_de_licitaciones.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
    with col2:
        if os.path.exists(PERSISTENT_ORDERS_FILE):
            with open(PERSISTENT_ORDERS_FILE, "rb") as f:
                st.download_button(
                    label="📥 Descargar Control de Órdenes de Compra",
                    data=f,
                    file_name="control_de_ordenes_de_compra.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )