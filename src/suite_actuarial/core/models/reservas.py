"""Modelos para metodos de reservas (Chain Ladder, BF, Bootstrap)."""

from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class TipoTriangulo(StrEnum):
    """Tipo de triangulo de desarrollo"""

    ACUMULADO = "acumulado"
    INCREMENTAL = "incremental"


class MetodoReserva(StrEnum):
    """Metodos de calculo de reservas soportados"""

    CHAIN_LADDER = "chain_ladder"
    BORNHUETTER_FERGUSON = "bornhuetter_ferguson"
    BOOTSTRAP = "bootstrap"


class MetodoPromedio(StrEnum):
    """Metodos para calcular promedio de factores de desarrollo"""

    SIMPLE = "simple"
    PONDERADO = "weighted"
    GEOMETRICO = "geometric"


class ConfiguracionChainLadder(BaseModel):
    """
    Configuracion para metodo Chain Ladder.

    El Chain Ladder es el metodo mas usado en la industria
    para proyectar desarrollo de siniestros.
    """

    metodo_promedio: MetodoPromedio = Field(
        default=MetodoPromedio.SIMPLE,
        description="Metodo para calcular factores de desarrollo",
    )
    calcular_tail_factor: bool = Field(
        default=False,
        description="Si se debe calcular factor de cola (tail)",
    )
    tail_factor: Decimal | None = Field(
        default=None,
        ge=Decimal("1.0"),
        le=Decimal("2.0"),
        description="Factor de cola manual (si no se calcula)",
    )


class ConfiguracionBornhuetterFerguson(BaseModel):
    """
    Configuracion para metodo Bornhuetter-Ferguson.

    Combina siniestros observados con expectativa a priori.
    Mas estable para anos con poco desarrollo.
    """

    loss_ratio_apriori: Decimal = Field(
        ...,
        gt=0,
        le=Decimal("2.0"),
        description="Loss ratio esperado (tipicamente 0.60-0.75)",
    )
    metodo_promedio: MetodoPromedio = Field(
        default=MetodoPromedio.SIMPLE,
        description="Metodo para factores de desarrollo",
    )

    @field_validator("loss_ratio_apriori")
    @classmethod
    def validar_loss_ratio(cls, v: Decimal) -> Decimal:
        """Loss ratio debe ser razonable"""
        if v < Decimal("0.3"):
            raise ValueError("Loss ratio muy bajo (tipicamente >= 30%)")
        if v > Decimal("1.5"):
            raise ValueError("Loss ratio muy alto (tipicamente <= 150%)")
        return v


class ConfiguracionBootstrap(BaseModel):
    """
    Configuracion para metodo Bootstrap.

    Usa simulacion Monte Carlo para estimar distribucion
    completa de reservas.
    """

    num_simulaciones: int = Field(
        default=1000,
        ge=100,
        le=10000,
        description="Numero de simulaciones a ejecutar",
    )
    seed: int | None = Field(
        default=None,
        description="Semilla para reproducibilidad",
    )
    metodo_residuales: str = Field(
        default="pearson",
        description="Metodo para calcular residuales",
    )
    percentiles: list[int] = Field(
        default=[50, 75, 90, 95, 99],
        description="Percentiles a calcular",
    )

    @field_validator("percentiles")
    @classmethod
    def validar_percentiles(cls, v: list[int]) -> list[int]:
        """Percentiles deben estar entre 1 y 99"""
        for p in v:
            if not (1 <= p <= 99):
                raise ValueError(f"Percentil {p} fuera de rango [1, 99]")
        return sorted(set(v))  # Ordenar y eliminar duplicados


class ResultadoReserva(BaseModel):
    """
    Resultado de calculo de reservas.

    Contiene estimaciones de ultimate y reservas por ano de origen.
    """

    metodo: MetodoReserva = Field(
        ...,
        description="Metodo utilizado para el calculo",
    )
    reserva_total: Decimal = Field(
        ...,
        ge=0,
        description="Reserva total estimada",
    )
    ultimate_total: Decimal = Field(
        ...,
        ge=0,
        description="Estimacion final total de siniestros",
    )
    pagado_total: Decimal = Field(
        ...,
        ge=0,
        description="Total pagado a la fecha",
    )

    # Por ano de origen
    reservas_por_anio: dict[int, Decimal] = Field(
        default_factory=dict,
        description="Reservas estimadas por ano de origen",
    )
    ultimates_por_anio: dict[int, Decimal] = Field(
        default_factory=dict,
        description="Ultimate estimado por ano de origen",
    )

    # Factores de desarrollo (solo Chain Ladder y BF)
    factores_desarrollo: list[Decimal] | None = Field(
        default=None,
        description="Factores age-to-age calculados",
    )

    # Distribucion (solo Bootstrap)
    percentiles: dict[int, Decimal] | None = Field(
        default=None,
        description="Percentiles de la distribucion (solo Bootstrap)",
    )

    detalles: dict[str, Any] = Field(
        default_factory=dict,
        description="Detalles adicionales del calculo",
    )

    @model_validator(mode="after")
    def validar_consistencia(self) -> "ResultadoReserva":
        """Validar que ultimate = pagado + reserva"""
        expected_ultimate = self.pagado_total + self.reserva_total
        # Permitir pequena diferencia por redondeo
        if abs(self.ultimate_total - expected_ultimate) > Decimal("0.01"):
            raise ValueError(
                f"Inconsistencia: ultimate ({self.ultimate_total}) != "
                f"pagado ({self.pagado_total}) + reserva ({self.reserva_total})"
            )
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "metodo": "chain_ladder",
                    "reserva_total": "2500000.00",
                    "ultimate_total": "12500000.00",
                    "pagado_total": "10000000.00",
                    "reservas_por_anio": {
                        "2020": "100000.00",
                        "2021": "500000.00",
                        "2022": "900000.00",
                        "2023": "1000000.00",
                    },
                    "factores_desarrollo": ["1.20", "1.10", "1.05"],
                }
            ]
        }
    }
