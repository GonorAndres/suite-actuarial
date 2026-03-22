"""
Tests para rentas vitalicias (life annuities).

Verifica prima unica, reserva matematica, rentas diferidas,
periodo garantizado y tabla de pagos.
"""

from decimal import Decimal

import pandas as pd
import pytest

from suite_actuarial.actuarial.mortality.tablas import TablaMortalidad
from suite_actuarial.core.models.common import Sexo
from suite_actuarial.pensiones.conmutacion import TablaConmutacion
from suite_actuarial.pensiones.renta_vitalicia import RentaVitalicia


# ======================================================================
# Fixtures
# ======================================================================

@pytest.fixture
def tabla_emssa09():
    """Load EMSSA-09 table."""
    try:
        return TablaMortalidad.cargar_emssa09()
    except FileNotFoundError:
        pytest.skip("EMSSA-09 table not available")


@pytest.fixture
def renta_inmediata(tabla_emssa09):
    """Immediate annuity: male age 65, $10,000/month, 5.5%."""
    return RentaVitalicia(
        edad=65,
        sexo="H",
        monto_mensual=Decimal("10000"),
        tabla_mortalidad=tabla_emssa09,
        tasa_interes=Decimal("0.055"),
    )


@pytest.fixture
def renta_diferida(tabla_emssa09):
    """Deferred annuity: male age 55, deferred 10 years."""
    return RentaVitalicia(
        edad=55,
        sexo="H",
        monto_mensual=Decimal("10000"),
        tabla_mortalidad=tabla_emssa09,
        tasa_interes=Decimal("0.055"),
        periodo_diferimiento=10,
    )


@pytest.fixture
def renta_garantizada(tabla_emssa09):
    """Annuity with 10-year guaranteed period."""
    return RentaVitalicia(
        edad=65,
        sexo="H",
        monto_mensual=Decimal("10000"),
        tabla_mortalidad=tabla_emssa09,
        tasa_interes=Decimal("0.055"),
        periodo_garantizado=10,
    )


@pytest.fixture
def renta_mujer(tabla_emssa09):
    """Immediate annuity for a woman."""
    return RentaVitalicia(
        edad=65,
        sexo="M",
        monto_mensual=Decimal("10000"),
        tabla_mortalidad=tabla_emssa09,
        tasa_interes=Decimal("0.055"),
    )


# ======================================================================
# Tests: immediate annuity (prima unica)
# ======================================================================

class TestImmediateAnnuity:
    """Test immediate life annuity calculations."""

    def test_prima_unica_positive(self, renta_inmediata):
        """Single premium should be positive."""
        prima = renta_inmediata.calcular_prima_unica()
        assert prima > Decimal("0")

    def test_prima_unica_reasonable_range(self, renta_inmediata):
        """For $10k/month at 65, prima should be ~$1M-$2M range."""
        prima = renta_inmediata.calcular_prima_unica()
        # $120k/year * ~8-15 annuity factor
        assert Decimal("500_000") < prima < Decimal("3_000_000")

    def test_factor_renta_reasonable(self, renta_inmediata):
        """Annuity factor at 65 should be roughly 8-14."""
        factor = renta_inmediata.calcular_factor_renta()
        assert Decimal("5") < factor < Decimal("20")

    def test_prima_proportional_to_monto(self, tabla_emssa09):
        """Doubling monthly amount should double the premium."""
        rv1 = RentaVitalicia(
            edad=65, sexo="H", monto_mensual=Decimal("5000"),
            tabla_mortalidad=tabla_emssa09, tasa_interes=Decimal("0.055"),
        )
        rv2 = RentaVitalicia(
            edad=65, sexo="H", monto_mensual=Decimal("10000"),
            tabla_mortalidad=tabla_emssa09, tasa_interes=Decimal("0.055"),
        )
        prima1 = rv1.calcular_prima_unica()
        prima2 = rv2.calcular_prima_unica()
        ratio = float(prima2 / prima1)
        assert abs(ratio - 2.0) < 0.01

    def test_women_premium_higher(self, renta_inmediata, renta_mujer):
        """Women live longer so premium should be higher."""
        prima_h = renta_inmediata.calcular_prima_unica()
        prima_m = renta_mujer.calcular_prima_unica()
        assert prima_m > prima_h

    def test_older_age_lower_premium(self, tabla_emssa09):
        """Older person = fewer expected payments = lower premium."""
        rv60 = RentaVitalicia(
            edad=60, sexo="H", monto_mensual=Decimal("10000"),
            tabla_mortalidad=tabla_emssa09, tasa_interes=Decimal("0.055"),
        )
        rv70 = RentaVitalicia(
            edad=70, sexo="H", monto_mensual=Decimal("10000"),
            tabla_mortalidad=tabla_emssa09, tasa_interes=Decimal("0.055"),
        )
        assert rv60.calcular_prima_unica() > rv70.calcular_prima_unica()

    def test_lower_interest_higher_premium(self, tabla_emssa09):
        """Lower interest rate = less discounting = higher premium."""
        rv_low = RentaVitalicia(
            edad=65, sexo="H", monto_mensual=Decimal("10000"),
            tabla_mortalidad=tabla_emssa09, tasa_interes=Decimal("0.03"),
        )
        rv_high = RentaVitalicia(
            edad=65, sexo="H", monto_mensual=Decimal("10000"),
            tabla_mortalidad=tabla_emssa09, tasa_interes=Decimal("0.07"),
        )
        assert rv_low.calcular_prima_unica() > rv_high.calcular_prima_unica()


# ======================================================================
# Tests: deferred annuity
# ======================================================================

class TestDeferredAnnuity:
    """Test deferred annuity calculations."""

    def test_deferred_prima_less_than_immediate(self, tabla_emssa09):
        """Deferred annuity should cost less (probability of not reaching payment)."""
        rv_imm = RentaVitalicia(
            edad=55, sexo="H", monto_mensual=Decimal("10000"),
            tabla_mortalidad=tabla_emssa09, tasa_interes=Decimal("0.055"),
        )
        rv_def = RentaVitalicia(
            edad=55, sexo="H", monto_mensual=Decimal("10000"),
            tabla_mortalidad=tabla_emssa09, tasa_interes=Decimal("0.055"),
            periodo_diferimiento=10,
        )
        assert rv_def.calcular_prima_unica() < rv_imm.calcular_prima_unica()

    def test_deferred_factor_positive(self, renta_diferida):
        """Deferred factor should still be positive."""
        factor = renta_diferida.calcular_factor_renta()
        assert factor > Decimal("0")

    def test_longer_deferral_lower_premium(self, tabla_emssa09):
        """Longer deferral = lower premium."""
        rv5 = RentaVitalicia(
            edad=55, sexo="H", monto_mensual=Decimal("10000"),
            tabla_mortalidad=tabla_emssa09, tasa_interes=Decimal("0.055"),
            periodo_diferimiento=5,
        )
        rv10 = RentaVitalicia(
            edad=55, sexo="H", monto_mensual=Decimal("10000"),
            tabla_mortalidad=tabla_emssa09, tasa_interes=Decimal("0.055"),
            periodo_diferimiento=10,
        )
        assert rv10.calcular_prima_unica() < rv5.calcular_prima_unica()


# ======================================================================
# Tests: guaranteed period
# ======================================================================

class TestGuaranteedAnnuity:
    """Test annuity with guaranteed payment period."""

    def test_guaranteed_prima_higher(self, tabla_emssa09):
        """Guaranteed period should increase premium (more certain payments)."""
        rv_no_gar = RentaVitalicia(
            edad=65, sexo="H", monto_mensual=Decimal("10000"),
            tabla_mortalidad=tabla_emssa09, tasa_interes=Decimal("0.055"),
        )
        rv_gar = RentaVitalicia(
            edad=65, sexo="H", monto_mensual=Decimal("10000"),
            tabla_mortalidad=tabla_emssa09, tasa_interes=Decimal("0.055"),
            periodo_garantizado=10,
        )
        assert rv_gar.calcular_prima_unica() > rv_no_gar.calcular_prima_unica()

    def test_longer_guarantee_higher_premium(self, tabla_emssa09):
        """Longer guaranteed period = higher premium."""
        rv5 = RentaVitalicia(
            edad=65, sexo="H", monto_mensual=Decimal("10000"),
            tabla_mortalidad=tabla_emssa09, tasa_interes=Decimal("0.055"),
            periodo_garantizado=5,
        )
        rv15 = RentaVitalicia(
            edad=65, sexo="H", monto_mensual=Decimal("10000"),
            tabla_mortalidad=tabla_emssa09, tasa_interes=Decimal("0.055"),
            periodo_garantizado=15,
        )
        assert rv15.calcular_prima_unica() > rv5.calcular_prima_unica()

    def test_guaranteed_factor_positive(self, renta_garantizada):
        """Annuity factor with guarantee should be positive."""
        factor = renta_garantizada.calcular_factor_renta()
        assert factor > Decimal("0")


# ======================================================================
# Tests: reserva matematica
# ======================================================================

class TestReservaMatematica:
    """Test mathematical reserve calculations."""

    def test_reserva_at_zero_equals_prima(self, renta_inmediata):
        """At t=0, reserve should equal the single premium."""
        reserva = renta_inmediata.calcular_reserva_matematica(0)
        prima = renta_inmediata.calcular_prima_unica()
        # Should be the same since the full annuity is still ahead
        ratio = float(reserva / prima) if prima > 0 else 0
        assert abs(ratio - 1.0) < 0.01

    def test_reserva_decreases_over_time(self, renta_inmediata):
        """Reserve should generally decrease as the annuitant ages."""
        r0 = renta_inmediata.calcular_reserva_matematica(0)
        r5 = renta_inmediata.calcular_reserva_matematica(5)
        r10 = renta_inmediata.calcular_reserva_matematica(10)
        assert r0 > r5 > r10

    def test_reserva_positive(self, renta_inmediata):
        """Reserve should be non-negative."""
        for t in range(0, 20, 5):
            reserva = renta_inmediata.calcular_reserva_matematica(t)
            assert reserva >= Decimal("0"), f"Reserve at t={t} is {reserva}"

    def test_reserva_negative_time_raises(self, renta_inmediata):
        """Negative time should raise ValueError."""
        with pytest.raises(ValueError, match="negativo"):
            renta_inmediata.calcular_reserva_matematica(-1)

    def test_reserva_deferred_during_deferral(self, renta_diferida):
        """Reserve during deferral period should be positive (building up)."""
        reserva = renta_diferida.calcular_reserva_matematica(5)
        assert reserva > Decimal("0")


# ======================================================================
# Tests: tabla de pagos
# ======================================================================

class TestTablaPagos:
    """Test payment schedule generation."""

    def test_tabla_pagos_returns_list(self, renta_inmediata):
        """tabla_pagos should return a list of dicts."""
        pagos = renta_inmediata.tabla_pagos(anos=10)
        assert isinstance(pagos, list)
        assert len(pagos) > 0

    def test_tabla_pagos_has_required_keys(self, renta_inmediata):
        """Each row should have required fields."""
        pagos = renta_inmediata.tabla_pagos(anos=5)
        required = {"ano", "edad", "pago_anual", "prob_supervivencia", "pago_esperado"}
        for row in pagos:
            assert required.issubset(row.keys()), f"Missing keys in {row.keys()}"

    def test_tabla_pagos_immediate_has_payments(self, renta_inmediata):
        """Immediate annuity should have payments from year 0."""
        pagos = renta_inmediata.tabla_pagos(anos=5)
        assert pagos[0]["pago_anual"] == Decimal("120000")  # 10k * 12

    def test_tabla_pagos_deferred_no_payment_during_deferral(self, renta_diferida):
        """Deferred annuity should have $0 payments during deferral."""
        pagos = renta_diferida.tabla_pagos(anos=15)
        # First 10 years should have no payment
        for row in pagos[:10]:
            assert row["pago_anual"] == Decimal("0"), f"Payment at year {row['ano']}"
            assert row["en_diferimiento"] is True

    def test_tabla_pagos_survival_decreases(self, renta_inmediata):
        """Survival probability should decrease over time."""
        pagos = renta_inmediata.tabla_pagos(anos=20)
        for i in range(1, len(pagos)):
            assert pagos[i]["prob_supervivencia"] <= pagos[i - 1]["prob_supervivencia"]

    def test_tabla_pagos_guaranteed_certain(self, renta_garantizada):
        """During guaranteed period, pago_esperado should equal full payment."""
        pagos = renta_garantizada.tabla_pagos(anos=15)
        # First 10 years guaranteed
        for row in pagos[:10]:
            assert row["en_garantia"] is True
            assert row["pago_esperado"] == Decimal("120000")


# ======================================================================
# Tests: repr
# ======================================================================

class TestRentaRepr:

    def test_repr_immediate(self, renta_inmediata):
        r = repr(renta_inmediata)
        assert "RentaVitalicia" in r
        assert "inmediata" in r

    def test_repr_deferred(self, renta_diferida):
        r = repr(renta_diferida)
        assert "diferida" in r
