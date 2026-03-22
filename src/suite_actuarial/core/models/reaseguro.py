"""Modelos para contratos de reaseguro y siniestros."""

from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from suite_actuarial.core.models.common import Moneda


class TipoContrato(StrEnum):
    """Tipos de contratos de reaseguro soportados"""

    QUOTA_SHARE = "quota_share"
    EXCESS_OF_LOSS = "excess_of_loss"
    STOP_LOSS = "stop_loss"


class TipoSiniestro(StrEnum):
    """Tipo de siniestro para efectos de reaseguro"""

    INDIVIDUAL = "individual"
    EVENTO_CATASTROFICO = "evento_catastrofico"


class ModalidadXL(StrEnum):
    """Modalidades de Excess of Loss"""

    POR_RIESGO = "por_riesgo"
    POR_EVENTO = "por_evento"


class Siniestro(BaseModel):
    """
    Representa un siniestro individual o agregado.

    Se usa para calcular recuperaciones de reaseguro.
    """

    id_siniestro: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Identificador unico del siniestro",
    )
    fecha_ocurrencia: date = Field(
        ...,
        description="Fecha en que ocurrio el siniestro",
    )
    monto_bruto: Decimal = Field(
        ...,
        gt=0,
        description="Monto del siniestro antes de reaseguro",
    )
    tipo: TipoSiniestro = Field(
        default=TipoSiniestro.INDIVIDUAL,
        description="Tipo de siniestro (individual o catastrofico)",
    )
    id_poliza: str | None = Field(
        default=None,
        description="ID de la poliza asociada (si aplica)",
    )
    descripcion: str | None = Field(
        default=None,
        max_length=500,
        description="Descripcion del siniestro",
    )

    @field_validator("monto_bruto")
    @classmethod
    def validar_monto_razonable(cls, v: Decimal) -> Decimal:
        """El monto debe ser positivo y razonable"""
        if v <= 0:
            raise ValueError("El monto del siniestro debe ser mayor a cero")
        if v > Decimal("1e9"):  # 1,000 millones - limite razonable
            raise ValueError("Monto de siniestro excesivamente alto")
        return v

    @field_validator("fecha_ocurrencia")
    @classmethod
    def validar_fecha_no_futura(cls, v: date) -> date:
        """La fecha del siniestro no puede ser futura"""
        from datetime import date as dt_date

        hoy = dt_date.today()
        if v > hoy:
            raise ValueError(
                f"La fecha del siniestro ({v}) no puede ser futura"
            )
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id_siniestro": "SIN-2024-001",
                    "fecha_ocurrencia": "2024-03-15",
                    "monto_bruto": "350000.00",
                    "tipo": "individual",
                    "id_poliza": "POL-12345",
                    "descripcion": "Fallecimiento del asegurado",
                }
            ]
        }
    }


class ConfiguracionReaseguro(BaseModel):
    """
    Configuracion base para contratos de reaseguro.

    Clase base que comparten todos los tipos de contratos.
    """

    tipo_contrato: TipoContrato = Field(
        ...,
        description="Tipo de contrato de reaseguro",
    )
    vigencia_inicio: date = Field(
        ...,
        description="Fecha de inicio de vigencia del contrato",
    )
    vigencia_fin: date = Field(
        ...,
        description="Fecha de fin de vigencia del contrato",
    )
    moneda: Moneda = Field(
        default=Moneda.MXN,
        description="Moneda del contrato",
    )

    @model_validator(mode="after")
    def validar_vigencia(self) -> "ConfiguracionReaseguro":
        """La fecha de fin debe ser posterior a la de inicio"""
        if self.vigencia_fin <= self.vigencia_inicio:
            raise ValueError(
                "La fecha de fin debe ser posterior a la de inicio"
            )

        # Validar que el periodo no sea mayor a 5 anos
        dias_vigencia = (self.vigencia_fin - self.vigencia_inicio).days
        if dias_vigencia > 365 * 5:
            raise ValueError(
                "El periodo de vigencia no puede exceder 5 anos"
            )

        return self


class QuotaShareConfig(ConfiguracionReaseguro):
    """
    Configuracion para contrato Quota Share (Cuota Parte).

    El reasegurador acepta un % fijo de cada riesgo y paga
    una comision a la cedente.
    """

    porcentaje_cesion: Decimal = Field(
        ...,
        gt=0,
        le=100,
        description="Porcentaje cedido al reasegurador (0-100%)",
    )
    comision_reaseguro: Decimal = Field(
        ...,
        ge=0,
        le=50,
        description="Comision que el reasegurador paga a la cedente (%)",
    )
    comision_override: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        le=10,
        description="Comision adicional (override) si aplica (%)",
    )

    @field_validator("porcentaje_cesion")
    @classmethod
    def validar_porcentaje(cls, v: Decimal) -> Decimal:
        """Porcentaje debe estar entre 0 y 100"""
        if not (0 < v <= 100):
            raise ValueError(
                f"Porcentaje de cesion debe estar entre 0 y 100, recibido: {v}"
            )
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "tipo_contrato": "quota_share",
                    "vigencia_inicio": "2024-01-01",
                    "vigencia_fin": "2024-12-31",
                    "moneda": "MXN",
                    "porcentaje_cesion": "30.00",
                    "comision_reaseguro": "25.00",
                    "comision_override": "2.50",
                }
            ]
        }
    }


class ExcessOfLossConfig(ConfiguracionReaseguro):
    """
    Configuracion para contrato Excess of Loss (Exceso de Perdida).

    El reasegurador paga cuando un siniestro excede la retencion,
    hasta un limite maximo.
    """

    retencion: Decimal = Field(
        ...,
        gt=0,
        description="Retencion de la cedente (prioridad)",
    )
    limite: Decimal = Field(
        ...,
        gt=0,
        description="Limite de cobertura del reasegurador",
    )
    modalidad: ModalidadXL = Field(
        default=ModalidadXL.POR_RIESGO,
        description="Modalidad del XL (por riesgo o por evento)",
    )
    numero_reinstatements: int = Field(
        default=0,
        ge=0,
        le=3,
        description="Numero de reinstalaciones permitidas",
    )
    tasa_prima: Decimal = Field(
        ...,
        gt=0,
        le=100,
        description="Tasa de prima (% sobre el limite)",
    )

    @model_validator(mode="after")
    def validar_limite_mayor_retencion(self) -> "ExcessOfLossConfig":
        """El limite debe ser mayor que la retencion"""
        if self.limite <= self.retencion:
            raise ValueError(
                f"El limite ({self.limite}) debe ser mayor que "
                f"la retencion ({self.retencion})"
            )
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "tipo_contrato": "excess_of_loss",
                    "vigencia_inicio": "2024-01-01",
                    "vigencia_fin": "2024-12-31",
                    "moneda": "MXN",
                    "retencion": "200000.00",
                    "limite": "500000.00",
                    "modalidad": "por_riesgo",
                    "numero_reinstatements": 2,
                    "tasa_prima": "5.00",
                }
            ]
        }
    }


class StopLossConfig(ConfiguracionReaseguro):
    """
    Configuracion para contrato Stop Loss.

    Protege cuando la siniestralidad agregada excede un porcentaje
    (attachment point) hasta un limite.
    """

    attachment_point: Decimal = Field(
        ...,
        gt=0,
        le=200,
        description="Punto de activacion (% de siniestralidad)",
    )
    limite_cobertura: Decimal = Field(
        ...,
        gt=0,
        le=100,
        description="Limite de cobertura adicional (%)",
    )
    primas_sujetas: Decimal = Field(
        ...,
        gt=0,
        description="Primas sujetas al contrato (base de calculo)",
    )

    @field_validator("attachment_point")
    @classmethod
    def validar_attachment(cls, v: Decimal) -> Decimal:
        """El attachment debe ser razonable (tipicamente 60-150%)"""
        if v < 50:
            raise ValueError(
                "Attachment point muy bajo (tipicamente >= 60%)"
            )
        if v > 200:
            raise ValueError(
                "Attachment point muy alto (tipicamente <= 150%)"
            )
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "tipo_contrato": "stop_loss",
                    "vigencia_inicio": "2024-01-01",
                    "vigencia_fin": "2024-12-31",
                    "moneda": "MXN",
                    "attachment_point": "80.00",
                    "limite_cobertura": "20.00",
                    "primas_sujetas": "10000000.00",
                }
            ]
        }
    }


class ResultadoReaseguro(BaseModel):
    """
    Resultado de aplicar un contrato de reaseguro.

    Contiene los montos cedidos, retenidos y recuperados,
    asi como las comisiones y primas pagadas.
    """

    tipo_contrato: TipoContrato = Field(
        ...,
        description="Tipo de contrato aplicado",
    )
    monto_cedido: Decimal = Field(
        ...,
        ge=0,
        description="Monto cedido al reasegurador",
    )
    monto_retenido: Decimal = Field(
        ...,
        ge=0,
        description="Monto retenido por la cedente",
    )
    recuperacion_reaseguro: Decimal = Field(
        ...,
        ge=0,
        description="Monto recuperado del reasegurador",
    )
    comision_recibida: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        description="Comision recibida del reasegurador",
    )
    prima_reaseguro_pagada: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        description="Prima pagada al reasegurador",
    )
    ratio_cesion: Decimal = Field(
        ...,
        ge=0,
        le=100,
        description="% de cesion efectivo",
    )
    resultado_neto_cedente: Decimal = Field(
        ...,
        description="Resultado neto para la cedente (puede ser negativo)",
    )
    detalles: dict[str, Any] = Field(
        default_factory=dict,
        description="Detalles adicionales del calculo",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "tipo_contrato": "quota_share",
                    "monto_cedido": "300000.00",
                    "monto_retenido": "700000.00",
                    "recuperacion_reaseguro": "150000.00",
                    "comision_recibida": "82500.00",
                    "prima_reaseguro_pagada": "300000.00",
                    "ratio_cesion": "30.00",
                    "resultado_neto_cedente": "532500.00",
                    "detalles": {
                        "porcentaje_cesion": "30%",
                        "comision_total": "27.5%",
                    },
                }
            ]
        }
    }
