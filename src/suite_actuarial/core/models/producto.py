"""Modelos para configuracion de productos y resultados de calculo."""

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from suite_actuarial.core.models.common import Moneda


class ConfiguracionProducto(BaseModel):
    """
    Configuracion de un producto de seguros.

    Aqui van los parametros que definen como funciona el producto:
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
        description="Plazo del seguro en anos",
    )
    tasa_interes_tecnico: Decimal = Field(
        default=Decimal("0.055"),
        ge=0,
        le=1,
        description="Tasa de interes tecnico (tipicamente 5.5% en Mexico)",
    )
    recargo_gastos_admin: Decimal = Field(
        default=Decimal("0.05"),
        ge=0,
        le=1,
        description="Recargo por gastos de administracion (% de prima)",
    )
    recargo_gastos_adq: Decimal = Field(
        default=Decimal("0.10"),
        ge=0,
        le=1,
        description="Recargo por gastos de adquisicion (% de prima)",
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
        La tasa de interes tecnico debe estar en rangos razonables.
        CNSF tipicamente permite hasta 5.5% para ciertos productos.
        """
        if v < 0:
            raise ValueError("La tasa de interes no puede ser negativa")
        if v > Decimal("0.15"):
            raise ValueError(
                "Tasa de interes muy alta (tipicamente max 15% anual)"
            )
        return v

    @model_validator(mode="after")
    def validar_recargos_totales(self) -> "ConfiguracionProducto":
        """Los recargos totales no deberian ser mayores al 100%"""
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
                    "nombre_producto": "Vida Temporal 20 Anos",
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
    Resultado de un calculo actuarial.

    Almacena los resultados de primas, reservas, etc.
    con metadatos sobre como se calculo.
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
        description="Moneda del calculo",
    )
    desglose_recargos: dict[str, Decimal] = Field(
        default_factory=dict,
        description="Desglose detallado de cada recargo aplicado",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Informacion adicional sobre el calculo",
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
