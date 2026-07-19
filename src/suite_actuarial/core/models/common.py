"""Enumeraciones y tipos comunes usados en todo el sistema."""

from datetime import date
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


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


class CalculationMetadata(BaseModel):
    """Linaje minimo que acompaña resultados publicados por el workbench."""

    model_version: str = "2.1.0"
    valuation_date: date | None = None
    assumption_id: str | None = None
    assumption_hash: str | None = None
    validation_tier: str = "experimental"
    sources: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    reproducibility_id: str | None = None
    assumptions_snapshot: dict[str, Any] = Field(default_factory=dict)
