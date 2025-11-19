"""
Utilidades para manejo de triángulos de desarrollo.

Proporciona funciones para validar, transformar y manipular
triángulos de datos de siniestros para cálculo de reservas.
"""

from decimal import Decimal
from typing import List

import pandas as pd

from mexican_insurance.core.validators import TipoTriangulo


def validar_triangulo(df: pd.DataFrame, tipo: TipoTriangulo = None) -> bool:
    """
    Valida que un DataFrame sea un triángulo de desarrollo válido.

    Un triángulo válido debe:
    - Tener índice de años de origen (int)
    - Tener columnas de períodos de desarrollo (int)
    - Ser triangular superior (NaN en diagonal inferior)
    - Tener valores no negativos
    - Si es acumulado, cada valor debe ser >= al anterior en la misma fila

    Args:
        df: DataFrame con el triángulo
        tipo: Tipo de triángulo (acumulado o incremental)

    Returns:
        True si es válido

    Raises:
        ValueError: Si el triángulo no es válido
    """
    if df.empty:
        raise ValueError("El triángulo está vacío")

    # Validar que índice y columnas sean numéricos
    if not pd.api.types.is_numeric_dtype(df.index):
        raise ValueError("El índice debe ser numérico (años de origen)")

    if not all(pd.api.types.is_numeric_dtype(df[col]) for col in df.columns):
        raise ValueError("Todas las columnas deben ser numéricas")

    # Validar estructura triangular
    n_rows, n_cols = df.shape
    for i in range(n_rows):
        # Contar valores no-NaN en esta fila
        valores_no_nan = df.iloc[i].notna().sum()
        # Debe haber exactamente (n_cols - i) valores
        expected = n_cols - i
        if valores_no_nan != expected:
            raise ValueError(
                f"Fila {i} tiene {valores_no_nan} valores, "
                f"esperaba {expected} (estructura triangular)"
            )

    # Validar que no haya valores negativos
    if (df < 0).any().any():
        raise ValueError("El triángulo contiene valores negativos")

    # Si es acumulado, validar monotonicidad
    if tipo == TipoTriangulo.ACUMULADO:
        for i in range(n_rows):
            row = df.iloc[i].dropna()
            if not row.is_monotonic_increasing:
                raise ValueError(
                    f"Año {df.index[i]}: valores no son monótonos "
                    "(triángulo acumulado debe incrementar)"
                )

    return True


def incrementar_triangulo(df_acumulado: pd.DataFrame) -> pd.DataFrame:
    """
    Convierte triángulo acumulado a incremental.

    Args:
        df_acumulado: Triángulo con valores acumulados

    Returns:
        Triángulo con valores incrementales (diferencias)
    """
    validar_triangulo(df_acumulado, TipoTriangulo.ACUMULADO)

    df_incremental = df_acumulado.copy()

    # Calcular diferencias por fila
    for i in range(len(df_incremental)):
        row = df_incremental.iloc[i]
        valores = row.dropna().values

        if len(valores) > 1:
            # Calcular incrementos (diff inverso para mantener orden)
            incrementos = [valores[0]] + list(valores[1:] - valores[:-1])
            df_incremental.iloc[i, : len(incrementos)] = incrementos

    return df_incremental


def acumular_triangulo(df_incremental: pd.DataFrame) -> pd.DataFrame:
    """
    Convierte triángulo incremental a acumulado.

    Args:
        df_incremental: Triángulo con valores incrementales

    Returns:
        Triángulo con valores acumulados (sumas)
    """
    validar_triangulo(df_incremental, TipoTriangulo.INCREMENTAL)

    df_acumulado = df_incremental.copy()

    # Calcular suma acumulada por fila
    for i in range(len(df_acumulado)):
        row = df_acumulado.iloc[i]
        valores = row.dropna().values

        if len(valores) > 0:
            acumulados = valores.cumsum()
            df_acumulado.iloc[i, : len(acumulados)] = acumulados

    return df_acumulado


def calcular_age_to_age(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula factores age-to-age (link ratios) de un triángulo acumulado.

    Factor age-to-age del período i al i+1:
        LR[i,j] = Triangle[i, j+1] / Triangle[i, j]

    Args:
        df: Triángulo acumulado

    Returns:
        DataFrame con factores age-to-age
    """
    validar_triangulo(df, TipoTriangulo.ACUMULADO)

    n_cols = df.shape[1]
    factores = pd.DataFrame(index=df.index, columns=range(n_cols - 1))

    for i in range(len(df)):
        for j in range(n_cols - 1):
            valor_actual = df.iloc[i, j]
            valor_siguiente = df.iloc[i, j + 1]

            if pd.notna(valor_actual) and pd.notna(valor_siguiente):
                if valor_actual > 0:
                    factores.iloc[i, j] = valor_siguiente / valor_actual
                else:
                    factores.iloc[i, j] = None

    return factores


def promedio_simple(valores: List[float]) -> float:
    """
    Calcula promedio aritmético simple.

    Args:
        valores: Lista de valores

    Returns:
        Promedio simple
    """
    valores_limpios = [v for v in valores if pd.notna(v) and v > 0]
    if not valores_limpios:
        return 1.0
    return sum(valores_limpios) / len(valores_limpios)


def promedio_ponderado(
    valores: List[float], volumenes: List[float]
) -> float:
    """
    Calcula promedio ponderado por volumen.

    Args:
        valores: Lista de factores
        volumenes: Lista de volúmenes (para ponderar)

    Returns:
        Promedio ponderado
    """
    if len(valores) != len(volumenes):
        raise ValueError("valores y volumenes deben tener la misma longitud")

    suma_ponderada = 0.0
    suma_volumenes = 0.0

    for v, vol in zip(valores, volumenes):
        if pd.notna(v) and pd.notna(vol) and v > 0 and vol > 0:
            suma_ponderada += v * vol
            suma_volumenes += vol

    if suma_volumenes == 0:
        return 1.0

    return suma_ponderada / suma_volumenes


def promedio_geometrico(valores: List[float]) -> float:
    """
    Calcula promedio geométrico.

    Args:
        valores: Lista de valores

    Returns:
        Promedio geométrico
    """
    valores_limpios = [v for v in valores if pd.notna(v) and v > 0]
    if not valores_limpios:
        return 1.0

    # Producto de valores elevado a (1/n)
    producto = 1.0
    for v in valores_limpios:
        producto *= v

    return producto ** (1.0 / len(valores_limpios))


def obtener_ultima_diagonal(df: pd.DataFrame) -> pd.Series:
    """
    Obtiene la última diagonal del triángulo (valores más recientes).

    Args:
        df: Triángulo de desarrollo

    Returns:
        Serie con los valores de la última diagonal
    """
    ultima_diagonal = []
    indices = []

    for i in range(len(df)):
        row = df.iloc[i]
        # Último valor no-NaN de la fila
        valores_no_nan = row.dropna()
        if len(valores_no_nan) > 0:
            ultima_diagonal.append(valores_no_nan.iloc[-1])
            indices.append(df.index[i])

    return pd.Series(ultima_diagonal, index=indices)


def convertir_a_decimal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convierte todos los valores numéricos de un DataFrame a Decimal.

    Args:
        df: DataFrame con valores float

    Returns:
        DataFrame con valores Decimal
    """
    df_decimal = df.copy()

    for col in df_decimal.columns:
        df_decimal[col] = df_decimal[col].apply(
            lambda x: Decimal(str(x)) if pd.notna(x) else x
        )

    return df_decimal


def crear_triangulo_ejemplo(tipo: TipoTriangulo = TipoTriangulo.ACUMULADO) -> pd.DataFrame:
    """
    Crea un triángulo de ejemplo para testing y demostraciones.

    Returns:
        DataFrame con triángulo de desarrollo de 5 años
    """
    # Triángulo acumulado de 5 años x 5 períodos
    data = {
        0: [1000, 1200, 1100, 1300, 1250],
        1: [1500, 1800, 1650, 1950, None],
        2: [1800, 2100, 1950, None, None],
        3: [1950, 2250, None, None, None],
        4: [2000, None, None, None, None],
    }

    df_acumulado = pd.DataFrame(data, index=[2020, 2021, 2022, 2023, 2024])

    if tipo == TipoTriangulo.ACUMULADO:
        return df_acumulado
    else:
        return incrementar_triangulo(df_acumulado)
