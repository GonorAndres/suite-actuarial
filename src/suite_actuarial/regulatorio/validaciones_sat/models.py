"""
Modelos Pydantic para validaciones fiscales SAT.

Define estructuras de datos para validar el tratamiento fiscal correcto
de primas y siniestros según la Ley del ISR mexicana.
"""

from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class EstadoFiscal(StrEnum):
    """Resultado fiscal tri-state; indeterminate evita inferencias peligrosas."""

    ELIGIBLE = "eligible"
    NOT_ELIGIBLE = "not_eligible"
    INDETERMINATE = "indeterminate"


class EstadoTopeGlobal(StrEnum):
    """Como se aplico el tope global del ultimo parrafo del Art. 151 LISR.

    El ultimo parrafo limita el **total** de deducciones personales del
    articulo a la menor de dos cantidades: cinco veces el valor anual de la UMA
    o el 15% del total de los ingresos del contribuyente. Con solo una de las
    dos cifras el tope no queda determinado, y decirlo es parte del resultado.
    """

    APLICADO = "aplicado"
    """Se evaluaron las dos ramas del tope: 5 UMA anuales y 15% de ingresos."""

    PARCIAL_SIN_INGRESOS = "parcial_sin_ingresos"
    """Solo se aplico la rama de 5 UMA: falto el ingreso total del contribuyente.

    El monto deducible resultante es una **cota superior**: la rama del 15% solo
    puede bajarlo.
    """

    NO_APLICABLE = "no_aplicable"
    """La deduccion queda fuera del tope global, o no hay deduccion que topar.

    Cubre la fraccion V (el ultimo parrafo la excluye expresamente), las primas
    no deducibles para persona fisica y el regimen de persona moral, que no usa
    deducciones personales.
    """


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
    estado: EstadoFiscal | None = None
    factores_faltantes: list[str] = Field(default_factory=list)
    tope_global: EstadoTopeGlobal = Field(
        default=EstadoTopeGlobal.NO_APLICABLE,
        description=(
            "Como se aplico el tope global del ultimo parrafo del Art. 151 "
            "LISR. Nunca se omite: un 100% deducible sin decir que paso con el "
            "tope es el defecto que este campo existe para evitar."
        ),
    )
    nota_tope_global: str | None = Field(
        default=None,
        description=(
            "Explicacion en prosa del estado del tope global: que rama se "
            "aplico, que falto y que alcance tiene la cifra resultante."
        ),
    )

    @model_validator(mode="after")
    def derive_status(self) -> "ResultadoDeducibilidadPrima":
        if self.estado is None:
            self.estado = EstadoFiscal.ELIGIBLE if self.es_deducible else EstadoFiscal.NOT_ELIGIBLE
        return self

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
    estado: EstadoFiscal | None = None
    factores_faltantes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def derive_status(self) -> "ResultadoGravabilidadSiniestro":
        if self.estado is None:
            self.estado = EstadoFiscal.ELIGIBLE if self.esta_gravado else EstadoFiscal.NOT_ELIGIBLE
        return self


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
    regla_aplicada: str | None = Field(
        default=None,
        description=(
            "Rama del calculo que determino el resultado. Describe que condicion "
            "se cumplio, no su fundamento legal: las citas de articulos de este "
            "modulo estan sin verificar (ver docs/AUDIT.md)."
        ),
    )


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
