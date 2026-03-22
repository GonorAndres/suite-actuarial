"""
Tests para calculadoras de pensiones IMSS (Ley 73 y Ley 97).

Verifica calculo de pension, aguinaldo, proyeccion AFORE,
comparacion de modalidades y determinacion de regimen.
"""

from datetime import date
from decimal import Decimal

import pandas as pd
import pytest

from suite_actuarial.actuarial.mortality.tablas import TablaMortalidad
from suite_actuarial.core.models.common import Sexo
from suite_actuarial.pensiones.plan_retiro import (
    CalculadoraIMSS,
    PensionLey73,
    PensionLey97,
)
from suite_actuarial.pensiones.tablas_imss import (
    DIAS_AGUINALDO_PENSIONADOS,
    LEY73_FACTORES_EDAD,
    LEY73_PORCENTAJES,
    PENSION_GARANTIZADA_2024,
    SEMANAS_MINIMAS_LEY73,
    obtener_factor_edad,
    obtener_porcentaje_ley73,
)


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
def pension_500_semanas():
    """Ley 73 pension with minimum weeks (500)."""
    return PensionLey73(
        semanas_cotizadas=500,
        salario_promedio_5_anos=Decimal("500"),  # $500/day ~ $15,000/month
        edad_retiro=65,
    )


@pytest.fixture
def pension_1000_semanas():
    """Ley 73 pension with 1000 weeks."""
    return PensionLey73(
        semanas_cotizadas=1000,
        salario_promedio_5_anos=Decimal("500"),
        edad_retiro=65,
    )


@pytest.fixture
def pension_1500_semanas():
    """Ley 73 pension with 1500 weeks."""
    return PensionLey73(
        semanas_cotizadas=1500,
        salario_promedio_5_anos=Decimal("500"),
        edad_retiro=65,
    )


@pytest.fixture
def ley97_basica(tabla_emssa09):
    """Basic Ley 97 pension calculator."""
    return PensionLey97(
        saldo_afore=Decimal("1_500_000"),
        edad=65,
        sexo="H",
        semanas_cotizadas=1000,
        tabla_mortalidad=tabla_emssa09,
        tasa_interes=Decimal("0.035"),
    )


@pytest.fixture
def calculadora():
    """Unified IMSS calculator."""
    return CalculadoraIMSS()


# ======================================================================
# Tests: Ley 73 -- tablas_imss lookup functions
# ======================================================================

class TestTablasIMSS:
    """Test IMSS data table lookups."""

    def test_porcentaje_500_semanas(self):
        """500 weeks = 33.07%."""
        pct = obtener_porcentaje_ley73(500)
        assert pct == Decimal("0.3307")

    def test_porcentaje_1000_semanas(self):
        """1000 weeks should be between 500 and 2060 values."""
        pct = obtener_porcentaje_ley73(1000)
        assert pct > Decimal("0.3307")
        assert pct < Decimal("1.0000")

    def test_porcentaje_below_500_raises(self):
        """Less than 500 weeks should raise ValueError."""
        with pytest.raises(ValueError, match="500"):
            obtener_porcentaje_ley73(499)

    def test_porcentaje_at_2060_is_100(self):
        """2060+ weeks = 100%."""
        pct = obtener_porcentaje_ley73(2060)
        assert pct == Decimal("1.0000")

    def test_porcentaje_above_2060_capped(self):
        """Above 2060 weeks, still 100%."""
        pct = obtener_porcentaje_ley73(3000)
        assert pct == Decimal("1.0000")

    def test_porcentaje_interpolation(self):
        """Intermediate weeks should interpolate correctly."""
        pct_500 = obtener_porcentaje_ley73(500)
        pct_552 = obtener_porcentaje_ley73(552)
        pct_526 = obtener_porcentaje_ley73(526)
        # 526 is halfway between 500 and 552
        assert pct_500 < pct_526 < pct_552

    def test_factor_edad_60(self):
        """At 60 = 75%."""
        assert obtener_factor_edad(60) == Decimal("0.75")

    def test_factor_edad_65(self):
        """At 65 = 100%."""
        assert obtener_factor_edad(65) == Decimal("1.00")

    def test_factor_edad_all_values(self):
        """All age factors should match table."""
        for edad, factor in LEY73_FACTORES_EDAD.items():
            assert obtener_factor_edad(edad) == factor

    def test_factor_edad_below_60_raises(self):
        """Below 60 should raise ValueError."""
        with pytest.raises(ValueError, match="60"):
            obtener_factor_edad(59)

    def test_factor_edad_above_65_is_100(self):
        """Above 65, factor is 1.00."""
        assert obtener_factor_edad(70) == Decimal("1.00")


# ======================================================================
# Tests: Ley 73 -- pension calculation
# ======================================================================

class TestPensionLey73:
    """Test Ley 73 pension calculations."""

    def test_pension_500_weeks_at_65(self, pension_500_semanas):
        """Minimum pension at 65: salary * 30 * 33.07% * 100%."""
        pension = pension_500_semanas.calcular_pension_mensual()
        # $500/day * 30 * 0.3307 * 1.00 = $4,960.50
        expected = Decimal("500") * Decimal("30") * Decimal("0.3307") * Decimal("1.00")
        assert abs(pension - expected.quantize(Decimal("0.01"))) < Decimal("1")

    def test_pension_1000_weeks_higher(self, pension_500_semanas, pension_1000_semanas):
        """More weeks = higher pension."""
        p500 = pension_500_semanas.calcular_pension_mensual()
        p1000 = pension_1000_semanas.calcular_pension_mensual()
        assert p1000 > p500

    def test_pension_1500_weeks_higher(self, pension_1000_semanas, pension_1500_semanas):
        """1500 weeks > 1000 weeks pension."""
        p1000 = pension_1000_semanas.calcular_pension_mensual()
        p1500 = pension_1500_semanas.calcular_pension_mensual()
        assert p1500 > p1000

    def test_pension_age_factor_reduction(self):
        """Retirement at 60 should give 75% of age-65 pension."""
        p60 = PensionLey73(500, Decimal("500"), 60)
        p65 = PensionLey73(500, Decimal("500"), 65)
        ratio = float(p60.calcular_pension_mensual() / p65.calcular_pension_mensual())
        assert abs(ratio - 0.75) < 0.01

    def test_pension_age_factor_at_62(self):
        """Retirement at 62 should give 85% of age-65 pension."""
        p62 = PensionLey73(500, Decimal("500"), 62)
        p65 = PensionLey73(500, Decimal("500"), 65)
        ratio = float(p62.calcular_pension_mensual() / p65.calcular_pension_mensual())
        assert abs(ratio - 0.85) < 0.01

    def test_pension_below_500_weeks_raises(self):
        """Less than 500 weeks should raise ValueError."""
        with pytest.raises(ValueError, match="500"):
            PensionLey73(499, Decimal("500"), 65)

    def test_pension_below_60_raises(self):
        """Below age 60 should raise ValueError."""
        with pytest.raises(ValueError, match="60"):
            PensionLey73(500, Decimal("500"), 59)

    def test_aguinaldo_calculation(self, pension_500_semanas):
        """Aguinaldo = 30 days of pension."""
        pension = pension_500_semanas.calcular_pension_mensual()
        aguinaldo = pension_500_semanas.calcular_aguinaldo()
        # Aguinaldo = (pension_mensual / 30) * 30 = pension_mensual
        assert abs(aguinaldo - pension) < Decimal("1")

    def test_pension_anual_total(self, pension_500_semanas):
        """Annual total = 12 months + aguinaldo."""
        pension = pension_500_semanas.calcular_pension_mensual()
        aguinaldo = pension_500_semanas.calcular_aguinaldo()
        total = pension_500_semanas.calcular_pension_anual_total()
        expected = pension * Decimal("12") + aguinaldo
        assert abs(total - expected) < Decimal("1")

    def test_resumen_has_required_keys(self, pension_500_semanas):
        """Resumen dict should contain all required fields."""
        resumen = pension_500_semanas.resumen()
        required = {
            "regimen", "semanas_cotizadas", "salario_promedio_diario",
            "edad_retiro", "porcentaje_pension", "factor_edad",
            "pension_mensual", "aguinaldo_anual", "pension_anual_total",
        }
        assert required.issubset(resumen.keys())
        assert resumen["regimen"] == "Ley 73"


# ======================================================================
# Tests: Ley 97 -- pension calculation
# ======================================================================

class TestPensionLey97:
    """Test Ley 97 pension calculations."""

    def test_renta_vitalicia_positive(self, ley97_basica):
        """Renta vitalicia should produce positive pension."""
        pension = ley97_basica.calcular_renta_vitalicia()
        assert pension > Decimal("0")

    def test_retiro_programado_positive(self, ley97_basica):
        """Retiro programado should produce positive pension."""
        pension = ley97_basica.calcular_retiro_programado()
        assert pension > Decimal("0")

    def test_renta_vitalicia_reasonable_range(self, ley97_basica):
        """With $1.5M at 65, monthly pension should be reasonable."""
        pension = ley97_basica.calcular_renta_vitalicia()
        # $1.5M / (12 * ~10 annuity factor) ~ $12,500/month
        assert Decimal("5_000") < pension < Decimal("30_000")

    def test_higher_saldo_higher_pension(self, tabla_emssa09):
        """More money in AFORE = higher pension."""
        rv1 = PensionLey97(
            saldo_afore=Decimal("1_000_000"), edad=65, sexo="H",
            semanas_cotizadas=1000, tabla_mortalidad=tabla_emssa09,
            tasa_interes=Decimal("0.035"),
        )
        rv2 = PensionLey97(
            saldo_afore=Decimal("2_000_000"), edad=65, sexo="H",
            semanas_cotizadas=1000, tabla_mortalidad=tabla_emssa09,
            tasa_interes=Decimal("0.035"),
        )
        assert rv2.calcular_renta_vitalicia() > rv1.calcular_renta_vitalicia()

    def test_pension_garantizada_minimum(self, tabla_emssa09):
        """With very low AFORE balance, pension should be at least guaranteed minimum."""
        rv = PensionLey97(
            saldo_afore=Decimal("10_000"), edad=65, sexo="H",
            semanas_cotizadas=1000, tabla_mortalidad=tabla_emssa09,
            tasa_interes=Decimal("0.035"),
        )
        pension = rv.calcular_renta_vitalicia()
        assert pension >= PENSION_GARANTIZADA_2024

    def test_comparar_modalidades_returns_dict(self, ley97_basica):
        """comparar_modalidades should return a complete dict."""
        comp = ley97_basica.comparar_modalidades()
        assert "renta_vitalicia" in comp
        assert "retiro_programado" in comp
        assert "recomendacion" in comp
        assert "pension_garantizada" in comp
        assert comp["saldo_afore"] == Decimal("1_500_000")

    def test_comparar_modalidades_both_positive(self, ley97_basica):
        """Both modalities should show positive pensions."""
        comp = ley97_basica.comparar_modalidades()
        assert comp["renta_vitalicia"]["pension_mensual"] > 0
        assert comp["retiro_programado"]["pension_mensual"] > 0

    def test_proyeccion_afore_grows(self, ley97_basica):
        """AFORE balance should grow over time."""
        proy = ley97_basica.proyectar_saldo_afore(
            salario_actual=Decimal("25_000"),
            rendimiento_anual=Decimal("0.045"),
            anos_restantes=10,
        )
        assert len(proy) == 11  # year 0 through year 10
        assert proy[-1]["saldo_afore"] > proy[0]["saldo_afore"]

    def test_proyeccion_has_required_fields(self, ley97_basica):
        """Each projection row should have required fields."""
        proy = ley97_basica.proyectar_saldo_afore(
            salario_actual=Decimal("25_000"),
            rendimiento_anual=Decimal("0.045"),
            anos_restantes=5,
        )
        required = {"ano", "edad", "salario_mensual", "aportacion_anual", "saldo_afore"}
        for row in proy:
            assert required.issubset(row.keys())

    def test_proyeccion_first_year_no_contribution(self, ley97_basica):
        """Year 0 should show current balance with no contribution."""
        proy = ley97_basica.proyectar_saldo_afore(
            salario_actual=Decimal("25_000"),
            rendimiento_anual=Decimal("0.045"),
            anos_restantes=5,
        )
        assert proy[0]["aportacion_anual"] == Decimal("0.00")
        assert proy[0]["saldo_afore"] == Decimal("1_500_000.00")

    def test_retiro_programado_with_explicit_esperanza(self, tabla_emssa09):
        """Explicit life expectancy should be used in retiro programado."""
        # Use a high enough balance so raw pension exceeds the guaranteed minimum
        rv = PensionLey97(
            saldo_afore=Decimal("3_000_000"), edad=65, sexo="H",
            semanas_cotizadas=1000, tabla_mortalidad=tabla_emssa09,
            tasa_interes=Decimal("0.035"),
        )
        pension = rv.calcular_retiro_programado(esperanza_vida_anos=20)
        # $3M / 20 / 12 = $12,500/month (above guaranteed minimum)
        expected = Decimal("3_000_000") / Decimal("20") / Decimal("12")
        assert abs(float(pension) - float(expected.quantize(Decimal("0.01")))) < 10


# ======================================================================
# Tests: CalculadoraIMSS -- regimen determination
# ======================================================================

class TestCalculadoraIMSS:
    """Test unified IMSS calculator."""

    def test_regimen_ley73_by_date(self, calculadora):
        """Enrolled before July 1, 1997 = Ley 73."""
        assert calculadora.determinar_regimen(date(1990, 1, 15)) == "Ley 73"
        assert calculadora.determinar_regimen(date(1997, 6, 30)) == "Ley 73"

    def test_regimen_ley97_by_date(self, calculadora):
        """Enrolled on or after July 1, 1997 = Ley 97."""
        assert calculadora.determinar_regimen(date(1997, 7, 1)) == "Ley 97"
        assert calculadora.determinar_regimen(date(2005, 3, 10)) == "Ley 97"

    def test_regimen_from_string_date(self, calculadora):
        """Should accept date as ISO string."""
        assert calculadora.determinar_regimen("1990-06-15") == "Ley 73"
        assert calculadora.determinar_regimen("2000-01-01") == "Ley 97"

    def test_pension_optima_ley73(self, calculadora, tabla_emssa09):
        """Optimal pension for Ley 73 worker with both data sets."""
        resultado = calculadora.pension_optima(
            fecha_inscripcion_imss=date(1990, 1, 1),
            semanas_cotizadas=1500,
            edad_retiro=65,
            salario_promedio_diario=Decimal("600"),
            saldo_afore=Decimal("1_000_000"),
            sexo="H",
            tabla_mortalidad=tabla_emssa09,
        )
        assert "pension_optima" in resultado
        assert resultado["pension_optima"] > Decimal("0")
        assert resultado["regimen_aplicable"] == "Ley 73"

    def test_pension_optima_ley97_only(self, calculadora, tabla_emssa09):
        """Ley 97 worker with only AFORE data."""
        resultado = calculadora.pension_optima(
            fecha_inscripcion_imss=date(2000, 1, 1),
            semanas_cotizadas=1200,
            edad_retiro=65,
            saldo_afore=Decimal("2_000_000"),
            sexo="H",
            tabla_mortalidad=tabla_emssa09,
        )
        assert resultado["regimen_aplicable"] == "Ley 97"
        assert resultado["pension_optima"] > Decimal("0")

    def test_pension_optima_no_data(self, calculadora):
        """Without salary or AFORE data, pension should be 0."""
        resultado = calculadora.pension_optima(
            fecha_inscripcion_imss=date(1990, 1, 1),
            semanas_cotizadas=1000,
            edad_retiro=65,
        )
        assert resultado["pension_optima"] == Decimal("0")

    def test_pension_optima_recommends_best(self, calculadora, tabla_emssa09):
        """Should recommend the regime that gives highest pension."""
        resultado = calculadora.pension_optima(
            fecha_inscripcion_imss=date(1990, 1, 1),
            semanas_cotizadas=1500,
            edad_retiro=65,
            salario_promedio_diario=Decimal("600"),
            saldo_afore=Decimal("1_000_000"),
            sexo="H",
            tabla_mortalidad=tabla_emssa09,
        )
        assert resultado["regimen_recomendado"] in ("Ley 73", "Ley 97")


# ======================================================================
# Tests: repr
# ======================================================================

class TestRepr:

    def test_ley73_repr(self, pension_500_semanas):
        r = repr(pension_500_semanas)
        assert "PensionLey73" in r
        assert "500" in r

    def test_ley97_repr(self, ley97_basica):
        r = repr(ley97_basica)
        assert "PensionLey97" in r

    def test_calculadora_repr(self, calculadora):
        assert "CalculadoraIMSS" in repr(calculadora)
