"""
Tablas de referencia para tarificacion de autos en Mexico.

Basado en la estructura publica de AMIS (Asociacion Mexicana de
Instituciones de Seguros). Los valores son representativos, no datos
confidenciales de ninguna aseguradora.

Las tasas base estan expresadas por millar (por cada 1,000 pesos de
valor asegurado) y corresponden a la tarifa de referencia de mercado.
"""

from decimal import Decimal

DISCLAIMER = (
    "AVISO: Las tasas y tablas en este modulo son REPRESENTATIVAS y no constituyen "
    "las tablas oficiales vigentes de la AMIS. Para uso en produccion, consulte "
    "las tablas de tarificacion vigentes publicadas por la AMIS."
)

# ---------------------------------------------------------------------------
# Grupos de vehiculo (1 = mas barato de reparar, 10 = mas costoso)
# ---------------------------------------------------------------------------

GRUPOS_VEHICULO: dict[str, int] = {
    "sedan_compacto": 1,
    "sedan_mediano": 3,
    "sedan_lujo": 6,
    "suv_compacto": 4,
    "suv_mediano": 5,
    "suv_lujo": 8,
    "pickup": 4,
    "deportivo": 9,
    "electrico": 7,
    "motocicleta": 2,
}

# ---------------------------------------------------------------------------
# Factores de zona de riesgo (simplificado de ~80 zonas AMIS)
# Mas alto = mas riesgo (robo, accidentes)
# ---------------------------------------------------------------------------

ZONAS_RIESGO: dict[str, Decimal] = {
    "cdmx_norte": Decimal("1.40"),
    "cdmx_sur": Decimal("1.25"),
    "cdmx_poniente": Decimal("1.30"),
    "cdmx_oriente": Decimal("1.35"),
    "edo_mex_ecatepec": Decimal("1.50"),
    "edo_mex_naucalpan": Decimal("1.35"),
    "edo_mex_tlalnepantla": Decimal("1.40"),
    "guadalajara": Decimal("1.10"),
    "monterrey": Decimal("1.15"),
    "puebla": Decimal("1.05"),
    "merida": Decimal("0.85"),
    "queretaro": Decimal("0.90"),
    "leon": Decimal("0.95"),
    "cancun": Decimal("1.00"),
    "tijuana": Decimal("1.20"),
    "chihuahua": Decimal("0.95"),
    "veracruz": Decimal("1.00"),
    "oaxaca": Decimal("0.80"),
    "aguascalientes": Decimal("0.88"),
    "san_luis_potosi": Decimal("0.92"),
    "morelia": Decimal("0.98"),
    "toluca": Decimal("1.10"),
    "resto_pais": Decimal("0.90"),
}

# ---------------------------------------------------------------------------
# Tasas base por millar por cobertura y grupo de vehiculo
# ---------------------------------------------------------------------------

TASAS_BASE: dict[str, dict[int, Decimal]] = {
    # Danos materiales: cubren reparacion por choque, volcadura, etc.
    "danos_materiales": {
        1: Decimal("25.00"),
        2: Decimal("28.50"),
        3: Decimal("32.00"),
        4: Decimal("35.50"),
        5: Decimal("39.00"),
        6: Decimal("44.00"),
        7: Decimal("48.00"),
        8: Decimal("53.00"),
        9: Decimal("60.00"),
        10: Decimal("68.00"),
    },
    # Robo total: prima por millar de valor asegurado
    "robo_total": {
        1: Decimal("12.00"),
        2: Decimal("15.00"),
        3: Decimal("18.00"),
        4: Decimal("20.00"),
        5: Decimal("22.00"),
        6: Decimal("26.00"),
        7: Decimal("28.00"),
        8: Decimal("32.00"),
        9: Decimal("38.00"),
        10: Decimal("45.00"),
    },
    # Responsabilidad civil bienes: dano a propiedad de terceros
    "rc_bienes": {
        1: Decimal("4.50"),
        2: Decimal("5.00"),
        3: Decimal("5.80"),
        4: Decimal("6.20"),
        5: Decimal("6.80"),
        6: Decimal("7.50"),
        7: Decimal("8.00"),
        8: Decimal("8.80"),
        9: Decimal("9.50"),
        10: Decimal("10.50"),
    },
    # Responsabilidad civil personas: lesiones a terceros
    "rc_personas": {
        1: Decimal("3.80"),
        2: Decimal("4.20"),
        3: Decimal("4.80"),
        4: Decimal("5.20"),
        5: Decimal("5.60"),
        6: Decimal("6.20"),
        7: Decimal("6.80"),
        8: Decimal("7.50"),
        9: Decimal("8.20"),
        10: Decimal("9.00"),
    },
    # Gastos medicos ocupantes
    "gastos_medicos": {
        1: Decimal("2.00"),
        2: Decimal("2.20"),
        3: Decimal("2.50"),
        4: Decimal("2.80"),
        5: Decimal("3.00"),
        6: Decimal("3.30"),
        7: Decimal("3.50"),
        8: Decimal("3.80"),
        9: Decimal("4.20"),
        10: Decimal("4.50"),
    },
    # Asistencia vial: costo fijo anual, no depende tanto del grupo
    "asistencia_vial": {
        1: Decimal("1.50"),
        2: Decimal("1.50"),
        3: Decimal("1.60"),
        4: Decimal("1.70"),
        5: Decimal("1.70"),
        6: Decimal("1.80"),
        7: Decimal("1.80"),
        8: Decimal("1.90"),
        9: Decimal("2.00"),
        10: Decimal("2.00"),
    },
}

# ---------------------------------------------------------------------------
# Factor de depreciacion por antiguedad del vehiculo
# (porcentaje del valor original)
# ---------------------------------------------------------------------------

DEPRECIACION_VEHICULO: dict[int, Decimal] = {
    0: Decimal("1.00"),   # Nuevo
    1: Decimal("0.80"),   # 1 ano
    2: Decimal("0.70"),   # 2 anos
    3: Decimal("0.62"),   # 3 anos
    4: Decimal("0.55"),   # 4 anos
    5: Decimal("0.49"),   # 5 anos
    6: Decimal("0.44"),   # 6 anos
    7: Decimal("0.39"),   # 7 anos
    8: Decimal("0.35"),   # 8 anos
    9: Decimal("0.32"),   # 9 anos
    10: Decimal("0.29"),  # 10+ anos
}

# ---------------------------------------------------------------------------
# Relatividades por edad del conductor
# ---------------------------------------------------------------------------

FACTOR_EDAD_CONDUCTOR: dict[str, Decimal] = {
    "18-25": Decimal("1.35"),
    "26-35": Decimal("1.00"),
    "36-50": Decimal("0.95"),
    "51-65": Decimal("1.05"),
    "66+": Decimal("1.20"),
}

# ---------------------------------------------------------------------------
# Factor de deducible (descuento por deducible mas alto)
# ---------------------------------------------------------------------------

FACTOR_DEDUCIBLE: dict[Decimal, Decimal] = {
    Decimal("0.03"): Decimal("1.10"),   # 3% = prima mas alta
    Decimal("0.05"): Decimal("1.00"),   # 5% = base
    Decimal("0.10"): Decimal("0.85"),   # 10% = descuento
    Decimal("0.15"): Decimal("0.75"),   # 15% = descuento mayor
    Decimal("0.20"): Decimal("0.70"),   # 20% = mayor descuento
}

# ---------------------------------------------------------------------------
# Genero del conductor (factor regulatorio para algunas coberturas)
# ---------------------------------------------------------------------------

FACTOR_GENERO: dict[str, Decimal] = {
    "masculino": Decimal("1.05"),
    "femenino": Decimal("0.95"),
    "no_binario": Decimal("1.00"),
}

# ---------------------------------------------------------------------------
# Factor de uso del vehiculo
# ---------------------------------------------------------------------------

FACTOR_USO_VEHICULO: dict[str, Decimal] = {
    "particular": Decimal("1.00"),
    "comercial": Decimal("1.25"),
    "taxi": Decimal("1.60"),
    "uber_didi": Decimal("1.40"),
    "carga": Decimal("1.35"),
}


# ---------------------------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------------------------

def obtener_grupo(tipo_vehiculo: str) -> int:
    """Devuelve el grupo de vehiculo o lanza error si no existe."""
    if tipo_vehiculo not in GRUPOS_VEHICULO:
        raise ValueError(
            f"Tipo de vehiculo desconocido: {tipo_vehiculo}. "
            f"Opciones: {list(GRUPOS_VEHICULO)}"
        )
    return GRUPOS_VEHICULO[tipo_vehiculo]


def obtener_zona(zona: str) -> Decimal:
    """Devuelve el factor de zona o lanza error si no existe."""
    if zona not in ZONAS_RIESGO:
        raise ValueError(
            f"Zona desconocida: {zona}. Opciones: {list(ZONAS_RIESGO)}"
        )
    return ZONAS_RIESGO[zona]


def obtener_depreciacion(antiguedad: int) -> Decimal:
    """Factor de depreciacion. Vehiculos con 10+ anos usan el factor de 10."""
    if antiguedad < 0:
        raise ValueError("La antiguedad no puede ser negativa.")
    clave = min(antiguedad, 10)
    return DEPRECIACION_VEHICULO[clave]


def rango_edad_conductor(edad: int) -> str:
    """Convierte una edad numerica al rango correspondiente."""
    if edad < 18:
        raise ValueError("El conductor debe tener al menos 18 anos.")
    if edad <= 25:
        return "18-25"
    if edad <= 35:
        return "26-35"
    if edad <= 50:
        return "36-50"
    if edad <= 65:
        return "51-65"
    return "66+"
