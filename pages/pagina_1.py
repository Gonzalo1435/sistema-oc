import streamlit as st
import pandas as pd
from io import BytesIO
from utils.pdf_extraction import extract_data_from_pdf
import hashlib


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

    st.write("""
    En esta página puedes subir archivos PDF de órdenes de compra, 
    extraer los datos relevantes y guardarlos en un archivo Excel.
    """)

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

        # Extraer datos de los PDFs
        extracted_data = []
        for uploaded_file in unique_files_list:
            pdf_data = extract_data_from_pdf(uploaded_file, processed_orders)  # Pasar processed_orders aquí
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
            st.download_button(
                label="📥 Descargar Excel con Datos Extraídos",
                data=towrite,
                file_name="ordenes_de_compra.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("No se pudieron extraer datos de los PDFs o todas las órdenes de compra estaban duplicadas.")