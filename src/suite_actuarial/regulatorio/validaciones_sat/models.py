"""
Modelos Pydantic para validaciones fiscales SAT.

Define estructuras de datos para validar el tratamiento fiscal correcto
de primas y siniestros según la Ley del ISR mexicana.
"""

from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class TipoSeguroFiscal(StrEnum):
    """Tipos de seguro para efectos fiscales SAT"""

    VIDA = "vida"
    GASTOS_MEDICOS = "gastos_medicos"  # GMM - Gastos Médicos Mayores
    DANOS = "danos"
    PENSIONES = "pensiones"
    INVALIDEZ = "invalidez"


class ResultadoDeducibilidadPrima(BaseModel):
    """
    Resultado de validación de deducibilidad de prima.

    Determina si una prima es deducible para ISR y hasta qué monto.
    """

    es_deducible: bool
    monto_prima: Decimal = Field(..., ge=0)
    monto_deducible: Decimal = Field(..., ge=0)
    porcentaje_deducible: Decimal = Field(..., ge=0, le=100)
    limite_aplicado: str | None = None
    fundamento_legal: str

    @property
    def monto_no_deducible(self) -> Decimal:
        """Monto no deducible de la prima"""
        return self.monto_prima - self.monto_deducible


class ResultadoGravabilidadSiniestro(BaseModel):
    """
    Resultado de validación de gravabilidad de siniestro.

    Determina si un siniestro está gravado o exento de ISR.
    """

    esta_gravado: bool
    monto_siniestro: Decimal = Field(..., ge=0)
    monto_gravado: Decimal = Field(..., ge=0)
    monto_exento: Decimal = Field(..., ge=0)
    tasa_isr_aplicable: Decimal = Field(..., ge=0, le=1)
    fundamento_legal: str


class ResultadoRetencion(BaseModel):
    """
    Resultado de cálculo de retención de ISR.

    Calcula la retención que debe aplicarse en pagos de seguros.
    """

    monto_pago: Decimal = Field(..., ge=0)
    base_retencion: Decimal = Field(..., ge=0)
    tasa_retencion: Decimal = Field(..., ge=0, le=1)
    monto_retencion: Decimal = Field(..., ge=0)
    monto_neto_pagar: Decimal = Field(..., ge=0)
    requiere_retencion: bool


class ResultadoIVA(BaseModel):
    """
    Resultado de validación de IVA en primas.

    Las primas de seguros están exentas de IVA en México,
    salvo algunas excepciones.
    """

    aplica_iva: bool
    monto_prima: Decimal = Field(..., ge=0)
    tasa_iva: Decimal = Field(default=Decimal("0"), ge=0, le=1)
    monto_iva: Decimal = Field(default=Decimal("0"), ge=0)
    fundamento_legal: str

    @property
    def monto_total(self) -> Decimal:
        """Monto total incluyendo IVA"""
        return self.monto_prima + self.monto_iva
