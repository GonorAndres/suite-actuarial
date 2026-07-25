"""
Tests para rentas vitalicias (life annuities).

Verifica prima unica, reserva matematica, rentas diferidas,
periodo garantizado y tabla de pagos.
"""

from decimal import Decimal

import pytest

from suite_actuarial.actuarial.mortality.tablas import TablaMortalidad
from suite_actuarial.pensiones.conmutacion import TablaConmutacion
from suite_actuarial.pensiones.plan_retiro import PensionLey97
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
            edad=65,
            sexo="H",
            monto_mensual=Decimal("5000"),
            tabla_mortalidad=tabla_emssa09,
            tasa_interes=Decimal("0.055"),
        )
        rv2 = RentaVitalicia(
            edad=65,
            sexo="H",
            monto_mensual=Decimal("10000"),
            tabla_mortalidad=tabla_emssa09,
            tasa_interes=Decimal("0.055"),
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
            edad=60,
            sexo="H",
            monto_mensual=Decimal("10000"),
            tabla_mortalidad=tabla_emssa09,
            tasa_interes=Decimal("0.055"),
        )
        rv70 = RentaVitalicia(
            edad=70,
            sexo="H",
            monto_mensual=Decimal("10000"),
            tabla_mortalidad=tabla_emssa09,
            tasa_interes=Decimal("0.055"),
        )
        assert rv60.calcular_prima_unica() > rv70.calcular_prima_unica()

    def test_lower_interest_higher_premium(self, tabla_emssa09):
        """Lower interest rate = less discounting = higher premium."""
        rv_low = RentaVitalicia(
            edad=65,
            sexo="H",
            monto_mensual=Decimal("10000"),
            tabla_mortalidad=tabla_emssa09,
            tasa_interes=Decimal("0.03"),
        )
        rv_high = RentaVitalicia(
            edad=65,
            sexo="H",
            monto_mensual=Decimal("10000"),
            tabla_mortalidad=tabla_emssa09,
            tasa_interes=Decimal("0.07"),
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
            edad=55,
            sexo="H",
            monto_mensual=Decimal("10000"),
            tabla_mortalidad=tabla_emssa09,
            tasa_interes=Decimal("0.055"),
        )
        rv_def = RentaVitalicia(
            edad=55,
            sexo="H",
            monto_mensual=Decimal("10000"),
            tabla_mortalidad=tabla_emssa09,
            tasa_interes=Decimal("0.055"),
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
            edad=55,
            sexo="H",
            monto_mensual=Decimal("10000"),
            tabla_mortalidad=tabla_emssa09,
            tasa_interes=Decimal("0.055"),
            periodo_diferimiento=5,
        )
        rv10 = RentaVitalicia(
            edad=55,
            sexo="H",
            monto_mensual=Decimal("10000"),
            tabla_mortalidad=tabla_emssa09,
            tasa_interes=Decimal("0.055"),
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
            edad=65,
            sexo="H",
            monto_mensual=Decimal("10000"),
            tabla_mortalidad=tabla_emssa09,
            tasa_interes=Decimal("0.055"),
        )
        rv_gar = RentaVitalicia(
            edad=65,
            sexo="H",
            monto_mensual=Decimal("10000"),
            tabla_mortalidad=tabla_emssa09,
            tasa_interes=Decimal("0.055"),
            periodo_garantizado=10,
        )
        assert rv_gar.calcular_prima_unica() > rv_no_gar.calcular_prima_unica()

    def test_longer_guarantee_higher_premium(self, tabla_emssa09):
        """Longer guaranteed period = higher premium."""
        rv5 = RentaVitalicia(
            edad=65,
            sexo="H",
            monto_mensual=Decimal("10000"),
            tabla_mortalidad=tabla_emssa09,
            tasa_interes=Decimal("0.055"),
            periodo_garantizado=5,
        )
        rv15 = RentaVitalicia(
            edad=65,
            sexo="H",
            monto_mensual=Decimal("10000"),
            tabla_mortalidad=tabla_emssa09,
            tasa_interes=Decimal("0.055"),
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


# ======================================================================
# Tests: correccion 1/m (hallazgo A6 de docs/AUDIT.md)
# ======================================================================


class TestCorreccionFraccionamiento:
    """La renta es mensual, así que se valúa con `a_x^(12)`, no con `a_x`.

    La versión anterior valuaba pagos mensuales con la anualidad anual, que
    supone todo el año cobrado el 1 de enero. El sesgo es unidireccional:
    sobreestima la prima única y subestima la pensión que un saldo compra.
    """

    def test_el_ajuste_es_exactamente_once_veinticuatroavos(self, tabla_emssa09):
        """Para m = 12, `(m-1)/(2m) = 11/24`.

        Se contrasta contra la fracción exacta, no contra un decimal
        redondeado: el ajuste es un número cerrado, no una calibración.
        """
        tc = TablaConmutacion(tabla_emssa09, sexo="H", tasa_interes=Decimal("0.055"))

        assert tc.ajuste_fraccionamiento(12) == Decimal("11") / Decimal("24")
        assert tc.ajuste_fraccionamiento(1) == Decimal("0")
        assert tc.ajuste_fraccionamiento(2) == Decimal("1") / Decimal("4")

    def test_pago_anual_no_lleva_ajuste(self, tabla_emssa09):
        """Con m = 1 la anualidad fraccionada es la anual: no hay qué corregir."""
        tc = TablaConmutacion(tabla_emssa09, sexo="H", tasa_interes=Decimal("0.055"))

        assert tc.ax_m(65, m=1) == tc.ax(65)

    def test_el_factor_mensual_es_menor_que_el_anual(self, tabla_emssa09):
        """`a_x^(12) = a_x - 11/24`, y el sesgo ronda 4% a los 65 años.

        Es la magnitud que reporta el hallazgo A6: usar el factor anual para
        pagos mensuales desplaza el resultado ~3.9%.
        """
        tc = TablaConmutacion(tabla_emssa09, sexo="H", tasa_interes=Decimal("0.055"))
        anual = float(tc.ax(65))
        mensual = float(tc.ax_m(65, m=12))

        assert anual - mensual == pytest.approx(11 / 24, rel=1e-9)
        assert (anual / mensual - 1) == pytest.approx(0.04, abs=0.01)

    def test_la_prima_unica_baja_al_corregir(self, renta_inmediata, tabla_emssa09):
        """La prima correcta es menor que la que daba el factor anual.

        El contraste se construye aquí con el factor anual, que es la ruta
        defectuosa, para fijar la dirección del sesgo.
        """
        tc = TablaConmutacion(tabla_emssa09, sexo="H", tasa_interes=Decimal("0.055"))
        prima_correcta = renta_inmediata.calcular_prima_unica()
        prima_defectuosa = renta_inmediata.monto_anual * tc.ax(65)

        assert prima_correcta < prima_defectuosa
        assert float(prima_defectuosa / prima_correcta - 1) == pytest.approx(0.04, abs=0.01)

    def test_reserva_en_cero_iguala_la_prima_unica(
        self, renta_inmediata, renta_diferida, renta_garantizada
    ):
        """Identidad obligatoria en las tres modalidades.

        La reserva al momento de comprar es, por definición, el valor de los
        pagos futuros: la prima única. La corrección 1/m se aplicó primero solo
        a la prima y esta identidad se rompió, lo que reveló que prima y
        reserva tenían definiciones duplicadas del factor. Ahora comparten una.
        """
        for renta in (renta_inmediata, renta_diferida, renta_garantizada):
            reserva = renta.calcular_reserva_matematica(0)
            prima = renta.calcular_prima_unica()
            assert float(reserva) == pytest.approx(float(prima), rel=1e-12)

    def test_la_renta_diferida_es_la_inmediata_descontada(self, renta_diferida, tabla_emssa09):
        """`10|a_55 = a_65 * 10E_55`, con la corrección en ambos lados.

        Ruta independiente: la diferida se construye a partir de la inmediata a
        la edad de inicio, descontada por supervivencia. Si la corrección se
        aplicara en un solo tramo, la identidad fallaría.
        """
        tc = TablaConmutacion(tabla_emssa09, sexo="H", tasa_interes=Decimal("0.055"))
        inmediata_a_65 = tc.ax_m(65, m=12)
        esperado = inmediata_a_65 * tc.nEx(55, 10)

        assert float(renta_diferida.calcular_factor_renta()) == pytest.approx(
            float(esperado), rel=1e-12
        )

    def test_la_garantia_vale_mas_que_la_vitalicia_pura(self, renta_garantizada, renta_inmediata):
        """Garantizar 10 años solo puede agregar valor a la misma edad."""
        assert renta_garantizada.calcular_factor_renta() > renta_inmediata.calcular_factor_renta()

    def test_la_pension_que_compra_un_saldo_sube_al_corregir(self, tabla_emssa09):
        """Con el factor correcto, el mismo saldo compra una pensión mayor.

        Es la otra cara del mismo sesgo: la prima baja y la pensión sube. Se
        verifica sobre la Ley 97, que es donde el saldo AFORE se convierte en
        pensión mensual.
        """
        pension = PensionLey97(
            saldo_afore=Decimal("1_500_000"),
            edad=65,
            sexo="H",
            semanas_cotizadas=1500,
            tabla_mortalidad=tabla_emssa09,
        )
        tc = pension._get_tabla_conmutacion()

        correcta = pension.calcular_renta_vitalicia()
        defectuosa = pension.saldo_afore / tc.ax(65) / Decimal("12")

        assert correcta > defectuosa
        assert float(correcta / defectuosa - 1) == pytest.approx(0.04, abs=0.015)
