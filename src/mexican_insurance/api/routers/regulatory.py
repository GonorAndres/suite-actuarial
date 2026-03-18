"""
Regulatory router -- RCS capital requirements and SAT fiscal validations.

Wraps AgregadorRCS, ValidadorPrimasDeducibles, and CalculadoraRetencionesISR.
"""

from decimal import Decimal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from mexican_insurance.regulatorio.agregador_rcs import AgregadorRCS
from mexican_insurance.regulatorio.validaciones_sat.models import TipoSeguroFiscal
from mexican_insurance.regulatorio.validaciones_sat.validador_primas import (
    ValidadorPrimasDeducibles,
)
from mexican_insurance.regulatorio.validaciones_sat.validador_retenciones import (
    CalculadoraRetencionesISR,
)

router = APIRouter(prefix="/regulatory", tags=["regulatory"])


# ── RCS request / response models ────────────────────────────────────────────


class RCSVidaIn(BaseModel):
    """Life subscription risk inputs for RCS."""

    suma_asegurada_total: float = Field(..., gt=0)
    reserva_matematica: float = Field(..., ge=0)
    edad_promedio_asegurados: int = Field(..., ge=18, le=100)
    duracion_promedio_polizas: int = Field(..., ge=1, le=50)
    numero_asegurados: int = Field(default=1000, ge=1)


class RCSDanosIn(BaseModel):
    """Property & casualty subscription risk inputs for RCS."""

    primas_retenidas_12m: float = Field(..., gt=0)
    reserva_siniestros: float = Field(..., ge=0)
    coeficiente_variacion: float = Field(default=0.15, ge=0.05, le=0.50)
    numero_ramos: int = Field(default=1, ge=1, le=20)


class RCSInversionIn(BaseModel):
    """Investment risk inputs for RCS."""

    valor_acciones: float = Field(default=0.0, ge=0)
    valor_bonos_gubernamentales: float = Field(default=0.0, ge=0)
    valor_bonos_corporativos: float = Field(default=0.0, ge=0)
    valor_inmuebles: float = Field(default=0.0, ge=0)
    duracion_promedio_bonos: float = Field(default=5.0, ge=0.5, le=30.0)
    calificacion_promedio_bonos: str = Field(default="AAA")


class RCSRequest(BaseModel):
    """Full RCS calculation request."""

    config_vida: RCSVidaIn | None = None
    config_danos: RCSDanosIn | None = None
    config_inversion: RCSInversionIn | None = None
    capital_minimo_pagado: float = Field(..., gt=0)


class RCSResponse(BaseModel):
    """Full RCS calculation response."""

    rcs_mortalidad: float
    rcs_longevidad: float
    rcs_invalidez: float
    rcs_gastos: float
    rcs_prima: float
    rcs_reserva: float
    rcs_mercado: float
    rcs_credito: float
    rcs_concentracion: float
    rcs_suscripcion_vida: float
    rcs_suscripcion_danos: float
    rcs_inversion: float
    rcs_total: float
    capital_minimo_pagado: float
    excedente_solvencia: float
    ratio_solvencia: float
    cumple_regulacion: bool
    desglose_por_riesgo: dict[str, float]


# ── SAT request / response models ────────────────────────────────────────────


class DeductibilityRequest(BaseModel):
    """Request body for SAT premium deductibility check."""

    tipo_seguro: str = Field(
        ...,
        description="Insurance type: vida, gastos_medicos, danos, pensiones, invalidez",
    )
    monto_prima: float = Field(..., gt=0)
    es_persona_fisica: bool = Field(default=True)
    uma_anual: float = Field(
        default=39960.60,
        gt=0,
        description="Annual UMA value (UMA diaria x 365)",
    )


class DeductibilityResponse(BaseModel):
    """SAT deductibility check response."""

    es_deducible: bool
    monto_prima: float
    monto_deducible: float
    porcentaje_deducible: float
    limite_aplicado: str | None = None
    fundamento_legal: str


class WithholdingRequest(BaseModel):
    """Request body for ISR withholding calculation."""

    tipo_seguro: str = Field(
        ...,
        description="Insurance type: vida, gastos_medicos, danos, pensiones, invalidez",
    )
    monto_pago: float = Field(..., gt=0)
    monto_gravable: float = Field(..., ge=0)
    es_renta_vitalicia: bool = Field(default=False)
    es_retiro_ahorro: bool = Field(default=False)
    requiere_retencion_forzosa: bool = Field(default=False)


class WithholdingResponse(BaseModel):
    """ISR withholding calculation response."""

    requiere_retencion: bool
    monto_pago: float
    base_retencion: float
    tasa_retencion: float
    monto_retencion: float
    monto_neto_pagar: float


# ── Helpers ──────────────────────────────────────────────────────────────────


def _rcs_resultado_to_response(resultado) -> RCSResponse:
    return RCSResponse(
        rcs_mortalidad=float(resultado.rcs_mortalidad),
        rcs_longevidad=float(resultado.rcs_longevidad),
        rcs_invalidez=float(resultado.rcs_invalidez),
        rcs_gastos=float(resultado.rcs_gastos),
        rcs_prima=float(resultado.rcs_prima),
        rcs_reserva=float(resultado.rcs_reserva),
        rcs_mercado=float(resultado.rcs_mercado),
        rcs_credito=float(resultado.rcs_credito),
        rcs_concentracion=float(resultado.rcs_concentracion),
        rcs_suscripcion_vida=float(resultado.rcs_suscripcion_vida),
        rcs_suscripcion_danos=float(resultado.rcs_suscripcion_danos),
        rcs_inversion=float(resultado.rcs_inversion),
        rcs_total=float(resultado.rcs_total),
        capital_minimo_pagado=float(resultado.capital_minimo_pagado),
        excedente_solvencia=float(resultado.excedente_solvencia),
        ratio_solvencia=float(resultado.ratio_solvencia),
        cumple_regulacion=resultado.cumple_regulacion,
        desglose_por_riesgo={k: float(v) for k, v in resultado.desglose_por_riesgo.items()},
    )


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/rcs", response_model=RCSResponse)
def calculate_rcs(req: RCSRequest):
    """Calculate the full Requerimiento de Capital de Solvencia (RCS).

    Aggregates subscription risks (life and P&C) and investment risks
    using a correlation matrix per CNSF regulations.
    At least one of config_vida, config_danos, or config_inversion must be provided.
    """
    try:
        from mexican_insurance.core.validators import (
            ConfiguracionRCSDanos,
            ConfiguracionRCSInversion,
            ConfiguracionRCSVida,
        )

        cfg_vida = None
        cfg_danos = None
        cfg_inversion = None

        if req.config_vida is not None:
            v = req.config_vida
            cfg_vida = ConfiguracionRCSVida(
                suma_asegurada_total=Decimal(str(v.suma_asegurada_total)),
                reserva_matematica=Decimal(str(v.reserva_matematica)),
                edad_promedio_asegurados=v.edad_promedio_asegurados,
                duracion_promedio_polizas=v.duracion_promedio_polizas,
                numero_asegurados=v.numero_asegurados,
            )

        if req.config_danos is not None:
            d = req.config_danos
            cfg_danos = ConfiguracionRCSDanos(
                primas_retenidas_12m=Decimal(str(d.primas_retenidas_12m)),
                reserva_siniestros=Decimal(str(d.reserva_siniestros)),
                coeficiente_variacion=Decimal(str(d.coeficiente_variacion)),
                numero_ramos=d.numero_ramos,
            )

        if req.config_inversion is not None:
            i = req.config_inversion
            cfg_inversion = ConfiguracionRCSInversion(
                valor_acciones=Decimal(str(i.valor_acciones)),
                valor_bonos_gubernamentales=Decimal(str(i.valor_bonos_gubernamentales)),
                valor_bonos_corporativos=Decimal(str(i.valor_bonos_corporativos)),
                valor_inmuebles=Decimal(str(i.valor_inmuebles)),
                duracion_promedio_bonos=Decimal(str(i.duracion_promedio_bonos)),
                calificacion_promedio_bonos=i.calificacion_promedio_bonos,
            )

        agregador = AgregadorRCS(
            config_vida=cfg_vida,
            config_danos=cfg_danos,
            config_inversion=cfg_inversion,
            capital_minimo_pagado=Decimal(str(req.capital_minimo_pagado)),
        )

        resultado = agregador.calcular_rcs_completo()
        return _rcs_resultado_to_response(resultado)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/sat/deductibility", response_model=DeductibilityResponse)
def check_deductibility(req: DeductibilityRequest):
    """Check premium deductibility for ISR purposes per SAT rules.

    Determines whether an insurance premium is tax-deductible and up to
    what amount, based on the type of insurance and taxpayer category
    (persona fisica or moral).
    """
    try:
        validador = ValidadorPrimasDeducibles(uma_anual=Decimal(str(req.uma_anual)))
        resultado = validador.validar_deducibilidad(
            tipo_seguro=TipoSeguroFiscal(req.tipo_seguro),
            monto_prima=Decimal(str(req.monto_prima)),
            es_persona_fisica=req.es_persona_fisica,
        )
        return DeductibilityResponse(
            es_deducible=resultado.es_deducible,
            monto_prima=float(resultado.monto_prima),
            monto_deducible=float(resultado.monto_deducible),
            porcentaje_deducible=float(resultado.porcentaje_deducible),
            limite_aplicado=resultado.limite_aplicado,
            fundamento_legal=resultado.fundamento_legal,
        )
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/sat/withholding", response_model=WithholdingResponse)
def calculate_withholding(req: WithholdingRequest):
    """Calculate ISR withholding on an insurance payment.

    Determines whether withholding applies and computes the retention
    amount based on payment type (annuities, savings withdrawals, etc.)
    per Ley del ISR.
    """
    try:
        calculadora = CalculadoraRetencionesISR()
        resultado = calculadora.calcular_retencion(
            tipo_seguro=TipoSeguroFiscal(req.tipo_seguro),
            monto_pago=Decimal(str(req.monto_pago)),
            monto_gravable=Decimal(str(req.monto_gravable)),
            es_renta_vitalicia=req.es_renta_vitalicia,
            es_retiro_ahorro=req.es_retiro_ahorro,
            requiere_retencion_forzosa=req.requiere_retencion_forzosa,
        )
        return WithholdingResponse(
            requiere_retencion=resultado.requiere_retencion,
            monto_pago=float(resultado.monto_pago),
            base_retencion=float(resultado.base_retencion),
            tasa_retencion=float(resultado.tasa_retencion),
            monto_retencion=float(resultado.monto_retencion),
            monto_neto_pagar=float(resultado.monto_neto_pagar),
        )
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
