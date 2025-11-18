"""
Validadores con Pydantic para datos de seguros

Aquí van todas las validaciones de entrada/salida para asegurar
que los datos cumplen con las reglas de negocio y de la CNSF.
"""

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class Sexo(str, Enum):
    """Sexo del asegurado según tablas actuariales"""

    HOMBRE = "H"
    MUJER = "M"


class Fumador(str, Enum):
    """Estatus de fumador (usado en algunas tablas de mortalidad)"""

    SI = "fumador"
    NO = "no_fumador"
    NO_ESPECIFICADO = "no_especificado"


class Moneda(str, Enum):
    """Monedas soportadas en el sistema"""

    MXN = "MXN"
    USD = "USD"


class Asegurado(BaseModel):
    """
    Representa a una persona asegurada.

    Esta clase valida que los datos estén en el rango correcto
    según las regulaciones de la CNSF y la práctica actuarial.
    """

    edad: int = Field(
        ...,
        ge=0,
        le=120,
        description="Edad del asegurado en años cumplidos",
    )
    sexo: Sexo = Field(
        ...,
        description="Sexo del asegurado para selección de tabla",
    )
    fumador: Fumador = Field(
        default=Fumador.NO_ESPECIFICADO,
        description="Estatus de fumador (algunas tablas lo requieren)",
    )
    fecha_nacimiento: Optional[date] = Field(
        default=None,
        description="Fecha de nacimiento (opcional, para cálculos exactos)",
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
        if v > Decimal("1e12"):  # 1 billón - límite razonable
            raise ValueError("La suma asegurada es excesivamente alta")
        return v

    @field_validator("edad")
    @classmethod
    def validar_edad(cls, v: int) -> int:
        """Validar que la edad esté en un rango asegurable típico"""
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


class ConfiguracionProducto(BaseModel):
    """
    Configuración de un producto de seguros.

    Aquí van los parámetros que definen cómo funciona el producto:
    tasas, plazos, recargos, etc.
    """

    nombre_producto: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Nombre del producto",
    )
    plazo_years: int = Field(
        ...,
        ge=1,
        le=99,
        description="Plazo del seguro en años",
    )
    tasa_interes_tecnico: Decimal = Field(
        default=Decimal("0.055"),
        ge=0,
        le=1,
        description="Tasa de interés técnico (típicamente 5.5% en México)",
    )
    recargo_gastos_admin: Decimal = Field(
        default=Decimal("0.05"),
        ge=0,
        le=1,
        description="Recargo por gastos de administración (% de prima)",
    )
    recargo_gastos_adq: Decimal = Field(
        default=Decimal("0.10"),
        ge=0,
        le=1,
        description="Recargo por gastos de adquisición (% de prima)",
    )
    recargo_utilidad: Decimal = Field(
        default=Decimal("0.03"),
        ge=0,
        le=1,
        description="Recargo por utilidad esperada (% de prima)",
    )
    moneda: Moneda = Field(
        default=Moneda.MXN,
        description="Moneda del producto",
    )

    @field_validator("tasa_interes_tecnico")
    @classmethod
    def validar_tasa_interes(cls, v: Decimal) -> Decimal:
        """
        La tasa de interés técnico debe estar en rangos razonables.
        CNSF típicamente permite hasta 5.5% para ciertos productos.
        """
        if v < 0:
            raise ValueError("La tasa de interés no puede ser negativa")
        if v > Decimal("0.15"):
            raise ValueError(
                "Tasa de interés muy alta (típicamente máx 15% anual)"
            )
        return v

    @model_validator(mode="after")
    def validar_recargos_totales(self) -> "ConfiguracionProducto":
        """Los recargos totales no deberían ser mayores al 100%"""
        total_recargos = (
            self.recargo_gastos_admin
            + self.recargo_gastos_adq
            + self.recargo_utilidad
        )
        if total_recargos > Decimal("1.0"):
            raise ValueError(
                f"Recargos totales ({total_recargos:.2%}) superan el 100%"
            )
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "nombre_producto": "Vida Temporal 20 Años",
                    "plazo_years": 20,
                    "tasa_interes_tecnico": "0.055",
                    "recargo_gastos_admin": "0.05",
                    "recargo_gastos_adq": "0.10",
                    "recargo_utilidad": "0.03",
                    "moneda": "MXN",
                }
            ]
        }
    }


class ResultadoCalculo(BaseModel):
    """
    Resultado de un cálculo actuarial.

    Almacena los resultados de primas, reservas, etc.
    con metadatos sobre cómo se calculó.
    """

    prima_neta: Decimal = Field(
        ...,
        ge=0,
        description="Prima neta (sin recargos)",
    )
    prima_total: Decimal = Field(
        ...,
        ge=0,
        description="Prima total (con todos los recargos)",
    )
    moneda: Moneda = Field(
        ...,
        description="Moneda del cálculo",
    )
    desglose_recargos: Dict[str, Decimal] = Field(
        default_factory=dict,
        description="Desglose detallado de cada recargo aplicado",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Información adicional sobre el cálculo",
    )

    @model_validator(mode="after")
    def validar_prima_total(self) -> "ResultadoCalculo":
        """La prima total debe ser >= prima neta"""
        if self.prima_total < self.prima_neta:
            raise ValueError(
                "La prima total no puede ser menor a la prima neta"
            )
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "prima_neta": "5000.00",
                    "prima_total": "5900.00",
                    "moneda": "MXN",
                    "desglose_recargos": {
                        "gastos_admin": "250.00",
                        "gastos_adq": "500.00",
                        "utilidad": "150.00",
                    },
                    "metadata": {
                        "tabla_mortalidad": "EMSSA-09",
                        "metodo": "prima_nivelada",
                    },
                }
            ]
        }
    }


# Validador para tablas de mortalidad
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
    lx: Optional[int] = Field(
        default=None,
        ge=0,
        description="Número de sobrevivientes a edad x (opcional)",
    )

    @field_validator("qx")
    @classmethod
    def validar_qx(cls, v: Decimal) -> Decimal:
        """qx debe estar entre 0 y 1"""
        if not (0 <= v <= 1):
            raise ValueError(f"qx debe estar entre 0 y 1, se recibió {v}")
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
