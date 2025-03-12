import pandas as pd
import os
from io import BytesIO
import re
import streamlit as st

def verificar_archivos_requeridos(archivos, mostrar_error=True):
    """
    Verifica si los archivos requeridos existen.
    
    Args:
        archivos (list): Lista de rutas de archivos a verificar.
        mostrar_error (bool): Si es True, muestra un mensaje de error en Streamlit.
        
    Returns:
        bool: True si todos los archivos existen, False en caso contrario.
    """
    archivos_faltantes = [archivo for archivo in archivos if not os.path.exists(archivo)]
    
    if archivos_faltantes:
        if mostrar_error:
            st.error(f"No se encontraron los siguientes archivos: {', '.join(archivos_faltantes)}")
        return False
    return True

def limpiar_nombre_columna(nombre):
    """
    Normaliza el nombre de una columna:
    - Convierte a minúsculas
    - Elimina espacios al inicio y final
    - Reemplaza espacios internos por underscore
    - Elimina caracteres especiales
    
    Args:
        nombre (str): Nombre de la columna a normalizar.
        
    Returns:
        str: Nombre de columna normalizado.
    """
    # Convertir a minúsculas y eliminar espacios al inicio y final
    nombre = nombre.lower().strip()
    
    # Eliminar caracteres especiales y reemplazar espacios por guiones bajos
    nombre = re.sub(r'[^\w\s]', '', nombre)
    nombre = re.sub(r'\s+', '_', nombre)
    
    return nombre

def normalizar_dataframe(df, mapeo_columnas=None):
    """
    Normaliza un DataFrame:
    - Limpia los nombres de las columnas
    - Aplica un mapeo de nombres si se proporciona
    
    Args:
        df (DataFrame): DataFrame a normalizar.
        mapeo_columnas (dict, optional): Diccionario de mapeo de nombres {nombre_actual: nombre_deseado}.
        
    Returns:
        DataFrame: DataFrame normalizado.
    """
    # Limpiar nombres de columnas
    df.columns = [limpiar_nombre_columna(col) for col in df.columns]
    
    # Aplicar mapeo si se proporciona
    if mapeo_columnas:
        df = df.rename(columns=mapeo_columnas)
    
    return df

def consolidar_hojas_excel(archivo_excel, columna_adicional=None):
    """
    Consolida todas las hojas de un archivo Excel en un solo DataFrame,
    opcionalmente añadiendo el nombre de la hoja como una columna.
    
    Args:
        archivo_excel (str or BytesIO): Ruta al archivo Excel o objeto BytesIO.
        columna_adicional (str, optional): Nombre de la columna para guardar el nombre de la hoja.
        
    Returns:
        DataFrame: DataFrame consolidado con todas las hojas.
    """
    try:
        excel = pd.ExcelFile(archivo_excel)
        
        # Concatenar todas las hojas
        if columna_adicional:
            dfs = [excel.parse(sheet).assign(**{columna_adicional: sheet}) 
                   for sheet in excel.sheet_names]
        else:
            dfs = [excel.parse(sheet) for sheet in excel.sheet_names]
            
        # Concatenar todos los DataFrames
        return pd.concat(dfs, ignore_index=True)
        
    except Exception as e:
        st.error(f"Error al consolidar las hojas de Excel: {e}")
        return pd.DataFrame()  # Devolver DataFrame vacío en caso de error

def guardar_dataframe_por_hojas(df, archivo_destino, columna_agrupacion, motor='openpyxl'):
    """
    Guarda un DataFrame en un archivo Excel, separando los datos en hojas
    basadas en una columna de agrupación.
    
    Args:
        df (DataFrame): DataFrame a guardar.
        archivo_destino (str or BytesIO): Ruta de destino o objeto BytesIO.
        columna_agrupacion (str): Nombre de la columna para agrupar y separar por hojas.
        motor (str): Motor de Excel a utilizar ('openpyxl', 'xlsxwriter').
        
    Returns:
        bool: True si se guardó correctamente, False en caso de error.
    """
    try:
        with pd.ExcelWriter(archivo_destino, engine=motor) as writer:
            for nombre_grupo, grupo in df.groupby(columna_agrupacion):
                # Limitar el nombre de la hoja a 31 caracteres (límite de Excel)
                nombre_hoja = str(nombre_grupo)[:31]
                grupo.to_excel(writer, sheet_name=nombre_hoja, index=False)
        return True
    except Exception as e:
        st.error(f"Error al guardar el archivo Excel: {e}")
        return False

def crear_archivo_descargable(df, nombre_archivo, formato='excel'):
    """
    Crea un archivo descargable a partir de un DataFrame.
    
    Args:
        df (DataFrame): DataFrame a convertir.
        nombre_archivo (str): Nombre del archivo a generar (sin extensión).
        formato (str): Formato de salida ('excel', 'csv').
        
    Returns:
        tuple: (BytesIO, str) con el archivo y su tipo MIME.
    """
    output = BytesIO()
    
    if formato.lower() == 'excel':
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        nombre_archivo += ".xlsx"
    elif formato.lower() == 'csv':
        df.to_csv(output, index=False)
        mime = "text/csv"
        nombre_archivo += ".csv"
    else:
        raise ValueError(f"Formato no soportado: {formato}")
    
    output.seek(0)
    return output, nombre_archivo, mime

def generar_boton_descarga(df, texto_boton, nombre_archivo, formato='excel'):
    """
    Genera un botón de descarga para un DataFrame en Streamlit.
    
    Args:
        df (DataFrame): DataFrame a descargar.
        texto_boton (str): Texto a mostrar en el botón.
        nombre_archivo (str): Nombre del archivo a generar (sin extensión).
        formato (str): Formato de salida ('excel', 'csv').
        
    Returns:
        bool: True si se hizo clic en el botón, False en caso contrario.
    """
    try:
        archivo, nombre, mime = crear_archivo_descargable(df, nombre_archivo, formato)
        return st.download_button(
            label=texto_boton,
            data=archivo,
            file_name=nombre,
            mime=mime
        )
    except Exception as e:
        st.error(f"Error al generar el botón de descarga: {e}")
        return False