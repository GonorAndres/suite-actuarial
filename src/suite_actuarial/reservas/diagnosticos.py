"""Diagnosticos reproducibles para reservas de siniestros."""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class MackUncertainty:
    """Estimacion aproximada de error de proceso y parametro de Mack."""

    standard_error: Decimal
    coefficient_of_variation: Decimal
    reserve_range: tuple[Decimal, Decimal]
    method: str = "mack-approximation"


@dataclass(frozen=True)
class ReserveValidationReport:
    """Reporte de calidad, idoneidad y sensibilidad de una reserva."""

    data_quality_findings: list[str] = field(default_factory=list)
    method_suitability: str = "unknown"
    reserve_range: tuple[Decimal, Decimal] | None = None
    material_assumptions: list[str] = field(default_factory=list)
    diagnostics: dict[str, Any] = field(default_factory=dict)


def calcular_mack_uncertainty(
    triangulo: pd.DataFrame,
    reserva: Decimal,
    *,
    confidence_z: Decimal = Decimal("1.96"),
) -> MackUncertainty:
    """Calcula una banda Mack reproducible basada en residuales link-ratio.

    La implementacion es deliberadamente conservadora y reporta su metodo;
    no sustituye una revision actuarial independiente de supuestos Mack.
    """
    if triangulo.empty:
        raise ValueError("Se requiere un triangulo no vacio")
    links: list[float] = []
    for col in range(triangulo.shape[1] - 1):
        for row in range(triangulo.shape[0]):
            current = triangulo.iloc[row, col]
            nxt = triangulo.iloc[row, col + 1]
            if pd.notna(current) and pd.notna(nxt) and current > 0:
                links.append(float(nxt / current))
    if len(links) < 2:
        raise ValueError("No hay suficientes link-ratios para incertidumbre Mack")
    series = pd.Series(links)
    se = Decimal(str(float(series.std(ddof=1)))) * max(Decimal(str(reserva)), Decimal("0"))
    cv = (se / reserva) if reserva > 0 else Decimal("0")
    lower = max(Decimal("0"), Decimal(str(reserva)) - confidence_z * se)
    upper = Decimal(str(reserva)) + confidence_z * se
    return MackUncertainty(
        standard_error=se.quantize(Decimal("0.01")),
        coefficient_of_variation=cv.quantize(Decimal("0.0001")),
        reserve_range=(lower.quantize(Decimal("0.01")), upper.quantize(Decimal("0.01"))),
    )


def validar_reserva(
    triangulo: pd.DataFrame,
    reserva: Decimal,
    *,
    metodo: str,
    tail_factor: Decimal | None = None,
) -> ReserveValidationReport:
    """Genera hallazgos de calidad y disclosure de supuestos."""
    findings: list[str] = []
    if triangulo.isna().all(axis=1).any():
        findings.append("Hay anos de origen sin observaciones")
    if (triangulo.fillna(0) < 0).any().any():
        findings.append("Hay importes negativos en el triangulo")
    if triangulo.shape[0] < 3 or triangulo.shape[1] < 3:
        findings.append("Triangulo pequeno: interpretar con cautela")
    assumptions = [f"metodo={metodo}"]
    if tail_factor is not None:
        assumptions.append(f"tail_factor={tail_factor}")
    try:
        uncertainty = calcular_mack_uncertainty(triangulo, reserva)
        reserve_range = uncertainty.reserve_range
        diagnostics = {
            "mack_standard_error": str(uncertainty.standard_error),
            "mack_cv": str(uncertainty.coefficient_of_variation),
        }
    except ValueError as exc:
        reserve_range = None
        diagnostics = {"mack_warning": str(exc)}
        findings.append(str(exc))
    suitability = "suitable_with_review" if not findings else "requires_review"
    return ReserveValidationReport(findings, suitability, reserve_range, assumptions, diagnostics)
