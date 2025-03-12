import streamlit as st
import pandas as pd
import os
import sys
import json
from datetime import datetime
import matplotlib.pyplot as plt

# Verificar si Streamlit ya está configurado (será definido por auth_app.py)
if not getattr(__builtins__, 'STREAMLIT_ALREADY_CONFIGURED', False):
    # Configurar la página solo si se ejecuta directamente
    st.set_page_config(
        page_title="Sistema de Gestión de Órdenes y Licitaciones",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    # Marcar como configurado
    __builtins__.STREAMLIT_ALREADY_CONFIGURED = True

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

# Importar gestión de usuarios
from user_management import get_user_data_path

# Rutas de archivos importantes - Serán personalizadas por usuario
# Estas variables serán modificadas en auth_app.py al iniciar sesión
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

# Estilos CSS personalizados (el mismo código que en tu app.py original)
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
    
    /* Estilos para información de usuario */
    .user-info-box {
        background-color: #e3f2fd;
        border-radius: 10px;
        padding: 10px;
        margin-top: 15px;
        margin-bottom: 15px;
    }
    
    .user-info-title {
        font-weight: bold;
        font-size: 1.2rem;
        color: #1565C0;
    }
    
    .user-info-detail {
        font-size: 0.9rem;
        color: #333;
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
    # Código original modificado para usar rutas específicas del usuario
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