"""Enumeraciones y tipos comunes usados en todo el sistema."""

from enum import StrEnum


class Sexo(StrEnum):
    """Sexo del asegurado segun tablas actuariales"""

    HOMBRE = "H"
    MUJER = "M"


class Fumador(StrEnum):
    """Estatus de fumador (usado en algunas tablas de mortalidad)"""

    SI = "fumador"
    NO = "no_fumador"
    NO_ESPECIFICADO = "no_especificado"


class Moneda(StrEnum):
    """Monedas soportadas en el sistema"""

    MXN = "MXN"
    USD = "USD"
