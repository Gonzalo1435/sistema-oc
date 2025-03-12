import streamlit as st
import pandas as pd
import os
import sys
import json
from datetime import datetime
import matplotlib.pyplot as plt

# Añadir la carpeta actual al path de Python para importar módulos locales
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar funciones de las páginas
from pages.pagina_1 import pagina_1
from pages.pagina_2 import pagina_2
from pages.pagina_3 import pagina_3
from pages.pagina_4 import pagina_4

# Importar la funcionalidad de reinicio (IMPORTANTE)
from reset_system import (crear_backup, reiniciar_certificados, 
                         verificar_contrasena)

# Rutas de archivos importantes
ORDENES_FILE = "data/control_de_ordenes_de_compra.xlsx"
GASTOS_FILE = "data/control_de_gasto_de_licitaciones.xlsx"
CONTROL_SUMMARY_FILE = "data/resumen_control_licitaciones.json"
CERTIFICADOS_LOG_FILE = "data/registro_certificados.json"

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Gestión de Órdenes y Licitaciones",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        margin-bottom: 1rem;
        text-align: center;
    }
    .subheader {
        font-size: 1.5rem;
        font-weight: 500;
        color: #333;
        margin-bottom: 1rem;
    }
    .dashboard-metrics {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: bold;
        color: #1E88E5;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #555;
    }
    .info-box {
        background-color: #e1f5fe;
        border-left: 5px solid #039be5;
        padding: 10px;
        border-radius: 3px;
    }
    .warning-box {
        background-color: #fff3e0;
        border-left: 5px solid #ff9800;
        padding: 10px;
        border-radius: 3px;
    }
    .success-box {
        background-color: #e8f5e9;
        border-left: 5px solid #4caf50;
        padding: 10px;
        border-radius: 3px;
    }
    .stButton>button {
        width: 100%;
    }
    
    /* Mejoras para tarjetas de acceso rápido */
    .quick-access-card {
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 15px;
        transition: all 0.3s ease;
        height: 100%;
        background-color: white;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    
    .quick-access-card:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        border-color: #1E88E5;
        transform: translateY(-3px);
    }
    
    .quick-access-card h4 {
        color: #1E88E5;
        margin-bottom: 10px;
    }
    
    /* Estilos para los botones dentro de las tarjetas */
    .quick-access-card .stButton > button {
        background-color: #1E88E5;
        color: white !important;
        font-weight: 500;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        margin-top: 10px;
        transition: all 0.2s ease;
        width: 100%;
    }
    
    .quick-access-card .stButton > button:hover {
        background-color: #1565C0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    
    /* Estilos para el sidebar mejorado */
    .sidebar-nav-button {
        margin-bottom: 8px !important;
    }
    
    .sidebar-nav-button button {
        background-color: transparent;
        border: 1px solid #ddd;
        color: #333;
        text-align: left;
        font-weight: normal;
        transition: all 0.3s ease;
    }
    
    .sidebar-nav-button button:hover {
        background-color: #f0f2f6;
        border-color: #1E88E5;
    }
    
    .sidebar-nav-active button {
        background-color: #e3f2fd;
        border-color: #1E88E5;
        color: #1E88E5;
        font-weight: 500;
    }
    
    .sidebar-section {
        margin-top: 15px;
        margin-bottom: 5px;
        border-bottom: 1px solid #eee;
        padding-bottom: 5px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Función para obtener estadísticas del sistema
def obtener_estadisticas():
    """
    Obtiene estadísticas de los archivos de control para mostrar en el dashboard.
    Versión mejorada para detectar correctamente las licitaciones activas.
    
    Returns:
        dict: Diccionario con las estadísticas del sistema
    """
    estadisticas = {
        "archivos_existentes": 0,
        "licitaciones_activas": 0,
        "certificados_generados": 0,
        "presupuesto_total": 0,
        "presupuesto_ejecutado": 0,
        "presupuesto_certificado": 0,
        "ordenes_totales": 0,
        "ordenes_certificadas": 0
    }
    
    # Verificar existencia de archivos
    if os.path.exists(ORDENES_FILE):
        estadisticas["archivos_existentes"] += 1
    
    if os.path.exists(GASTOS_FILE):
        estadisticas["archivos_existentes"] += 1
    
    # Obtener información de certificados
    if os.path.exists(CERTIFICADOS_LOG_FILE):
        try:
            with open(CERTIFICADOS_LOG_FILE, 'r', encoding='utf-8') as f:
                certificados = json.load(f)
                estadisticas["certificados_generados"] = len(certificados)
        except Exception as e:
            print(f"Error al leer certificados: {e}")
    
    # Obtener información de licitaciones (VERSIÓN MEJORADA)
    if os.path.exists(CONTROL_SUMMARY_FILE):
        try:
            with open(CONTROL_SUMMARY_FILE, 'r', encoding='utf-8') as f:
                try:
                    resumenes = json.load(f)
                    
                    # Imprimir información de depuración sobre licitaciones
                    print(f"Total de licitaciones encontradas: {len(resumenes)}")
                    
                    for i, resumen in enumerate(resumenes):
                        # Verificar si el estado de licitación existe y es válido
                        if "estado" in resumen:
                            # Obtener y normalizar el valor del estado
                            estado_valor = str(resumen["estado"]).lower().strip()
                            
                            # Imprimir información de depuración
                            print(f"Licitación {i+1}: Estado = '{resumen['estado']}', Normalizado = '{estado_valor}'")
                            
                            # Verificar si es activa - ampliamos los casos posibles
                            estados_activos = ["activa", "activo", "vigente", "en curso", "abierta", "abierto", "en proceso"]
                            if any(estado_activo in estado_valor for estado_activo in estados_activos):
                                estadisticas["licitaciones_activas"] += 1
                                print(f"  --> Marcada como ACTIVA")
                        else:
                            print(f"Licitación {i+1}: No tiene campo 'estado'")
                        
                        # Acumular valores de presupuesto
                        estadisticas["presupuesto_total"] += float(resumen.get("presupuesto_total", 0))
                        estadisticas["presupuesto_ejecutado"] += float(resumen.get("presupuesto_ejecutado", 0))
                        estadisticas["presupuesto_certificado"] += float(resumen.get("presupuesto_certificado", 0))
                
                except json.JSONDecodeError as e:
                    print(f"Error decodificando JSON de licitaciones: {e}")
        except Exception as e:
            print(f"Error al abrir archivo de licitaciones: {e}")
    
    # Obtener información de órdenes
    if os.path.exists(ORDENES_FILE):
        try:
            ordenes_excel = pd.ExcelFile(ORDENES_FILE)
            
            for hoja in ordenes_excel.sheet_names:
                ordenes = ordenes_excel.parse(hoja)
                
                estadisticas["ordenes_totales"] += len(ordenes)
                
                if "certificado" in ordenes.columns:
                    # Normalizar los valores para considerar distintas variantes
                    valores_si = ["sí", "si", "s", "yes", "y", "true", "1"]
                    ordenes_certificadas = ordenes[ordenes["certificado"].astype(str).str.lower().str.strip().isin(valores_si)]
                    estadisticas["ordenes_certificadas"] += len(ordenes_certificadas)
        except Exception as e:
            print(f"Error al leer órdenes: {e}")
    
    return estadisticas

# Función para mostrar el encabezado con métricas y logo
def mostrar_encabezado():
    # Mostrar título y logo en la misma línea
    col_title, col_logo = st.columns([4, 1])
    
    with col_title:
        st.markdown('<div class="main-header">Sistema de Gestión de Órdenes y Licitaciones</div>', unsafe_allow_html=True)
    
    with col_logo:
        # Verificar si existe la imagen
        logo_path = "images/logo_hospital.png"
        if os.path.exists(logo_path):
            st.image(logo_path, width=150)
        else:
            st.error("Logo no encontrado. Verifique que exista el archivo images/logo_hospital.png")
    
    # Obtener estadísticas
    estadisticas = obtener_estadisticas()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="dashboard-metrics">', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{estadisticas["archivos_existentes"]}/2</div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Archivos de Control</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="dashboard-metrics">', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{estadisticas["licitaciones_activas"]}</div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Licitaciones Activas</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col3:
        st.markdown('<div class="dashboard-metrics">', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{estadisticas["ordenes_totales"]}</div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Órdenes de Compra</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col4:
        st.markdown('<div class="dashboard-metrics">', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{estadisticas["certificados_generados"]}</div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Certificados Generados</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# Función para mostrar la barra de navegación
def mostrar_navbar():
    """
    Muestra una barra de navegación en la parte superior con botones para cada página.
    """
    # Definir páginas para la navegación
    nav_items = {
        "Inicio": "Inicio",
        "Página 1": "Subida de PDFs",
        "Página 2": "Control de Gastos",
        "Página 3": "Certificados",
        "Página 4": "Reportes"
    }
    
    cols = st.columns(len(nav_items))
    
    # Añadir botones a cada columna
    for i, (page_id, page_name) in enumerate(nav_items.items()):
        with cols[i]:
            # Determinar si este botón está activo
            is_active = st.session_state.pagina_seleccionada == page_id
            
            # Crear botón con estilo primario si está activo, secundario si no
            button_type = "primary" if is_active else "secondary"
            if st.button(page_name, key=f"nav_{page_id}", type=button_type):
                st.session_state.pagina_seleccionada = page_id
                st.rerun()

# Función para mostrar el sidebar con opciones de navegación mejoradas
def mostrar_sidebar_mejorado():
    """
    Muestra el menú de navegación en la barra lateral con estilos mejorados.
    """
    with st.sidebar:
        st.title("Navegación")
        
        # Botones para navegación por el sistema
        nav_items = [
            {"id": "Inicio", "label": "📊 Inicio", "desc": "Bienvenida y resumen"},
            {"id": "Página 1", "label": "📄 Subida de PDFs", "desc": "Subida de PDFs y Extracción de Datos"},
            {"id": "Página 2", "label": "💰 Control de Gastos", "desc": "Control de Órdenes y Gasto de Licitaciones"},
            {"id": "Página 3", "label": "🔖 Certificados", "desc": "Generación de Certificados de Cumplimiento"},
            {"id": "Página 4", "label": "📊 Reportes", "desc": "Control de Gastos y Certificados Generados"}
        ]
        
        for item in nav_items:
            is_active = st.session_state.pagina_seleccionada == item["id"]
            css_class = "sidebar-nav-button sidebar-nav-active" if is_active else "sidebar-nav-button"
            
            # Envolver el botón en un div con clase CSS
            st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
            if st.button(item["label"], key=f"sidebar_{item['id']}", use_container_width=True):
                st.session_state.pagina_seleccionada = item["id"]
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Mostrar descripción si el botón está activo
            if is_active:
                st.info(item["desc"])
        
        # Separador
        st.markdown("---")
        
        # Añadir información de ayuda
        with st.expander("ℹ️ Ayuda"):
            st.markdown("""
            **Flujo de trabajo recomendado:**
            
            1. **Página 1**: Sube los PDFs de órdenes de compra para extraer sus datos.
            2. **Página 2**: Sube el archivo de licitaciones y procesa las órdenes extraídas.
            3. **Página 3**: Genera certificados de cumplimiento para órdenes específicas.
            4. **Página 4**: Visualiza el resumen de gastos y certificados generados.
            """)
        
        # Configuración Avanzada (expandible)
        with st.expander("⚙️ Configuración avanzada"):
            st.info("Esta sección contiene opciones avanzadas y de administración.")
            if st.button("Acceder a configuración", key="btn_config_avanzada"):
                st.session_state.mostrar_config_avanzada = True
                st.rerun()
        
        # Información de la aplicación
        st.markdown("---")
        st.markdown("### Información")
        st.markdown("""
        **Sistema de Gestión de Órdenes**
        Versión 1.0.0
        
        Desarrollado para el control de órdenes de compra
        y certificados de cumplimiento.
        """)

# Función para mostrar gráficos en el dashboard
def mostrar_graficos_dashboard():
    if not (os.path.exists(ORDENES_FILE) and os.path.exists(GASTOS_FILE)):
        st.warning("No se pueden mostrar gráficos porque no se han generado los archivos de control.")
        return
    
    try:
        # Obtener datos
        estadisticas = obtener_estadisticas()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de órdenes certificadas vs sin certificar
            fig1, ax1 = plt.subplots(figsize=(6, 4))
            ordenes_sin_certificado = estadisticas["ordenes_totales"] - estadisticas["ordenes_certificadas"]
            
            ax1.pie(
                [estadisticas["ordenes_certificadas"], ordenes_sin_certificado],
                labels=["Con Certificado", "Sin Certificado"],
                autopct="%1.1f%%",
                startangle=90,
                colors=["lightgreen", "salmon"],
            )
            ax1.set_title("Órdenes de Compra: Con y Sin Certificado")
            
            st.pyplot(fig1)
        
        with col2:
            # Gráfico de ejecución presupuestaria
            if estadisticas["presupuesto_total"] > 0:
                fig2, ax2 = plt.subplots(figsize=(6, 4))
                
                presupuesto_disponible = estadisticas["presupuesto_total"] - estadisticas["presupuesto_ejecutado"]
                presupuesto_comprometido = estadisticas["presupuesto_ejecutado"] - estadisticas["presupuesto_certificado"]
                
                categorias = ["Certificado", "Comprometido", "Disponible"]
                valores = [
                    estadisticas["presupuesto_certificado"],
                    presupuesto_comprometido,
                    presupuesto_disponible
                ]
                
                ax2.bar(categorias, valores, color=["lightgreen", "skyblue", "lightgray"])
                ax2.set_title("Distribución Presupuestaria")
                ax2.set_ylabel("Monto ($)")
                
                # Añadir etiquetas con valores
                for i, v in enumerate(valores):
                    if v > 0:
                        ax2.text(i, v + 0.5, f"${v:,.0f}", ha='center')
                
                st.pyplot(fig2)
            else:
                st.info("No hay datos presupuestarios disponibles para visualizar.")
    
    except Exception as e:
        st.error(f"Error al generar gráficos: {e}")

# Función para la página de inicio
def mostrar_pagina_inicio():
    st.markdown('<div class="subheader">Bienvenido al Sistema de Gestión de Órdenes y Licitaciones</div>', unsafe_allow_html=True)
    
    # Mostrar gráficos en el dashboard
    mostrar_graficos_dashboard()
    
    st.markdown("""
    Este sistema te permite gestionar el ciclo completo de órdenes de compra y licitaciones:
    
    - **Extracción de datos** desde archivos PDF de órdenes de compra
    - **Control de gastos** para diferentes licitaciones
    - **Generación de certificados** de cumplimiento
    - **Visualización** de estadísticas y reportes
    """)
    
    # Mostrar alertas si faltan archivos
    if not os.path.exists("data"):
        st.markdown('<div class="warning-box">No se ha creado la carpeta "data". Se creará automáticamente cuando generes los archivos de control.</div>', unsafe_allow_html=True)
    
    if not os.path.exists(ORDENES_FILE):
        st.markdown('<div class="info-box">No se ha generado el archivo de órdenes de compra. Ve a la Página 1 para comenzar.</div>', unsafe_allow_html=True)
    
    if not os.path.exists(GASTOS_FILE):
        st.markdown('<div class="info-box">No se ha generado el archivo de control de gastos. Ve a la Página 2 después de procesar órdenes.</div>', unsafe_allow_html=True)
    
    # Mostrar tarjetas para acceso directo a las funciones principales
    st.markdown("### Acceso Rápido")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="quick-access-card">', unsafe_allow_html=True)
        st.markdown("#### 📄 Subir PDFs de Órdenes")
        st.markdown("Sube archivos PDF de órdenes de compra para extraer sus datos.")
        if st.button("Ir a Subida de PDFs", key="btn_pdfs"):
            st.session_state.pagina_seleccionada = "Página 1"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="quick-access-card" style="margin-top:10px;">', unsafe_allow_html=True)
        st.markdown("#### 🔖 Generar Certificados")
        st.markdown("Genera certificados de cumplimiento para órdenes específicas.")
        if st.button("Ir a Certificados", key="btn_certs"):
            st.session_state.pagina_seleccionada = "Página 3"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="quick-access-card">', unsafe_allow_html=True)
        st.markdown("#### 💰 Control de Gastos")
        st.markdown("Administra el presupuesto y gastos de tus licitaciones.")
        if st.button("Ir a Control de Gastos", key="btn_gastos"):
            st.session_state.pagina_seleccionada = "Página 2"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="quick-access-card" style="margin-top:10px;">', unsafe_allow_html=True)
        st.markdown("#### 📊 Visualizar Reportes")
        st.markdown("Consulta estadísticas y reportes sobre tus órdenes y certificados.")
        if st.button("Ir a Reportes", key="btn_reports"):
            st.session_state.pagina_seleccionada = "Página 4"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Mostrar información del sistema
    st.markdown("### Información del Sistema")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fecha_actual = datetime.now().strftime("%d-%m-%Y")
        st.markdown(f"**Fecha actual:** {fecha_actual}")
        st.markdown("**Versión:** 1.0.0")
    
    with col2:
        # Mostrar fecha de último certificado generado
        if os.path.exists(CERTIFICADOS_LOG_FILE):
            try:
                with open(CERTIFICADOS_LOG_FILE, 'r') as f:
                    certificados = json.load(f)
                    if certificados:
                        ultimo_certificado = certificados[-1]
                        fecha_ultimo = ultimo_certificado.get("fecha_generacion", "No disponible")
                        st.markdown(f"**Último certificado generado:** {fecha_ultimo}")
            except:
                pass

# Función para manejar la configuración avanzada
def manejar_configuracion_avanzada():
    """
    Maneja la sección de configuración avanzada, que incluye las opciones
    de administración protegidas por contraseña.
    """
    st.header("Configuración Avanzada")
    
    # Inicializar variables de sesión si no existen
    if 'admin_autenticado' not in st.session_state:
        st.session_state.admin_autenticado = False
    if 'intentos_fallidos' not in st.session_state:
        st.session_state.intentos_fallidos = 0
    
    # Si el usuario no está autenticado, mostrar pantalla de login
    if not st.session_state.admin_autenticado and st.session_state.intentos_fallidos < 3:
        st.warning("⚠️ Esta sección requiere acceso de administrador")
        
        with st.form("admin_login_form"):
            st.subheader("Acceso de Administrador")
            password = st.text_input("Contraseña:", type="password")
            
            submit_button = st.form_submit_button("Acceder")
            
            if submit_button:
                # Usar la función de verificación de contraseña del módulo reset_system
                if verificar_contrasena(password):
                    st.session_state.admin_autenticado = True
                    st.session_state.intentos_fallidos = 0
                    st.success("✅ Acceso concedido")
                    st.rerun()  # Recargar para mostrar las opciones de administrador
                else:
                    st.session_state.intentos_fallidos += 1
                    restantes = 3 - st.session_state.intentos_fallidos
                    if restantes > 0:
                        st.error(f"❌ Contraseña incorrecta. Intentos restantes: {restantes}")
                    else:
                        st.error("❌ Demasiados intentos fallidos. Acceso bloqueado.")
    elif st.session_state.intentos_fallidos >= 3:
        st.warning("⚠️ Acceso bloqueado por demasiados intentos fallidos. Reinicie la aplicación para intentar de nuevo.")
        if st.button("Reiniciar contador de intentos"):
            st.session_state.intentos_fallidos = 0
            st.rerun()
    else:
        # Usuario ya autenticado, mostrar opciones de administración
        st.success(f"✅ Sesión iniciada como administrador")
        
        if st.button("Cerrar sesión", key="btn_logout"):
            st.session_state.admin_autenticado = False
            st.info("Sesión cerrada correctamente")
            st.rerun()
            
        # Crear pestañas para las diferentes secciones de administración
        tab1, tab2, tab3 = st.tabs(["Sistema", "Archivos", "Seguridad"])
        
        with tab1:
            st.subheader("Administración del Sistema")
            
            # Sección de reinicio del sistema usando funciones originales de reset_system.py
            st.markdown("#### Reinicio de Certificados")
            if st.button("Reiniciar Certificados", key="btn_reset_certs"):
                # Checkbox para confirmar
                confirmar = st.checkbox("Confirmar reinicio de certificados", key="confirmar_reinicio_certs")
                
                if confirmar:
                    with st.spinner("Creando copia de seguridad..."):
                        backup_folder = crear_backup()
                    with st.spinner("Reiniciando certificados..."):
                        success = reiniciar_certificados()
                    if success:
                        st.success(f"✅ Certificados reiniciados. Copia de seguridad creada en: {backup_folder}")
                    else:
                        st.error("❌ Error al reiniciar certificados")
                else:
                    st.warning("⚠️ Debes confirmar antes de reiniciar.")
            
            # Reinicio completo del sistema
            st.markdown("#### Reinicio Completo del Sistema")
            if st.button("Reinicio Completo", key="btn_full_reset"):
                confirmar_completo = st.checkbox("Confirmar reinicio completo del sistema", key="confirm_full_reset")
                
                if confirmar_completo:
                    # Crear respaldo primero
                    try:
                        with st.spinner("Creando copia de seguridad..."):
                            backup_folder = crear_backup()
                            st.success(f"✅ Copia de seguridad creada en: {backup_folder}")
                            
                        # Eliminar todos los archivos del sistema
                        archivos_a_eliminar = [
                            "data/control_de_ordenes_de_compra.xlsx",
                            "data/control_de_gasto_de_licitaciones.xlsx",
                            "data/resumen_control_licitaciones.json",
                            "data/registro_certificados.json"
                        ]
                        
                        for archivo in archivos_a_eliminar:
                            if os.path.exists(archivo):
                                os.remove(archivo)
                                st.info(f"Eliminado: {archivo}")
                        
                        # Reiniciar estados de sesión
                        for key in list(st.session_state.keys()):
                            if key != "admin_autenticado" and key != "mostrar_config_avanzada" and key != "intentos_fallidos":
                                del st.session_state[key]
                        
                        st.success("✅ Sistema reiniciado correctamente")
                        
                        # Botón para volver al inicio
                        if st.button("Volver al Inicio", key="btn_back_to_home"):
                            st.session_state.pagina_seleccionada = "Inicio"
                            st.session_state.mostrar_config_avanzada = False
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error al reiniciar el sistema: {e}")
                else:
                    st.warning("⚠️ Debes confirmar antes de realizar un reinicio completo.")
            
            # Información del sistema
            st.markdown("#### Información del Sistema")
            
            # Mostrar estadísticas y estado actual
            col1, col2 = st.columns(2)
            
            with col1:
                fecha_actual = datetime.now().strftime("%d-%m-%Y")
                st.markdown(f"**Fecha del sistema:** {fecha_actual}")
                st.markdown(f"**Versión:** 1.0.0")
                st.markdown(f"**Archivos de control:** {obtener_estadisticas()['archivos_existentes']}/2")
            
            with col2:
                st.markdown(f"**Órdenes totales:** {obtener_estadisticas()['ordenes_totales']}")
                st.markdown(f"**Licitaciones activas:** {obtener_estadisticas()['licitaciones_activas']}")
                st.markdown(f"**Certificados generados:** {obtener_estadisticas()['certificados_generados']}")
        
        with tab2:
            st.subheader("Gestión de Archivos")
            
            # Verificación de archivos
            st.markdown("#### Verificación de Integridad")
            
            if st.button("Verificar archivos del sistema", key="btn_verify_files"):
                # Verificar que existan los archivos necesarios
                archivos_requeridos = [
                    "data/control_de_ordenes_de_compra.xlsx",
                    "data/control_de_gasto_de_licitaciones.xlsx",
                    "data/resumen_control_licitaciones.json",
                    "data/registro_certificados.json"
                ]
                
                resultados = []
                for archivo in archivos_requeridos:
                    existe = os.path.exists(archivo)
                    resultados.append({"archivo": archivo, "existe": existe})
                
                # Mostrar resultados en una tabla
                df_archivos = pd.DataFrame(resultados)
                st.dataframe(df_archivos, use_container_width=True)
                
                # Calcular porcentaje de integridad
                porcentaje = sum([1 for r in resultados if r["existe"]]) / len(resultados) * 100
                st.progress(porcentaje / 100)
                st.markdown(f"**Integridad del sistema:** {porcentaje:.1f}%")
            
            # Creación de respaldo manual
            st.markdown("#### Respaldo del Sistema")
            
            if st.button("Crear respaldo de archivos", key="btn_backup"):
                with st.spinner("Creando copia de seguridad..."):
                    backup_folder = crear_backup()
                    st.success(f"✅ Respaldo creado correctamente en: {backup_folder}")
                    
                    # Listar archivos respaldados
                    if os.path.exists(backup_folder):
                        archivos_respaldados = os.listdir(backup_folder)
                        if archivos_respaldados:
                            st.info("Archivos respaldados:")
                            for archivo in archivos_respaldados:
                                st.markdown(f"- {archivo}")
                        else:
                            st.warning("No se encontraron archivos para respaldar.")
                    else:
                        st.error("La carpeta de respaldo no se creó correctamente.")
        
        with tab3:
            st.subheader("Seguridad del Sistema")
            
            # Registro de actividad (simulado)
            st.markdown("#### Registro de Actividad")
            
            # En un sistema real, esto se obtendría de una base de datos o archivo de registro
            registros = [
                {"fecha": datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "usuario": "admin", "acción": "Inicio de sesión", "detalles": "Acceso exitoso"},
                {"fecha": (datetime.now()).strftime("%d/%m/%Y %H:%M:%S"), "usuario": "admin", "acción": "Acceso a configuración", "detalles": "Configuración avanzada"}
            ]
            
            # Si hay certificados generados, mostrarlos en el registro
            if os.path.exists(CERTIFICADOS_LOG_FILE):
                try:
                    with open(CERTIFICADOS_LOG_FILE, 'r') as f:
                        certificados = json.load(f)
                        for cert in certificados[-3:]:  # Mostrar solo los últimos 3 certificados
                            registros.append({
                                "fecha": cert.get("fecha_generacion", "Desconocida"),
                                "usuario": "sistema",
                                "acción": "Generación de certificado",
                                "detalles": f"Certificado #{cert.get('numero_certificado', '?')}"
                            })
                except Exception as e:
                    st.error(f"Error al leer certificados: {e}")
            
            df_registros = pd.DataFrame(registros)
            st.dataframe(df_registros, use_container_width=True)

# Función principal que define el flujo de la aplicación
def main():
    # Inicializar variables de estado si no existen
    if 'pagina_seleccionada' not in st.session_state:
        st.session_state.pagina_seleccionada = "Inicio"
    if 'mostrar_config_avanzada' not in st.session_state:
        st.session_state.mostrar_config_avanzada = False
    if 'admin_autenticado' not in st.session_state:
        st.session_state.admin_autenticado = False
    
    # Mostrar el sidebar mejorado
    mostrar_sidebar_mejorado()
    
    # Verificar si se debe mostrar la configuración avanzada
    if st.session_state.get("mostrar_config_avanzada", False):
        manejar_configuracion_avanzada()
        # Botón para volver
        if st.button("Volver al sistema principal", key="btn_back_main"):
            st.session_state.mostrar_config_avanzada = False
            st.rerun()
        return  # Salir para no mostrar el resto de la interfaz
    
    # Mostrar el encabezado
    mostrar_encabezado()
    
    # Mostrar barra de navegación superior
    mostrar_navbar()
    
    # Mostrar la página seleccionada
    if st.session_state.pagina_seleccionada == "Inicio":
        mostrar_pagina_inicio()
    elif st.session_state.pagina_seleccionada == "Página 1":
        pagina_1()
    elif st.session_state.pagina_seleccionada == "Página 2":
        pagina_2()
    elif st.session_state.pagina_seleccionada == "Página 3":
        pagina_3()
    elif st.session_state.pagina_seleccionada == "Página 4":
        pagina_4()

# Punto de entrada de la aplicación
if __name__ == "__main__":
    try:
        # Crear carpeta data si no existe
        os.makedirs("data", exist_ok=True)
        
        # Ejecutar la aplicación
        main()
    except Exception as e:
        st.error(f"Ha ocurrido un error al iniciar la aplicación: {e}")