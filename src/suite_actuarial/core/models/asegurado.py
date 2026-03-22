"""Modelos para datos de asegurados y tablas de mortalidad."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from suite_actuarial.core.models.common import Fumador, Sexo


class Asegurado(BaseModel):
    """
    Representa a una persona asegurada.

    Esta clase valida que los datos esten en el rango correcto
    segun las regulaciones de la CNSF y la practica actuarial.
    """

    edad: int = Field(
        ...,
        ge=0,
        le=120,
        description="Edad del asegurado en anos cumplidos",
    )
    sexo: Sexo = Field(
        ...,
        description="Sexo del asegurado para seleccion de tabla",
    )
    fumador: Fumador = Field(
        default=Fumador.NO_ESPECIFICADO,
        description="Estatus de fumador (algunas tablas lo requieren)",
    )
    fecha_nacimiento: date | None = Field(
        default=None,
        description="Fecha de nacimiento (opcional, para calculos exactos)",
    )
    suma_asegurada: Decimal = Field(
        ...,
        gt=0,
        description="Suma asegurada en la moneda especificada",
    )

    @field_validator("suma_asegurada")
    @classmethod
    def validar_suma_asegurada(cls, v: Decimal) -> Decimal:
        """La suma asegurada debe ser positiva y razonable"""
        if v <= 0:
            raise ValueError("La suma asegurada debe ser mayor a cero")
        if v > Decimal("1e12"):  # 1 billon - limite razonable
            raise ValueError("La suma asegurada es excesivamente alta")
        return v

    @field_validator("edad")
    @classmethod
    def validar_edad(cls, v: int) -> int:
        """Validar que la edad este en un rango asegurable tipico"""
        if v < 0:
            raise ValueError("La edad no puede ser negativa")
        if v > 100:
            # Warning: edades muy altas pueden no tener datos en tablas
            pass
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "edad": 35,
                    "sexo": "H",
                    "fumador": "no_fumador",
                    "suma_asegurada": "1000000.00",
                }
            ]
        }
    }


class RegistroMortalidad(BaseModel):
    """
    Un registro en una tabla de mortalidad.

    Representa la probabilidad de muerte (qx) para una edad y sexo dados.
    """

    edad: int = Field(..., ge=0, le=120)
    sexo: Sexo
    qx: Decimal = Field(
        ...,
        ge=0,
        le=1,
        description="Probabilidad de muerte entre edad x y x+1",
    )
    lx: int | None = Field(
        default=None,
        ge=0,
        description="Numero de sobrevivientes a edad x (opcional)",
    )

    @field_validator("qx")
    @classmethod
    def validar_qx(cls, v: Decimal) -> Decimal:
        """qx debe estar entre 0 y 1"""
        if not (0 <= v <= 1):
            raise ValueError(f"qx debe estar entre 0 y 1, se recibio {v}")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "edad": 35,
                    "sexo": "H",
                    "qx": "0.001234",
                    "lx": 98765,
                }
            ]
        }
    }
