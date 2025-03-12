import pdfplumber
import re
from datetime import datetime


def clean_text(text):
    """
    Limpia el texto eliminando saltos de línea y espacios redundantes.
    """
    return ' '.join(text.split())


def parse_chilean_currency(value):
    """
    Convierte un string de moneda chilena (con separador de miles y coma como decimal) a un número flotante.
    Ejemplo:
        "1.234.567,89" -> 1234567.89
    """
    try:
        # Eliminar los separadores de miles (puntos) y reemplazar la coma por un punto
        value = value.replace(".", "").replace(",", ".")
        return float(value)
    except (ValueError, AttributeError):
        return None


def extract_data_from_pdf(pdf_file, processed_orders):
    """
    Extrae datos relevantes de un archivo PDF y valida duplicidad de órdenes de compra.
    :param pdf_file: Archivo PDF a procesar.
    :param processed_orders: Conjunto de órdenes de compra ya procesadas.
    :return: Diccionario con los datos extraídos o None si es duplicada.
    """
    try:
        with pdfplumber.open(pdf_file) as pdf:
            lines = []
            for page in pdf.pages:
                lines.extend(page.extract_text().split("\n"))

        # Limpieza inicial del texto por líneas
        lines = [clean_text(line) for line in lines]

        # Combinar todas las líneas en un texto completo
        full_text = " ".join(lines)

        # Expresiones regulares mejoradas
        extracted_data = {
            # Número Licitación: Buscar específicamente "Número Licitación"
            "Número Licitación": re.search(r"(\d{7}-\d{1,2}-[A-Z]{2}\d{2})", full_text),
            # Orden de Compra: Buscar específicamente el formato esperado
            "Orden de Compra": re.search(r"(\d{7}-\d{1,4}-SE\d{2})", full_text),
            # Estado: Buscar valores predefinidos
            "Estado": re.search(r"(Aceptada|Cancelada|Recepcion Conforme|Rechazada|Enviada a Proveedor)", full_text),
            # Proveedor
            "Proveedor": re.search(r"SEÑOR \(ES\)\s*:\s*([\w\s\.]+)", full_text),
            # RUT del Proveedor
            "RUT Proveedor": re.search(r"RUT\s*:\s*([\d\.]+-[\dkK])", full_text),
            # Nombre de la Orden
            "Nombre Orden": re.search(r"NOMBRE ORDEN DE COMPRA\s*:\s*([\w\s\/,]+)", full_text),
            # Fecha de Envío de la Orden de Compra
            "Fecha Envío OC": re.search(r"Fecha Envio OC\.\s*:\s*([\d\-:\s]+)", full_text),
            # Total
            "Total": re.search(r"Total\s*\$\s*([\d\.,]+)", full_text),
        }

        # Extraer valores y limpiar
        for key, match in extracted_data.items():
            extracted_data[key] = match.group(1).strip() if match else None

        # Validar el formato del Número de Licitación
        if extracted_data["Número Licitación"] and not re.match(r"\d{7}-\d{1,2}-[A-Z]{2}\d{2}", extracted_data["Número Licitación"]):
            extracted_data["Número Licitación"] = None

        # Validar el formato de la Orden de Compra
        if extracted_data["Orden de Compra"] and not re.match(r"\d{7}-\d{1,4}-SE\d+", extracted_data["Orden de Compra"]):
            extracted_data["Orden de Compra"] = None

        # Validar el campo "Estado" con valores predefinidos
        valid_states = ["Aceptada", "Cancelada", "Recepcion Conforme", "Rechazada", "Enviada a Proveedor"]
        if extracted_data["Estado"] not in valid_states:
            extracted_data["Estado"] = None

        # Validar duplicidad de la Orden de Compra
        order_number = extracted_data.get("Orden de Compra")
        if order_number in processed_orders:
            print(f"Advertencia: La Orden de Compra '{order_number}' ya fue procesada. Ignorando archivo.")
            return None  # Ignorar archivo si la orden ya fue procesada

        # Agregar la Orden de Compra al conjunto de procesadas
        if order_number:
            processed_orders.add(order_number)

        # Convertir Fecha Envío OC al formato corto
        if extracted_data["Fecha Envío OC"]:
            try:
                extracted_data["Fecha Envío OC"] = datetime.strptime(
                    extracted_data["Fecha Envío OC"], "%d-%m-%Y %H:%M:%S"
                ).strftime("%d/%m/%Y")
            except ValueError:
                extracted_data["Fecha Envío OC"] = None

        # Convertir Total a número en formato flotante
        if extracted_data["Total"]:
            extracted_data["Total"] = parse_chilean_currency(extracted_data["Total"])

        return extracted_data

    except Exception as e:
        print(f"Error al procesar el archivo PDF: {e}")
        return None