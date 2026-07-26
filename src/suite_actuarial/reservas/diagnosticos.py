"""Diagnosticos reproducibles para reservas de siniestros.

Dos medidas distintas conviven aqui, y conviene no confundirlas:

- `banda_dispersion_link_ratios`: dispersion cruda de las razones age-to-age,
  agrupando todos los periodos. Es una senal de estabilidad del triangulo, no un
  error de prediccion.
- `mack.calcular_mack`: error de prediccion del Chain Ladder segun Mack (1993),
  con `sigma_k` por periodo y MSEP por ano de origen. Es la medida de
  incertidumbre que este modulo expone en `validar_reserva`.
"""

import warnings
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

import pandas as pd

from suite_actuarial.core.warnings import ExperimentalModelWarning
from suite_actuarial.reservas.mack import ResultadoMack, calcular_mack

DISCLAIMER_BANDA = (
    "AVISO: esta banda agrupa TODOS los link ratios de TODOS los periodos de "
    "desarrollo en una sola desviacion estandar. No es el error estandar de Mack "
    "(1993): no estima sigma_k por periodo, no calcula el MSEP por ano de origen "
    "ni el termino de correlacion entre anos. Es una medida cruda de dispersion "
    "de razones age-to-age, util como senal, no como error de prediccion."
)

DISCLAIMER_MACK = (
    "El error estandar de Mack (1993) mide el error de prediccion CONDICIONADO al "
    "metodo Chain Ladder: varianza de proceso mas varianza de estimacion de los "
    "factores. No cubre riesgo de modelo, cambio de mezcla, inflacion no "
    "observada ni la incertidumbre de un factor de cola. El rango reportado es "
    "reserva +/- z*SE; Mack no supone normalidad, asi que es una escala de "
    "magnitud, no una cobertura exacta."
)


@dataclass(frozen=True)
class BandaDispersion:
    """Dispersion cruda de los link ratios de un triangulo.

    No es una estimacion de error de prediccion. `standard_error` es la
    desviacion estandar muestral de todas las razones age-to-age agrupadas,
    escalada por la reserva; `reserve_range` es simplemente
    `reserva +/- z * standard_error`, no un intervalo con cobertura declarada.
    """

    standard_error: Decimal
    coefficient_of_variation: Decimal
    reserve_range: tuple[Decimal, Decimal]
    method: str = "dispersion-link-ratios"


#: Alias retrocompatible. Desde la fase 2 apunta al modelo de Mack real.
MackUncertainty = ResultadoMack


@dataclass(frozen=True)
class ReserveValidationReport:
    """Reporte de calidad, idoneidad y sensibilidad de una reserva."""

    data_quality_findings: list[str] = field(default_factory=list)
    method_suitability: str = "unknown"
    reserve_range: tuple[Decimal, Decimal] | None = None
    material_assumptions: list[str] = field(default_factory=list)
    diagnostics: dict[str, Any] = field(default_factory=dict)


def banda_dispersion_link_ratios(
    triangulo: pd.DataFrame,
    reserva: Decimal,
    *,
    confidence_z: Decimal = Decimal("1.96"),
) -> BandaDispersion:
    """Dispersion agrupada de las razones age-to-age del triangulo.

    Toma todas las razones `C[i, j+1] / C[i, j]` observadas, de todos los
    periodos de desarrollo, y calcula una sola desviacion estandar muestral.
    El resultado se escala por la reserva.

    Esto NO es Mack (1993). Mack estima una varianza `sigma_k^2` **por periodo
    de desarrollo** y compone el MSEP por ano de origen con un termino de
    correlacion entre anos. Agrupar los periodos mezcla la variabilidad
    *entre* periodos con la variabilidad *dentro* de cada periodo: sobre un
    triangulo perfectamente multiplicativo, donde cada `sigma_k` de Mack es
    exactamente cero, esta funcion devuelve un numero positivo grande.

    Args:
        triangulo: Triangulo acumulado
        reserva: Reserva a la que se escala la dispersion
        confidence_z: Multiplicador del rango reportado (no es una cobertura)

    Returns:
        BandaDispersion con la dispersion cruda y su rango

    Raises:
        ValueError: si el triangulo esta vacio o tiene menos de dos razones
    """
    warnings.warn(DISCLAIMER_BANDA, ExperimentalModelWarning, stacklevel=2)

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
        raise ValueError("No hay suficientes link-ratios para estimar dispersion")
    series = pd.Series(links)
    se = Decimal(str(float(series.std(ddof=1)))) * max(Decimal(str(reserva)), Decimal("0"))
    cv = (se / reserva) if reserva > 0 else Decimal("0")
    lower = max(Decimal("0"), Decimal(str(reserva)) - confidence_z * se)
    upper = Decimal(str(reserva)) + confidence_z * se
    return BandaDispersion(
        standard_error=se.quantize(Decimal("0.01")),
        coefficient_of_variation=cv.quantize(Decimal("0.0001")),
        reserve_range=(lower.quantize(Decimal("0.01")), upper.quantize(Decimal("0.01"))),
    )


def calcular_mack_uncertainty(
    triangulo: pd.DataFrame,
    reserva: Decimal | None = None,
    *,
    confidence_z: Decimal = Decimal("1.96"),
) -> ResultadoMack:
    """Deprecado: use `mack.calcular_mack`, que es donde vive el modelo.

    Se conserva la firma anterior por compatibilidad. El argumento `reserva` se
    ignora: Mack (1993) deriva su propia reserva a partir de los factores
    ponderados por volumen que el modelo exige, y su error estandar solo
    corresponde a esa reserva.

    Args:
        triangulo: Triangulo acumulado
        reserva: Ignorado (ver arriba); se mantiene por compatibilidad
        confidence_z: Multiplicador de `reserve_range`

    Returns:
        ResultadoMack con reserva, error estandar y detalle por ano de origen
    """
    warnings.warn(
        "calcular_mack_uncertainty esta deprecado: use mack.calcular_mack. El "
        "argumento 'reserva' se ignora porque Mack deriva la suya con factores "
        "ponderados por volumen.",
        DeprecationWarning,
        stacklevel=2,
    )
    return calcular_mack(triangulo, confidence_z=confidence_z)


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
    reserve_range: tuple[Decimal, Decimal] | None = None
    diagnostics: dict[str, Any] = {}

    # Medida principal de incertidumbre: error de prediccion de Mack (1993).
    # Se centra en la reserva del Chain Ladder ponderado por volumen, que es la
    # que el modelo exige; si el metodo del llamador usa otra, la diferencia
    # queda visible en `mack_reserva`.
    try:
        resultado_mack = calcular_mack(triangulo)
        reserve_range = resultado_mack.reserve_range
        diagnostics.update(
            {
                "mack_reserva": str(resultado_mack.reserva_total),
                "mack_standard_error": str(resultado_mack.standard_error),
                "mack_cv": str(resultado_mack.coefficient_of_variation),
                "mack_metodo": resultado_mack.method,
                "mack_limite": DISCLAIMER_MACK,
            }
        )
        if resultado_mack.reserva_total != reserva:
            diagnostics["mack_diferencia_vs_metodo"] = str(resultado_mack.reserva_total - reserva)
    except ValueError as exc:
        diagnostics["mack_warning"] = str(exc)
        findings.append(str(exc))

    # Senal secundaria: dispersion cruda de los link ratios.
    try:
        banda = banda_dispersion_link_ratios(triangulo, reserva)
        diagnostics.update(
            {
                "dispersion_standard_error": str(banda.standard_error),
                "dispersion_cv": str(banda.coefficient_of_variation),
                "dispersion_metodo": banda.method,
                "dispersion_limite": DISCLAIMER_BANDA,
            }
        )
    except ValueError as exc:
        diagnostics["dispersion_warning"] = str(exc)
        findings.append(str(exc))
    suitability = "suitable_with_review" if not findings else "requires_review"
    return ReserveValidationReport(findings, suitability, reserve_range, assumptions, diagnostics)
