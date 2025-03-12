import streamlit as st
import pandas as pd
from io import BytesIO
import os
import hashlib
from utils.pdf_extraction import extract_data_from_pdf

# Importar funciones de gestión de usuarios
from user_management import get_user_data_path


def generate_file_hash(file):
    """
    Genera un hash único para un archivo basado en su contenido.
    """
    file.seek(0)
    content = file.read()
    file.seek(0)
    return hashlib.md5(content).hexdigest()


def format_rut(rut):
    """
    Formatea un RUT en el formato XX.XXX.XXX-X (si no lo está).
    """
    if rut and len(rut) > 1:
        rut = rut.replace(".", "").replace("-", "")
        return f"{rut[:-8]}.{rut[-8:-5]}.{rut[-5:-2]}-{rut[-1]}"
    return rut


def pagina_1():
    st.title("Página 1: Subida de PDFs y Extracción de Datos")

    # Verificar si hay un usuario autenticado
    if "user" not in st.session_state or not st.session_state.user:
        st.error("Debes iniciar sesión para acceder a esta funcionalidad.")
        return
    
    # Obtener ID del usuario actual
    current_user = st.session_state.user["username"]
    
    # Obtener ruta de datos del usuario
    user_data_path = get_user_data_path(current_user)
    
    # Mostrar información del usuario
    st.info(f"Usuario actual: {current_user} ({st.session_state.user['role']})")

    st.write("""
    En esta página puedes subir archivos PDF de órdenes de compra, 
    extraer los datos relevantes y guardarlos en tu perfil de usuario.
    """)

    # Ruta del archivo de órdenes específica para este usuario
    user_orders_file = os.path.join(user_data_path, "ordenes_de_compra.xlsx")
    
    # Subida de archivos PDF
    uploaded_files = st.file_uploader(
        "Sube uno o más archivos PDF",
        type=["pdf"],
        accept_multiple_files=True
    )

    if uploaded_files:
        # Verificar archivos duplicados
        unique_files = {}
        st.write("Archivos subidos:")

        for uploaded_file in uploaded_files:
            file_hash = generate_file_hash(uploaded_file)
            if file_hash not in unique_files:
                unique_files[file_hash] = uploaded_file
                st.write(f"- {uploaded_file.name}")
            else:
                st.warning(f"El archivo '{uploaded_file.name}' ya fue subido y será ignorado.")

        unique_files_list = list(unique_files.values())

        # Inicializar conjunto para rastrear órdenes de compra procesadas
        processed_orders = set()
        
        # Cargar órdenes existentes para evitar duplicados
        if os.path.exists(user_orders_file):
            try:
                existing_orders = pd.read_excel(user_orders_file)
                if "Orden de Compra" in existing_orders.columns:
                    # Añadir al conjunto de órdenes procesadas
                    for order in existing_orders["Orden de Compra"]:
                        if order and not pd.isna(order):
                            processed_orders.add(f"{current_user}_{order}")
                    st.info(f"Se encontraron {len(processed_orders)} órdenes de compra existentes.")
            except Exception as e:
                st.warning(f"Error al cargar órdenes existentes: {e}")

        # Extraer datos de los PDFs
        extracted_data = []
        for uploaded_file in unique_files_list:
            # Pasar el ID del usuario para evitar duplicados entre usuarios diferentes
            pdf_data = extract_data_from_pdf(uploaded_file, processed_orders, current_user)
            if pdf_data:
                # Formatear RUT
                if "RUT Proveedor" in pdf_data:
                    pdf_data["RUT Proveedor"] = format_rut(pdf_data["RUT Proveedor"])
                extracted_data.append(pdf_data)

        # Si se extrajeron datos, mostrarlos y permitir la descarga
        if extracted_data:
            df = pd.DataFrame(extracted_data)

            st.subheader("Datos Extraídos")
            st.dataframe(df)

            # Generar archivo Excel para descarga
            towrite = BytesIO()
            df.to_excel(towrite, index=False, engine='openpyxl')
            towrite.seek(0)
            
            # Opción para descargar
            col1, col2 = st.columns(2)
            
            with col1:
                st.download_button(
                    label="📥 Descargar Excel con Datos Extraídos",
                    data=towrite,
                    file_name="ordenes_de_compra.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            # Opción para guardar en la carpeta del usuario
            with col2:
                if st.button("💾 Guardar en Mi Perfil", type="primary"):
                    try:
                        # Crear directorio de usuario si no existe
                        os.makedirs(user_data_path, exist_ok=True)
                        
                        # Verificar si existe un archivo previo para concatenar
                        if os.path.exists(user_orders_file):
                            # Cargar archivo existente
                            existing_df = pd.read_excel(user_orders_file)
                            
                            # Concatenar con los nuevos datos
                            combined_df = pd.concat([existing_df, df], ignore_index=True)
                            
                            # Guardar archivo combinado
                            combined_df.to_excel(user_orders_file, index=False, engine='openpyxl')
                            st.success(f"✅ Datos añadidos a tu archivo existente: {user_orders_file}")
                        else:
                            # Guardar nuevo archivo
                            df.to_excel(user_orders_file, index=False, engine='openpyxl')
                            st.success(f"✅ Datos guardados en tu perfil: {user_orders_file}")
                            
                    except Exception as e:
                        st.error(f"❌ Error al guardar el archivo: {e}")
        else:
            st.error("No se pudieron extraer datos de los PDFs o todas las órdenes de compra estaban duplicadas.")