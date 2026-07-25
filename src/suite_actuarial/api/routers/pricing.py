"""
Pricing router -- life insurance product pricing endpoints.

Wraps VidaTemporal, VidaOrdinario, and VidaDotal product classes,
loading the EMSSA-09 mortality table once and caching it at module level.
"""

from decimal import Decimal
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from suite_actuarial.actuarial.mortality.tablas import TablaMortalidad
from suite_actuarial.core.models.common import CalculationMetadata
from suite_actuarial.core.models.producto import ResultadoCalculo
from suite_actuarial.core.validators import (
    Asegurado,
    ConfiguracionProducto,
    Sexo,
)
from suite_actuarial.vida.dotal import VidaDotal
from suite_actuarial.vida.ordinario import VidaOrdinario
from suite_actuarial.vida.temporal import VidaTemporal

router = APIRouter(prefix="/pricing", tags=["pricing"])

# ── Mortality table cache ────────────────────────────────────────────────────
_tabla_mortalidad: TablaMortalidad | None = None


def _get_tabla() -> TablaMortalidad:
    """Load and cache the EMSSA-09 mortality table."""
    global _tabla_mortalidad
    if _tabla_mortalidad is None:
        _tabla_mortalidad = TablaMortalidad.cargar_emssa09()
    return _tabla_mortalidad


# ── Request / Response models ────────────────────────────────────────────────


class PricingRequest(BaseModel):
    """Shared request body for all life-pricing endpoints."""

    edad: int = Field(..., ge=0, le=120, description="Age of the insured (completed years)")
    sexo: str = Field(..., pattern="^[HM]$", description="Sex: H (male) or M (female)")
    suma_asegurada: float = Field(..., gt=0, description="Sum insured")
    plazo_years: int = Field(..., ge=1, le=99, description="Policy term in years")
    tasa_interes: float = Field(default=0.055, ge=0, le=0.15, description="Technical interest rate")
    frecuencia_pago: str = Field(
        default="anual",
        description="Payment frequency: anual, semestral, trimestral, mensual",
    )
    recargo_gastos_admin: float = Field(
        default=0.05, ge=0, le=1, description="Admin expense loading"
    )
    recargo_gastos_adq: float = Field(
        default=0.10, ge=0, le=1, description="Acquisition expense loading"
    )
    recargo_utilidad: float = Field(default=0.03, ge=0, le=1, description="Profit loading")


class PricingResponse(BaseModel):
    """Unified response for a single product pricing result."""

    producto: str
    prima_neta: float
    prima_total: float
    moneda: str
    desglose_recargos: dict[str, float]
    metadata: dict[str, Any]
    calculation_metadata: CalculationMetadata | None = None


class CompareResponse(BaseModel):
    """Response for the compare endpoint."""

    temporal: PricingResponse
    ordinario: PricingResponse
    dotal: PricingResponse


class DotalLabRequest(PricingRequest):
    """Assumptions for the guided limited-pay endowment laboratory."""

    plazo_pago: int = Field(..., ge=1, le=99, description="Premium-paying term")
    frecuencia_pago: Literal["anual", "semestral", "trimestral", "mensual"] = "anual"


class ReservaDotalResponse(BaseModel):
    """One point of the prospective reserve profile."""

    anio: int
    edad_alcanzada: int
    reserva: float


class VerificacionesDotalResponse(BaseModel):
    """Actuarial checks evaluated by the domain model.

    Each check contrasts the pricing engine against an independent path:
    commutation columns (Dx/Nx/Mx) for the benefit decomposition, and the
    retrospective Fackler recursion for the reserve path. The `diferencia_*`
    fields expose how far each identity sits from exact, so a caller can judge
    the margin instead of trusting a bare boolean.
    """

    descomposicion_beneficios: bool
    principio_equivalencia: bool
    reserva_inicial_cero: bool
    reserva_final_igual_beneficio: bool
    recursion_fackler: bool
    diferencia_equivalencia: float
    diferencia_descomposicion: float
    diferencia_recursion: float


class DotalLabResponse(BaseModel):
    """Inspectable result for the guided endowment experiment."""

    prima: PricingResponse
    plazo_pago: int
    vp_beneficio_muerte: float
    vp_beneficio_supervivencia: float
    vp_beneficios_total: float
    factor_anualidad_primas: float
    prima_neta_anual_equivalente: float
    reservas: list[ReservaDotalResponse]
    verificaciones: VerificacionesDotalResponse


# ── Helpers ──────────────────────────────────────────────────────────────────


def _build_config(req: PricingRequest, nombre: str) -> ConfiguracionProducto:
    return ConfiguracionProducto(
        nombre_producto=nombre,
        plazo_years=req.plazo_years,
        tasa_interes_tecnico=Decimal(str(req.tasa_interes)),
        recargo_gastos_admin=Decimal(str(req.recargo_gastos_admin)),
        recargo_gastos_adq=Decimal(str(req.recargo_gastos_adq)),
        recargo_utilidad=Decimal(str(req.recargo_utilidad)),
    )


def _build_asegurado(req: PricingRequest) -> Asegurado:
    return Asegurado(
        edad=req.edad,
        sexo=Sexo(req.sexo),
        suma_asegurada=Decimal(str(req.suma_asegurada)),
    )


def _resultado_to_response(producto_nombre: str, resultado: ResultadoCalculo) -> PricingResponse:
    return PricingResponse(
        producto=producto_nombre,
        prima_neta=float(resultado.prima_neta),
        prima_total=float(resultado.prima_total),
        moneda=resultado.moneda.value,
        desglose_recargos={k: float(v) for k, v in resultado.desglose_recargos.items()},
        metadata={
            k: (float(v) if isinstance(v, Decimal) else v) for k, v in resultado.metadata.items()
        },
        calculation_metadata=resultado.calculation_metadata,
    )


def _price_temporal(req: PricingRequest) -> PricingResponse:
    tabla = _get_tabla()
    config = _build_config(req, f"Vida Temporal {req.plazo_years} anios")
    asegurado = _build_asegurado(req)
    producto = VidaTemporal(config, tabla)
    resultado = producto.calcular_prima(asegurado, frecuencia_pago=req.frecuencia_pago)
    return _resultado_to_response("temporal", resultado)


def _price_ordinario(req: PricingRequest) -> PricingResponse:
    tabla = _get_tabla()
    config = _build_config(req, f"Vida Ordinario - Pago {req.plazo_years} anios")
    asegurado = _build_asegurado(req)
    producto = VidaOrdinario(config, tabla)
    resultado = producto.calcular_prima(asegurado, frecuencia_pago=req.frecuencia_pago)
    return _resultado_to_response("ordinario", resultado)


def _price_dotal(req: PricingRequest) -> PricingResponse:
    tabla = _get_tabla()
    config = _build_config(req, f"Dotal {req.plazo_years} anios")
    asegurado = _build_asegurado(req)
    producto = VidaDotal(config, tabla)
    resultado = producto.calcular_prima(asegurado, frecuencia_pago=req.frecuencia_pago)
    return _resultado_to_response("dotal", resultado)


def _analyze_dotal(req: DotalLabRequest) -> DotalLabResponse:
    tabla = _get_tabla()
    config = _build_config(req, f"Dotal educativo {req.plazo_years}/{req.plazo_pago}")
    asegurado = _build_asegurado(req)
    producto = VidaDotal(config, tabla, plazo_pago=req.plazo_pago)
    analisis = producto.analizar_producto(
        asegurado,
        frecuencia_pago=req.frecuencia_pago,
    )
    return DotalLabResponse(
        prima=_resultado_to_response("dotal", analisis.resultado_prima),
        plazo_pago=analisis.plazo_pago,
        vp_beneficio_muerte=float(analisis.vp_beneficio_muerte),
        vp_beneficio_supervivencia=float(analisis.vp_beneficio_supervivencia),
        vp_beneficios_total=float(analisis.vp_beneficios_total),
        factor_anualidad_primas=float(analisis.factor_anualidad_primas),
        prima_neta_anual_equivalente=float(analisis.prima_neta_anual_equivalente),
        reservas=[
            ReservaDotalResponse(
                anio=punto.anio,
                edad_alcanzada=punto.edad_alcanzada,
                reserva=float(punto.reserva),
            )
            for punto in analisis.reservas
        ],
        verificaciones=VerificacionesDotalResponse(
            descomposicion_beneficios=analisis.verificaciones.descomposicion_beneficios,
            principio_equivalencia=analisis.verificaciones.principio_equivalencia,
            reserva_inicial_cero=analisis.verificaciones.reserva_inicial_cero,
            reserva_final_igual_beneficio=(analisis.verificaciones.reserva_final_igual_beneficio),
            recursion_fackler=analisis.verificaciones.recursion_fackler,
            diferencia_equivalencia=float(analisis.verificaciones.diferencia_equivalencia),
            diferencia_descomposicion=float(analisis.verificaciones.diferencia_descomposicion),
            diferencia_recursion=float(analisis.verificaciones.diferencia_recursion),
        ),
    )


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/temporal", response_model=PricingResponse)
def price_temporal(req: PricingRequest) -> PricingResponse:
    """Price a term life (vida temporal) policy.

    Calculates the net and gross premium for a term life insurance product
    using the EMSSA-09 mortality table and standard actuarial methods.
    """
    try:
        return _price_temporal(req)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/ordinario", response_model=PricingResponse)
def price_ordinario(req: PricingRequest) -> PricingResponse:
    """Price a whole life (vida ordinario) policy.

    Calculates the net and gross premium for a whole-life insurance product.
    The plazo_years field controls the premium payment period (limited pay).
    """
    try:
        return _price_ordinario(req)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/dotal", response_model=PricingResponse)
def price_dotal(req: PricingRequest) -> PricingResponse:
    """Price an endowment (dotal) policy.

    Calculates the net and gross premium for an endowment product that
    pays on death OR survival at the end of the term.
    """
    try:
        return _price_dotal(req)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/dotal/lab", response_model=DotalLabResponse)
def analyze_dotal_lab(req: DotalLabRequest) -> DotalLabResponse:
    """Build and inspect a limited-pay endowment product."""
    try:
        return _analyze_dotal(req)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/compare", response_model=CompareResponse)
def compare_products(req: PricingRequest) -> CompareResponse:
    """Compare all three life products for the same insured.

    Returns pricing results for temporal, ordinario, and dotal products
    side-by-side using identical insured and configuration parameters.
    """
    try:
        return CompareResponse(
            temporal=_price_temporal(req),
            ordinario=_price_ordinario(req),
            dotal=_price_dotal(req),
        )
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
