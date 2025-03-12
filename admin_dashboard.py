import streamlit as st
import pandas as pd
import os
import json
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from user_management import get_all_users, get_user_data_path

def mostrar_dashboard_admin():
    """
    Muestra el dashboard de administración con estadísticas de todos los usuarios.
    """
    st.title("Panel de Administración")
    
    # Obtener todos los usuarios
    users = get_all_users()
    
    # Filtrar solo usuarios normales (no admin)
    normal_users = [user for user in users if user.get("role") != "Administrador"]
    
    # Mostrar resumen de usuarios
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total de Usuarios", len(users))
    
    with col2:
        st.metric("Usuarios Normales", len(normal_users))
    
    with col3:
        admins = len(users) - len(normal_users)
        st.metric("Administradores", admins)
    
    # Gráfico de último acceso de usuarios
    st.subheader("Actividad de Usuarios")
    
    # Preparar datos para el gráfico
    user_activity = []
    for user in users:
        last_login = user.get("last_login")
        if last_login:
            try:
                last_login_date = datetime.strptime(last_login, "%Y-%m-%d %H:%M:%S")
                days_ago = (datetime.now() - last_login_date).days
                user_activity.append({
                    "username": user["username"],
                    "last_login": last_login,
                    "days_ago": days_ago
                })
            except:
                user_activity.append({
                    "username": user["username"],
                    "last_login": "Desconocido",
                    "days_ago": 999
                })
        else:
            user_activity.append({
                "username": user["username"],
                "last_login": "Nunca",
                "days_ago": 999
            })
    
    # Ordenar por días de inactividad
    user_activity = sorted(user_activity, key=lambda x: x["days_ago"])
    
    # Crear DataFrame
    df_activity = pd.DataFrame(user_activity)
    
    # Mostrar tabla
    st.dataframe(df_activity)
    
    # Mostrar estadísticas por usuario
    st.subheader("Estadísticas por Usuario")
    
    # Seleccionar usuario para ver detalles
    selected_user = st.selectbox(
        "Seleccionar Usuario para Ver Detalles",
        [user["username"] for user in users]
    )
    
    if selected_user:
        mostrar_estadisticas_usuario(selected_user)

def mostrar_estadisticas_usuario(username):
    """
    Muestra estadísticas detalladas de un usuario específico.
    
    Args:
        username (str): Nombre del usuario.
    """
    user_data_path = get_user_data_path(username)
    
    # Definir rutas de archivos del usuario
    ordenes_file = os.path.join(user_data_path, "control_de_ordenes_de_compra.xlsx")
    gastos_file = os.path.join(user_data_path, "control_de_gasto_de_licitaciones.xlsx")
    summary_file = os.path.join(user_data_path, "resumen_control_licitaciones.json")
    certificados_file = os.path.join(user_data_path, "registro_certificados.json")
    
    # Verificar si existen archivos
    files_exist = os.path.exists(ordenes_file) or os.path.exists(gastos_file) or os.path.exists(summary_file)
    
    if not files_exist:
        st.warning(f"El usuario {username} no tiene datos registrados aún.")
        return
    
    # Estadísticas de órdenes
    if os.path.exists(ordenes_file):
        try:
            # Leer archivo de órdenes
            ordenes_excel = pd.ExcelFile(ordenes_file)
            
            # Obtener lista de licitaciones
            licitaciones = ordenes_excel.sheet_names
            
            # Contar órdenes totales y certificadas
            ordenes_totales = 0
            ordenes_certificadas = 0
            
            for sheet in licitaciones:
                df = ordenes_excel.parse(sheet)
                df.columns = [col.lower() for col in df.columns]
                
                ordenes_totales += len(df)
                
                if "certificado" in df.columns:
                    # Valores positivos para certificado
                    valores_positivos = ["sí", "si", "yes", "s", "y", "true", "1"]
                    ordenes_certificadas += df["certificado"].astype(str).str.lower().isin(valores_positivos).sum()
            
            # Mostrar métricas de órdenes
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Licitaciones", len(licitaciones))
            
            with col2:
                st.metric("Órdenes Totales", ordenes_totales)
            
            with col3:
                st.metric("Órdenes Certificadas", ordenes_certificadas)
            
            # Crear gráfico de órdenes
            if ordenes_totales > 0:
                fig, ax = plt.subplots(figsize=(6, 6))
                
                # Datos para el gráfico
                labels = ["Con Certificado", "Sin Certificado"]
                sizes = [ordenes_certificadas, ordenes_totales - ordenes_certificadas]
                explode = (0.1, 0)
                colors = ["lightgreen", "lightcoral"]
                
                # Crear gráfico de torta
                ax.pie(sizes, explode=explode, labels=labels, colors=colors,
                      autopct="%1.1f%%", shadow=True, startangle=90)
                ax.axis("equal")
                
                # Título
                plt.title(f"Órdenes de Compra de {username}")
                
                # Mostrar gráfico
                st.pyplot(fig)
        except Exception as e:
            st.error(f"Error al leer el archivo de órdenes: {e}")
    
    # Estadísticas de resumenes
    if os.path.exists(summary_file):
        try:
            with open(summary_file, "r", encoding="utf-8") as f:
                resumenes = json.load(f)
            
            if resumenes:
                # Crear gráfico de distribución de presupuesto
                mostrar_grafico_presupuesto(resumenes, username)
                
                # Mostrar tabla resumen
                st.subheader("Resumen de Licitaciones")
                
                # Preparar datos para la tabla
                tabla_resumenes = []
                for resumen in resumenes:
                    tabla_resumenes.append({
                        "Licitación": resumen.get("numero_licitacion", ""),
                        "Estado": resumen.get("estado", ""),
                        "Presupuesto Total": resumen.get("presupuesto_total", 0),
                        "Ejecutado": resumen.get("presupuesto_ejecutado", 0),
                        "Disponible": resumen.get("presupuesto_disponible", 0),
                        "% Ejecución": resumen.get("porcentaje_ejecucion", 0)
                    })
                
                # Mostrar tabla
                df_resumenes = pd.DataFrame(tabla_resumenes)
                st.dataframe(df_resumenes)
        except Exception as e:
            st.error(f"Error al leer el archivo de resúmenes: {e}")
    
    # Estadísticas de certificados
    if os.path.exists(certificados_file):
        try:
            with open(certificados_file, "r", encoding="utf-8") as f:
                certificados = json.load(f)
            
            if certificados:
                st.subheader("Certificados Generados")
                
                # Preparar datos para la tabla
                tabla_certificados = []
                for cert in certificados:
                    tabla_certificados.append({
                        "Orden de Compra": cert.get("orden_de_compra", ""),
                        "Proveedor": cert.get("proveedor", ""),
                        "Monto": cert.get("monto", 0),
                        "Tipo": cert.get("tipo_operacion", ""),
                        "Fecha Generación": cert.get("fecha_generacion", ""),
                        "Licitación": cert.get("licitacion", "")
                    })
                
                # Mostrar tabla
                df_certificados = pd.DataFrame(tabla_certificados)
                st.dataframe(df_certificados)
        except Exception as e:
            st.error(f"Error al leer el archivo de certificados: {e}")

def mostrar_grafico_presupuesto(resumenes, username):
    """
    Muestra un gráfico de barras con la distribución de presupuesto.
    
    Args:
        resumenes (list): Lista de diccionarios con información de licitaciones.
        username (str): Nombre del usuario.
    """
    # Preparar datos para el gráfico
    licitaciones = []
    presupuesto_disponible = []
    presupuesto_ejecutado = []
    presupuesto_certificado = []
    
    for resumen in resumenes:
        licitaciones.append(resumen.get("numero_licitacion", ""))
        presupuesto_disponible.append(resumen.get("presupuesto_disponible", 0))
        
        # Calcular el presupuesto ejecutado sin certificado
        ejecutado_sin_cert = resumen.get("presupuesto_ejecutado", 0) - resumen.get("presupuesto_certificado", 0)
        presupuesto_ejecutado.append(ejecutado_sin_cert)
        
        presupuesto_certificado.append(resumen.get("presupuesto_certificado", 0))
    
    # Crear gráfico
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Ancho de las barras
    width = 0.8
    
    # Crear barras apiladas
    ax.bar(licitaciones, presupuesto_disponible, width, label="Disponible", color="lightgray")
    ax.bar(licitaciones, presupuesto_ejecutado, width, bottom=presupuesto_disponible, 
           label="Ejecutado", color="skyblue")
    ax.bar(licitaciones, presupuesto_certificado, width, 
           bottom=np.array(presupuesto_disponible) + np.array(presupuesto_ejecutado), 
           label="Certificado", color="lightgreen")
    
    # Configuración del gráfico
    ax.set_title(f"Distribución de Presupuesto - Usuario: {username}")
    ax.set_xlabel("Número de Licitación")
    ax.set_ylabel("Monto ($)")
    ax.legend()
    
    # Rotar etiquetas del eje x si hay muchas licitaciones
    if len(licitaciones) > 5:
        plt.xticks(rotation=45, ha="right")
    
    plt.tight_layout()
    
    # Mostrar gráfico
    st.pyplot(fig)

def comparar_usuarios():
    """
    Muestra una comparación de estadísticas entre usuarios.
    """
    st.subheader("Comparación de Usuarios")
    
    # Obtener todos los usuarios
    users = get_all_users()
    
    # Filtrar solo usuarios normales (no admin)
    normal_users = [user for user in users if user.get("role") != "Administrador"]
    
    if len(normal_users) < 2:
        st.warning("Se necesitan al menos 2 usuarios normales para hacer una comparación.")
        return
    
    # Seleccionar usuarios para comparar
    col1, col2 = st.columns(2)
    
    with col1:
        user1 = st.selectbox(
            "Usuario 1",
            [user["username"] for user in normal_users],
            key="user1"
        )
    
    with col2:
        user2 = st.selectbox(
            "Usuario 2",
            [user["username"] for user in normal_users if user["username"] != user1],
            key="user2"
        )
    
    if user1 and user2 and user1 != user2:
        # Obtener estadísticas de ambos usuarios
        stats1 = obtener_estadisticas_usuario(user1)
        stats2 = obtener_estadisticas_usuario(user2)
        
        # Mostrar comparación
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(f"Usuario: {user1}")
            
            st.metric("Licitaciones", stats1["licitaciones"])
            st.metric("Órdenes Totales", stats1["ordenes_totales"])
            st.metric("Órdenes Certificadas", stats1["ordenes_certificadas"])
            st.metric("Presupuesto Total", f"${stats1['presupuesto_total']:,.0f}")
            st.metric("Presupuesto Ejecutado", f"${stats1['presupuesto_ejecutado']:,.0f}")
        
        with col2:
            st.subheader(f"Usuario: {user2}")
            
            st.metric("Licitaciones", stats2["licitaciones"])
            st.metric("Órdenes Totales", stats2["ordenes_totales"])
            st.metric("Órdenes Certificadas", stats2["ordenes_certificadas"])
            st.metric("Presupuesto Total", f"${stats2['presupuesto_total']:,.0f}")
            st.metric("Presupuesto Ejecutado", f"${stats2['presupuesto_ejecutado']:,.0f}")
        
        # Crear gráfico comparativo
        crear_grafico_comparativo(user1, stats1, user2, stats2)

def obtener_estadisticas_usuario(username):
    """
    Obtiene estadísticas de un usuario específico.
    
    Args:
        username (str): Nombre del usuario
        
    Returns:
        dict: Diccionario con estadísticas del usuario
    """
    # Inicializar diccionario de estadísticas
    stats = {
        "licitaciones": 0,
        "ordenes_totales": 0,
        "ordenes_certificadas": 0,
        "presupuesto_total": 0,
        "presupuesto_ejecutado": 0,
        "presupuesto_certificado": 0,
        "presupuesto_disponible": 0
    }
    
    # Obtener ruta de datos del usuario
    user_data_path = get_user_data_path(username)
    
    # Ruta de archivos del usuario
    ordenes_file = os.path.join(user_data_path, "control_de_ordenes_de_compra.xlsx")
    summary_file = os.path.join(user_data_path, "resumen_control_licitaciones.json")
    
    # Obtener datos de órdenes
    if os.path.exists(ordenes_file):
        try:
            ordenes_excel = pd.ExcelFile(ordenes_file)
            
            # Contar licitaciones (hojas)
            stats["licitaciones"] = len(ordenes_excel.sheet_names)
            
            # Contar órdenes totales y certificadas
            for sheet in ordenes_excel.sheet_names:
                df = ordenes_excel.parse(sheet)
                df.columns = [col.lower() for col in df.columns]
                
                stats["ordenes_totales"] += len(df)
                
                if "certificado" in df.columns:
                    # Valores positivos para certificado
                    valores_positivos = ["sí", "si", "yes", "s", "y", "true", "1"]
                    stats["ordenes_certificadas"] += df["certificado"].astype(str).str.lower().isin(valores_positivos).sum()
        except Exception as e:
            print(f"Error al leer el archivo de órdenes de {username}: {e}")
    
    # Obtener datos de resúmenes
    if os.path.exists(summary_file):
        try:
            with open(summary_file, "r", encoding="utf-8") as f:
                resumenes = json.load(f)
            
            # Sumar presupuestos
            for resumen in resumenes:
                stats["presupuesto_total"] += float(resumen.get("presupuesto_total", 0))
                stats["presupuesto_ejecutado"] += float(resumen.get("presupuesto_ejecutado", 0))
                stats["presupuesto_certificado"] += float(resumen.get("presupuesto_certificado", 0))
                stats["presupuesto_disponible"] += float(resumen.get("presupuesto_disponible", 0))
        except Exception as e:
            print(f"Error al leer el archivo de resúmenes de {username}: {e}")
    
    return stats

def crear_grafico_comparativo(user1, stats1, user2, stats2):
    """
    Crea un gráfico de barras comparativo entre dos usuarios.
    
    Args:
        user1 (str): Nombre del primer usuario
        stats1 (dict): Estadísticas del primer usuario
        user2 (str): Nombre del segundo usuario
        stats2 (dict): Estadísticas del segundo usuario
    """
    # Crear figura
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Datos para el primer gráfico - Órdenes
    categorias = ["Licitaciones", "Órdenes Totales", "Órdenes Certificadas"]
    valores_user1 = [stats1["licitaciones"], stats1["ordenes_totales"], stats1["ordenes_certificadas"]]
    valores_user2 = [stats2["licitaciones"], stats2["ordenes_totales"], stats2["ordenes_certificadas"]]
    
    x = np.arange(len(categorias))
    width = 0.35
    
    # Crear barras para el primer gráfico
    ax1.bar(x - width/2, valores_user1, width, label=user1, color='skyblue')
    ax1.bar(x + width/2, valores_user2, width, label=user2, color='lightgreen')
    
    # Configuración del primer gráfico
    ax1.set_title("Comparación de Órdenes")
    ax1.set_xticks(x)
    ax1.set_xticklabels(categorias)
    ax1.legend()
    
    # Datos para el segundo gráfico - Presupuestos
    categorias = ["Total", "Ejecutado", "Certificado", "Disponible"]
    valores_user1 = [
        stats1["presupuesto_total"], 
        stats1["presupuesto_ejecutado"], 
        stats1["presupuesto_certificado"],
        stats1["presupuesto_disponible"]
    ]
    valores_user2 = [
        stats2["presupuesto_total"], 
        stats2["presupuesto_ejecutado"], 
        stats2["presupuesto_certificado"],
        stats2["presupuesto_disponible"]
    ]
    
    x = np.arange(len(categorias))
    
    # Crear barras para el segundo gráfico
    ax2.bar(x - width/2, valores_user1, width, label=user1, color='skyblue')
    ax2.bar(x + width/2, valores_user2, width, label=user2, color='lightgreen')
    
    # Configuración del segundo gráfico
    ax2.set_title("Comparación de Presupuestos")
    ax2.set_xticks(x)
    ax2.set_xticklabels(categorias)
    ax2.set_ylabel("Monto ($)")
    ax2.legend()
    
    # Ajustar diseño
    plt.tight_layout()
    
    # Mostrar gráfico
    st.pyplot(fig)
    