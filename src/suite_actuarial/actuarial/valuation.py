"""Valuacion de flujos de vida con supuestos explicitamente trazables.

Este motor cubre matematicas de flujos de efectivo y no pretende replicar por
si solo una valuacion institucional CUSF. La mejor estimacion y el margen de
riesgo se devuelven por separado para evitar confundirlos con una reserva
pro-rata pedagogica.
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from suite_actuarial.actuarial.interest.tasas import CurvaRendimiento
from suite_actuarial.actuarial.mortality.tablas import TablaMortalidad
from suite_actuarial.core.models.common import CalculationMetadata, Sexo


@dataclass(frozen=True)
class AssumptionSet:
    """Conjunto inmutable de supuestos de valuacion."""

    valuation_date: date
    currency: str
    mortality_table: TablaMortalidad
    discount_curve: CurvaRendimiento
    lapse_assumptions: Decimal = Decimal("0")
    expenses: Decimal = Decimal("0")
    inflation: Decimal = Decimal("0")
    provenance: dict[str, Any] = field(default_factory=dict)
    validation_status: str = "user_supplied"
    assumption_id: str = ""

    def __post_init__(self) -> None:
        if self.lapse_assumptions < 0 or self.lapse_assumptions >= 1:
            raise ValueError("lapse_assumptions debe estar en [0, 1)")
        if self.expenses < 0:
            raise ValueError("expenses no puede ser negativo")
        if self.inflation < -1:
            raise ValueError("inflation invalida")
        if not self.assumption_id:
            payload = {
                "valuation_date": self.valuation_date.isoformat(),
                "currency": self.currency,
                "mortality": self.mortality_table.nombre,
                "mortality_metadata": self.mortality_table.metadata,
                "curve": {"plazos": self.discount_curve.plazos, "tasas": [str(x) for x in self.discount_curve.tasas]},
                "lapse": str(self.lapse_assumptions),
                "expenses": str(self.expenses),
                "inflation": str(self.inflation),
                "provenance": self.provenance,
            }
            digest = hashlib.sha256(
                json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
            ).hexdigest()[:16]
            object.__setattr__(self, "assumption_id", f"assump-{digest}")


@dataclass
class LifeValuationResult:
    """Resultado auditable de una valuacion individual."""

    best_estimate: Decimal
    risk_margin: Decimal
    total_liability: Decimal
    present_value_components: dict[str, Decimal]
    assumptions_snapshot: dict[str, Any]
    sensitivities: dict[str, Decimal]
    warnings: list[str]
    reconciliation_total: Decimal
    calculation_metadata: CalculationMetadata

    @property
    def reserva_total(self) -> Decimal:
        """Alias en español para integraciones existentes."""
        return self.total_liability


@dataclass
class PortfolioValuationResult:
    """Agregado de polizas que conserva el linaje de cada resultado."""

    best_estimate: Decimal
    risk_margin: Decimal
    total_liability: Decimal
    policy_results: list[LifeValuationResult]
    calculation_metadata: CalculationMetadata


class LifeCashFlowValuator:
    """Proyecta beneficios, primas, gastos y supervivencia mensualmente."""

    def __init__(self, assumptions: AssumptionSet, risk_margin_rate: Decimal = Decimal("0.06")):
        if risk_margin_rate < 0:
            raise ValueError("risk_margin_rate no puede ser negativo")
        self.assumptions = assumptions
        self.risk_margin_rate = Decimal(str(risk_margin_rate))

    def _monthly_qx(self, age: int, sex: Sexo | str) -> Decimal:
        qx = self.assumptions.mortality_table.obtener_qx(age, sex)
        # La potencia se evalua en float solo para la conversion mensual de qx;
        # los flujos y resultados permanecen en Decimal.
        return Decimal(str(1 - (1 - float(qx)) ** (1 / 12)))

    def valorar_poliza(
        self,
        *,
        age: int,
        sex: Sexo | str,
        sum_assured: Decimal,
        monthly_premium: Decimal = Decimal("0"),
        term_months: int,
        expense_rate: Decimal | None = None,
        risk_margin_rate: Decimal | None = None,
    ) -> LifeValuationResult:
        """Calcula el pasivo de una poliza con flujos mensuales."""
        if term_months <= 0 or age < 0:
            raise ValueError("term_months y age deben ser positivos/no negativos")
        sum_assured = Decimal(str(sum_assured))
        monthly_premium = Decimal(str(monthly_premium))
        if sum_assured < 0 or monthly_premium < 0:
            raise ValueError("sum_assured y monthly_premium no pueden ser negativos")
        expense_rate = self.assumptions.expenses if expense_rate is None else Decimal(str(expense_rate))
        margin_rate = self.risk_margin_rate if risk_margin_rate is None else Decimal(str(risk_margin_rate))

        survival = Decimal("1")
        pv_death = Decimal("0")
        pv_premiums = Decimal("0")
        pv_expenses = Decimal("0")
        for month in range(1, term_months + 1):
            q_month = self._monthly_qx(age + (month - 1) // 12, sex)
            death = survival * q_month * (Decimal("1") - self.assumptions.lapse_assumptions)
            t = Decimal(month) / Decimal("12")
            discount = self.assumptions.discount_curve.factor_descuento(float(t))
            pv_death += death * sum_assured * discount
            pv_premiums += survival * monthly_premium * discount
            pv_expenses += survival * monthly_premium * expense_rate * discount
            survival *= Decimal("1") - q_month
            survival *= Decimal("1") - self.assumptions.lapse_assumptions

        best_estimate = (pv_death + pv_expenses - pv_premiums).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        best_estimate = max(best_estimate, Decimal("0"))
        risk_margin = (best_estimate * margin_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total = best_estimate + risk_margin
        warnings: list[str] = []
        if self.assumptions.validation_status != "supported":
            warnings.append("Los supuestos no tienen validacion supported")
        metadata = CalculationMetadata(
            valuation_date=self.assumptions.valuation_date,
            assumption_id=self.assumptions.assumption_id,
            validation_tier="supported" if self.assumptions.validation_status == "supported" else "experimental",
            sources=[str(value) for value in self.assumptions.provenance.values()],
            warnings=warnings,
            reproducibility_id=self.assumptions.assumption_id,
            assumptions_snapshot={"mortality_table": self.assumptions.mortality_table.nombre, "term_months": term_months},
        )
        return LifeValuationResult(
            best_estimate=best_estimate,
            risk_margin=risk_margin,
            total_liability=total,
            present_value_components={"death_benefits": pv_death.quantize(Decimal("0.01")), "premiums": pv_premiums.quantize(Decimal("0.01")), "expenses": pv_expenses.quantize(Decimal("0.01"))},
            assumptions_snapshot={"assumption_id": self.assumptions.assumption_id, "valuation_date": self.assumptions.valuation_date.isoformat(), "currency": self.assumptions.currency},
            sensitivities={"risk_margin_rate": margin_rate},
            warnings=warnings,
            reconciliation_total=total,
            calculation_metadata=metadata,
        )

    def valorar_portafolio(self, polizas: list[dict[str, Any]]) -> PortfolioValuationResult:
        """Agrega polizas sin perder sus resultados individuales."""
        results = [self.valorar_poliza(**policy) for policy in polizas]
        best = sum((item.best_estimate for item in results), Decimal("0"))
        margin = sum((item.risk_margin for item in results), Decimal("0"))
        metadata = CalculationMetadata(
            valuation_date=self.assumptions.valuation_date,
            assumption_id=self.assumptions.assumption_id,
            validation_tier="supported" if self.assumptions.validation_status == "supported" else "experimental",
            reproducibility_id=self.assumptions.assumption_id,
            assumptions_snapshot={"policies": len(results)},
        )
        return PortfolioValuationResult(best, margin, best + margin, results, metadata)

    calcular_best_estimate = valorar_poliza
