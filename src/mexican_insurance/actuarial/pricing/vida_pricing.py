"""
Funciones de pricing para seguros de vida

Aquí van las fórmulas actuariales clásicas para calcular primas
de seguros de vida usando tablas de mortalidad.

Referencias:
- Bowers et al. "Actuarial Mathematics"
- Notas técnicas CNSF
"""

from decimal import Decimal

from mexican_insurance.actuarial.mortality.tablas import TablaMortalidad
from mexican_insurance.core.validators import Sexo


def calcular_seguro_vida(
    tabla: TablaMortalidad,
    edad: int,
    sexo: Sexo | str,
    plazo: int,
    tasa_interes: Decimal,
    suma_asegurada: Decimal = Decimal("1"),
) -> Decimal:
    """
    Calcula el valor presente actuarial de un seguro temporal de vida.

    Formula: A[x:n] = Σ(v^(t+1) * t_p_x * q_(x+t)) para t=0 hasta n-1

    Donde:
    - v = factor de descuento = 1/(1+i)
    - t_p_x = probabilidad de sobrevivir t años desde edad x
    - q_(x+t) = probabilidad de morir en el año t+1

    Args:
        tabla: Tabla de mortalidad a usar
        edad: Edad actual del asegurado
        sexo: Sexo del asegurado
        plazo: Plazo del seguro en años
        tasa_interes: Tasa de interés técnico (ej: 0.055 = 5.5%)
        suma_asegurada: Suma asegurada (default=1 para calcular por unidad)

    Returns:
        Valor presente actuarial del seguro (A_x:n)

    Examples:
        >>> from decimal import Decimal
        >>> tabla = TablaMortalidad.cargar_emssa09()
        >>> axn = calcular_seguro_vida(
        ...     tabla, edad=35, sexo=Sexo.HOMBRE, plazo=20,
        ...     tasa_interes=Decimal("0.055"), suma_asegurada=Decimal("1000000")
        ... )
        >>> print(f"Valor presente: ${axn:,.2f}")
    """
    # Factor de descuento
    v = Decimal("1") / (Decimal("1") + tasa_interes)

    # Acumulador del valor presente
    valor_presente = Decimal("0")

    # Probabilidad acumulada de supervivencia
    prob_supervivencia = Decimal("1")

    for t in range(plazo):
        edad_actual = edad + t

        # Obtener qx para esta edad
        qx = tabla.obtener_qx(edad_actual, sexo, interpolar=True)

        # Calcular componente: v^(t+1) * t_p_x * q_(x+t)
        factor_descuento = v ** (t + 1)
        componente = factor_descuento * prob_supervivencia * qx

        valor_presente += componente

        # Actualizar probabilidad de supervivencia para siguiente iteración
        prob_supervivencia *= Decimal("1") - qx

    # Multiplicar por suma asegurada
    return valor_presente * suma_asegurada


def calcular_anualidad(
    tabla: TablaMortalidad,
    edad: int,
    sexo: Sexo | str,
    plazo: int,
    tasa_interes: Decimal,
    pago_anticipado: bool = True,
) -> Decimal:
    """
    Calcula el valor presente actuarial de una anualidad.

    Si es anticipada (pago al inicio): ä[x:n]
    Si es vencida (pago al final): a[x:n]

    Formula anticipada: ä[x:n] = Σ(v^t * t_p_x) para t=0 hasta n-1
    Formula vencida: a[x:n] = Σ(v^(t+1) * t_p_x) para t=0 hasta n-1

    Args:
        tabla: Tabla de mortalidad
        edad: Edad del asegurado
        sexo: Sexo del asegurado
        plazo: Número de pagos
        tasa_interes: Tasa de interés técnico
        pago_anticipado: True para anualidad anticipada, False para vencida

    Returns:
        Valor presente de la anualidad

    Examples:
        >>> anualidad = calcular_anualidad(
        ...     tabla, edad=35, sexo=Sexo.HOMBRE,
        ...     plazo=20, tasa_interes=Decimal("0.055")
        ... )
    """
    v = Decimal("1") / (Decimal("1") + tasa_interes)

    valor_presente = Decimal("0")
    prob_supervivencia = Decimal("1")

    for t in range(plazo):
        edad_actual = edad + t

        # Factor de descuento depende si es anticipado o vencido
        if pago_anticipado:
            factor_descuento = v**t
        else:
            factor_descuento = v ** (t + 1)

        # Componente: v^t * t_p_x
        componente = factor_descuento * prob_supervivencia
        valor_presente += componente

        # Actualizar probabilidad para siguiente año
        qx = tabla.obtener_qx(edad_actual, sexo, interpolar=True)
        prob_supervivencia *= Decimal("1") - qx

    return valor_presente


def calcular_prima_neta_temporal(
    tabla: TablaMortalidad,
    edad: int,
    sexo: Sexo | str,
    plazo_seguro: int,
    plazo_pago: int,
    tasa_interes: Decimal,
    suma_asegurada: Decimal,
    frecuencia_pago: str = "anual",
) -> Decimal:
    """
    Calcula la prima neta nivelada para un seguro temporal de vida.

    La prima neta se calcula como:
    P = (A[x:n] / ä[x:m]) * suma_asegurada

    Donde:
    - A[x:n] = valor presente del seguro (beneficio)
    - ä[x:m] = valor presente de la anualidad (pagos de prima)
    - n = plazo del seguro
    - m = plazo de pago de primas

    Args:
        tabla: Tabla de mortalidad
        edad: Edad del asegurado
        sexo: Sexo del asegurado
        plazo_seguro: Duración del seguro en años
        plazo_pago: Duración del pago de primas en años
        tasa_interes: Tasa de interés técnico
        suma_asegurada: Suma asegurada
        frecuencia_pago: "anual", "mensual", "semestral", "trimestral"

    Returns:
        Prima neta nivelada

    Raises:
        ValueError: Si el plazo de pago es mayor al plazo del seguro

    Examples:
        >>> prima = calcular_prima_neta_temporal(
        ...     tabla=tabla_emssa,
        ...     edad=35,
        ...     sexo=Sexo.HOMBRE,
        ...     plazo_seguro=20,
        ...     plazo_pago=20,
        ...     tasa_interes=Decimal("0.055"),
        ...     suma_asegurada=Decimal("1000000")
        ... )
        >>> print(f"Prima neta anual: ${prima:,.2f}")
    """
    if plazo_pago > plazo_seguro:
        raise ValueError(
            f"El plazo de pago ({plazo_pago}) no puede ser mayor "
            f"al plazo del seguro ({plazo_seguro})"
        )

    # Calcular valor presente del beneficio (seguro)
    axn = calcular_seguro_vida(
        tabla=tabla,
        edad=edad,
        sexo=sexo,
        plazo=plazo_seguro,
        tasa_interes=tasa_interes,
        suma_asegurada=Decimal("1"),  # Por unidad
    )

    # Calcular valor presente de los pagos (anualidad)
    axm = calcular_anualidad(
        tabla=tabla,
        edad=edad,
        sexo=sexo,
        plazo=plazo_pago,
        tasa_interes=tasa_interes,
        pago_anticipado=True,  # Primas se pagan al inicio
    )

    # Prima neta por unidad de suma asegurada
    prima_unitaria = axn / axm

    # Prima total
    prima_neta = prima_unitaria * suma_asegurada

    # Ajustar por frecuencia de pago
    factor_frecuencia = _obtener_factor_frecuencia(frecuencia_pago)
    prima_neta_ajustada = prima_neta * factor_frecuencia

    return prima_neta_ajustada


def _obtener_factor_frecuencia(frecuencia: str) -> Decimal:
    """
    Obtiene el factor de conversión para diferentes frecuencias de pago.

    En la práctica, las primas fraccionarias son ligeramente más caras
    que (prima_anual / m) debido a costos administrativos.

    Args:
        frecuencia: "anual", "semestral", "trimestral", "mensual"

    Returns:
        Factor multiplicador

    Note:
        Estos factores son aproximados. Cada aseguradora puede usar
        sus propios factores basados en costos administrativos.
    """
    factores = {
        "anual": Decimal("1.00"),
        "semestral": Decimal("0.51"),  # Ligeramente más que 1/2
        "trimestral": Decimal("0.26"),  # Ligeramente más que 1/4
        "mensual": Decimal("0.087"),  # Ligeramente más que 1/12
    }

    if frecuencia not in factores:
        raise ValueError(
            f"Frecuencia '{frecuencia}' no soportada. "
            f"Usa una de: {list(factores.keys())}"
        )

    return factores[frecuencia]
