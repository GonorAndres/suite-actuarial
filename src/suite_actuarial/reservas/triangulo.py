"""
Utilidades para manejo de triángulos de desarrollo.

Proporciona funciones para validar, transformar y manipular
triángulos de datos de siniestros para cálculo de reservas.
"""

from decimal import Decimal

import numpy as np
import pandas as pd

from suite_actuarial.core.validators import TipoTriangulo


def factores_volumen_ponderado(valores: np.ndarray) -> tuple[list[float], list[float]]:
    """Factores de desarrollo ponderados por volumen y el volumen que los pondera.

    Para el periodo `k` (de la columna k a la k+1), sobre las filas donde ambas
    celdas estan observadas:

        f_k = sum_i C(i,k+1) / sum_i C(i,k)
        S_k = sum_i C(i,k)

    Es el estimador que suponen tanto Mack (1993) como el modelo Poisson
    sobredispersado: es el unico insesgado bajo sus hipotesis de varianza, y es
    tambien el que hace que los valores ajustados reproduzcan las sumas
    observadas por fila y por columna.

    Args:
        valores: Triangulo acumulado como arreglo 2D con NaN en las celdas
            futuras

    Returns:
        Tupla `(factores, volumenes)` con un elemento por periodo de desarrollo.
        Un periodo sin observaciones utiles devuelve factor 1.0 y volumen 0.0.
    """
    n_cols = valores.shape[1]
    factores: list[float] = []
    volumenes: list[float] = []

    for k in range(n_cols - 1):
        actual = valores[:, k]
        siguiente = valores[:, k + 1]
        mask = ~np.isnan(actual) & ~np.isnan(siguiente) & (actual > 0)

        if not mask.any():
            factores.append(1.0)
            volumenes.append(0.0)
            continue

        suma_actual = float(actual[mask].sum())
        if suma_actual <= 0:
            factores.append(1.0)
            volumenes.append(0.0)
            continue

        factores.append(float(siguiente[mask].sum() / suma_actual))
        volumenes.append(suma_actual)

    return factores, volumenes


def validar_triangulo(
    df: pd.DataFrame,
    tipo: TipoTriangulo | None = None,
    permitir_desarrollo_negativo: bool = False,
) -> bool:
    """
    Valida que un DataFrame sea un triángulo de desarrollo válido.

    Un triángulo válido debe:
    - Tener índice de años de origen (int)
    - Tener columnas de períodos de desarrollo (int)
    - Ser triangular superior (NaN en diagonal inferior)
    - Tener valores no negativos
    - Si es acumulado, cada valor debe ser >= al anterior en la misma fila

    Las dos últimas condiciones describen desarrollo siempre creciente, que es
    lo normal en un triángulo de pagos, pero no lo único legítimo:

    - Un triángulo de **pagados** baja cuando hay salvamento o subrogación: la
      aseguradora recupera parte de lo pagado.
    - Un triángulo de **incurridos** baja cuando se libera reserva de un
      siniestro que resultó menos grave de lo estimado. Es rutinario.

    Por eso el desarrollo negativo se admite declarándolo, no por omisión: el
    caso corriente sigue siendo el creciente, y aceptarlo todo en silencio
    dejaría pasar un triángulo mal capturado (columnas cambiadas, incremental
    enviado como acumulado) sin decir nada.

    Args:
        df: DataFrame con el triángulo
        tipo: Tipo de triángulo (acumulado o incremental)
        permitir_desarrollo_negativo: Admite valores incrementales negativos y
            filas acumuladas no monótonas. Úselo cuando el triángulo lleve
            recuperaciones o liberaciones de reserva.

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
        observados = df.iloc[i].notna().to_numpy()
        n_obs = int(observados.sum())
        esperado = n_cols - i

        # Un año sin ninguna observación pasaba el conteo cuando `esperado`
        # daba 0 (más filas que columnas). Después reventaba adentro: Chain
        # Ladder con un KeyError del año y Mack con InvalidOperation, porque
        # `obtener_ultima_diagonal` no devuelve entrada para una fila vacía.
        # Un traceback interno es peor que rechazar la entrada aquí.
        if n_obs == 0:
            raise ValueError(
                f"Año {df.index[i]} no tiene ninguna observación. Un año de "
                "origen sin datos no se puede valuar: agregue al menos un "
                "periodo observado o quite el año del triángulo."
            )

        if n_obs != esperado:
            raise ValueError(
                f"Fila {i} tiene {n_obs} valores, esperaba {esperado} (estructura triangular)"
            )

        # Contar no basta: hay que exigir que los huecos queden al final. Un
        # triángulo se llena de izquierda a derecha, así que un hueco en medio
        # con valores a su derecha es un dato mal capturado. Sin esta
        # comprobación, `incrementar_triangulo` aplicaba `dropna()` y corría
        # los valores hacia la izquierda, restando contra periodos que no
        # correspondían y dejando la última celda acumulada sin tocar.
        if not observados[:n_obs].all():
            huecos = [str(df.columns[j]) for j in range(n_obs) if not observados[j]]
            raise ValueError(
                f"Año {df.index[i]}: faltan los periodos {', '.join(huecos)} y hay "
                "valores en periodos posteriores. Un triángulo se llena de "
                "izquierda a derecha: los huecos deben quedar al final de la fila."
            )

    # Validar que no haya valores negativos
    if not permitir_desarrollo_negativo and (df < 0).any().any():
        raise ValueError(
            "El triángulo contiene valores negativos. Si representan "
            "recuperaciones (salvamento, subrogación) o liberaciones de "
            "reserva, declárelo con permitir_desarrollo_negativo=True."
        )

    # Si es acumulado, validar monotonicidad
    if tipo == TipoTriangulo.ACUMULADO and not permitir_desarrollo_negativo:
        for i in range(n_rows):
            row = df.iloc[i].dropna()
            if not row.is_monotonic_increasing:
                raise ValueError(
                    f"Año {df.index[i]}: valores no son monótonos "
                    "(triángulo acumulado debe incrementar). Si el descenso es "
                    "real -recuperaciones o liberación de reserva-, declárelo "
                    "con permitir_desarrollo_negativo=True."
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


def acumular_triangulo(
    df_incremental: pd.DataFrame, permitir_desarrollo_negativo: bool = False
) -> pd.DataFrame:
    """
    Convierte triángulo incremental a acumulado.

    Args:
        df_incremental: Triángulo con valores incrementales
        permitir_desarrollo_negativo: Admite incrementos negativos
            (recuperaciones, liberación de reserva)

    Returns:
        Triángulo con valores acumulados (sumas)
    """
    validar_triangulo(df_incremental, TipoTriangulo.INCREMENTAL, permitir_desarrollo_negativo)

    df_acumulado = df_incremental.copy()

    # Calcular suma acumulada por fila
    for i in range(len(df_acumulado)):
        row = df_acumulado.iloc[i]
        valores = row.dropna().values

        if len(valores) > 0:
            acumulados = valores.cumsum()
            df_acumulado.iloc[i, : len(acumulados)] = acumulados

    return df_acumulado


def asegurar_acumulado(
    df: pd.DataFrame, tipo: TipoTriangulo, permitir_desarrollo_negativo: bool = False
) -> pd.DataFrame:
    """
    Devuelve el triángulo en forma acumulada, declarando su tipo de entrada.

    Los métodos de reserva (Chain Ladder, Bornhuetter-Ferguson, bootstrap ODP)
    operan sobre triángulos acumulados. El tipo se declara, no se infiere: una
    heurística sobre la monotonía de los valores confunde un triángulo
    incremental cuyo primer año de origen crece con uno ya acumulado, y produce
    una reserva menor a la correcta sin error ni advertencia.

    Args:
        df: Triángulo de desarrollo
        tipo: Forma en la que viene `df` (acumulada o incremental)

    Returns:
        Copia del triángulo en forma acumulada
    """
    if tipo is TipoTriangulo.INCREMENTAL:
        return acumular_triangulo(df, permitir_desarrollo_negativo)
    return df.copy()


def calcular_age_to_age(
    df: pd.DataFrame, permitir_desarrollo_negativo: bool = False
) -> pd.DataFrame:
    """
    Calcula factores age-to-age (link ratios) de un triángulo acumulado.

    Factor age-to-age del período i al i+1:
        LR[i,j] = Triangle[i, j+1] / Triangle[i, j]

    Args:
        df: Triángulo acumulado

    Returns:
        DataFrame con factores age-to-age
    """
    validar_triangulo(df, TipoTriangulo.ACUMULADO, permitir_desarrollo_negativo)

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


def promedio_simple(valores: list[float]) -> float:
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


def promedio_ponderado(valores: list[float], volumenes: list[float]) -> float:
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

    for v, vol in zip(valores, volumenes, strict=False):
        if pd.notna(v) and pd.notna(vol) and v > 0 and vol > 0:
            suma_ponderada += v * vol
            suma_volumenes += vol

    if suma_volumenes == 0:
        return 1.0

    return suma_ponderada / suma_volumenes


def promedio_geometrico(valores: list[float]) -> float:
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

    return float(producto ** (1.0 / len(valores_limpios)))


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
        df_decimal[col] = df_decimal[col].apply(lambda x: Decimal(str(x)) if pd.notna(x) else x)

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
