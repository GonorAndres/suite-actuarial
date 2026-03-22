"""
Reinsurance router -- quota share, excess of loss, and stop loss endpoints.

Thin wrappers around the library's reinsurance contract classes.
"""

from datetime import date
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from suite_actuarial.core.validators import (
    ExcessOfLossConfig,
    ModalidadXL,
    QuotaShareConfig,
    Siniestro,
    StopLossConfig,
    TipoContrato,
    TipoSiniestro,
)
from suite_actuarial.reaseguro.excess_of_loss import ExcessOfLoss
from suite_actuarial.reaseguro.quota_share import QuotaShare
from suite_actuarial.reaseguro.stop_loss import StopLoss

router = APIRouter(prefix="/reinsurance", tags=["reinsurance"])


# ── Request / Response models ────────────────────────────────────────────────


class SiniestroIn(BaseModel):
    """A single claim for reinsurance processing."""

    id_siniestro: str = Field(..., min_length=1, max_length=100)
    fecha_ocurrencia: date
    monto_bruto: float = Field(..., gt=0)
    tipo: str = Field(default="individual", description="individual or evento_catastrofico")
    id_poliza: str | None = None
    descripcion: str | None = None


class QuotaShareRequest(BaseModel):
    """Request body for quota share calculation."""

    porcentaje_cesion: float = Field(..., gt=0, le=100)
    comision_reaseguro: float = Field(..., ge=0, le=50)
    comision_override: float = Field(default=0.0, ge=0, le=10)
    vigencia_inicio: date
    vigencia_fin: date
    moneda: str = Field(default="MXN")
    prima_bruta: float = Field(..., gt=0)
    siniestros: list[SiniestroIn]


class ExcessOfLossRequest(BaseModel):
    """Request body for excess of loss calculation."""

    retencion: float = Field(..., gt=0)
    limite: float = Field(..., gt=0)
    modalidad: str = Field(default="por_riesgo", description="por_riesgo or por_evento")
    numero_reinstatements: int = Field(default=0, ge=0, le=3)
    tasa_prima: float = Field(..., gt=0, le=100)
    vigencia_inicio: date
    vigencia_fin: date
    moneda: str = Field(default="MXN")
    prima_reaseguro_cobrada: float = Field(..., gt=0)
    siniestros: list[SiniestroIn]


class StopLossRequest(BaseModel):
    """Request body for stop loss calculation."""

    attachment_point: float = Field(..., gt=0, le=200)
    limite_cobertura: float = Field(..., gt=0, le=100)
    primas_sujetas: float = Field(..., gt=0)
    vigencia_inicio: date
    vigencia_fin: date
    moneda: str = Field(default="MXN")
    primas_totales: float = Field(..., gt=0)
    prima_reaseguro_cobrada: float | None = Field(default=None)
    siniestros: list[SiniestroIn]


class ReinsuranceResponse(BaseModel):
    """Unified reinsurance calculation response."""

    tipo_contrato: str
    monto_cedido: float
    monto_retenido: float
    recuperacion_reaseguro: float
    comision_recibida: float
    prima_reaseguro_pagada: float
    ratio_cesion: float
    resultado_neto_cedente: float
    detalles: dict[str, Any]


# ── Helpers ──────────────────────────────────────────────────────────────────


def _to_siniestro(s: SiniestroIn) -> Siniestro:
    return Siniestro(
        id_siniestro=s.id_siniestro,
        fecha_ocurrencia=s.fecha_ocurrencia,
        monto_bruto=Decimal(str(s.monto_bruto)),
        tipo=TipoSiniestro(s.tipo),
        id_poliza=s.id_poliza,
        descripcion=s.descripcion,
    )


def _resultado_to_response(resultado) -> ReinsuranceResponse:
    def _convert(val):
        if isinstance(val, Decimal):
            return float(val)
        if isinstance(val, dict):
            return {k: _convert(v) for k, v in val.items()}
        if isinstance(val, list):
            return [_convert(i) for i in val]
        return val

    return ReinsuranceResponse(
        tipo_contrato=resultado.tipo_contrato.value,
        monto_cedido=float(resultado.monto_cedido),
        monto_retenido=float(resultado.monto_retenido),
        recuperacion_reaseguro=float(resultado.recuperacion_reaseguro),
        comision_recibida=float(resultado.comision_recibida),
        prima_reaseguro_pagada=float(resultado.prima_reaseguro_pagada),
        ratio_cesion=float(resultado.ratio_cesion),
        resultado_neto_cedente=float(resultado.resultado_neto_cedente),
        detalles=_convert(resultado.detalles),
    )


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/quota-share", response_model=ReinsuranceResponse)
def calculate_quota_share(req: QuotaShareRequest):
    """Calculate quota share reinsurance results.

    Applies a proportional cession percentage to premiums and claims,
    returning retained amounts, recoveries, and commissions.
    """
    try:
        config = QuotaShareConfig(
            tipo_contrato=TipoContrato.QUOTA_SHARE,
            vigencia_inicio=req.vigencia_inicio,
            vigencia_fin=req.vigencia_fin,
            moneda=req.moneda,
            porcentaje_cesion=Decimal(str(req.porcentaje_cesion)),
            comision_reaseguro=Decimal(str(req.comision_reaseguro)),
            comision_override=Decimal(str(req.comision_override)),
        )
        contrato = QuotaShare(config)
        siniestros = [_to_siniestro(s) for s in req.siniestros]
        resultado = contrato.calcular_resultado_neto(
            prima_bruta=Decimal(str(req.prima_bruta)),
            siniestros=siniestros,
        )
        return _resultado_to_response(resultado)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/excess-of-loss", response_model=ReinsuranceResponse)
def calculate_excess_of_loss(req: ExcessOfLossRequest):
    """Calculate excess of loss (XL) reinsurance results.

    The reinsurer pays when a claim exceeds the retention, up to the
    contract limit. Returns recoveries and net result for the ceding company.
    """
    try:
        config = ExcessOfLossConfig(
            tipo_contrato=TipoContrato.EXCESS_OF_LOSS,
            vigencia_inicio=req.vigencia_inicio,
            vigencia_fin=req.vigencia_fin,
            moneda=req.moneda,
            retencion=Decimal(str(req.retencion)),
            limite=Decimal(str(req.limite)),
            modalidad=ModalidadXL(req.modalidad),
            numero_reinstatements=req.numero_reinstatements,
            tasa_prima=Decimal(str(req.tasa_prima)),
        )
        contrato = ExcessOfLoss(config)
        siniestros = [_to_siniestro(s) for s in req.siniestros]
        resultado = contrato.calcular_resultado_neto(
            prima_reaseguro_cobrada=Decimal(str(req.prima_reaseguro_cobrada)),
            siniestros=siniestros,
        )
        return _resultado_to_response(resultado)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/stop-loss", response_model=ReinsuranceResponse)
def calculate_stop_loss(req: StopLossRequest):
    """Calculate stop loss reinsurance results.

    Protects when aggregate loss ratio exceeds the attachment point.
    Returns recovery and net result for the ceding company.
    """
    try:
        config = StopLossConfig(
            tipo_contrato=TipoContrato.STOP_LOSS,
            vigencia_inicio=req.vigencia_inicio,
            vigencia_fin=req.vigencia_fin,
            moneda=req.moneda,
            attachment_point=Decimal(str(req.attachment_point)),
            limite_cobertura=Decimal(str(req.limite_cobertura)),
            primas_sujetas=Decimal(str(req.primas_sujetas)),
        )
        contrato = StopLoss(config)
        siniestros = [_to_siniestro(s) for s in req.siniestros]

        prima_kwarg = {}
        if req.prima_reaseguro_cobrada is not None:
            prima_kwarg["prima_reaseguro_cobrada"] = Decimal(
                str(req.prima_reaseguro_cobrada)
            )

        resultado = contrato.calcular_resultado_neto(
            primas_totales=Decimal(str(req.primas_totales)),
            siniestros=siniestros,
            **prima_kwarg,
        )
        return _resultado_to_response(resultado)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
