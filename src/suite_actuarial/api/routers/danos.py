"""
Danos (P&C) router -- property and casualty insurance endpoints.

Wraps SeguroAuto, SeguroIncendio, SeguroRC, CalculadoraBonusMalus,
and ModeloColectivo domain classes.
"""

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from suite_actuarial.danos.auto import SeguroAuto
from suite_actuarial.danos.incendio import SeguroIncendio
from suite_actuarial.danos.rc import SeguroRC
from suite_actuarial.danos.tarifas import CalculadoraBonusMalus
from suite_actuarial.danos.frecuencia_severidad import ModeloColectivo

router = APIRouter(prefix="/danos", tags=["danos"])


# ── Helper ──────────────────────────────────────────────────────────────────


def _decimal_to_float(obj: Any) -> Any:
    """Recursively convert Decimal values to float for JSON serialisation."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _decimal_to_float(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_decimal_to_float(item) for item in obj]
    return obj


# ── 1. Auto insurance quotation ────────────────────────────────────────────


class AutoRequest(BaseModel):
    """Request body for auto insurance quotation."""

    valor_vehiculo: float = Field(..., gt=0, description="Valor comercial del vehiculo en pesos MXN")
    tipo_vehiculo: str = Field(..., description="Clave del tipo de vehiculo (ver GRUPOS_VEHICULO)")
    antiguedad_anos: int = Field(..., ge=0, description="Anos de antiguedad del vehiculo")
    zona: str = Field(..., description="Clave de la zona de riesgo")
    edad_conductor: int = Field(..., ge=18, description="Edad del conductor principal en anos")
    deducible_pct: float = Field(default=0.05, description="Porcentaje de deducible (default 5%)")
    coberturas: list[str] | None = Field(default=None, description="Lista de coberturas a cotizar (None = todas)")
    historial_siniestros: list[int] | None = Field(
        default=None, description="Historial de siniestros anuales para Bonus-Malus"
    )


class AutoResponse(BaseModel):
    """Response for auto insurance quotation."""

    vehiculo: dict[str, Any]
    conductor: dict[str, Any]
    zona: dict[str, Any]
    deducible: dict[str, Any]
    coberturas: dict[str, float]
    subtotal: float
    bonus_malus: dict[str, Any]
    prima_total: float


@router.post("/auto/calcular", response_model=AutoResponse)
def calcular_auto(req: AutoRequest):
    """Generate a complete auto insurance quotation.

    Calculates premiums per coverage using AMIS reference tables, zone
    factors, driver age, deductible, depreciation, and optional Bonus-Malus
    adjustment.
    """
    try:
        seguro = SeguroAuto(
            valor_vehiculo=Decimal(str(req.valor_vehiculo)),
            tipo_vehiculo=req.tipo_vehiculo,
            antiguedad_anos=req.antiguedad_anos,
            zona=req.zona,
            edad_conductor=req.edad_conductor,
            deducible_pct=Decimal(str(req.deducible_pct)),
        )
        from suite_actuarial.danos.auto import Cobertura
        coberturas_enum = [Cobertura(c) for c in req.coberturas] if req.coberturas else None
        cotizacion = seguro.generar_cotizacion(
            coberturas=coberturas_enum,
            historial_siniestros=req.historial_siniestros,
        )
        return _decimal_to_float(cotizacion)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ── 2. Fire insurance premium ──────────────────────────────────────────────


class IncendioRequest(BaseModel):
    """Request body for fire insurance quotation."""

    valor_inmueble: float = Field(..., gt=0, description="Valor de reposicion del inmueble en pesos MXN")
    tipo_construccion: str = Field(..., description="Tipo de construccion (concreto, acero, ladrillo, mixta, madera, lamina)")
    zona: str = Field(..., description="Zona de riesgo (urbana_baja, urbana_media, urbana_alta, industrial, rural, forestal)")
    uso: str = Field(..., description="Uso del inmueble (habitacional, comercial, oficinas, industrial, bodega, restaurante)")


class IncendioResponse(BaseModel):
    """Response for fire insurance quotation."""

    valor_inmueble: float
    tipo_construccion: str
    tasa_base: float
    zona: str
    factor_zona: float
    uso: str
    factor_uso: float
    prima_anual: float


@router.post("/incendio/calcular", response_model=IncendioResponse)
def calcular_incendio(req: IncendioRequest):
    """Generate a fire insurance quotation.

    Calculates the annual premium based on property value, construction
    type, risk zone, and property use.
    """
    try:
        seguro = SeguroIncendio(
            valor_inmueble=Decimal(str(req.valor_inmueble)),
            tipo_construccion=req.tipo_construccion,
            zona=req.zona,
            uso=req.uso,
        )
        cotizacion = seguro.generar_cotizacion()
        return _decimal_to_float(cotizacion)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ── 3. Liability insurance premium ─────────────────────────────────────────


class RCRequest(BaseModel):
    """Request body for liability insurance quotation."""

    limite_responsabilidad: float = Field(..., gt=0, description="Limite maximo de cobertura en pesos MXN")
    deducible: float = Field(..., ge=0, description="Monto del deducible en pesos MXN")
    clase_actividad: str = Field(
        ...,
        description="Tipo de actividad (oficinas, comercio_minorista, restaurante, "
        "manufactura_ligera, manufactura_pesada, construccion, transporte, "
        "servicios_profesionales, salud, educacion, hoteleria, inmobiliaria)",
    )


class RCResponse(BaseModel):
    """Response for liability insurance quotation."""

    limite_responsabilidad: float
    deducible: float
    clase_actividad: str
    tasa_base: float
    factor_deducible: float
    prima_anual: float


@router.post("/rc/calcular", response_model=RCResponse)
def calcular_rc(req: RCRequest):
    """Generate a general liability insurance quotation.

    Calculates the annual premium based on liability limit, deductible,
    and class of business activity.
    """
    try:
        seguro = SeguroRC(
            limite_responsabilidad=Decimal(str(req.limite_responsabilidad)),
            deducible=Decimal(str(req.deducible)),
            clase_actividad=req.clase_actividad,
        )
        cotizacion = seguro.generar_cotizacion()
        return _decimal_to_float(cotizacion)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ── 4. Bonus-Malus calculation ─────────────────────────────────────────────


class BonusMalusRequest(BaseModel):
    """Request body for Bonus-Malus calculation."""

    nivel_actual: int = Field(
        default=0, ge=-5, le=3, description="Nivel BMS actual (-5 a 3, default 0 = base)"
    )
    numero_siniestros: int = Field(..., ge=0, description="Numero de siniestros en el periodo")


class BonusMalusResponse(BaseModel):
    """Response for Bonus-Malus calculation."""

    nivel_previo: int
    siniestros: int
    nivel_nuevo: int
    factor: float


@router.post("/bonus-malus", response_model=BonusMalusResponse)
def calcular_bonus_malus(req: BonusMalusRequest):
    """Calculate the Bonus-Malus level transition.

    Applies the standard Mexican BMS scale: no claims = -1 level (discount),
    1 claim = +2 levels, 2+ claims = +3 levels.
    """
    try:
        bms = CalculadoraBonusMalus(nivel_actual=req.nivel_actual)
        nivel_previo = bms.nivel_actual
        nivel_nuevo = bms.transicion(req.numero_siniestros)
        factor = float(bms.factor_actual())
        return BonusMalusResponse(
            nivel_previo=nivel_previo,
            siniestros=req.numero_siniestros,
            nivel_nuevo=nivel_nuevo,
            factor=factor,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ── 5. Collective risk model (frequency-severity) ─────────────────────────


class FrecuenciaSeveridadRequest(BaseModel):
    """Request body for the collective risk model simulation."""

    dist_frecuencia: str = Field(
        ..., description="Distribucion de frecuencia: poisson, negbinom, binomial"
    )
    params_frecuencia: dict[str, float] = Field(
        ...,
        description="Parametros de la distribucion de frecuencia. "
        "poisson: {lambda_: float}, negbinom: {n: float, p: float}, "
        "binomial: {n: int, p: float}",
    )
    dist_severidad: str = Field(
        ..., description="Distribucion de severidad: lognormal, pareto, gamma, weibull, exponencial"
    )
    params_severidad: dict[str, float] = Field(
        ...,
        description="Parametros de la distribucion de severidad. "
        "lognormal: {mu, sigma}, pareto: {alpha, scale}, gamma: {alpha, beta}, "
        "weibull: {c, scale}, exponencial: {lambda_}",
    )
    n_simulaciones: int = Field(default=100_000, ge=1_000, le=1_000_000, description="Numero de simulaciones Monte Carlo")
    seed: int | None = Field(default=None, description="Semilla para reproducibilidad")


class FrecuenciaSeveridadResponse(BaseModel):
    """Response for the collective risk model simulation."""

    prima_pura: float
    varianza_agregada: float
    desviacion_estandar: float
    asimetria: float
    var_95: float
    tvar_95: float
    var_99: float
    tvar_99: float
    minimo: float
    maximo: float
    simulaciones: int


@router.post("/frecuencia-severidad", response_model=FrecuenciaSeveridadResponse)
def calcular_frecuencia_severidad(req: FrecuenciaSeveridadRequest):
    """Run a collective risk model simulation (S = X1 + ... + XN).

    Fits frequency and severity distributions, runs Monte Carlo simulation,
    and returns risk measures including VaR, TVaR, and pure premium.
    """
    try:
        modelo = ModeloColectivo(
            dist_frecuencia=req.dist_frecuencia,
            params_frecuencia=req.params_frecuencia,
            dist_severidad=req.dist_severidad,
            params_severidad=req.params_severidad,
        )
        stats = modelo.estadisticas(
            n_simulaciones=req.n_simulaciones,
            seed=req.seed,
        )
        return _decimal_to_float(stats)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
