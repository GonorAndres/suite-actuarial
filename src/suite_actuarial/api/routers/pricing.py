"""
Pricing router -- life insurance product pricing endpoints.

Wraps VidaTemporal, VidaOrdinario, and VidaDotal product classes,
loading the EMSSA-09 mortality table once and caching it at module level.
"""

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from suite_actuarial.actuarial.mortality.tablas import TablaMortalidad
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
    recargo_gastos_admin: float = Field(default=0.05, ge=0, le=1, description="Admin expense loading")
    recargo_gastos_adq: float = Field(default=0.10, ge=0, le=1, description="Acquisition expense loading")
    recargo_utilidad: float = Field(default=0.03, ge=0, le=1, description="Profit loading")


class PricingResponse(BaseModel):
    """Unified response for a single product pricing result."""

    producto: str
    prima_neta: float
    prima_total: float
    moneda: str
    desglose_recargos: dict[str, float]
    metadata: dict[str, Any]


class CompareResponse(BaseModel):
    """Response for the compare endpoint."""

    temporal: PricingResponse
    ordinario: PricingResponse
    dotal: PricingResponse


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


def _resultado_to_response(producto_nombre: str, resultado) -> PricingResponse:
    return PricingResponse(
        producto=producto_nombre,
        prima_neta=float(resultado.prima_neta),
        prima_total=float(resultado.prima_total),
        moneda=resultado.moneda.value,
        desglose_recargos={k: float(v) for k, v in resultado.desglose_recargos.items()},
        metadata={
            k: (float(v) if isinstance(v, Decimal) else v)
            for k, v in resultado.metadata.items()
        },
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


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/temporal", response_model=PricingResponse)
def price_temporal(req: PricingRequest):
    """Price a term life (vida temporal) policy.

    Calculates the net and gross premium for a term life insurance product
    using the EMSSA-09 mortality table and standard actuarial methods.
    """
    try:
        return _price_temporal(req)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/ordinario", response_model=PricingResponse)
def price_ordinario(req: PricingRequest):
    """Price a whole life (vida ordinario) policy.

    Calculates the net and gross premium for a whole-life insurance product.
    The plazo_years field controls the premium payment period (limited pay).
    """
    try:
        return _price_ordinario(req)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/dotal", response_model=PricingResponse)
def price_dotal(req: PricingRequest):
    """Price an endowment (dotal) policy.

    Calculates the net and gross premium for an endowment product that
    pays on death OR survival at the end of the term.
    """
    try:
        return _price_dotal(req)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/compare", response_model=CompareResponse)
def compare_products(req: PricingRequest):
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
