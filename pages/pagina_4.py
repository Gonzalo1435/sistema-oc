import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import json
from io import BytesIO
import numpy as np
from datetime import datetime

# Archivos de entrada
ORDENES_FILE = "data/control_de_ordenes_de_compra.xlsx"
GASTOS_FILE = "data/control_de_gasto_de_licitaciones.xlsx"
CONTROL_SUMMARY_FILE = "data/resumen_control_licitaciones.json"
CERTIFICADOS_LOG_FILE = "data/registro_certificados.json"

def cargar_datos():
    """
    Carga todos los datos necesarios para la página 4.
    
    Returns:
        tuple: Tupla con (ordenes_df, gastos_df, resumenes, certificados, licitaciones_disponibles)
    """
    # Validar si ambos archivos existen
    if not (os.path.exists(ORDENES_FILE) and os.path.exists(GASTOS_FILE)):
        return None, None, None, None, []
    
    try:
        # Cargar datos de órdenes
        ordenes_excel = pd.ExcelFile(ORDENES_FILE)
        ordenes_sheets = []
        
        # Obtener lista de licitaciones disponibles
        licitaciones_disponibles = ordenes_excel.sheet_names
        
        for sheet in ordenes_excel.sheet_names:
            sheet_df = ordenes_excel.parse(sheet)
            sheet_df["numero_licitacion"] = sheet
            ordenes_sheets.append(sheet_df)
        
        ordenes_df = pd.concat(ordenes_sheets, ignore_index=True)
        
        # Cargar datos de gastos
        gastos_excel = pd.ExcelFile(GASTOS_FILE)
        gastos_sheets = []
        
        for sheet in gastos_excel.sheet_names:
            sheet_df = gastos_excel.parse(sheet)
            sheet_df["numero_licitacion"] = sheet
            gastos_sheets.append(sheet_df)
        
        gastos_df = pd.concat(gastos_sheets, ignore_index=True)
        
        # Cargar resúmenes y certificados
        resumenes = []
        if os.path.exists(CONTROL_SUMMARY_FILE):
            with open(CONTROL_SUMMARY_FILE, 'r', encoding='utf-8') as f:
                resumenes = json.load(f)
        
        certificados = []
        if os.path.exists(CERTIFICADOS_LOG_FILE):
            with open(CERTIFICADOS_LOG_FILE, 'r', encoding='utf-8') as f:
                certificados = json.load(f)
        
        return ordenes_df, gastos_df, resumenes, certificados, licitaciones_disponibles
    
    except Exception as e:
        st.error(f"Error al cargar los datos: {e}")
        return None, None, None, None, []

def filtrar_datos_por_licitacion(ordenes_df, gastos_df, resumenes, certificados, licitacion):
    """
    Filtra todos los datos para mostrar solo la licitación seleccionada
    
    Returns:
        tuple: Datos filtrados por licitación
    """
    # Filtrar órdenes
    if ordenes_df is not None and not ordenes_df.empty:
        ordenes_filtradas = ordenes_df[ordenes_df["numero_licitacion"] == licitacion]
    else:
        ordenes_filtradas = pd.DataFrame()
        
    # Filtrar gastos
    if gastos_df is not None and not gastos_df.empty:
        gastos_filtrados = gastos_df[gastos_df["numero_licitacion"] == licitacion]
    else:
        gastos_filtrados = pd.DataFrame()
        
    # Filtrar resúmenes
    resumenes_filtrados = [r for r in resumenes if r.get("numero_licitacion") == licitacion]
    
    # Filtrar certificados
    certificados_filtrados = [c for c in certificados if c.get("licitacion") == licitacion]
    
    return ordenes_filtradas, gastos_filtrados, resumenes_filtrados, certificados_filtrados

def visualizar_distribucion_presupuesto(resumenes, titulo="Distribución del Presupuesto por Licitación"):
    """
    Genera un gráfico de barras apiladas que muestra la distribución del presupuesto
    entre certificado, comprometido y disponible para cada licitación.
    """
    if not resumenes:
        st.info("No hay datos de resúmenes disponibles.")
        return
    
    # Preparar datos para el gráfico
    licitaciones = []
    presupuesto_certificado = []
    presupuesto_comprometido = []
    presupuesto_disponible = []
    
    for resumen in resumenes:
        licitaciones.append(resumen.get("numero_licitacion", ""))
        presupuesto_certificado.append(resumen.get("presupuesto_certificado", 0))
        
        # Calcular el comprometido (ejecutado - certificado)
        comprometido = resumen.get("presupuesto_ejecutado", 0) - resumen.get("presupuesto_certificado", 0)
        presupuesto_comprometido.append(comprometido)
        
        presupuesto_disponible.append(resumen.get("presupuesto_disponible", 0))
    
    # Crear gráfico
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Crear barras apiladas
    width = 0.8
    
    # Barras para cada categoría
    ax.bar(licitaciones, presupuesto_disponible, width, label='Disponible', color='lightgray')
    ax.bar(licitaciones, presupuesto_comprometido, width, bottom=presupuesto_disponible, 
          label='Comprometido', color='skyblue')
    ax.bar(licitaciones, presupuesto_certificado, width, 
          bottom=np.array(presupuesto_disponible) + np.array(presupuesto_comprometido), 
          label='Certificado', color='lightgreen')
    
    # Configuración del gráfico
    ax.set_title(titulo)
    ax.set_xlabel('Número de Licitación')
    ax.set_ylabel('Monto ($)')
    ax.legend()
    
    # Rotar etiquetas del eje x si hay muchas licitaciones
    if len(licitaciones) > 5:
        plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    
    return fig

def visualizar_ordenes_certificadas(ordenes_df, titulo="Órdenes de Compra: Con y Sin Certificado"):
    """
    Genera un gráfico circular que muestra la proporción de órdenes con y sin certificado.
    """
    if ordenes_df is None or ordenes_df.empty:
        st.info("No hay datos de órdenes disponibles.")
        return
    
    # Normalizar columnas
    ordenes_df.columns = [col.lower() for col in ordenes_df.columns]
    
    # Verificar si existe la columna 'certificado'
    if 'certificado' not in ordenes_df.columns:
        st.warning("El archivo de órdenes no contiene la columna 'Certificado'.")
        return
    
    # Contar órdenes con y sin certificado
    ordenes_df['certificado'] = ordenes_df['certificado'].astype(str).str.upper()
    con_certificado = (ordenes_df['certificado'] == 'SÍ').sum()
    sin_certificado = len(ordenes_df) - con_certificado
    
    # Si no hay órdenes, no mostrar gráfico
    if con_certificado == 0 and sin_certificado == 0:
        st.info("No hay órdenes para mostrar en el gráfico.")
        return None
    
    # Crear gráfico
    fig, ax = plt.subplots(figsize=(6, 6))
    
    # Datos y etiquetas
    sizes = [con_certificado, sin_certificado]
    labels = ['Con Certificado', 'Sin Certificado']
    colors = ['lightgreen', 'salmon']
    explode = (0.1, 0)  # Resaltar el sector "Con Certificado"
    
    # Crear el gráfico circular
    ax.pie(sizes, explode=explode, labels=labels, colors=colors,
          autopct='%1.1f%%', shadow=True, startangle=90)
    
    # Ajustar aspecto
    ax.axis('equal')
    ax.set_title(titulo)
    
    plt.tight_layout()
    
    return fig

def visualizar_tendencia_gastos(gastos_df, titulo="Tendencia de Gastos Ejecutados por Mes"):
    """
    Genera un gráfico de línea que muestra la tendencia de los gastos ejecutados a lo largo del tiempo.
    """
    if gastos_df is None or gastos_df.empty:
        st.info("No hay datos de gastos disponibles.")
        return
    
    # Normalizar columnas
    gastos_df.columns = [col.lower() for col in gastos_df.columns]
    
    # Verificar si existen las columnas necesarias
    if 'fecha' not in gastos_df.columns or 'monto' not in gastos_df.columns:
        # Intentar con otros nombres de columna comunes
        fecha_col = None
        monto_col = None
        
        for col in gastos_df.columns:
            if 'fecha' in col.lower():
                fecha_col = col
            elif 'monto' in col.lower() or 'ejecutado' in col.lower():
                monto_col = col
        
        if fecha_col is None or monto_col is None:
            st.warning("No se pueden identificar las columnas de fecha y monto en el archivo de gastos.")
            return
    else:
        fecha_col = 'fecha'
        monto_col = 'monto'
    
    # Preparar datos para gráfico
    try:
        # Convertir la columna de fecha a datetime
        gastos_df[fecha_col] = pd.to_datetime(gastos_df[fecha_col], errors='coerce')
        
        # Filtrar filas donde la fecha no es NaT
        gastos_df = gastos_df.dropna(subset=[fecha_col])
        
        # Si no hay datos después de filtrar, retornar
        if gastos_df.empty:
            st.info("No hay datos de fechas válidas para generar el gráfico.")
            return None
        
        # Agrupar por mes y sumar montos
        gastos_df['mes'] = gastos_df[fecha_col].dt.strftime('%Y-%m')
        gastos_mensuales = gastos_df.groupby('mes')[monto_col].sum().reset_index()
        
        # Si no hay datos agrupados, retornar
        if gastos_mensuales.empty:
            st.info("No hay datos mensuales para generar el gráfico.")
            return None
        
        # Ordenar por mes
        gastos_mensuales = gastos_mensuales.sort_values('mes')
        
        # Crear gráfico
        fig, ax = plt.subplots(figsize=(10, 5))
        
        # Gráfico de línea
        ax.plot(gastos_mensuales['mes'], gastos_mensuales[monto_col], marker='o', 
               linewidth=2, markersize=8, color='#1E88E5')
        
        # Configuración del gráfico
        ax.set_title(titulo)
        ax.set_xlabel('Mes')
        ax.set_ylabel('Monto Ejecutado ($)')
        
        # Rotar etiquetas del eje x
        plt.xticks(rotation=45, ha='right')
        
        # Añadir valores sobre los puntos
        for i, v in enumerate(gastos_mensuales[monto_col]):
            ax.text(i, v + 0.5, f"${v:,.0f}", ha='center')
        
        plt.tight_layout()
        
        return fig
    
    except Exception as e:
        st.warning(f"No se pudo generar el gráfico de tendencia de gastos: {e}")
        return None

def mostrar_tabla_certificados(ordenes_df, certificados, titulo="Órdenes de Compra con Certificados Generados"):
    """
    Muestra una tabla con información de los certificados generados.
    """
    if ordenes_df is None or ordenes_df.empty:
        st.info("No hay datos de órdenes disponibles.")
        return
    
    # Normalizar columnas
    ordenes_df.columns = [col.lower() for col in ordenes_df.columns]
    
    # Verificar si existe la columna 'certificado'
    if 'certificado' not in ordenes_df.columns:
        st.warning("El archivo de órdenes no contiene la columna 'Certificado'.")
        return
    
    # Filtrar órdenes con certificado
    ordenes_df['certificado'] = ordenes_df['certificado'].astype(str).str.upper()
    ordenes_certificadas = ordenes_df[ordenes_df['certificado'] == 'SÍ']
    
    if ordenes_certificadas.empty:
        st.info("No se encontraron órdenes con certificado generado.")
        return
    
    # Mostrar tabla de órdenes certificadas
    st.subheader(titulo)
    
    # Seleccionar columnas relevantes
    columnas_mostrar = [
        'orden_de_compra', 'proveedor', 'rut_proveedor', 
        'nombre_orden', 'fecha_envio_oc', 'total',
        'numero_licitacion'
    ]
    
    # Filtrar columnas que existen en el DataFrame
    columnas_existentes = [col for col in columnas_mostrar if col in ordenes_certificadas.columns]
    
    # Mostrar tabla
    st.dataframe(ordenes_certificadas[columnas_existentes])
    
    # Mostrar registro de certificados si existe
    if certificados:
        st.subheader("Registro de Certificados Generados")
        
        # Crear DataFrame con la información de los certificados
        registro_df = pd.DataFrame(certificados)
        
        # Ordenar por fecha de generación
        if 'fecha_generacion' in registro_df.columns:
            registro_df = registro_df.sort_values('fecha_generacion', ascending=False)
        
        st.dataframe(registro_df)
    
    return ordenes_certificadas

def generar_archivo_control_certificados(ordenes_certificadas, gastos_df):
    """
    Genera un archivo de control de gastos solo con las órdenes certificadas.
    
    Args:
        ordenes_certificadas: DataFrame con las órdenes certificadas
        gastos_df: DataFrame con todos los gastos
        
    Returns:
        BytesIO: Archivo Excel en memoria con el control de gastos de certificados
    """
    if ordenes_certificadas is None or ordenes_certificadas.empty or gastos_df is None or gastos_df.empty:
        return None
    
    try:
        # Normalizar columnas
        gastos_df.columns = [col.lower() for col in gastos_df.columns]
        ordenes_certificadas.columns = [col.lower() for col in ordenes_certificadas.columns]
        
        # Filtrar gastos que corresponden a órdenes certificadas
        if 'orden_de_compra' in gastos_df.columns and 'orden_de_compra' in ordenes_certificadas.columns:
            gastos_certificados = gastos_df[gastos_df['orden_de_compra'].isin(ordenes_certificadas['orden_de_compra'])]
        elif 'orden_compra' in gastos_df.columns and 'orden_de_compra' in ordenes_certificadas.columns:
            gastos_certificados = gastos_df[gastos_df['orden_compra'].isin(ordenes_certificadas['orden_de_compra'])]
        else:
            st.warning("No se pueden relacionar las órdenes certificadas con los gastos.")
            return None
        
        if gastos_certificados.empty:
            st.info("No hay gastos relacionados con las órdenes certificadas.")
            return None
        
        # Generar archivo Excel
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            # Agrupar por licitación
            for numero_licitacion, grupo in gastos_certificados.groupby('numero_licitacion'):
                # Limitar nombre de hoja a 31 caracteres (límite de Excel)
                sheet_name = str(numero_licitacion)[:31]
                grupo.to_excel(writer, sheet_name=sheet_name, index=False)
        
        output.seek(0)
        return output
    
    except Exception as e:
        st.error(f"Error al generar el archivo de control de gastos certificados: {e}")
        return None

def pagina_4():
    st.title("Página 4: Control de Gastos y Certificados Generados")
    
    # Cargar datos
    ordenes_df, gastos_df, resumenes, certificados, licitaciones_disponibles = cargar_datos()
    
    # Verificar si se pudieron cargar los datos
    if ordenes_df is None or gastos_df is None:
        st.error("No se encontraron los archivos necesarios. Por favor, verifica la Página 1 y la Página 2.")
        return
    
    # Selector de visualización
    visualizacion_mode = st.radio(
        "Selecciona el modo de visualización:",
        ["Todas las licitaciones", "Licitación específica"],
        horizontal=True
    )
    
    # Si se selecciona una licitación específica, mostrar selector
    licitacion_seleccionada = None
    if visualizacion_mode == "Licitación específica":
        licitacion_seleccionada = st.selectbox(
            "Selecciona una licitación:",
            licitaciones_disponibles
        )
        
        # Filtrar datos por licitación seleccionada
        if licitacion_seleccionada:
            ordenes_licitacion, gastos_licitacion, resumenes_licitacion, certificados_licitacion = filtrar_datos_por_licitacion(
                ordenes_df, gastos_df, resumenes, certificados, licitacion_seleccionada
            )
            
            # Actualizar los datos para mostrar solo la licitación seleccionada
            ordenes_filtradas = ordenes_licitacion
            gastos_filtrados = gastos_licitacion
            resumenes_filtrados = resumenes_licitacion
            certificados_filtrados = certificados_licitacion
            
            # Mostrar información de la licitación seleccionada
            st.subheader(f"Información de la Licitación: {licitacion_seleccionada}")
            
            # Buscar el resumen de esta licitación
            if resumenes_licitacion:
                resumen = resumenes_licitacion[0]
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Presupuesto Total", f"${resumen.get('presupuesto_total', 0):,.0f}")
                
                with col2:
                    st.metric("Ejecutado", f"${resumen.get('presupuesto_ejecutado', 0):,.0f} ({resumen.get('porcentaje_ejecucion', 0):.1f}%)")
                
                with col3:
                    st.metric("Disponible", f"${resumen.get('presupuesto_disponible', 0):,.0f}")
    else:
        # Usar todos los datos si se selecciona "Todas las licitaciones"
        ordenes_filtradas = ordenes_df
        gastos_filtrados = gastos_df
        resumenes_filtrados = resumenes
        certificados_filtrados = certificados
    
    # Mostrar pestañas para organizar la información
    tab1, tab2, tab3 = st.tabs(["Certificados Generados", "Visualizaciones", "Exportar Datos"])
    
    with tab1:
        # Mostrar tabla de certificados
        if visualizacion_mode == "Licitación específica":
            titulo_certificados = f"Órdenes de Compra con Certificados Generados - {licitacion_seleccionada}"
        else:
            titulo_certificados = "Órdenes de Compra con Certificados Generados"
        ordenes_certificadas = mostrar_tabla_certificados(ordenes_filtradas, certificados_filtrados, titulo_certificados)
        
        # Generar y descargar archivo de control de gastos de certificados
        if ordenes_certificadas is not None and not ordenes_certificadas.empty:
            st.subheader("Descargar Control de Gastos Certificados")
            
            gastos_certificados_file = generar_archivo_control_certificados(ordenes_certificadas, gastos_filtrados)
            
            if gastos_certificados_file is not None:
                sufijo = f"_{licitacion_seleccionada}" if licitacion_seleccionada else ""
                st.download_button(
                    label="📥 Descargar Control de Gastos Certificados",
                    data=gastos_certificados_file,
                    file_name=f"control_gastos_certificados{sufijo}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
    
    with tab2:
        st.header("Visualizaciones")
        
        # Mostrar gráfico de distribución del presupuesto
        if visualizacion_mode == "Licitación específica":
            titulo_distribucion = f"Distribución del Presupuesto - {licitacion_seleccionada}"
        else:
            titulo_distribucion = "Distribución del Presupuesto por Licitación"
        st.subheader(titulo_distribucion)
        fig1 = visualizar_distribucion_presupuesto(resumenes_filtrados, titulo_distribucion)
        if fig1:
            st.pyplot(fig1)
        
        # Dividir en dos columnas
        col1, col2 = st.columns(2)
        
        with col1:
            # Mostrar gráfico de órdenes certificadas vs no certificadas
            if visualizacion_mode == "Licitación específica":
                titulo_ordenes = f"Órdenes de Compra: Con y Sin Certificado - {licitacion_seleccionada}"
            else:
                titulo_ordenes = "Órdenes de Compra: Con y Sin Certificado"
            st.subheader(titulo_ordenes)
            fig2 = visualizar_ordenes_certificadas(ordenes_filtradas, titulo_ordenes)
            if fig2:
                st.pyplot(fig2)
        
        with col2:
            # Mostrar gráfico de tendencia de gastos
            if visualizacion_mode == "Licitación específica":
                titulo_tendencia = f"Tendencia de Gastos Ejecutados - {licitacion_seleccionada}"
            else:
                titulo_tendencia = "Tendencia de Gastos Ejecutados"
            st.subheader(titulo_tendencia)
            fig3 = visualizar_tendencia_gastos(gastos_filtrados, titulo_tendencia)
            if fig3:
                st.pyplot(fig3)
    
    with tab3:
        st.header("Exportar Datos")
        
        # Descargar órdenes actualizadas
        st.subheader("Descargar Archivo Actualizado de Órdenes de Compra")
        
        if os.path.exists(ORDENES_FILE):
            with open(ORDENES_FILE, "rb") as f:
                st.download_button(
                    label="📥 Descargar Órdenes de Compra Actualizadas",
                    data=f,
                    file_name="ordenes_actualizadas.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
        
        # Descargar control de gastos
        st.subheader("Descargar Archivo de Control de Gastos")
        
        if os.path.exists(GASTOS_FILE):
            with open(GASTOS_FILE, "rb") as f:
                st.download_button(
                    label="📥 Descargar Control de Gastos",
                    data=f,
                    file_name="control_de_gastos.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
        
        # Si hay certificados, permitir descargar el registro
        if certificados_filtrados:
            st.subheader("Descargar Registro de Certificados")
            
            # Convertir a Excel
            registro_df = pd.DataFrame(certificados_filtrados)
            
            # Crear archivo en memoria
            output = BytesIO()
            registro_df.to_excel(output, index=False)
            output.seek(0)
            
            sufijo = f"_{licitacion_seleccionada}" if licitacion_seleccionada else ""
            st.download_button(
                label="📥 Descargar Registro de Certificados",
                data=output,
                file_name=f"registro_certificados{sufijo}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )