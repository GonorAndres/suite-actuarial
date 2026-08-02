"""Enumeraciones y tipos comunes usados en todo el sistema."""

from datetime import date
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Sexo(StrEnum):
    """Sexo del asegurado segun tablas actuariales.

    Los valores son palabras completas y no iniciales. La razon es una colision
    real que existio en este repositorio: `core/` codificaba "H"/"M"
    (hombre/mujer) mientras `salud/` codificaba "M"/"F" (masculino/femenino), de
    modo que el mismo caracter "M" significaba hombre en `/api/v1/salud/*` y
    mujer en `/api/v1/pricing/*`. Con iniciales no hay forma de que un valor
    heredado falle: se reinterpreta en silencio y cambia el sexo del asegurado.
    Con palabras completas, "H", "M" y "F" son todas invalidas y el error salta
    en la frontera.
    """

    MASCULINO = "masculino"
    FEMENINO = "femenino"


def normalizar_sexo(valor: "Sexo | str") -> Sexo:
    """Convierte un valor externo a `Sexo` con un error que nombra el conjunto valido.

    `Sexo("H")` levanta "'H' is not a valid Sexo", que no le dice al lector cuales
    son los valores aceptados. Esta funcion los enumera, y es el unico punto por
    el que el codigo del paquete deberia convertir texto libre a `Sexo`.

    Args:
        valor: Miembro de `Sexo` o su valor textual.

    Returns:
        El miembro de `Sexo` correspondiente.

    Raises:
        ValueError: Si el valor no es uno de los aceptados.
    """
    if isinstance(valor, Sexo):
        return valor
    try:
        return Sexo(valor)
    except ValueError as exc:
        validos = ", ".join(miembro.value for miembro in Sexo)
        raise ValueError(f"Sexo no valido: {valor!r}. Valores validos: {validos}.") from exc


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
