"""
Tablas de datos del IMSS para el sistema de pensiones mexicano.

Datos publicos basados en la Ley del Seguro Social (1973 y 1997),
resoluciones de la CONSAR, y parametros vigentes del IMSS.

Este modulo es SOLO datos -- no contiene logica de calculo.

Fuentes:
- Ley del Seguro Social 1973 (Arts. 167-171)
- Ley del Seguro Social 1997 (Arts. 154-162)
- CONSAR: Disposiciones de caracter general
- DOF: Publicaciones de UMA, pension garantizada
"""

from decimal import Decimal

# ======================================================================
# LEY 73: Porcentajes de pension por semanas cotizadas
# Art. 167 LSS 1973
#
# Con 500 semanas se tiene derecho a pension minima.
# Por cada 52 semanas adicionales se incrementa el porcentaje.
# El porcentaje se aplica al salario promedio de las ultimas 250 semanas.
# ======================================================================

LEY73_PORCENTAJES: dict[int, Decimal] = {
    500: Decimal("0.3307"),    # 33.07%
    552: Decimal("0.3536"),    # +2.29 pp por 52 semanas
    604: Decimal("0.3765"),
    656: Decimal("0.3994"),
    708: Decimal("0.4223"),
    760: Decimal("0.4452"),
    812: Decimal("0.4681"),
    864: Decimal("0.4910"),
    916: Decimal("0.5139"),
    968: Decimal("0.5368"),
    1020: Decimal("0.5597"),
    1072: Decimal("0.5826"),
    1124: Decimal("0.6055"),
    1176: Decimal("0.6284"),
    1228: Decimal("0.6513"),
    1280: Decimal("0.6742"),
    1332: Decimal("0.6971"),
    1384: Decimal("0.7200"),
    1436: Decimal("0.7429"),
    1488: Decimal("0.7658"),
    1540: Decimal("0.7887"),
    1592: Decimal("0.8116"),
    1644: Decimal("0.8345"),
    1696: Decimal("0.8574"),
    1748: Decimal("0.8803"),
    1800: Decimal("0.9032"),
    1852: Decimal("0.9261"),
    1904: Decimal("0.9490"),
    1956: Decimal("0.9719"),
    2008: Decimal("0.9948"),
    2060: Decimal("1.0000"),   # Tope: 100% (no puede exceder salario)
}

# Increment per 52-week block for Ley 73 interpolation
LEY73_INCREMENTO_POR_52_SEMANAS = Decimal("0.02290")


# ======================================================================
# LEY 73: Factores por edad de retiro
# Art. 171 LSS 1973
#
# Cesantia en edad avanzada: 60-64 anos con factor reducido
# Vejez: 65 anos con factor completo (100%)
# ======================================================================

LEY73_FACTORES_EDAD: dict[int, Decimal] = {
    60: Decimal("0.75"),   # 75%
    61: Decimal("0.80"),   # 80%
    62: Decimal("0.85"),   # 85%
    63: Decimal("0.90"),   # 90%
    64: Decimal("0.95"),   # 95%
    65: Decimal("1.00"),   # 100%
}


# ======================================================================
# LEY 97: Cuota social del gobierno
# Art. 168 fraccion IV LSS 1997, reformado 2020
#
# Aportacion del gobierno federal a la cuenta individual,
# expresada como porcentaje del salario base de cotizacion.
# Varia segun el nivel salarial en UMAs.
# ======================================================================

LEY97_CUOTA_SOCIAL: dict[str, Decimal] = {
    # Rango salarial en UMAs: porcentaje de cuota social sobre SBC
    "1.0_a_1.5_umas": Decimal("0.0632"),    # 6.32%
    "1.5_a_2.0_umas": Decimal("0.0596"),    # 5.96%
    "2.0_a_2.5_umas": Decimal("0.0560"),    # 5.60%
    "2.5_a_3.0_umas": Decimal("0.0524"),    # 5.24%
    "3.0_a_3.5_umas": Decimal("0.0488"),    # 4.88%
    "3.5_a_4.0_umas": Decimal("0.0452"),    # 4.52%
    "4.0_umas_o_mas": Decimal("0.0000"),    # 0.00% (sin cuota social)
}


# ======================================================================
# Cuotas obrero-patronales IMSS
# Porcentajes de aportacion por rama de seguro
# Vigentes con reforma 2020 (transicion 2023-2030)
# ======================================================================

CUOTAS_IMSS: dict[str, dict[str, Decimal]] = {
    "retiro": {
        "patronal": Decimal("0.02"),      # 2.0% del SBC
        "obrero": Decimal("0.0"),         # 0%
    },
    "cesantia_vejez": {
        "patronal": Decimal("0.0315"),    # 3.15% del SBC
        "obrero": Decimal("0.01125"),     # 1.125% del SBC
    },
    "enfermedades_maternidad_especie": {
        "patronal": Decimal("0.1395"),    # Cuota fija + excedente
        "obrero": Decimal("0.00375"),
    },
    "enfermedades_maternidad_dinero": {
        "patronal": Decimal("0.0070"),    # 0.70%
        "obrero": Decimal("0.0025"),      # 0.25%
    },
    "invalidez_vida": {
        "patronal": Decimal("0.0175"),    # 1.75%
        "obrero": Decimal("0.00625"),     # 0.625%
    },
    "riesgos_trabajo": {
        "patronal": Decimal("0.005"),     # Minimo clase I (varia por actividad)
        "obrero": Decimal("0.0"),
    },
    "guarderia": {
        "patronal": Decimal("0.01"),      # 1.0%
        "obrero": Decimal("0.0"),
    },
    "infonavit": {
        "patronal": Decimal("0.05"),      # 5.0%
        "obrero": Decimal("0.0"),
    },
}


# ======================================================================
# Pension garantizada (minima)
# Art. 170 LSS 1997, actualizado por CONSAR
# ======================================================================

PENSION_GARANTIZADA_2024 = Decimal("7467.40")   # MXN mensuales (2024)
PENSION_GARANTIZADA_2025 = Decimal("7800.00")   # Estimado
PENSION_GARANTIZADA_2026 = Decimal("8100.00")   # Estimado

# Pension minima por anos cotizados (reforma 2020)
# Semanas cotizadas -> pension garantizada mensual (como multiplo de UMA mensual)
PENSION_GARANTIZADA_POR_SEMANAS: dict[int, Decimal] = {
    750: Decimal("0.70"),    # 0.70 * UMA mensual (~$2,500)
    800: Decimal("0.78"),
    850: Decimal("0.85"),
    900: Decimal("0.93"),
    950: Decimal("1.00"),    # 1.0 UMA mensual
    1000: Decimal("1.08"),
    1050: Decimal("1.16"),
    1100: Decimal("1.23"),
    1150: Decimal("1.31"),
    1200: Decimal("1.39"),
    1250: Decimal("1.46"),
}


# ======================================================================
# Limites y topes legales
# ======================================================================

# Salario base de cotizacion maximo: 25 UMAs (Art. 28 LSS)
TOPE_SBC_UMAS = 25

# Semanas minimas para pension Ley 73
SEMANAS_MINIMAS_LEY73 = 500

# Semanas minimas para pension Ley 97 (reforma 2020, transitorio)
SEMANAS_MINIMAS_LEY97_2024 = 775    # Incremento anual de 25 semanas
SEMANAS_MINIMAS_LEY97_2025 = 800
SEMANAS_MINIMAS_LEY97_2026 = 825
SEMANAS_MINIMAS_LEY97_META = 1000   # Meta final (2031)

# Edad minima de retiro
EDAD_CESANTIA = 60      # Cesantia en edad avanzada
EDAD_VEJEZ = 65         # Pension por vejez

# Aguinaldo para pensionados IMSS (en dias de pension)
DIAS_AGUINALDO_PENSIONADOS = 30


# ======================================================================
# Rendimientos historicos AFORE (referencia)
# Rendimiento neto real promedio historico por SIEFORE
# ======================================================================

RENDIMIENTO_SIEFORE_REFERENCIA: dict[str, Decimal] = {
    "SB0_basica_inicial": Decimal("0.0350"),    # 3.50% real
    "SB1_basica_1": Decimal("0.0400"),           # 4.00%
    "SB2_basica_2": Decimal("0.0450"),           # 4.50%
    "SB3_basica_3": Decimal("0.0500"),           # 5.00% (jovenes)
    "SB4_basica_4": Decimal("0.0520"),           # 5.20%
    "promedio_sistema": Decimal("0.0450"),        # Promedio ponderado
}


def obtener_porcentaje_ley73(semanas: int) -> Decimal:
    """
    Obtiene el porcentaje de pension Ley 73 para un numero dado de semanas.

    Interpola linealmente entre los puntos definidos en la tabla.

    Args:
        semanas: Semanas cotizadas (minimo 500)

    Returns:
        Porcentaje de pension (ej: 0.3307 = 33.07%)

    Raises:
        ValueError: Si semanas < 500
    """
    if semanas < SEMANAS_MINIMAS_LEY73:
        raise ValueError(
            f"Se requieren al menos {SEMANAS_MINIMAS_LEY73} semanas cotizadas. "
            f"Se tienen {semanas}."
        )

    # Cap at maximum
    if semanas >= 2060:
        return Decimal("1.0000")

    # Find the bracket
    puntos = sorted(LEY73_PORCENTAJES.keys())
    for i, punto in enumerate(puntos):
        if semanas <= punto:
            if semanas == punto:
                return LEY73_PORCENTAJES[punto]
            # Interpolate between previous and current
            punto_anterior = puntos[i - 1] if i > 0 else puntos[0]
            pct_anterior = LEY73_PORCENTAJES[punto_anterior]

            # Linear interpolation within the 52-week block
            semanas_extra = semanas - punto_anterior
            semanas_bloque = punto - punto_anterior
            pct_incremento = LEY73_PORCENTAJES[punto] - pct_anterior
            fraccion = Decimal(str(semanas_extra)) / Decimal(str(semanas_bloque))

            return pct_anterior + pct_incremento * fraccion

    # Beyond last defined point but below 2060
    ultimo_punto = puntos[-1]
    pct_ultimo = LEY73_PORCENTAJES[ultimo_punto]
    semanas_extra = semanas - ultimo_punto
    incremento = LEY73_INCREMENTO_POR_52_SEMANAS * Decimal(str(semanas_extra)) / Decimal("52")
    resultado = pct_ultimo + incremento
    return min(resultado, Decimal("1.0000"))


def obtener_factor_edad(edad: int) -> Decimal:
    """
    Obtiene el factor de reduccion por edad de retiro (Ley 73).

    Args:
        edad: Edad de retiro (60-65)

    Returns:
        Factor de reduccion (0.75 a 1.00)

    Raises:
        ValueError: Si edad < 60 o > 65
    """
    if edad < 60:
        raise ValueError(
            f"Edad minima de retiro es 60 (cesantia en edad avanzada). "
            f"Edad proporcionada: {edad}"
        )
    if edad > 65:
        # After 65, factor is always 1.0
        return Decimal("1.00")

    return LEY73_FACTORES_EDAD[edad]
