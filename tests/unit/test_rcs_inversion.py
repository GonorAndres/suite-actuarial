"""
Tests para RCS Inversion (mercado, credito, concentracion).

Valida calculo del Requerimiento de Capital de Solvencia para riesgos
de inversion conforme a shocks de mercado, riesgo de credito por
calificacion y riesgo de concentracion.
"""

import math
from decimal import Decimal

import pytest

from suite_actuarial.core.validators import ConfiguracionRCSInversion
from suite_actuarial.regulatorio.rcs_inversion import RCSInversion


# ------------------------------------------------------------------
# Helpers / local fixtures
# ------------------------------------------------------------------


@pytest.fixture
def rcs_inversion(config_rcs_inversion):
    """RCSInversion instance from the conftest fixture."""
    return RCSInversion(config_rcs_inversion)


@pytest.fixture
def config_only_equities():
    """Portfolio with only equities (no bonds, no real estate)."""
    return ConfiguracionRCSInversion(
        valor_acciones=Decimal("50000000"),
        valor_bonos_gubernamentales=Decimal("0"),
        valor_bonos_corporativos=Decimal("0"),
        valor_inmuebles=Decimal("0"),
    )


@pytest.fixture
def config_only_bonds():
    """Portfolio with only bonds (no equities, no real estate)."""
    return ConfiguracionRCSInversion(
        valor_acciones=Decimal("0"),
        valor_bonos_gubernamentales=Decimal("30000000"),
        valor_bonos_corporativos=Decimal("15000000"),
        valor_inmuebles=Decimal("0"),
        duracion_promedio_bonos=Decimal("7"),
        calificacion_promedio_bonos="A",
    )


# ==================================================================
# 1. RCS mercado positive for nonzero portfolio
# ==================================================================


class TestRCSMercado:

    def test_rcs_mercado_acciones_positive(self, rcs_inversion):
        """RCS mercado acciones must be positive when valor_acciones > 0."""
        result = rcs_inversion.calcular_rcs_mercado_acciones()
        assert result > Decimal("0")

    def test_rcs_mercado_acciones_formula(self, config_rcs_inversion):
        """Acciones shock is exactly 35% of market value."""
        rcs = RCSInversion(config_rcs_inversion)
        result = rcs.calcular_rcs_mercado_acciones()
        expected = (config_rcs_inversion.valor_acciones * Decimal("0.35")).quantize(
            Decimal("0.01")
        )
        assert result == expected

    def test_rcs_mercado_inmuebles_formula(self, config_rcs_inversion):
        """Inmuebles shock is exactly 25% of market value."""
        rcs = RCSInversion(config_rcs_inversion)
        result = rcs.calcular_rcs_mercado_inmuebles()
        expected = (config_rcs_inversion.valor_inmuebles * Decimal("0.25")).quantize(
            Decimal("0.01")
        )
        assert result == expected

    def test_rcs_mercado_total_positive(self, rcs_inversion):
        """Total market RCS must be positive."""
        result = rcs_inversion.calcular_rcs_mercado_total()
        assert result > Decimal("0")
        assert isinstance(result, Decimal)


# ==================================================================
# 2. RCS credito positive for nonzero bonds
# ==================================================================


class TestRCSCredito:

    def test_rcs_credito_positive(self, rcs_inversion):
        """RCS credito must be positive when valor_bonos_corporativos > 0."""
        result = rcs_inversion.calcular_rcs_credito()
        assert result > Decimal("0")

    def test_rcs_credito_formula_aa(self, config_rcs_inversion):
        """AA rating => shock 0.005 applied to valor_bonos_corporativos."""
        rcs = RCSInversion(config_rcs_inversion)
        result = rcs.calcular_rcs_credito()
        expected = (
            config_rcs_inversion.valor_bonos_corporativos * Decimal("0.005")
        ).quantize(Decimal("0.01"))
        assert result == expected

    def test_rcs_credito_returns_decimal(self, rcs_inversion):
        """Return type must be Decimal."""
        assert isinstance(rcs_inversion.calcular_rcs_credito(), Decimal)


# ==================================================================
# 3. RCS concentracion calculation
# ==================================================================


class TestRCSConcentracion:

    def test_rcs_concentracion_positive(self, rcs_inversion):
        """RCS concentracion must be positive for nonzero portfolio."""
        result = rcs_inversion.calcular_rcs_concentracion()
        assert result > Decimal("0")

    def test_rcs_concentracion_formula(self, config_rcs_inversion):
        """Concentracion = 1% of total portfolio value."""
        rcs = RCSInversion(config_rcs_inversion)
        total_inv = (
            config_rcs_inversion.valor_acciones
            + config_rcs_inversion.valor_bonos_gubernamentales
            + config_rcs_inversion.valor_bonos_corporativos
            + config_rcs_inversion.valor_inmuebles
        )
        expected = (total_inv * Decimal("0.01")).quantize(Decimal("0.01"))
        result = rcs.calcular_rcs_concentracion()
        assert result == expected


# ==================================================================
# 4. Total = sqrt(mercado^2 + credito^2 + concentracion^2)
# ==================================================================


class TestRCSTotalInversion:

    def test_total_structure(self, rcs_inversion):
        """calcular_rcs_total_inversion returns (Decimal, dict)."""
        rcs_total, desglose = rcs_inversion.calcular_rcs_total_inversion()
        assert isinstance(rcs_total, Decimal)
        assert isinstance(desglose, dict)
        expected_keys = {
            "mercado",
            "credito",
            "concentracion",
            "acciones",
            "bonos_gubernamentales",
            "bonos_corporativos",
            "inmuebles",
        }
        assert set(desglose.keys()) == expected_keys

    def test_total_matches_formula(self, rcs_inversion):
        """Total must match sqrt(mercado^2 + credito^2 + concentracion^2)."""
        rcs_mercado = rcs_inversion.calcular_rcs_mercado_total()
        rcs_credito = rcs_inversion.calcular_rcs_credito()
        rcs_conc = rcs_inversion.calcular_rcs_concentracion()

        suma = rcs_mercado ** 2 + rcs_credito ** 2 + rcs_conc ** 2
        expected = Decimal(str(math.sqrt(float(suma)))).quantize(Decimal("0.01"))

        rcs_total, _ = rcs_inversion.calcular_rcs_total_inversion()
        assert rcs_total == expected

    def test_total_less_than_simple_sum(self, rcs_inversion):
        """sqrt aggregation implies total < simple sum (when all > 0)."""
        rcs_total, desglose = rcs_inversion.calcular_rcs_total_inversion()
        suma_simple = desglose["mercado"] + desglose["credito"] + desglose["concentracion"]
        assert rcs_total < suma_simple

    def test_mercado_correlation_less_than_sum(self, rcs_inversion):
        """RCS mercado total with rho=0.75 must be less than simple sum of sub-risks."""
        acc = rcs_inversion.calcular_rcs_mercado_acciones()
        bg = rcs_inversion.calcular_rcs_mercado_bonos_gubernamentales()
        bc = rcs_inversion.calcular_rcs_mercado_bonos_corporativos()
        inm = rcs_inversion.calcular_rcs_mercado_inmuebles()

        suma_simple = acc + bg + bc + inm
        rcs_mercado = rcs_inversion.calcular_rcs_mercado_total()

        assert rcs_mercado < suma_simple
        assert rcs_mercado > Decimal("0")


# ==================================================================
# 5. All-zero portfolio produces validation error
# ==================================================================


class TestZeroPortfolio:

    def test_all_zero_raises_validation_error(self):
        """All asset values zero must raise ValueError (model validator)."""
        with pytest.raises(ValueError, match="al menos un tipo"):
            ConfiguracionRCSInversion(
                valor_acciones=Decimal("0"),
                valor_bonos_gubernamentales=Decimal("0"),
                valor_bonos_corporativos=Decimal("0"),
                valor_inmuebles=Decimal("0"),
            )


# ==================================================================
# 6. Higher bond duration increases market risk
# ==================================================================


class TestDuracionSensitivity:

    def test_higher_duration_increases_bonos_gub(self):
        """Longer duration must increase governmental bond RCS."""
        short = ConfiguracionRCSInversion(
            valor_bonos_gubernamentales=Decimal("100000000"),
            duracion_promedio_bonos=Decimal("3"),
        )
        long_ = ConfiguracionRCSInversion(
            valor_bonos_gubernamentales=Decimal("100000000"),
            duracion_promedio_bonos=Decimal("15"),
        )

        rcs_short = RCSInversion(short).calcular_rcs_mercado_bonos_gubernamentales()
        rcs_long = RCSInversion(long_).calcular_rcs_mercado_bonos_gubernamentales()

        assert rcs_long > rcs_short

    def test_higher_duration_increases_bonos_corp(self):
        """Longer duration must increase corporate bond RCS."""
        short = ConfiguracionRCSInversion(
            valor_bonos_corporativos=Decimal("100000000"),
            duracion_promedio_bonos=Decimal("3"),
            calificacion_promedio_bonos="A",
        )
        long_ = ConfiguracionRCSInversion(
            valor_bonos_corporativos=Decimal("100000000"),
            duracion_promedio_bonos=Decimal("15"),
            calificacion_promedio_bonos="A",
        )

        rcs_short = RCSInversion(short).calcular_rcs_mercado_bonos_corporativos()
        rcs_long = RCSInversion(long_).calcular_rcs_mercado_bonos_corporativos()

        assert rcs_long > rcs_short

    def test_duration_adjustment_clamped_low(self):
        """Duration adjustment has a floor of 0.5."""
        cfg = ConfiguracionRCSInversion(
            valor_bonos_gubernamentales=Decimal("100000000"),
            duracion_promedio_bonos=Decimal("0.5"),
        )
        shocks = RCSInversion(cfg).obtener_shocks_aplicados()
        assert shocks["ajuste_duracion"] == Decimal("0.55").quantize(Decimal("0.01"))
        # 1.0 + (0.5-5)*0.1 = 1.0 - 0.45 = 0.55, which is >= 0.5

    def test_duration_adjustment_clamped_high(self):
        """Duration adjustment has a ceiling of 2.5."""
        cfg = ConfiguracionRCSInversion(
            valor_bonos_gubernamentales=Decimal("100000000"),
            duracion_promedio_bonos=Decimal("30"),
        )
        shocks = RCSInversion(cfg).obtener_shocks_aplicados()
        assert shocks["ajuste_duracion"] == Decimal("2.50")


# ==================================================================
# 7. Different credit ratings affect RCS
# ==================================================================


class TestCreditRatings:

    def test_worse_rating_higher_credito(self):
        """Worse credit rating must produce higher RCS credito."""
        cfg_aa = ConfiguracionRCSInversion(
            valor_bonos_corporativos=Decimal("100000000"),
            calificacion_promedio_bonos="AA",
        )
        cfg_b = ConfiguracionRCSInversion(
            valor_bonos_corporativos=Decimal("100000000"),
            calificacion_promedio_bonos="B",
        )

        rcs_aa = RCSInversion(cfg_aa).calcular_rcs_credito()
        rcs_b = RCSInversion(cfg_b).calcular_rcs_credito()

        assert rcs_b > rcs_aa

    def test_worse_rating_higher_bonos_corp_market(self):
        """Worse rating must also increase corporate bond market RCS (ajuste_calif)."""
        cfg_aaa = ConfiguracionRCSInversion(
            valor_bonos_corporativos=Decimal("100000000"),
            calificacion_promedio_bonos="AAA",
        )
        cfg_bb = ConfiguracionRCSInversion(
            valor_bonos_corporativos=Decimal("100000000"),
            calificacion_promedio_bonos="BB",
        )

        rcs_aaa = RCSInversion(cfg_aaa).calcular_rcs_mercado_bonos_corporativos()
        rcs_bb = RCSInversion(cfg_bb).calcular_rcs_mercado_bonos_corporativos()

        assert rcs_bb > rcs_aaa

    def test_invalid_rating_rejected(self):
        """Invalid credit rating must be rejected by the validator."""
        with pytest.raises(ValueError, match="no v"):
            ConfiguracionRCSInversion(
                valor_bonos_corporativos=Decimal("100000000"),
                calificacion_promedio_bonos="ZZZ",
            )


# ==================================================================
# 8. Only equities (no bonds) -- still works
# ==================================================================


class TestOnlyEquities:

    def test_only_equities_rcs_acciones(self, config_only_equities):
        """Equities-only portfolio still produces valid acciones RCS."""
        rcs = RCSInversion(config_only_equities)
        result = rcs.calcular_rcs_mercado_acciones()
        expected = (Decimal("50000000") * Decimal("0.35")).quantize(Decimal("0.01"))
        assert result == expected

    def test_only_equities_credito_zero(self, config_only_equities):
        """With no corporate bonds, credito RCS should be zero."""
        rcs = RCSInversion(config_only_equities)
        assert rcs.calcular_rcs_credito() == Decimal("0.00")

    def test_only_equities_total_works(self, config_only_equities):
        """Total RCS must still compute without errors for equity-only portfolio."""
        rcs = RCSInversion(config_only_equities)
        rcs_total, desglose = rcs.calcular_rcs_total_inversion()
        assert rcs_total > Decimal("0")
        assert desglose["credito"] == Decimal("0.00")


# ==================================================================
# 9. Only bonds (no equities) -- still works
# ==================================================================


class TestOnlyBonds:

    def test_only_bonds_acciones_zero(self, config_only_bonds):
        """With no equities, acciones RCS should be zero."""
        rcs = RCSInversion(config_only_bonds)
        assert rcs.calcular_rcs_mercado_acciones() == Decimal("0.00")

    def test_only_bonds_credito_positive(self, config_only_bonds):
        """With corporate bonds present, credito RCS must be positive."""
        rcs = RCSInversion(config_only_bonds)
        assert rcs.calcular_rcs_credito() > Decimal("0")

    def test_only_bonds_total_works(self, config_only_bonds):
        """Total RCS must still compute without errors for bond-only portfolio."""
        rcs = RCSInversion(config_only_bonds)
        rcs_total, desglose = rcs.calcular_rcs_total_inversion()
        assert rcs_total > Decimal("0")
        assert desglose["acciones"] == Decimal("0.00")
        assert desglose["inmuebles"] == Decimal("0.00")


# ==================================================================
# 10. Very large portfolio values (numeric stability)
# ==================================================================


class TestNumericStability:

    def test_large_portfolio_no_overflow(self):
        """Very large portfolio values should not cause overflow."""
        cfg = ConfiguracionRCSInversion(
            valor_acciones=Decimal("999999999999"),
            valor_bonos_gubernamentales=Decimal("999999999999"),
            valor_bonos_corporativos=Decimal("999999999999"),
            valor_inmuebles=Decimal("999999999999"),
            duracion_promedio_bonos=Decimal("10"),
            calificacion_promedio_bonos="BBB",
        )
        rcs = RCSInversion(cfg)
        rcs_total, desglose = rcs.calcular_rcs_total_inversion()

        assert rcs_total > Decimal("0")
        for key, value in desglose.items():
            assert value >= Decimal("0"), f"{key} should be non-negative"

    def test_large_values_quantized(self):
        """Even with large values, results are quantized to 2 decimals."""
        cfg = ConfiguracionRCSInversion(
            valor_acciones=Decimal("999999999999"),
        )
        rcs = RCSInversion(cfg)
        result = rcs.calcular_rcs_mercado_acciones()
        assert result == result.quantize(Decimal("0.01"))


# ==================================================================
# 11. obtener_shocks_aplicados
# ==================================================================


class TestShocksAplicados:

    def test_shocks_keys(self, rcs_inversion):
        """obtener_shocks_aplicados must return all expected keys."""
        shocks = rcs_inversion.obtener_shocks_aplicados()
        expected_keys = {
            "shock_acciones",
            "shock_bonos_gubernamentales",
            "shock_bonos_corporativos",
            "shock_inmuebles",
            "shock_credito",
            "duracion_bonos",
            "ajuste_duracion",
            "calificacion",
        }
        assert set(shocks.keys()) == expected_keys

    def test_shock_acciones_constant(self, rcs_inversion):
        """Acciones shock is always 0.35 regardless of config."""
        shocks = rcs_inversion.obtener_shocks_aplicados()
        assert shocks["shock_acciones"] == Decimal("0.35")

    def test_shock_inmuebles_constant(self, rcs_inversion):
        """Inmuebles shock is always 0.25 regardless of config."""
        shocks = rcs_inversion.obtener_shocks_aplicados()
        assert shocks["shock_inmuebles"] == Decimal("0.25")

    def test_calificacion_matches_config(self, rcs_inversion, config_rcs_inversion):
        """Calificacion in shocks must match the config."""
        shocks = rcs_inversion.obtener_shocks_aplicados()
        assert shocks["calificacion"] == config_rcs_inversion.calificacion_promedio_bonos


# ==================================================================
# 12. __repr__
# ==================================================================


class TestRepr:

    def test_repr_contains_class_name(self, rcs_inversion):
        """__repr__ must include class name."""
        assert "RCSInversion" in repr(rcs_inversion)

    def test_repr_contains_calificacion(self, rcs_inversion):
        """__repr__ must show calificacion."""
        r = repr(rcs_inversion)
        assert "calif=" in r
