import os
import shutil
import pandas as pd
from datetime import datetime
import streamlit as st
import hashlib  # Importación necesaria para calcular el hash de la contraseña

# Función para crear una copia de seguridad de la carpeta "data"
def crear_backup():
    """
    Crea una copia de seguridad de la carpeta 'data' en la carpeta 'backups'.

    Returns:
        str: Ruta de la carpeta de copia de seguridad creada.
    """
    os.makedirs("backups", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_folder = f"backups/backup_{timestamp}"
    os.makedirs(backup_folder, exist_ok=True)
    
    if os.path.exists("data"):
        for file in os.listdir("data"):
            source_path = os.path.join("data", file)
            dest_path = os.path.join(backup_folder, file)
            try:
                shutil.copy2(source_path, dest_path)
            except Exception as e:
                st.error(f"Error al copiar {file}: {e}")
    
    return backup_folder

# Función para reiniciar los certificados
def reiniciar_certificados():
    """
    Reinicia los certificados y actualiza el archivo de control de órdenes de compra.

    Returns:
        bool: True si el reinicio fue exitoso, False en caso de error.
    """
    try:
        # Eliminar el archivo de registro de certificados
        if os.path.exists("data/registro_certificados.json"):
            os.remove("data/registro_certificados.json")
            st.info("Archivo de registro de certificados eliminado.")

        # Reiniciar el archivo de órdenes de compra
        if os.path.exists("data/control_de_ordenes_de_compra.xlsx"):
            ordenes_excel = pd.ExcelFile("data/control_de_ordenes_de_compra.xlsx")
            with pd.ExcelWriter("data/control_de_ordenes_de_compra.xlsx", engine="openpyxl") as writer:
                for sheet_name in ordenes_excel.sheet_names:
                    df = ordenes_excel.parse(sheet_name)
                    df.columns = [col.lower().strip() for col in df.columns]
                    if "certificado" in df.columns:
                        df["certificado"] = "NO"
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            st.info("Archivo de órdenes de compra reiniciado.")
        
        return True
    except Exception as e:
        st.error(f"Error al reiniciar certificados: {e}")
        return False

# Función para refrescar la interfaz actual
def refrescar_interfaz():
    """
    Refresca la interfaz actual utilizando los parámetros de consulta de Streamlit.
    """
    # Reemplazamos la función obsoleta por la nueva recomendada
    st.query_params = {"refresh": datetime.now().timestamp()}

# Función para mostrar el panel de administración
def mostrar_panel_admin():
    """
    Muestra el panel de administración en la barra lateral para gestionar el sistema.
    """
    st.sidebar.markdown("---")
    with st.sidebar.expander("⚙️ Configuración avanzada"):
        # Variables de sesión para el control de acceso
        if 'admin_autenticado' not in st.session_state:
            st.session_state.admin_autenticado = False
        if 'intentos_fallidos' not in st.session_state:
            st.session_state.intentos_fallidos = 0
        if 'confirmar_reinicio' not in st.session_state:
            st.session_state.confirmar_reinicio = False

        # Panel de login
        if not st.session_state.admin_autenticado and st.session_state.intentos_fallidos < 3:
            st.subheader("🔒 Acceso de Administrador")
            with st.form("admin_login"):
                contrasena = st.text_input("Contraseña", type="password")
                submitted = st.form_submit_button("Acceder")
                if submitted:
                    if verificar_contrasena(contrasena):
                        st.session_state.admin_autenticado = True
                        st.session_state.intentos_fallidos = 0
                        st.success("✅ Acceso concedido")
                        refrescar_interfaz()
                    else:
                        st.session_state.intentos_fallidos += 1
                        restantes = 3 - st.session_state.intentos_fallidos
                        if restantes > 0:
                            st.error(f"❌ Contraseña incorrecta. Intentos restantes: {restantes}")
                        else:
                            st.error("❌ Demasiados intentos fallidos. Acceso bloqueado.")
        elif st.session_state.intentos_fallidos >= 3:
            st.warning("⚠️ Acceso bloqueado por demasiados intentos fallidos. Reinicie la aplicación para intentar de nuevo.")

        # Panel de administración
        if st.session_state.admin_autenticado:
            st.subheader("⚙️ Panel de Administración")
            
            # Botón para reiniciar certificados
            if st.button("Reiniciar Certificados"):
                # Checkbox para confirmar
                confirmar = st.checkbox("Confirmar reinicio de certificados", key="confirmar_reinicio")
                
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

            # Botón para cerrar sesión
            if st.button("Cerrar sesión de administrador"):
                st.session_state.admin_autenticado = False
                st.info("🔓 Sesión cerrada.")
                refrescar_interfaz()

# Función para verificar la contraseña
def verificar_contrasena(contrasena):
    """
    Verifica la contraseña utilizando un hash predefinido.

    Args:
        contrasena (str): Contraseña ingresada por el usuario.

    Returns:
        bool: True si la contraseña es correcta, False en caso contrario.
    """
    contrasena_hash = "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"  # Hash SHA-256 de "admin123"
    input_hash = hashlib.sha256(contrasena.encode()).hexdigest()
    return input_hash == contrasena_hash