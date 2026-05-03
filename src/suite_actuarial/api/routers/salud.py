"""
Salud (Health) router -- GMM and Accidentes & Enfermedades endpoints.

Wraps the GMM and AccidentesEnfermedades product classes, providing
premium calculation endpoints for Mexican health insurance products.
"""

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from suite_actuarial.salud.gmm import GMM, NivelHospitalario, ZonaGeografica
from suite_actuarial.salud.accidentes import AccidentesEnfermedades

router = APIRouter(prefix="/salud", tags=["salud"])


# ── Helpers ─────────────────────────────────────────────────────────────────


def _decimal_to_float(obj: Any) -> Any:
    """Recursively convert Decimal values to float for JSON serialization."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _decimal_to_float(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_decimal_to_float(item) for item in obj]
    return obj


# ── GMM Request / Response models ──────────────────────────────────────────


class GMMRequest(BaseModel):
    """Request body for GMM premium calculation."""

    edad: int = Field(..., ge=0, le=110, description="Edad del asegurado (0-110)")
    sexo: str = Field(..., pattern="^[MF]$", description="Sexo: M (masculino) o F (femenino)")
    suma_asegurada: float = Field(..., ge=1_000_000, description="Suma asegurada en MXN (minimo 1,000,000)")
    deducible: float = Field(..., ge=0, description="Monto del deducible en MXN")
    coaseguro_pct: float = Field(..., gt=0, le=1, description="Porcentaje de coaseguro (ej: 0.10 = 10%)")
    tope_coaseguro: float | None = Field(default=None, ge=0, description="Tope maximo de coaseguro en MXN (None = sin tope)")
    zona: str = Field(default="urbano", description="Zona geografica: metro, urbano, foraneo")
    nivel: str = Field(default="medio", description="Nivel hospitalario: estandar, medio, alto")


class GMMResponse(BaseModel):
    """Response for GMM premium calculation."""

    asegurado: dict[str, Any]
    producto: dict[str, Any]
    tarificacion: dict[str, Any]
    siniestralidad_esperada: float


# ── Accidentes Request / Response models ───────────────────────────────────


class AccidentesRequest(BaseModel):
    """Request body for Accidentes y Enfermedades premium calculation."""

    edad: int = Field(..., ge=18, le=70, description="Edad del asegurado (18-70)")
    sexo: str = Field(..., pattern="^[MF]$", description="Sexo: M (masculino) o F (femenino)")
    suma_asegurada: float = Field(..., gt=0, description="Suma asegurada en MXN")
    ocupacion: str = Field(
        default="oficina",
        description="Clase de riesgo: oficina, comercio, industrial_ligero, industrial_pesado, alto_riesgo",
    )
    indemnizacion_diaria: float | None = Field(
        default=None,
        gt=0,
        description="Monto diario por hospitalizacion (None = 0.1% de SA)",
    )


class AccidentesResponse(BaseModel):
    """Response for Accidentes y Enfermedades premium calculation."""

    suma_asegurada: float
    prima_anual: float
    perdidas_organicas: dict[str, Any]
    indemnizacion_diaria: dict[str, float]
    gastos_funerarios: float


# ── Endpoints ──────────────────────────────────────────────────────────────


@router.post("/gmm/calcular", response_model=GMMResponse)
def calcular_gmm(req: GMMRequest):
    """Calculate GMM (Gastos Medicos Mayores) premium.

    Returns a detailed premium breakdown including base rate, adjustment
    factors (zone, hospital level, deductible, coinsurance), adjusted
    premium, and expected claims.
    """
    try:
        producto = GMM(
            edad=req.edad,
            sexo=req.sexo,
            suma_asegurada=Decimal(str(req.suma_asegurada)),
            deducible=Decimal(str(req.deducible)),
            coaseguro_pct=Decimal(str(req.coaseguro_pct)),
            tope_coaseguro=Decimal(str(req.tope_coaseguro)) if req.tope_coaseguro is not None else None,
            zona=ZonaGeografica(req.zona),
            nivel=NivelHospitalario(req.nivel),
        )
        desglose = producto.desglose_prima()
        return _decimal_to_float(desglose)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/accidentes/calcular", response_model=AccidentesResponse)
def calcular_accidentes(req: AccidentesRequest):
    """Calculate Accidentes y Enfermedades (A&E) premium.

    Returns the annual premium, organic-loss indemnification table,
    daily hospitalization benefit, and funeral expenses.
    """
    try:
        producto = AccidentesEnfermedades(
            edad=req.edad,
            sexo=req.sexo,
            suma_asegurada=Decimal(str(req.suma_asegurada)),
            ocupacion=req.ocupacion,
            indemnizacion_diaria=(
                Decimal(str(req.indemnizacion_diaria))
                if req.indemnizacion_diaria is not None
                else None
            ),
        )
        tabla = producto.tabla_indemnizaciones()
        return _decimal_to_float(tabla)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
