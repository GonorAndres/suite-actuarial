"""
Reserves router -- Chain Ladder, Bornhuetter-Ferguson, and Bootstrap endpoints.

Accepts triangles as list-of-lists and origin years, converts them to
pandas DataFrames, then delegates to the library reserve calculators.
"""

from decimal import Decimal
from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from suite_actuarial.core.validators import (
    ConfiguracionBootstrap,
    ConfiguracionBornhuetterFerguson,
    ConfiguracionChainLadder,
    MetodoPromedio,
)
from suite_actuarial.reservas.bootstrap import Bootstrap
from suite_actuarial.reservas.bornhuetter_ferguson import BornhuetterFerguson
from suite_actuarial.reservas.chain_ladder import ChainLadder

router = APIRouter(prefix="/reserves", tags=["reserves"])


# ── Request / Response models ────────────────────────────────────────────────


class ChainLadderRequest(BaseModel):
    """Request body for Chain Ladder reserve calculation."""

    triangle: list[list[float | None]] = Field(
        ..., description="Cumulative triangle as list of rows (None for missing cells)"
    )
    origin_years: list[int] = Field(
        ..., description="Origin year labels (one per row)"
    )
    metodo_promedio: str = Field(
        default="simple", description="Averaging method: simple, weighted, geometric"
    )
    calcular_tail_factor: bool = Field(
        default=False, description="Whether to estimate a tail factor"
    )
    tail_factor: float | None = Field(
        default=None, ge=1.0, le=2.0, description="Manual tail factor (if not auto-calculated)"
    )


class BornhuetterFergusonRequest(BaseModel):
    """Request body for Bornhuetter-Ferguson reserve calculation."""

    triangle: list[list[float | None]] = Field(...)
    origin_years: list[int] = Field(...)
    primas_por_anio: dict[int, float] = Field(
        ..., description="Earned premiums by origin year"
    )
    loss_ratio_apriori: float = Field(
        ..., gt=0, le=2.0, description="A-priori expected loss ratio (e.g. 0.65)"
    )
    metodo_promedio: str = Field(default="simple")


class BootstrapRequest(BaseModel):
    """Request body for Bootstrap reserve calculation."""

    triangle: list[list[float | None]] = Field(...)
    origin_years: list[int] = Field(...)
    num_simulaciones: int = Field(default=1000, ge=100, le=10000)
    seed: int | None = Field(default=None)
    percentiles: list[int] = Field(default=[50, 75, 90, 95, 99])


class ReserveResponse(BaseModel):
    """Unified reserve calculation response."""

    metodo: str
    reserva_total: float
    ultimate_total: float
    pagado_total: float
    reservas_por_anio: dict[int, float]
    ultimates_por_anio: dict[int, float]
    factores_desarrollo: list[float] | None = None
    percentiles: dict[int, float] | None = None
    detalles: dict[str, Any] = {}


# ── Helpers ──────────────────────────────────────────────────────────────────


def _build_triangle(rows: list[list[float | None]], years: list[int]) -> pd.DataFrame:
    """Convert list-of-lists + origin years into a pandas DataFrame."""
    if len(rows) != len(years):
        raise ValueError(
            f"Number of rows ({len(rows)}) must match number of origin years ({len(years)})"
        )
    n_cols = max(len(r) for r in rows)
    col_labels = list(range(1, n_cols + 1))
    df = pd.DataFrame(rows, index=years, columns=col_labels, dtype=float)
    return df


def _resultado_to_response(resultado) -> ReserveResponse:
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
            k: (float(v) if isinstance(v, Decimal) else v)
            for k, v in resultado.detalles.items()
        },
    )


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/chain-ladder", response_model=ReserveResponse)
def calculate_chain_ladder(req: ChainLadderRequest):
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
        )
        cl = ChainLadder(config)
        resultado = cl.calcular(triangulo)
        return _resultado_to_response(resultado)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/bornhuetter-ferguson", response_model=ReserveResponse)
def calculate_bornhuetter_ferguson(req: BornhuetterFergusonRequest):
    """Calculate reserves using the Bornhuetter-Ferguson method.

    Combines observed development (Chain Ladder factors) with an a-priori
    loss ratio estimate, providing more stable reserves for immature years.
    """
    try:
        triangulo = _build_triangle(req.triangle, req.origin_years)
        config = ConfiguracionBornhuetterFerguson(
            loss_ratio_apriori=Decimal(str(req.loss_ratio_apriori)),
            metodo_promedio=MetodoPromedio(req.metodo_promedio),
        )
        primas = {k: Decimal(str(v)) for k, v in req.primas_por_anio.items()}
        bf = BornhuetterFerguson(config)
        resultado = bf.calcular(triangulo, primas)
        return _resultado_to_response(resultado)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/bootstrap", response_model=ReserveResponse)
def calculate_bootstrap(req: BootstrapRequest):
    """Calculate reserves using the Bootstrap simulation method.

    Runs Monte Carlo simulations on re-sampled triangles to produce
    a full distribution of reserve estimates including percentiles.
    """
    try:
        triangulo = _build_triangle(req.triangle, req.origin_years)
        config = ConfiguracionBootstrap(
            num_simulaciones=req.num_simulaciones,
            seed=req.seed,
            percentiles=req.percentiles,
        )
        bs = Bootstrap(config)
        resultado = bs.calcular(triangulo)
        return _resultado_to_response(resultado)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
