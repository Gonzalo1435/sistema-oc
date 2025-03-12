import streamlit as st

# DEBE ser la primera instrucción de Streamlit
st.set_page_config(
    page_title="Sistema de Gestión de Órdenes y Licitaciones",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

import os
from user_management import (
    init_user_system, login_form, admin_user_management, 
    admin_view_user_data, get_user_data_path, generate_user_report
)

def initialize_session_state():
    """
    Inicializa las variables de estado de la sesión.
    """
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'current_view' not in st.session_state:
        st.session_state.current_view = "login"

def auth_sidebar():
    """
    Muestra la barra lateral para usuarios autenticados.
    """
    if st.session_state.authenticated and st.session_state.user:
        with st.sidebar:
            st.title(f"Bienvenido, {st.session_state.user['username']}")
            st.markdown(f"**Rol:** {st.session_state.user['role']}")
            st.markdown("---")
            
            # Botones de navegación
            st.subheader("Navegación")
            
            if st.button("📊 Panel Principal", key="nav_panel", use_container_width=True):
                st.session_state.current_view = "main"
                st.rerun()
            
            if st.session_state.user["role"] == "Administrador":
                if st.button("👥 Gestión de Usuarios", key="nav_users", use_container_width=True):
                    st.session_state.current_view = "admin_users"
                    st.rerun()
                
                if st.button("📋 Ver Datos de Usuarios", key="nav_data", use_container_width=True):
                    st.session_state.current_view = "admin_data"
                    st.rerun()
                
                if st.button("📊 Informe de Usuarios", key="nav_report", use_container_width=True):
                    st.session_state.current_view = "admin_report"
                    st.rerun()
            
            # Cerrar sesión
            st.markdown("---")
            if st.button("🚪 Cerrar Sesión", type="primary", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.user = None
                st.session_state.current_view = "login"
                st.rerun()

def auth_page():
    """
    Muestra la página de autenticación.
    """
    st.title("Sistema de Gestión de Órdenes y Licitaciones")
    
    st.header("Iniciar Sesión")
    user = login_form()
    if user:
        st.session_state.authenticated = True
        st.session_state.user = user
        st.session_state.current_view = "main"
        st.rerun()
    
    # Mensaje informativo para nuevos usuarios
    st.info("Si no tienes una cuenta, contacta con un administrador para que te cree una.")

def redirect_to_app():
    """
    Redirige al usuario a la aplicación principal después del inicio de sesión.
    """
    # Obtener el nombre de usuario actual
    current_username = st.session_state.user["username"]
    current_role = st.session_state.user["role"]
    
    # Configurar rutas específicas para el usuario actual
    user_data_path = get_user_data_path(current_username)
    os.makedirs(user_data_path, exist_ok=True)
    
    try:
        # Crear contenedores para el contenido principal
        main_container = st.container()
        
        with main_container:
            # Mostrar encabezado personalizado
            st.title("Sistema de Gestión de Órdenes y Licitaciones")
            st.header(f"Usuario: {current_username} ({current_role})")
            
            # Crear variables de sesión necesarias
            if 'pagina_seleccionada' not in st.session_state:
                st.session_state.pagina_seleccionada = "Inicio"
            
            # Crear navegación simplificada
            tabs = st.tabs(["Inicio", "Subida de PDFs", "Control de Gastos", "Certificados", "Reportes"])
            
            # Modificar las rutas de archivos para este usuario
            from pages.pagina_1 import pagina_1
            from pages.pagina_2 import pagina_2
            from pages.pagina_3 import pagina_3
            from pages.pagina_4 import pagina_4
            
            # Modificar la ruta de los archivos globalmente
            import pages.pagina_2 as pagina_2_module
            import pages.pagina_3 as pagina_3_module
            import pages.pagina_4 as pagina_4_module
            
            # Establecer las rutas específicas del usuario
            pagina_2_module.PERSISTENT_EXPENSES_FILE = f"{user_data_path}/control_de_gasto_de_licitaciones.xlsx"
            pagina_2_module.PERSISTENT_ORDERS_FILE = f"{user_data_path}/control_de_ordenes_de_compra.xlsx"
            pagina_2_module.CONTROL_SUMMARY_FILE = f"{user_data_path}/resumen_control_licitaciones.json"
            
            pagina_3_module.GASTOS_FILE = f"{user_data_path}/control_de_gasto_de_licitaciones.xlsx"
            pagina_3_module.ORDENES_FILE = f"{user_data_path}/control_de_ordenes_de_compra.xlsx"
            pagina_3_module.CONTROL_SUMMARY_FILE = f"{user_data_path}/resumen_control_licitaciones.json"
            pagina_3_module.CERTIFICADOS_LOG_FILE = f"{user_data_path}/registro_certificados.json"
            
            pagina_4_module.ORDENES_FILE = f"{user_data_path}/control_de_ordenes_de_compra.xlsx"
            pagina_4_module.GASTOS_FILE = f"{user_data_path}/control_de_gasto_de_licitaciones.xlsx"
            pagina_4_module.CONTROL_SUMMARY_FILE = f"{user_data_path}/resumen_control_licitaciones.json"
            pagina_4_module.CERTIFICADOS_LOG_FILE = f"{user_data_path}/registro_certificados.json"
            
            # Mostrar la página según la pestaña seleccionada
            with tabs[0]:  # Inicio
                st.write("## Bienvenido al Sistema de Gestión")
                st.write("Selecciona una de las pestañas para acceder a las diferentes funcionalidades.")
                
                # Mostrar estadísticas básicas
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Tu carpeta", user_data_path)
                with col2:
                    # Contar archivos en la carpeta del usuario
                    num_files = len([f for f in os.listdir(user_data_path) if os.path.isfile(os.path.join(user_data_path, f))])
                    st.metric("Archivos", num_files)
                with col3:
                    st.metric("Rol", current_role)
            
            with tabs[1]:  # Subida de PDFs
                pagina_1()
            
            with tabs[2]:  # Control de Gastos
                pagina_2()
            
            with tabs[3]:  # Certificados
                pagina_3()
            
            with tabs[4]:  # Reportes
                pagina_4()
    
    except Exception as e:
        st.error(f"Error al cargar la aplicación: {e}")
        import traceback
        st.error(traceback.format_exc())

def main():
    """
    Función principal que gestiona el flujo de la aplicación con autenticación.
    """
    # Inicializar sistema de usuarios
    init_user_system()
    
    # Inicializar variables de estado de la sesión
    initialize_session_state()
    
    # Mostrar la barra lateral para usuarios autenticados
    if st.session_state.authenticated:
        auth_sidebar()
    
    # Determinar qué vista mostrar
    if not st.session_state.authenticated:
        auth_page()
    else:
        if st.session_state.current_view == "main":
            redirect_to_app()
        elif st.session_state.current_view == "admin_users":
            admin_user_management()
        elif st.session_state.current_view == "admin_data":
            admin_view_user_data()
        elif st.session_state.current_view == "admin_report":
            generate_user_report()

if __name__ == "__main__":
    main()