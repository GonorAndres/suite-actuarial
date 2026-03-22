"""Modelos para RCS (Requerimiento de Capital de Solvencia) y regulatorio."""

from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class TipoRiesgoRCS(StrEnum):
    """Tipos de riesgo para calculo de RCS"""

    MORTALIDAD = "mortalidad"
    LONGEVIDAD = "longevidad"
    INVALIDEZ = "invalidez"
    GASTOS = "gastos"
    PRIMA = "prima"
    RESERVA = "reserva"
    MERCADO = "mercado"
    CREDITO = "credito"
    CONCENTRACION = "concentracion"


class TipoRamo(StrEnum):
    """Tipo de ramo para clasificacion"""

    VIDA = "vida"
    DANOS = "danos"
    ACCIDENTES_SALUD = "accidentes_salud"


class ConfiguracionRCSVida(BaseModel):
    """
    Configuracion para calculo de RCS de suscripcion en ramos de vida.

    El RCS de vida considera riesgos de:
    - Mortalidad: Muerte antes de lo esperado
    - Longevidad: Supervivencia mayor a la esperada
    - Invalidez: Incapacidad del asegurado
    - Gastos: Gastos de administracion mayores a proyectados
    """

    suma_asegurada_total: Decimal = Field(
        ...,
        gt=0,
        description="Suma asegurada total de la cartera de vida",
    )
    reserva_matematica: Decimal = Field(
        ...,
        ge=0,
        description="Reserva matematica total (pasivo actuarial)",
    )
    edad_promedio_asegurados: int = Field(
        ...,
        ge=18,
        le=100,
        description="Edad promedio ponderada de asegurados",
    )
    duracion_promedio_polizas: int = Field(
        ...,
        ge=1,
        le=50,
        description="Duracion promedio de polizas en anos",
    )
    numero_asegurados: int = Field(
        default=1000,
        ge=1,
        description="Numero total de asegurados",
    )

    @field_validator("reserva_matematica")
    @classmethod
    def validar_reserva_vs_suma_asegurada(cls, v: Decimal, info: Any) -> Decimal:
        """La reserva no deberia exceder la suma asegurada"""
        if "suma_asegurada_total" in info.data:
            suma = info.data["suma_asegurada_total"]
            if v > suma * Decimal("2"):
                raise ValueError(
                    f"Reserva matematica ({v}) parece muy alta vs suma asegurada ({suma})"
                )
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "suma_asegurada_total": "500000000.00",
                    "reserva_matematica": "350000000.00",
                    "edad_promedio_asegurados": 45,
                    "duracion_promedio_polizas": 15,
                    "numero_asegurados": 10000,
                }
            ]
        }
    }


class ConfiguracionRCSDanos(BaseModel):
    """
    Configuracion para calculo de RCS de suscripcion en ramos de danos.

    El RCS de danos considera:
    - Riesgo de prima: Insuficiencia de primas vs siniestralidad
    - Riesgo de reserva: Insuficiencia de reservas de siniestros
    """

    primas_retenidas_12m: Decimal = Field(
        ...,
        gt=0,
        description="Primas retenidas (netas de reaseguro) ultimos 12 meses",
    )
    reserva_siniestros: Decimal = Field(
        ...,
        ge=0,
        description="Reserva de siniestros pendientes",
    )
    coeficiente_variacion: Decimal = Field(
        default=Decimal("0.15"),
        ge=Decimal("0.05"),
        le=Decimal("0.50"),
        description="Coeficiente de variacion historico de siniestralidad",
    )
    numero_ramos: int = Field(
        default=1,
        ge=1,
        le=20,
        description="Numero de ramos diferentes en cartera",
    )

    @field_validator("coeficiente_variacion")
    @classmethod
    def validar_coeficiente(cls, v: Decimal) -> Decimal:
        """CV tipicamente entre 5% y 50%"""
        if v < Decimal("0.05"):
            raise ValueError(
                "Coeficiente de variacion muy bajo (tipicamente >= 5%)"
            )
        if v > Decimal("0.50"):
            raise ValueError(
                "Coeficiente de variacion muy alto (tipicamente <= 50%)"
            )
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "primas_retenidas_12m": "250000000.00",
                    "reserva_siniestros": "180000000.00",
                    "coeficiente_variacion": "0.15",
                    "numero_ramos": 5,
                }
            ]
        }
    }


class ConfiguracionRCSInversion(BaseModel):
    """
    Configuracion para calculo de RCS de inversion (riesgos de mercado).

    Considera riesgos de:
    - Mercado: Caida en valor de acciones, bonos, etc.
    - Credito: Incumplimiento de emisores
    - Concentracion: Exceso de exposicion a un solo emisor
    """

    valor_acciones: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        description="Valor de mercado de acciones",
    )
    valor_bonos_gubernamentales: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        description="Valor de bonos gubernamentales",
    )
    valor_bonos_corporativos: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        description="Valor de bonos corporativos",
    )
    valor_inmuebles: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        description="Valor de bienes raices",
    )
    duracion_promedio_bonos: Decimal = Field(
        default=Decimal("5.0"),
        ge=Decimal("0.5"),
        le=Decimal("30.0"),
        description="Duracion promedio de cartera de bonos (anos)",
    )
    calificacion_promedio_bonos: str = Field(
        default="AAA",
        description="Calificacion crediticia promedio (AAA, AA, A, BBB, etc.)",
    )

    @field_validator("calificacion_promedio_bonos")
    @classmethod
    def validar_calificacion(cls, v: str) -> str:
        """Calificacion debe ser valida"""
        calificaciones_validas = [
            "AAA",
            "AA",
            "A",
            "BBB",
            "BB",
            "B",
            "CCC",
            "CC",
            "C",
        ]
        if v not in calificaciones_validas:
            raise ValueError(
                f"Calificacion '{v}' no v\u00e1lida. Debe ser una de: {calificaciones_validas}"
            )
        return v

    @model_validator(mode="after")
    def validar_total_inversiones(self) -> "ConfiguracionRCSInversion":
        """Debe haber al menos algunas inversiones"""
        total = (
            self.valor_acciones
            + self.valor_bonos_gubernamentales
            + self.valor_bonos_corporativos
            + self.valor_inmuebles
        )
        if total == 0:
            raise ValueError(
                "Debe especificar al menos un tipo de inversion con valor > 0"
            )
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "valor_acciones": "50000000.00",
                    "valor_bonos_gubernamentales": "300000000.00",
                    "valor_bonos_corporativos": "150000000.00",
                    "valor_inmuebles": "100000000.00",
                    "duracion_promedio_bonos": "7.5",
                    "calificacion_promedio_bonos": "AA",
                }
            ]
        }
    }


class ResultadoRCS(BaseModel):
    """
    Resultado del calculo completo de RCS.

    El RCS total se calcula agregando diferentes tipos de riesgo
    con una matriz de correlacion para evitar doble conteo.
    """

    # RCS por tipo de riesgo (vida)
    rcs_mortalidad: Decimal = Field(
        default=Decimal("0"), ge=0, description="RCS por riesgo de mortalidad"
    )
    rcs_longevidad: Decimal = Field(
        default=Decimal("0"), ge=0, description="RCS por riesgo de longevidad"
    )
    rcs_invalidez: Decimal = Field(
        default=Decimal("0"), ge=0, description="RCS por riesgo de invalidez"
    )
    rcs_gastos: Decimal = Field(
        default=Decimal("0"), ge=0, description="RCS por riesgo de gastos"
    )

    # RCS por tipo de riesgo (danos)
    rcs_prima: Decimal = Field(
        default=Decimal("0"), ge=0, description="RCS por riesgo de prima"
    )
    rcs_reserva: Decimal = Field(
        default=Decimal("0"), ge=0, description="RCS por riesgo de reserva"
    )

    # RCS por tipo de riesgo (inversion)
    rcs_mercado: Decimal = Field(
        default=Decimal("0"), ge=0, description="RCS por riesgo de mercado"
    )
    rcs_credito: Decimal = Field(
        default=Decimal("0"), ge=0, description="RCS por riesgo de credito"
    )
    rcs_concentracion: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        description="RCS por riesgo de concentracion",
    )

    # Agregados por categoria
    rcs_suscripcion_vida: Decimal = Field(
        ..., ge=0, description="RCS total de suscripcion vida"
    )
    rcs_suscripcion_danos: Decimal = Field(
        ..., ge=0, description="RCS total de suscripcion danos"
    )
    rcs_inversion: Decimal = Field(
        ..., ge=0, description="RCS total de inversion"
    )

    # RCS total agregado
    rcs_total: Decimal = Field(
        ..., gt=0, description="RCS total (con correlaciones aplicadas)"
    )

    # Capital y solvencia
    capital_minimo_pagado: Decimal = Field(
        ..., gt=0, description="Capital minimo pagado de la aseguradora"
    )
    excedente_solvencia: Decimal = Field(
        ..., description="Excedente o deficit de capital (puede ser negativo)"
    )
    ratio_solvencia: Decimal = Field(
        ..., gt=0, description="Ratio RCS/Capital (debe ser <= 1.0 para cumplir)"
    )
    cumple_regulacion: bool = Field(
        ..., description="True si cumple con RCS (capital >= RCS)"
    )

    # Desglose detallado
    desglose_por_riesgo: dict[str, Decimal] = Field(
        default_factory=dict,
        description="Desglose detallado de RCS por cada tipo de riesgo",
    )

    @model_validator(mode="after")
    def validar_agregacion(self) -> "ResultadoRCS":
        """Validar que los agregados sean consistentes"""
        # Validar que RCS total >= cada componente
        if self.rcs_total < self.rcs_suscripcion_vida:
            raise ValueError(
                "RCS total no puede ser menor que RCS suscripcion vida"
            )
        if self.rcs_total < self.rcs_suscripcion_danos:
            raise ValueError(
                "RCS total no puede ser menor que RCS suscripcion danos"
            )
        if self.rcs_total < self.rcs_inversion:
            raise ValueError("RCS total no puede ser menor que RCS inversion")

        # Validar ratio de solvencia
        ratio_calculado = (
            self.rcs_total / self.capital_minimo_pagado
            if self.capital_minimo_pagado > 0
            else Decimal("999")
        )
        if abs(ratio_calculado - self.ratio_solvencia) > Decimal("0.01"):
            raise ValueError(
                f"Ratio de solvencia inconsistente: "
                f"calculado={ratio_calculado}, proporcionado={self.ratio_solvencia}"
            )

        # Validar cumplimiento
        cumple_esperado = self.capital_minimo_pagado >= self.rcs_total
        if cumple_esperado != self.cumple_regulacion:
            raise ValueError(
                f"cumple_regulacion inconsistente: capital={self.capital_minimo_pagado}, "
                f"RCS={self.rcs_total}, cumple={self.cumple_regulacion}"
            )

        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "rcs_mortalidad": "15000000.00",
                    "rcs_longevidad": "8000000.00",
                    "rcs_invalidez": "5000000.00",
                    "rcs_gastos": "3000000.00",
                    "rcs_prima": "20000000.00",
                    "rcs_reserva": "12000000.00",
                    "rcs_mercado": "25000000.00",
                    "rcs_credito": "8000000.00",
                    "rcs_concentracion": "5000000.00",
                    "rcs_suscripcion_vida": "28000000.00",
                    "rcs_suscripcion_danos": "30000000.00",
                    "rcs_inversion": "35000000.00",
                    "rcs_total": "75000000.00",
                    "capital_minimo_pagado": "100000000.00",
                    "excedente_solvencia": "25000000.00",
                    "ratio_solvencia": "0.75",
                    "cumple_regulacion": True,
                    "desglose_por_riesgo": {
                        "mortalidad": "15000000.00",
                        "longevidad": "8000000.00",
                        "prima": "20000000.00",
                        "mercado": "25000000.00",
                    },
                }
            ]
        }
    }
