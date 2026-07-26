"""
Reserves router -- Chain Ladder, Bornhuetter-Ferguson, and Bootstrap endpoints.

Accepts triangles as list-of-lists and origin years, converts them to
pandas DataFrames, then delegates to the library reserve calculators.
"""

from decimal import Decimal
from typing import Any, Literal

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from suite_actuarial.api.schemas import SolicitudBase
from suite_actuarial.core.models.common import CalculationMetadata
from suite_actuarial.core.models.reservas import ResultadoReserva
from suite_actuarial.core.validators import (
    ConfiguracionBootstrap,
    ConfiguracionBornhuetterFerguson,
    ConfiguracionChainLadder,
    MetodoPromedio,
    TipoTriangulo,
)
from suite_actuarial.reservas.bootstrap import Bootstrap
from suite_actuarial.reservas.bornhuetter_ferguson import BornhuetterFerguson
from suite_actuarial.reservas.chain_ladder import ChainLadder

router = APIRouter(prefix="/reserves", tags=["reserves"])

# Cota explicita del tamano del triangulo. Antes solo lo limitaban los valores
# por omision de Cloud Run (cuerpo de ~32 MB, timeout de 60 s), que son de la
# infraestructura y no del servicio: un triangulo enorme agotaba el tiempo de
# una de las 2 instancias en lugar de recibir un rechazo inmediato. 60x60 cubre
# con holgura cualquier triangulo real (60 anios de origen).
MAX_ANIOS_ORIGEN = 60
MAX_PERIODOS_DESARROLLO = 60


# ── Request / Response models ────────────────────────────────────────────────


class ChainLadderRequest(SolicitudBase):
    """Request body for Chain Ladder reserve calculation."""

    triangle: list[list[float | None]] = Field(
        ...,
        max_length=MAX_ANIOS_ORIGEN,
        description="Development triangle as list of rows (None for missing cells)",
    )
    origin_years: list[int] = Field(..., description="Origin year labels (one per row)")
    tipo_triangulo: Literal["acumulado", "incremental"] = Field(
        ...,
        description=(
            "Shape of the submitted triangle. Required and declared, never "
            "inferred: an incremental triangle read as cumulative understates "
            "the reserve"
        ),
    )
    permitir_desarrollo_negativo: bool = Field(
        default=False,
        description=(
            "Allow negative development: negative increments, or cumulative rows "
            "that decrease. Real in paid triangles with salvage/subrogation and in "
            "incurred triangles with reserve releases. Off by default so a "
            "mis-keyed triangle does not pass silently"
        ),
    )
    metodo_promedio: str = Field(
        default="simple", description="Averaging method: simple, weighted, geometric"
    )
    calcular_tail_factor: bool = Field(
        default=False,
        description=(
            "Estimate the tail factor by fitting Sherman's (1984) inverse power "
            "curve to the observed development factors. This is extrapolation: "
            "check tail_ajuste_r2 and tail_horizonte in the response details"
        ),
    )
    tail_factor: float | None = Field(
        default=None, ge=1.0, le=2.0, description="Manual tail factor (if not auto-calculated)"
    )
    unidad_monetaria: Literal["millones_mxn"] = Field(
        default="millones_mxn",
        description="Reporting scale for every monetary value in the triangle",
    )


class BornhuetterFergusonRequest(SolicitudBase):
    """Request body for Bornhuetter-Ferguson reserve calculation."""

    triangle: list[list[float | None]] = Field(..., max_length=MAX_ANIOS_ORIGEN)
    origin_years: list[int] = Field(...)
    tipo_triangulo: Literal["acumulado", "incremental"] = Field(
        ...,
        description=(
            "Shape of the submitted triangle. Required and declared, never "
            "inferred: an incremental triangle read as cumulative understates "
            "the reserve"
        ),
    )
    permitir_desarrollo_negativo: bool = Field(
        default=False,
        description=(
            "Allow negative development: negative increments, or cumulative rows "
            "that decrease. Real in paid triangles with salvage/subrogation and in "
            "incurred triangles with reserve releases. Off by default so a "
            "mis-keyed triangle does not pass silently"
        ),
    )
    primas_por_anio: dict[int, float] = Field(..., description="Earned premiums by origin year")
    loss_ratio_apriori: float = Field(
        ..., gt=0, le=2.0, description="A-priori expected loss ratio (e.g. 0.65)"
    )
    metodo_promedio: str = Field(default="simple")
    unidad_monetaria: Literal["millones_mxn"] = "millones_mxn"


class BootstrapRequest(SolicitudBase):
    """Request body for the residual re-sampling band (illustrative).

    Not an ODP bootstrap — see `calculate_bootstrap` and `docs/AUDIT.md` (A2).
    """

    triangle: list[list[float | None]] = Field(..., max_length=MAX_ANIOS_ORIGEN)
    origin_years: list[int] = Field(...)
    tipo_triangulo: Literal["acumulado", "incremental"] = Field(
        ...,
        description=(
            "Shape of the submitted triangle. Required and declared, never "
            "inferred: an incremental triangle read as cumulative understates "
            "the reserve"
        ),
    )
    permitir_desarrollo_negativo: bool = Field(
        default=False,
        description=(
            "Allow negative development: negative increments, or cumulative rows "
            "that decrease. Real in paid triangles with salvage/subrogation and in "
            "incurred triangles with reserve releases. Off by default so a "
            "mis-keyed triangle does not pass silently"
        ),
    )
    num_simulaciones: int = Field(default=1000, ge=100, le=10000)
    seed: int | None = Field(default=None)
    percentiles: list[int] = Field(default=[50, 75, 90, 95, 99])
    unidad_monetaria: Literal["millones_mxn"] = "millones_mxn"


class ReserveResponse(BaseModel):
    """Unified reserve calculation response."""

    metodo: str
    unidad_monetaria: Literal["millones_mxn"] = "millones_mxn"
    reserva_total: float
    ultimate_total: float
    pagado_total: float
    reservas_por_anio: dict[int, float]
    ultimates_por_anio: dict[int, float]
    factores_desarrollo: list[float] | None = None
    percentiles: dict[int, float] | None = None
    detalles: dict[str, Any] = {}
    calculation_metadata: CalculationMetadata | None = None


# ── Helpers ──────────────────────────────────────────────────────────────────


def _build_triangle(rows: list[list[float | None]], years: list[int]) -> pd.DataFrame:
    """Convert list-of-lists + origin years into a pandas DataFrame."""
    if len(rows) != len(years):
        raise ValueError(
            f"Number of rows ({len(rows)}) must match number of origin years ({len(years)})"
        )
    n_cols = max(len(r) for r in rows)
    if n_cols > MAX_PERIODOS_DESARROLLO:
        raise ValueError(
            f"El triangulo tiene {n_cols} periodos de desarrollo, por encima del "
            f"limite de {MAX_PERIODOS_DESARROLLO}."
        )
    col_labels = list(range(1, n_cols + 1))
    df = pd.DataFrame(rows, index=years, columns=col_labels, dtype=float)
    return df


def _resultado_to_response(resultado: ResultadoReserva) -> ReserveResponse:
    return ReserveResponse(
        metodo=resultado.metodo.value,
        reserva_total=float(resultado.reserva_total),
        ultimate_total=float(resultado.ultimate_total),
        pagado_total=float(resultado.pagado_total),
        reservas_por_anio={k: float(v) for k, v in resultado.reservas_por_anio.items()},
        ultimates_por_anio={k: float(v) for k, v in resultado.ultimates_por_anio.items()},
        factores_desarrollo=(
            [float(f) for f in resultado.factores_desarrollo]
            if resultado.factores_desarrollo is not None
            else None
        ),
        percentiles=(
            {k: float(v) for k, v in resultado.percentiles.items()}
            if resultado.percentiles is not None
            else None
        ),
        detalles={
            k: (float(v) if isinstance(v, Decimal) else v) for k, v in resultado.detalles.items()
        },
        calculation_metadata=resultado.calculation_metadata,
    )


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/chain-ladder", response_model=ReserveResponse)
def calculate_chain_ladder(req: ChainLadderRequest) -> ReserveResponse:
    """Calculate reserves using the Chain Ladder method.

    Accepts a cumulative development triangle and returns projected
    ultimates, IBNR reserves per origin year, and development factors.
    """
    try:
        triangulo = _build_triangle(req.triangle, req.origin_years)
        config = ConfiguracionChainLadder(
            metodo_promedio=MetodoPromedio(req.metodo_promedio),
            calcular_tail_factor=req.calcular_tail_factor,
            tail_factor=Decimal(str(req.tail_factor)) if req.tail_factor is not None else None,
            permitir_desarrollo_negativo=req.permitir_desarrollo_negativo,
        )
        cl = ChainLadder(config)
        resultado = cl.calcular(triangulo, TipoTriangulo(req.tipo_triangulo))
        return _resultado_to_response(resultado)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/bornhuetter-ferguson", response_model=ReserveResponse)
def calculate_bornhuetter_ferguson(req: BornhuetterFergusonRequest) -> ReserveResponse:
    """Calculate reserves using the Bornhuetter-Ferguson method.

    Combines observed development (Chain Ladder factors) with an a-priori
    loss ratio estimate, providing more stable reserves for immature years.
    """
    try:
        triangulo = _build_triangle(req.triangle, req.origin_years)
        config = ConfiguracionBornhuetterFerguson(
            loss_ratio_apriori=Decimal(str(req.loss_ratio_apriori)),
            metodo_promedio=MetodoPromedio(req.metodo_promedio),
            permitir_desarrollo_negativo=req.permitir_desarrollo_negativo,
        )
        primas = {k: Decimal(str(v)) for k, v in req.primas_por_anio.items()}
        bf = BornhuetterFerguson(config)
        resultado = bf.calcular(triangulo, primas, TipoTriangulo(req.tipo_triangulo))
        return _resultado_to_response(resultado)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/bootstrap", response_model=ReserveResponse)
def calculate_bootstrap(req: BootstrapRequest) -> ReserveResponse:
    """England-Verrall ODP bootstrap: predictive distribution of the reserve.

    Pearson residuals are computed on *incremental* claims against values fitted
    backwards from the ultimate, so the fitted diagonal reproduces the observed
    one and the fitted incrementals reproduce the observed row and column sums.
    The dispersion parameter `phi` is estimated with `n - p` degrees of freedom
    (`p = I + J - 1`), residuals carry England's (2002) degrees-of-freedom
    adjustment, and each future cell is simulated from a Gamma with variance
    `phi * mean` — so the spread covers both estimation and process error.

    `reserva_total` is the mean of the replicates and `detalles.error_prediccion`
    its standard deviation. `detalles.conciliacion_cl_relativa` reports the gap
    against the Chain Ladder reserve, which stays near 1%: the reserve is convex
    in the development factors, so re-sampling them lifts the mean (Jensen).

    The distribution is conditional on the model — stable development pattern and
    variance proportional to the mean. It does not cover model risk, mix change,
    unobserved inflation or tail-factor uncertainty, and it is not a regulatory
    capital measure.
    """
    try:
        triangulo = _build_triangle(req.triangle, req.origin_years)
        config = ConfiguracionBootstrap(
            num_simulaciones=req.num_simulaciones,
            seed=req.seed,
            percentiles=req.percentiles,
            permitir_desarrollo_negativo=req.permitir_desarrollo_negativo,
        )
        bs = Bootstrap(config)
        resultado = bs.calcular(triangulo, TipoTriangulo(req.tipo_triangulo))
        return _resultado_to_response(resultado)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
