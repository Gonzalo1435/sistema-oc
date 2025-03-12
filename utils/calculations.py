import pandas as pd

def validate_columns(data, required_columns):
    """
    Valida que un DataFrame contenga las columnas necesarias.

    Parámetros:
    - data (pd.DataFrame): El DataFrame a validar.
    - required_columns (list): Lista de nombres de columnas requeridas.

    Retorna:
    - tuple: (bool, list) -> True si todas las columnas están presentes, False en caso contrario.
    """
    missing_columns = [col for col in required_columns if col not in data.columns]
    return len(missing_columns) == 0, missing_columns

def filter_accepted_orders(data):
    """
    Filtra las órdenes de compra con estado 'Aceptada'.

    Parámetros:
    - data (pd.DataFrame): El DataFrame con las órdenes de compra.

    Retorna:
    - pd.DataFrame: Un DataFrame con las órdenes de compra aceptadas.
    """
    return data[data["Estado"].str.lower() == "aceptada"]