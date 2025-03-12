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

# Copia todas las funciones de tu app.py aquí, sin modificarlas
# Por ejemplo:

def obtener_estadisticas():
    """
    Obtiene estadísticas de los archivos de control para mostrar en el dashboard.
    """
    # Contenido de la función original de app.py
    pass

def mostrar_encabezado():
    """
    Muestra el encabezado con métricas y logo.
    """
    # Contenido de la función original de app.py
    pass

def mostrar_sidebar_mejorado():
    """
    Muestra el menú de navegación en la barra lateral con estilos mejorados.
    """
    # Contenido de la función original de app.py
    pass

def mostrar_navbar():
    """
    Muestra una barra de navegación en la parte superior con botones para cada página.
    """
    # Contenido de la función original de app.py
    pass

def mostrar_graficos_dashboard():
    """
    Muestra gráficos en el dashboard.
    """
    # Contenido de la función original de app.py
    pass

def mostrar_pagina_inicio():
    """
    Muestra la página de inicio.
    """
    # Contenido de la función original de app.py
    pass

def manejar_configuracion_avanzada():
    """
    Maneja la sección de configuración avanzada.
    """
    # Contenido de la función original de app.py
    pass

def main():
    """
    Función principal que define el flujo de la aplicación.
    """
    # Inicializar variables de estado si no existen
    if 'pagina_seleccionada' not in st.session_state:
        st.session_state.pagina_seleccionada = "Inicio"
    if 'mostrar_config_avanzada' not in st.session_state:
        st.session_state.mostrar_config_avanzada = False
    if 'admin_autenticado' not in st.session_state:
        st.session_state.admin_autenticado = False
    
    # Asegurar que las carpetas de datos específicas del usuario existan
    if "user" in st.session_state and st.session_state.user:
        # Obtener ruta de datos del usuario
        user_data_path = f"data/users/{st.session_state.user['username']}"
        os.makedirs(user_data_path, exist_ok=True)
    
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