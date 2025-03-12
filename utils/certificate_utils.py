from io import BytesIO
import openpyxl
import os
from datetime import datetime

def generate_certificate(tipo_operacion, es_contrato, es_prorroga, unidad_medida,
                         aplica_multa, detalle_multa, observaciones,
                         nombre_funcionario, cargo_funcionario,
                         contraparte_tecnica, jefe_servicio, centro_costo,
                         selected_data, saldo_anterior, cantidad_ejecutada, saldo_disponible,
                         fecha_inicio, fecha_final, presupuesto_total,
                         id_compra, descripcion_servicio, rut, nombre_proveedor, referente_tecnico):
    """
    Genera un certificado de cumplimiento en formato Excel.

    Parámetros:
    - tipo_operacion: Tipo de operación (Mantenimiento o Arriendo).
    - es_contrato: Indica si es contrato (Sí o No).
    - es_prorroga: Indica si es prórroga (Sí o No).
    - unidad_medida: Unidad de medida (Pesos, Meses, Otros).
    - aplica_multa: Indica si aplica multa (Sí o No).
    - detalle_multa: Detalles de la multa (si aplica).
    - observaciones: Observaciones adicionales.
    - nombre_funcionario: Nombre del funcionario que emite el certificado.
    - cargo_funcionario: Cargo del funcionario.
    - contraparte_tecnica: Nombre de la contraparte técnica.
    - jefe_servicio: Nombre del jefe de servicio.
    - centro_costo: Centro de costo que recibe el servicio.
    - selected_data: Datos de la orden seleccionada.
    - saldo_anterior: Saldo anterior extraído del archivo de control de gastos.
    - cantidad_ejecutada: Cantidad ejecutada extraída del archivo de control de gastos.
    - saldo_disponible: Saldo disponible extraído del archivo de control de gastos.
    - fecha_inicio: Fecha de inicio del contrato.
    - fecha_final: Fecha de fin del contrato.
    - presupuesto_total: Total contratado para la licitación.
    - id_compra: ID de la compra (número de licitación).
    - descripcion_servicio: Descripción del servicio contratado.
    - rut: RUT del proveedor.
    - nombre_proveedor: Nombre del proveedor.
    - referente_tecnico: Nombre del referente técnico (igual al nombre del proveedor).

    Retorna:
    - BytesIO: Archivo Excel con el certificado generado.
    """
    # Rutas posibles de la plantilla
    TEMPLATE_PATHS = [
        "data/planilla_certificado.xlsx",           # Ruta original
        "templates/planilla_certificado.xlsx",      # Ruta en carpeta templates con extensión
        "templates/planilla_certificado",           # Ruta en carpeta templates sin extensión
        "planilla_certificado.xlsx",                # Ruta en directorio raíz con extensión
        "planilla_certificado"                      # Ruta en directorio raíz sin extensión
    ]
    
    # Buscar la plantilla en las rutas posibles
    template_path = None
    for path in TEMPLATE_PATHS:
        if os.path.exists(path):
            template_path = path
            break
            
    # Si no se encuentra, intentar buscar la plantilla en subdirectorios
    if template_path is None:
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file == 'planilla_certificado.xlsx' or file == 'planilla_certificado':
                    template_path = os.path.join(root, file)
                    break
            if template_path:
                break
    
    # Si aún no se encuentra, lanzar error
    if template_path is None:
        # Mostrar información de depuración
        current_dir = os.getcwd()
        print(f"Directorio actual: {current_dir}")
        print(f"Contenido del directorio actual: {os.listdir(current_dir)}")
        
        # Comprobar carpeta templates si existe
        templates_dir = os.path.join(current_dir, 'templates')
        if os.path.exists(templates_dir):
            print(f"Contenido de la carpeta templates: {os.listdir(templates_dir)}")
        
        # Comprobar carpeta data si existe
        data_dir = os.path.join(current_dir, 'data')
        if os.path.exists(data_dir):
            print(f"Contenido de la carpeta data: {os.listdir(data_dir)}")
            
        raise FileNotFoundError(f"No se encontró la plantilla 'planilla_certificado.xlsx' en ninguna ruta conocida. "
                              f"Ubicaciones verificadas: {TEMPLATE_PATHS}")

    try:
        # Cargar la plantilla
        wb = openpyxl.load_workbook(template_path)
        sheet = wb.active

        # Manejar fechas correctamente
        def format_date(date):
            if isinstance(date, str):
                try:
                    date = datetime.strptime(date, "%d-%m-%Y")
                except ValueError:
                    try:
                        date = datetime.strptime(date, "%Y-%m-%d")
                    except ValueError:
                        return "No disponible"
            if isinstance(date, datetime):
                return date.strftime("%d.%m.%Y")
            return "No disponible"

        fecha_inicio_formateada = format_date(fecha_inicio)
        fecha_final_formateada = format_date(fecha_final)

        # Validar datos requeridos
        id_compra = id_compra or "No disponible"
        descripcion_servicio = descripcion_servicio or "No disponible"
        rut = rut or "No disponible"
        nombre_proveedor = nombre_proveedor or "No disponible"
        referente_tecnico = referente_tecnico or nombre_proveedor

        # Imprimir información de depuración para verificar los datos
        print(f"Debug - ID Compra (Licitación): {id_compra}")
        print(f"Debug - ID Orden de Compra: {selected_data.get('orden_de_compra', 'No disponible')}")

        # Rellenar la plantilla con los datos proporcionados
        # Datos generales del establecimiento y la orden
        sheet["C8"] = selected_data.get("nombre_establecimiento", "HOSPITAL DE CAUQUENES")  # Nombre del establecimiento
        sheet["H8"] = selected_data.get("fecha_envio_oc", "")  # Fecha del certificado
        
        # CORRECCIÓN: Colocar ID Compra (número de licitación) en A15
        sheet["A15"] = id_compra  # ID Compra (número de licitación)
        
        sheet["B15"] = descripcion_servicio  # Descripción del servicio contratado
        sheet["D15"] = centro_costo  # Centro de costo que recibe el servicio
        
        # CORRECCIÓN: Colocar ID Orden de Compra en F16
        sheet["F16"] = selected_data.get("orden_de_compra", "")  # ID Orden de Compra

        # Datos del proveedor
        sheet["C21"] = rut  # Celda B21: RUT del proveedor
        sheet["F21"] = nombre_proveedor  # Celda F21: Nombre del proveedor
        sheet["C22"] = referente_tecnico  # Celda C22: Nombre del referente técnico

        # Fechas del contrato
        sheet["C17"] = fecha_inicio_formateada  # Fecha de inicio del contrato
        sheet["C18"] = fecha_final_formateada  # Fecha de fin del contrato

        # Datos financieros
        sheet["F18"] = presupuesto_total  # Total contratado
        sheet["A29"] = saldo_anterior  # Saldo Anterior
        sheet["B29"] = cantidad_ejecutada  # Cantidad Ejecutada
        sheet["C29"] = saldo_disponible  # Saldo Disponible

        # Unidad de medida
        sheet["D18"] = unidad_medida

        # Tipo de operación
        if tipo_operacion == "Mantenimiento":
            sheet["D11"] = "X"  # Marcar Mantenimiento
        elif tipo_operacion == "Arriendo":
            sheet["F11"] = "X"  # Marcar Arriendo

        # Contrato o prórroga
        if es_contrato == "Sí":
            sheet["B16"] = "X"  # Marcar Contrato
        if es_prorroga == "Sí":
            sheet["D16"] = "X"  # Marcar Prórroga

        # Multas
        if aplica_multa == "Sí":
            sheet["E29"] = "X"  # Marcar que aplica multa
            sheet["H29"] = detalle_multa  # Detalles de la multa
        else:
            sheet["G29"] = "X"  # Marcar que no aplica multa

        # Observaciones
        sheet["A42"] = observaciones  # Observaciones generales

        # Datos del funcionario
        sheet["C25"] = nombre_funcionario  # Nombre del funcionario
        sheet["F25"] = cargo_funcionario  # Cargo del funcionario

        # Firmas
        sheet["A50"] = contraparte_tecnica  # Contraparte técnica
        sheet["E50"] = jefe_servicio  # Jefe de servicio

        # Guardar el certificado en memoria
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        return output

    except Exception as e:
        raise RuntimeError(f"Error al generar el certificado: {e}")