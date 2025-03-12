import streamlit as st
import pandas as pd
import os
from datetime import datetime
import json
import traceback
from utils.certificate_utils import generate_certificate
from utils.file_operations import consolidar_hojas_excel

# Rutas para los archivos persistentes generados en la página 2
GASTOS_FILE = "data/control_de_gasto_de_licitaciones.xlsx"
ORDENES_FILE = "data/control_de_ordenes_de_compra.xlsx"
CONTROL_SUMMARY_FILE = "data/resumen_control_licitaciones.json"
CERTIFICADOS_LOG_FILE = "data/registro_certificados.json"

def actualizar_estado_certificado(orden_compra, valor="SÍ"):
    """
    Actualiza el estado de certificación de una orden de compra en el archivo de control.
    Versión mejorada para asegurar que se establece correctamente el valor "SÍ".
    
    Args:
        orden_compra (str): Número de la orden de compra a actualizar.
        valor (str): Valor a establecer en la columna "Certificado" (por defecto "SÍ").
        
    Returns:
        bool: True si la actualización fue exitosa, False en caso contrario.
    """
    try:
        # Imprimir información de depuración
        st.write(f"Debug - Actualizando estado de certificado para orden: {orden_compra}")
        st.write(f"Debug - Valor a establecer: {valor}")
        
        # Cargar el archivo de órdenes
        ordenes_excel = pd.ExcelFile(ORDENES_FILE)
        hojas_actualizadas = {}
        orden_encontrada = False
        
        # Procesar cada hoja (licitación)
        for hoja in ordenes_excel.sheet_names:
            # Cargar la hoja
            df_hoja = ordenes_excel.parse(hoja)
            
            # Normalizar nombres de columnas
            df_hoja.columns = [col.lower().strip() for col in df_hoja.columns]
            
            # Imprimir información de depuración
            st.write(f"Debug - Procesando hoja: {hoja}")
            st.write(f"Debug - Columnas en la hoja: {list(df_hoja.columns)}")
            
            # Buscar la orden de compra en esta hoja
            if "orden_de_compra" in df_hoja.columns:
                # Convertir a string para comparación segura
                df_hoja["orden_de_compra"] = df_hoja["orden_de_compra"].astype(str)
                
                # Ver si la orden existe en esta hoja
                if orden_compra in df_hoja["orden_de_compra"].values:
                    st.write(f"Debug - Orden encontrada en hoja: {hoja}")
                    # Actualizar el estado del certificado
                    mask = df_hoja["orden_de_compra"] == orden_compra
                    
                    # Asegurar que existe la columna certificado
                    if "certificado" not in df_hoja.columns:
                        st.write("Debug - Agregando columna 'certificado' que no existía")
                        df_hoja["certificado"] = "NO"
                    
                    # Actualizar el valor
                    st.write(f"Debug - Actualizando {sum(mask)} filas con el valor: {valor}")
                    df_hoja.loc[mask, "certificado"] = valor
                    orden_encontrada = True
            
            # Guardar la hoja actualizada
            hojas_actualizadas[hoja] = df_hoja
        
        if not orden_encontrada:
            st.warning(f"La orden de compra '{orden_compra}' no se encontró en ninguna hoja del archivo.")
            return False
        
        # Guardar todas las hojas actualizadas al archivo
        st.write("Debug - Guardando archivo actualizado...")
        with pd.ExcelWriter(ORDENES_FILE, engine="openpyxl") as writer:
            for hoja, df in hojas_actualizadas.items():
                # Verificar si la columna certificado existe y tiene el valor esperado
                if "certificado" in df.columns:
                    certificados_si = sum(df["certificado"] == valor)
                    st.write(f"Debug - Hoja {hoja}: {certificados_si} órdenes con certificado = '{valor}'")
                df.to_excel(writer, sheet_name=hoja, index=False)
        
        st.success(f"✅ Estado de certificado actualizado correctamente para la orden {orden_compra}")
        return True
        
    except Exception as e:
        st.error(f"Error al actualizar el estado del certificado: {e}")
        st.error(traceback.format_exc())
        return False

def registrar_certificado(datos_certificado):
    """
    Registra los datos del certificado generado en un archivo JSON.
    
    Args:
        datos_certificado (dict): Diccionario con los datos del certificado.
        
    Returns:
        bool: True si el registro fue exitoso, False en caso contrario.
    """
    try:
        # Crear carpeta data si no existe
        os.makedirs("data", exist_ok=True)
        
        # Cargar registro existente o crear uno nuevo
        if os.path.exists(CERTIFICADOS_LOG_FILE):
            with open(CERTIFICADOS_LOG_FILE, 'r', encoding='utf-8') as f:
                registro = json.load(f)
        else:
            registro = []
        
        # Añadir fecha de generación
        datos_certificado["fecha_generacion"] = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        
        # Convertir cualquier objeto de pandas a tipos Python nativos
        for key, value in datos_certificado.items():
            if isinstance(value, pd.Timestamp):
                datos_certificado[key] = value.strftime("%Y-%m-%d")
        
        # Añadir nuevo certificado al registro
        registro.append(datos_certificado)
        
        # Guardar registro actualizado
        with open(CERTIFICADOS_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(registro, f, ensure_ascii=False, indent=2)
        
        return True
    
    except Exception as e:
        st.error(f"Error al registrar el certificado: {e}")
        st.error(traceback.format_exc())
        return False

def listar_licitaciones_disponibles():
    """
    Lista todas las licitaciones disponibles en los archivos de control.
    
    Returns:
        list: Lista de nombres de licitaciones disponibles
    """
    licitaciones = []
    
    # Verificar archivo de gastos
    if os.path.exists(GASTOS_FILE):
        try:
            gastos_data = pd.ExcelFile(GASTOS_FILE)
            licitaciones.extend(gastos_data.sheet_names)
        except Exception as e:
            st.warning(f"No se pudieron leer las licitaciones del archivo de gastos: {e}")
    
    # Verificar archivo de órdenes
    if os.path.exists(ORDENES_FILE):
        try:
            ordenes_data = pd.ExcelFile(ORDENES_FILE)
            licitaciones.extend(ordenes_data.sheet_names)
        except Exception as e:
            st.warning(f"No se pudieron leer las licitaciones del archivo de órdenes: {e}")
    
    # Eliminar duplicados y ordenar
    licitaciones = sorted(list(set(licitaciones)))
    
    return licitaciones

def cargar_ordenes_licitacion(licitacion):
    """
    Carga las órdenes de una licitación específica.
    
    Args:
        licitacion (str): Nombre de la licitación a cargar
        
    Returns:
        DataFrame: DataFrame con las órdenes de la licitación, o None si hay error
    """
    if not os.path.exists(ORDENES_FILE):
        st.error(f"El archivo de órdenes '{ORDENES_FILE}' no existe.")
        return None
    
    try:
        # Cargar el archivo Excel
        ordenes_excel = pd.ExcelFile(ORDENES_FILE)
        
        # Verificar si la licitación existe como hoja
        if licitacion not in ordenes_excel.sheet_names:
            st.error(f"La licitación '{licitacion}' no se encontró en el archivo de órdenes.")
            st.info(f"Hojas disponibles: {', '.join(ordenes_excel.sheet_names)}")
            return None
        
        # Cargar la hoja correspondiente
        df = ordenes_excel.parse(licitacion)
        
        # Normalizar nombres de columnas
        df.columns = [col.lower().strip() for col in df.columns]
        
        return df
    
    except Exception as e:
        st.error(f"Error al cargar las órdenes de la licitación '{licitacion}': {e}")
        st.error(traceback.format_exc())
        return None

def cargar_gastos_licitacion(licitacion):
    """
    Carga los datos de gastos de una licitación específica.
    
    Args:
        licitacion (str): Nombre de la licitación a cargar
        
    Returns:
        DataFrame: DataFrame con los gastos de la licitación, o None si hay error
    """
    if not os.path.exists(GASTOS_FILE):
        st.error(f"El archivo de gastos '{GASTOS_FILE}' no existe.")
        return None
    
    try:
        # Cargar el archivo Excel
        gastos_excel = pd.ExcelFile(GASTOS_FILE)
        
        # Verificar si la licitación existe como hoja
        if licitacion not in gastos_excel.sheet_names:
            st.error(f"La licitación '{licitacion}' no se encontró en el archivo de gastos.")
            st.info(f"Hojas disponibles: {', '.join(gastos_excel.sheet_names)}")
            return None
        
        # Cargar la hoja correspondiente
        df = gastos_excel.parse(licitacion)
        
        # Normalizar nombres de columnas
        df.columns = [col.lower().strip() for col in df.columns]
        
        return df
    
    except Exception as e:
        st.error(f"Error al cargar los gastos de la licitación '{licitacion}': {e}")
        st.error(traceback.format_exc())
        return None

def obtener_certificados_licitacion(licitacion):
    """
    Obtiene todos los certificados generados previamente para una licitación.
    
    Args:
        licitacion (str): Nombre de la licitación
        
    Returns:
        list: Lista de certificados generados previamente
    """
    certificados = []
    
    # Verificar si existe el archivo de certificados
    if not os.path.exists(CERTIFICADOS_LOG_FILE):
        return certificados
    
    try:
        with open(CERTIFICADOS_LOG_FILE, 'r', encoding='utf-8') as f:
            all_certificados = json.load(f)
        
        # Filtrar certificados de la licitación
        certificados = [cert for cert in all_certificados if cert.get("licitacion") == licitacion]
        
        return certificados
    except Exception as e:
        st.warning(f"Error al cargar certificados previos: {e}")
        return certificados

def calcular_saldos_licitacion(licitacion, presupuesto_total, monto_actual):
    """
    Calcula los saldos de una licitación basados en los certificados generados previamente.
    Solo tiene en cuenta los certificados, no las órdenes sin certificado.
    
    Args:
        licitacion (str): Nombre de la licitación
        presupuesto_total (float): Presupuesto total de la licitación
        monto_actual (float): Monto de la orden actual
        
    Returns:
        tuple: (saldo_anterior, monto_ejecutado, saldo_disponible)
    """
    # Obtener certificados previos
    certificados_previos = obtener_certificados_licitacion(licitacion)
    
    # Sumar todos los montos de certificados previos
    monto_certificados_previos = sum(cert.get("monto", 0) for cert in certificados_previos)
    
    # Calcular saldo anterior (presupuesto total - certificados previos)
    saldo_anterior = presupuesto_total - monto_certificados_previos
    
    # Monto ejecutado (el de esta orden)
    monto_ejecutado = monto_actual
    
    # Saldo disponible (saldo anterior - monto ejecutado)
    saldo_disponible = saldo_anterior - monto_ejecutado
    
    return saldo_anterior, monto_ejecutado, saldo_disponible

def pagina_3():
    # Almacenar el certificado en la sesión para descargarlo más tarde
    if 'certificado' not in st.session_state:
        st.session_state.certificado = None
        st.session_state.nombre_archivo_certificado = None

    st.title("Página 3: Generación de Certificados de Cumplimiento")
    
    # Crear contenedores para organizar la interfaz
    verificacion_container = st.container()
    seleccion_container = st.container()
    formulario_container = st.container()
    descarga_container = st.container()
    
    # Validar si ambos archivos persistentes existen
    with verificacion_container:
        archivos_faltantes = []
        
        if not os.path.exists(GASTOS_FILE):
            archivos_faltantes.append(GASTOS_FILE)
        
        if not os.path.exists(ORDENES_FILE):
            archivos_faltantes.append(ORDENES_FILE)
        
        if archivos_faltantes:
            st.error(f"No se encontraron los siguientes archivos: {', '.join(archivos_faltantes)}. Por favor, genera estos archivos en la página 2.")
            return
        
        st.success("✅ Se han cargado los archivos de control de gastos y órdenes de compra.")
    
    # Obtener licitaciones disponibles
    licitaciones_disponibles = listar_licitaciones_disponibles()
    
    if not licitaciones_disponibles:
        st.warning("No se encontraron licitaciones disponibles en los archivos de control.")
        return
    
    # Selección de licitación y orden de compra
    with seleccion_container:
        st.header("Selección de Licitación y Orden de Compra")
        
        # Seleccionar licitación
        selected_licitacion = st.selectbox(
            "Seleccione una licitación:",
            options=licitaciones_disponibles
        )
        
        # Cargar órdenes de la licitación seleccionada
        ordenes_licitacion = cargar_ordenes_licitacion(selected_licitacion)
        
        if ordenes_licitacion is None or ordenes_licitacion.empty:
            st.warning(f"No hay órdenes disponibles para la licitación '{selected_licitacion}'.")
            return
        
        # Filtrar órdenes en estado "aceptada" o "Recepción Conforme" y sin certificado
        filtros_estado = ["aceptada", "recepcion conforme", "recepción conforme"]
        
        # Asegurarse de que existe la columna estado
        if "estado" not in ordenes_licitacion.columns:
            st.warning("La columna 'estado' no existe en el archivo de órdenes.")
            st.info("Se asumirá que todas las órdenes están en estado 'Recepcion Conforme'.")
            ordenes_licitacion["estado"] = "Recepcion Conforme"
        
        # Asegurarse de que existe la columna certificado
        if "certificado" not in ordenes_licitacion.columns:
            ordenes_licitacion["certificado"] = "NO"
        
        # Normalizar valores de estado y certificado
        ordenes_licitacion["estado"] = ordenes_licitacion["estado"].astype(str).str.lower()
        ordenes_licitacion["certificado"] = ordenes_licitacion["certificado"].astype(str).str.upper()
        
        # Filtrar órdenes elegibles
        ordenes_elegibles = ordenes_licitacion[
            (ordenes_licitacion["estado"].str.contains("aceptada|conforme|recepcion", case=False, na=False)) & 
            (ordenes_licitacion["certificado"] != "SÍ")
        ]
        
        if ordenes_elegibles.empty:
            st.warning("No hay órdenes elegibles para certificación en esta licitación. Todas las órdenes ya tienen certificado o no están en estado aceptado.")
            return
        
        # Mostrar órdenes elegibles
        st.subheader("Órdenes Elegibles para Certificación")
        st.dataframe(ordenes_elegibles)
        
        # CORRECCIÓN: Mejorar la selección de orden de compra
        st.subheader("Seleccionar Orden de Compra")
        
        # Verificar si existen todas las columnas necesarias
        format_cols = ["orden_de_compra", "proveedor", "total"]
        missing_cols = [col for col in format_cols if col not in ordenes_elegibles.columns]
        
        # Crear un diccionario con las órdenes para la selección
        orden_options = {}
        
        if missing_cols:
            st.warning(f"Faltan columnas para mostrar la selección: {', '.join(missing_cols)}")
            # Crear opciones simplificadas si faltan columnas
            if "orden_de_compra" in ordenes_elegibles.columns:
                # Crear un diccionario usando orden de compra
                for idx, row in ordenes_elegibles.reset_index().iterrows():
                    orden_options[f"Orden {row['orden_de_compra']}"] = idx
            else:
                # Usar índices numéricos como alternativa
                for i in range(len(ordenes_elegibles)):
                    orden_options[f"Orden #{i+1}"] = i
        else:
            # Crear opciones completas con todas las columnas disponibles
            for idx, row in ordenes_elegibles.reset_index().iterrows():
                # Formatear texto descriptivo para cada orden
                option_text = f"{row['orden_de_compra']} - {row['proveedor']} - ${row['total']:,.0f}"
                orden_options[option_text] = idx
        
        # Obtener lista de opciones para mostrar en el selectbox
        orden_keys = list(orden_options.keys())
        
        # Mostrar el selectbox con las opciones formateadas
        selected_key = st.selectbox(
            "Seleccione una orden de compra:",
            options=orden_keys
        )
        
        # Recuperar el índice correspondiente a la opción seleccionada
        selected_index = orden_options[selected_key]
        
        # Obtener los datos de la orden seleccionada directamente a partir del índice
        selected_order = ordenes_elegibles.iloc[selected_index].to_dict()
        # FIN DE LA CORRECCIÓN
        
        # Mostrar detalles de la orden seleccionada
        st.subheader("Detalles de la Orden Seleccionada")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Orden de Compra:** {selected_order.get('orden_de_compra', 'No disponible')}")
            st.markdown(f"**Proveedor:** {selected_order.get('proveedor', 'No disponible')}")
            st.markdown(f"**RUT:** {selected_order.get('rut_proveedor', 'No disponible')}")
        
        with col2:
            st.markdown(f"**Fecha Envío:** {selected_order.get('fecha_envio_oc', 'No disponible')}")
            st.markdown(f"**Total:** ${selected_order.get('total', 0):,.0f}")
            st.markdown(f"**Estado:** {selected_order.get('estado', 'No disponible')}")
        
        # Obtener datos financieros de la licitación
        gastos_licitacion = cargar_gastos_licitacion(selected_licitacion)
        
        # Inicializar variables financieras
        fecha_inicio = "No disponible"
        fecha_final = "No disponible"
        presupuesto_total = 0
        
        if gastos_licitacion is None:
            st.warning("No se pudieron cargar los datos financieros de la licitación.")
        else:
            # Obtener las primeras filas que normalmente contienen el resumen
            resumen_rows = gastos_licitacion.head(2)
            
            # Intentar obtener valores del resumen
            for _, row in resumen_rows.iterrows():
                for col in row.index:
                    col_lower = str(col).lower()
                    if 'fecha_inicio' in col_lower and pd.notna(row[col]):
                        fecha_inicio = row[col]
                    elif 'fecha_final' in col_lower and pd.notna(row[col]):
                        fecha_final = row[col]
                    elif 'presupuesto_total' in col_lower and pd.notna(row[col]):
                        presupuesto_total = row[col]
            
            # Si no se encontraron, buscar en nombres de columna específicos
            if fecha_inicio == "No disponible" and 'fecha_inicio' in gastos_licitacion.columns:
                fecha_inicio = gastos_licitacion['fecha_inicio'].iloc[0]
            if fecha_final == "No disponible" and 'fecha_final' in gastos_licitacion.columns:
                fecha_final = gastos_licitacion['fecha_final'].iloc[0]
            if presupuesto_total == 0 and 'presupuesto_total' in gastos_licitacion.columns:
                presupuesto_total = gastos_licitacion['presupuesto_total'].iloc[0]
        
        # Si aún no tenemos un presupuesto total, usar un valor predeterminado
        if presupuesto_total == 0:
            # Intentar obtener del archivo de resumen
            if os.path.exists(CONTROL_SUMMARY_FILE):
                try:
                    with open(CONTROL_SUMMARY_FILE, 'r', encoding='utf-8') as f:
                        resumenes = json.load(f)
                        
                    # Buscar la licitación en los resúmenes
                    for resumen in resumenes:
                        if resumen.get("numero_licitacion") == selected_licitacion:
                            presupuesto_total = resumen.get("presupuesto_total", 0)
                            break
                except:
                    pass
            
            # Si aún no tenemos valor, usar un valor por defecto basado en la orden actual
            if presupuesto_total == 0:
                presupuesto_total = selected_order.get("total", 0) * 5  # Estimación por defecto
        
        # Calcular saldos basados en certificados previos
        monto_actual = selected_order.get("total", 0)
        saldo_anterior, monto_ejecutado, saldo_disponible = calcular_saldos_licitacion(
            selected_licitacion, presupuesto_total, monto_actual
        )
        
        # Verificar si hay saldo disponible
        if saldo_disponible < 0:
            st.error(f"No es posible ejecutar la orden. El monto ejecutado (${monto_ejecutado:,.0f}) supera el saldo disponible actual (${saldo_anterior:,.0f}).")
            return
        
        # Mostrar información financiera
        st.subheader("Información Financiera")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Presupuesto Total:** ${presupuesto_total:,.0f}")
            st.markdown(f"**Saldo Anterior:** ${saldo_anterior:,.0f}")
        with col2:
            st.markdown(f"**Monto a Ejecutar:** ${monto_ejecutado:,.0f}")
            st.markdown(f"**Saldo Disponible Resultante:** ${saldo_disponible:,.0f}")
    
    # Formulario para el certificado
    with formulario_container:
        st.header("Formulario para el Certificado")
        
        # Usar st.form para agrupar los inputs
        with st.form("certificado_form"):
            # Formulario para los datos del certificado
            col1, col2 = st.columns(2)
            
            with col1:
                tipo_operacion = st.selectbox("Tipo de operación:", ["Mantenimiento", "Arriendo"])
                es_contrato = st.radio("¿Es contrato?", ["Sí", "No"])
                es_prorroga = st.radio("¿Es prórroga?", ["Sí", "No"])
                unidad_medida = st.text_input("Unidad de medida:", "Pesos")
                aplica_multa = st.radio("¿Aplica multa?", ["Sí", "No"])
            
            with col2:
                detalle_multa = st.text_area("Detalle de la multa (si aplica):", "" if aplica_multa == "No" else "")
                centro_costo = st.text_input("Centro de costo que recibe el servicio:", "")
                observaciones = st.text_area("Observaciones:", "")
            
            st.subheader("Información del Funcionario")
            
            col3, col4 = st.columns(2)
            
            with col3:
                nombre_funcionario = st.text_input("Nombre del funcionario:", "")
                cargo_funcionario = st.text_input("Cargo del funcionario:", "")
            
            with col4:
                contraparte_tecnica = st.text_input("Contraparte técnica:", "")
                jefe_servicio = st.text_input("Jefe de servicio:", "")
            
            # Botón de envío del formulario
            submitted = st.form_submit_button("Generar Certificado")
            
            if submitted:
                # Validar campos obligatorios
                if not nombre_funcionario or not cargo_funcionario or not contraparte_tecnica or not jefe_servicio or not centro_costo:
                    st.error("Por favor, completa todos los campos obligatorios.")
                else:
                    try:
                        with st.spinner("Generando certificado..."):
                            # CORRECCIÓN: Extraer explícitamente el número de orden y el número de licitación
                            id_orden = selected_order.get("orden_de_compra", "")
                            
                            # Obtener el número de licitación (ID Compra)
                            id_compra = selected_licitacion  # El número de licitación es el ID de Compra que debe ir en A15
                            
                            # Debug: imprimir información relevante
                            st.write(f"Debug - ID de Orden que se enviará al certificado: {id_orden}")
                            st.write(f"Debug - ID de Compra (Licitación) que se enviará al certificado: {id_compra}")
                            st.write(f"Debug - Datos relevantes de la orden: {selected_order.get('orden_de_compra')}, {selected_order.get('proveedor')}")
                            
                            # Generar el certificado pasando explícitamente el ID de orden y el ID de compra (licitación)
                            certificado = generate_certificate(
                                tipo_operacion, es_contrato, es_prorroga, unidad_medida,
                                aplica_multa, detalle_multa, observaciones,
                                nombre_funcionario, cargo_funcionario,
                                contraparte_tecnica, jefe_servicio, centro_costo, 
                                selected_order,
                                saldo_anterior, monto_ejecutado, saldo_disponible,
                                fecha_inicio, fecha_final, presupuesto_total,
                                id_compra,  # Pasar el número de licitación como ID Compra
                                selected_order.get("nombre_orden", ""),
                                selected_order.get("rut_proveedor", ""), 
                                selected_order.get("proveedor", ""),
                                selected_order.get("proveedor", "")  # Referente técnico igual al proveedor
                            )
                            # FIN DE LA CORRECCIÓN
                            
                            # Actualizar el estado del certificado en el archivo de órdenes
                            actualizacion_exitosa = actualizar_estado_certificado(
                                selected_order.get("orden_de_compra", "")
                            )
                            
                            # Registrar el certificado generado
                            datos_certificado = {
                                "orden_de_compra": selected_order.get("orden_de_compra", ""),
                                "proveedor": selected_order.get("proveedor", "No disponible"),
                                "monto": float(monto_ejecutado),
                                "tipo_operacion": tipo_operacion,
                                "es_contrato": es_contrato,
                                "es_prorroga": es_prorroga,
                                "funcionario": nombre_funcionario,
                                "cargo_funcionario": cargo_funcionario,
                                "licitacion": selected_licitacion
                            }
                            
                            registro_exitoso = registrar_certificado(datos_certificado)
                            
                            if actualizacion_exitosa and registro_exitoso:
                                st.success("✅ Certificado generado con éxito y registro actualizado.")
                                
                                # Guardar el certificado en la sesión para descargarlo más tarde
                                fecha_actual = datetime.now().strftime("%Y-%m-%d")
                                nombre_archivo = f"certificado_de_cumplimiento_{selected_order.get('orden_de_compra', 'SN')}_{fecha_actual}.xlsx"
                                
                                st.session_state.certificado = certificado
                                st.session_state.nombre_archivo_certificado = nombre_archivo
                            else:
                                st.warning("El certificado se generó pero hubo problemas al actualizar los registros.")
                    
                    except Exception as e:
                        st.error(f"Error al generar el certificado: {e}")
                        st.error(traceback.format_exc())
    
    # Colocar el botón de descarga FUERA del formulario
    with descarga_container:
        if st.session_state.certificado is not None:
            st.download_button(
                label="📥 Descargar Certificado",
                data=st.session_state.certificado,
                file_name=st.session_state.nombre_archivo_certificado,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )