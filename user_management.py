import os
import json
import streamlit as st
import hashlib
import shutil
from datetime import datetime

# Ruta para el archivo de usuarios
USERS_FILE = "data/users.json"
USER_ROLES = ["Usuario", "Administrador"]

def init_user_system():
    """
    Inicializa el sistema de usuarios, creando el archivo de usuarios
    si no existe.
    """
    # Crear directorio de datos si no existe
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/users", exist_ok=True)
    
    # Inicializar archivo de usuarios si no existe
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)
        
        # Crear usuario administrador por defecto
        create_user("admin", "admin123", "Administrador")

def hash_password(password):
    """
    Genera un hash seguro para la contraseña.
    
    Args:
        password (str): Contraseña a hashear.
        
    Returns:
        str: Hash de la contraseña.
    """
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password, role="Usuario"):
    """
    Crea un nuevo usuario en el sistema.
    
    Args:
        username (str): Nombre de usuario.
        password (str): Contraseña sin hashear.
        role (str): Rol del usuario ("Usuario" o "Administrador").
        
    Returns:
        bool: True si el usuario se creó correctamente, False si ya existe.
    """
    # Verificar si el archivo de usuarios existe
    if not os.path.exists(USERS_FILE):
        init_user_system()
    
    # Cargar usuarios existentes
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        users = json.load(f)
    
    # Verificar si el username es válido (no vacío y sin espacios)
    if not username or ' ' in username:
        return False
    
    # Verificar si el usuario ya existe
    if any(user["username"] == username for user in users):
        return False
    
    # Crear usuario nuevo
    new_user = {
        "username": username,
        "password": hash_password(password),
        "role": role,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "last_login": None
    }
    
    # Agregar usuario a la lista
    users.append(new_user)
    
    # Guardar usuarios actualizados
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2)
    
    # Crear directorio para los datos de este usuario
    os.makedirs(f"data/users/{username}", exist_ok=True)
    
    return True

def authenticate_user(username, password):
    """
    Autentica a un usuario en el sistema.
    
    Args:
        username (str): Nombre de usuario.
        password (str): Contraseña sin hashear.
        
    Returns:
        dict: Información del usuario si la autenticación es exitosa, None en caso contrario.
    """
    # Verificar si el archivo de usuarios existe
    if not os.path.exists(USERS_FILE):
        init_user_system()
    
    # Cargar usuarios existentes
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        users = json.load(f)
    
    # Buscar el usuario
    hashed_password = hash_password(password)
    for user in users:
        if user["username"] == username and user["password"] == hashed_password:
            # Actualizar último inicio de sesión
            user["last_login"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Guardar usuarios actualizados
            with open(USERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(users, f, indent=2)
            
            return user
    
    return None

def get_all_users():
    """
    Obtiene la lista de todos los usuarios del sistema.
    
    Returns:
        list: Lista de diccionarios con información de usuarios.
    """
    # Verificar si el archivo de usuarios existe
    if not os.path.exists(USERS_FILE):
        init_user_system()
    
    # Cargar usuarios existentes
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        users = json.load(f)
    
    return users

def change_password(username, new_password):
    """
    Cambia la contraseña de un usuario.
    
    Args:
        username (str): Nombre de usuario.
        new_password (str): Nueva contraseña sin hashear.
        
    Returns:
        bool: True si el cambio fue exitoso, False si el usuario no existe.
    """
    # Verificar si el archivo de usuarios existe
    if not os.path.exists(USERS_FILE):
        init_user_system()
    
    # Cargar usuarios existentes
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        users = json.load(f)
    
    # Buscar el usuario y actualizar contraseña
    for user in users:
        if user["username"] == username:
            user["password"] = hash_password(new_password)
            
            # Guardar usuarios actualizados
            with open(USERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(users, f, indent=2)
            
            return True
    
    return False

def delete_user(username):
    """
    Elimina un usuario del sistema.
    
    Args:
        username (str): Nombre de usuario a eliminar.
        
    Returns:
        bool: True si el usuario se eliminó correctamente, False si no existe.
    """
    # Verificar si el archivo de usuarios existe
    if not os.path.exists(USERS_FILE):
        init_user_system()
    
    # No permitir eliminar al usuario admin
    if username == "admin":
        return False
    
    # Cargar usuarios existentes
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        users = json.load(f)
    
    # Buscar y eliminar el usuario
    for i, user in enumerate(users):
        if user["username"] == username:
            del users[i]
            
            # Guardar usuarios actualizados
            with open(USERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(users, f, indent=2)
            
            # Eliminar directorio de datos del usuario (opcional)
            user_data_dir = f"data/users/{username}"
            if os.path.exists(user_data_dir):
                shutil.rmtree(user_data_dir)
            
            return True
    
    return False

def get_user_data_path(username):
    """
    Obtiene la ruta de los datos de un usuario específico.
    
    Args:
        username (str): Nombre de usuario.
        
    Returns:
        str: Ruta del directorio de datos del usuario.
    """
    user_data_dir = f"data/users/{username}"
    os.makedirs(user_data_dir, exist_ok=True)
    return user_data_dir

def login_form():
    """
    Muestra un formulario de inicio de sesión.
    
    Returns:
        dict: Información del usuario si el inicio de sesión es exitoso, None en caso contrario.
    """
    with st.form("login_form"):
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Iniciar Sesión")
        
        if submitted:
            if not username or not password:
                st.error("Por favor, complete todos los campos")
                return None
            
            user = authenticate_user(username, password)
            
            if user:
                st.success(f"Bienvenido, {username}!")
                return user
            else:
                st.error("Usuario o contraseña incorrectos")
    
    return None

def admin_user_management():
    """
    Muestra la interfaz mejorada de administración de usuarios para administradores.
    """
    st.subheader("Administración de Usuarios")
    
    # Verificar si el usuario actual es administrador
    if "user" not in st.session_state or st.session_state.user["role"] != "Administrador":
        st.error("No tienes permiso para acceder a esta sección.")
        return
    
    # Obtener todos los usuarios
    users = get_all_users()
    
    # Crear nuevo usuario (destacado y más visible)
    st.markdown("### Crear Nuevo Usuario")
    
    with st.form("create_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_username = st.text_input("Nombre de Usuario")
            new_password = st.text_input("Contraseña", type="password")
        
        with col2:
            confirm_password = st.text_input("Confirmar Contraseña", type="password")
            new_role = st.selectbox("Rol", USER_ROLES)
        
        submitted = st.form_submit_button("Crear Usuario", use_container_width=True)
        
        if submitted:
            if not new_username or not new_password:
                st.error("Por favor, complete todos los campos")
            elif ' ' in new_username:
                st.error("El nombre de usuario no puede contener espacios")
            elif new_password != confirm_password:
                st.error("Las contraseñas no coinciden")
            else:
                success = create_user(new_username, new_password, new_role)
                
                if success:
                    st.success(f"Usuario {new_username} creado correctamente")
                    st.rerun()
                else:
                    st.error(f"El usuario {new_username} ya existe o es inválido")
    
    # Mostrar tabla de usuarios existentes
    st.markdown("### Usuarios Existentes")
    
    users_df = []
    for user in users:
        users_df.append({
            "Usuario": user["username"],
            "Rol": user["role"],
            "Creado": user["created_at"],
            "Último Acceso": user["last_login"] or "Nunca"
        })
    
    import pandas as pd
    users_table = pd.DataFrame(users_df)
    st.dataframe(users_table, use_container_width=True)
    
    # Gestión de contraseñas
    st.markdown("### Gestión de Contraseñas")
    
    with st.form("change_password_form"):
        username_to_change = st.selectbox(
            "Seleccione Usuario",
            [user["username"] for user in users]
        )
        
        new_password = st.text_input("Nueva Contraseña", type="password", key="new_pwd")
        confirm_new_password = st.text_input("Confirmar Contraseña", type="password", key="confirm_pwd")
        
        submitted = st.form_submit_button("Cambiar Contraseña")
        
        if submitted:
            if not new_password:
                st.error("Por favor, ingrese una nueva contraseña")
            elif new_password != confirm_new_password:
                st.error("Las contraseñas no coinciden")
            else:
                success = change_password(username_to_change, new_password)
                
                if success:
                    st.success(f"Contraseña de {username_to_change} actualizada correctamente")
    
    # Eliminar usuarios
    st.markdown("### Eliminar Usuario")
    
    with st.form("delete_user_form"):
        # Filtrar para no mostrar el usuario admin en las opciones
        deletable_users = [user["username"] for user in users if user["username"] != "admin" 
                          and user["username"] != st.session_state.user["username"]]
        
        if not deletable_users:
            st.info("No hay usuarios que puedas eliminar.")
            st.form_submit_button("Eliminar Usuario", disabled=True)
        else:
            username_to_delete = st.selectbox(
                "Seleccione Usuario a Eliminar",
                deletable_users
            )
            
            confirm_delete = st.checkbox("Confirmo que deseo eliminar este usuario permanentemente")
            
            submitted = st.form_submit_button("Eliminar Usuario")
            
            if submitted:
                if not confirm_delete:
                    st.error("Debes confirmar la eliminación")
                else:
                    success = delete_user(username_to_delete)
                    
                    if success:
                        st.success(f"Usuario {username_to_delete} eliminado correctamente")
                        st.rerun()
                    else:
                        st.error(f"Error al eliminar el usuario {username_to_delete}")

def admin_view_user_data():
    """
    Permite a los administradores ver los datos de otros usuarios.
    """
    st.subheader("Ver Datos de Usuarios")
    
    # Verificar si el usuario actual es administrador
    if "user" not in st.session_state or st.session_state.user["role"] != "Administrador":
        st.error("No tienes permiso para acceder a esta sección.")
        return
    
    # Obtener todos los usuarios
    users = get_all_users()
    
    # Filtrar para mostrar solo usuarios (no administradores)
    regular_users = [user["username"] for user in users if user["role"] != "Administrador" 
                   or user["username"] != st.session_state.user["username"]]
    
    if not regular_users:
        st.info("No hay usuarios regulares para visualizar.")
        return
    
    # Seleccionar usuario
    username_to_view = st.selectbox(
        "Seleccione Usuario",
        regular_users
    )
    
    if username_to_view:
        user_data_path = get_user_data_path(username_to_view)
        
        # Verificar si el usuario tiene archivos de datos
        if os.path.exists(user_data_path):
            st.success(f"Mostrando datos del usuario: {username_to_view}")
            
            # Mostrar archivos disponibles
            files = os.listdir(user_data_path)
            
            if files:
                st.write("Archivos disponibles:")
                
                for file in files:
                    file_path = os.path.join(user_data_path, file)
                    file_size = os.path.getsize(file_path)
                    file_modified = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M:%S")
                    
                    st.write(f"- **{file}** (Tamaño: {file_size/1024:.1f} KB, Modificado: {file_modified})")
                    
                    # Si es un archivo Excel o JSON, ofrecer visualización
                    if file.endswith('.xlsx'):
                        if st.button(f"Ver contenido de {file}", key=f"view_{file}"):
                            try:
                                import pandas as pd
                                excel = pd.ExcelFile(file_path)
                                
                                for sheet_name in excel.sheet_names:
                                    st.write(f"**Hoja: {sheet_name}**")
                                    df = excel.parse(sheet_name)
                                    st.dataframe(df)
                            except Exception as e:
                                st.error(f"Error al leer el archivo: {e}")
                    
                    elif file.endswith('.json'):
                        if st.button(f"Ver contenido de {file}", key=f"view_{file}"):
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                st.json(data)
                            except Exception as e:
                                st.error(f"Error al leer el archivo: {e}")
            else:
                st.info(f"El usuario {username_to_view} no tiene archivos de datos")
        else:
            st.warning(f"No hay datos disponibles para el usuario {username_to_view}")

def generate_user_report():
    """
    Genera un informe de todos los usuarios del sistema y su actividad.
    """
    st.subheader("Informe de Usuarios")
    
    # Verificar si el usuario actual es administrador
    if "user" not in st.session_state or st.session_state.user["role"] != "Administrador":
        st.error("No tienes permiso para acceder a esta sección.")
        return
    
    # Obtener todos los usuarios
    users = get_all_users()
    
    # Preparar datos del informe
    report_data = []
    for user in users:
        user_data_path = get_user_data_path(user["username"])
        
        # Contar archivos
        file_count = 0
        total_size = 0
        
        if os.path.exists(user_data_path):
            files = os.listdir(user_data_path)
            file_count = len(files)
            
            # Calcular tamaño total
            for file in files:
                file_path = os.path.join(user_data_path, file)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)
        
        # Calcular días desde último acceso
        last_login = user.get("last_login")
        if last_login:
            try:
                last_login_date = datetime.strptime(last_login, "%Y-%m-%d %H:%M:%S")
                days_since_login = (datetime.now() - last_login_date).days
            except:
                days_since_login = "N/A"
        else:
            days_since_login = "Nunca"
        
        # Añadir datos al informe
        report_data.append({
            "Usuario": user["username"],
            "Rol": user["role"],
            "Archivos": file_count,
            "Tamaño Total (KB)": round(total_size / 1024, 2),
            "Último Acceso": user.get("last_login", "Nunca"),
            "Días desde último acceso": days_since_login,
            "Fecha de Creación": user.get("created_at", "Desconocida")
        })
    
    # Mostrar informe
    import pandas as pd
    report_df = pd.DataFrame(report_data)
    st.dataframe(report_df, use_container_width=True)
    
    # Generar gráficos
    st.subheader("Análisis Gráfico")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de roles
        import matplotlib.pyplot as plt
        import numpy as np
        
        roles = [user["role"] for user in users]
        role_counts = {}
        
        for role in roles:
            if role in role_counts:
                role_counts[role] += 1
            else:
                role_counts[role] = 1
        
        fig, ax = plt.subplots()
        ax.pie(role_counts.values(), labels=role_counts.keys(), autopct='%1.1f%%')
        ax.set_title("Distribución de Roles")
        st.pyplot(fig)
    
    with col2:
        # Gráfico de actividad
        active_users = sum(1 for user in users if user.get("last_login") is not None)
        inactive_users = len(users) - active_users
        
        activity_data = {"Activos": active_users, "Nunca conectados": inactive_users}
        
        fig, ax = plt.subplots()
        ax.bar(activity_data.keys(), activity_data.values())
        ax.set_title("Actividad de Usuarios")
        st.pyplot(fig)