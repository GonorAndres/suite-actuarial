"""
Tests para RCS Danos (suscripcion).

Valida calculo del Requerimiento de Capital de Solvencia para riesgos
de suscripcion en seguros de danos (no vida): riesgo de prima, riesgo
de reserva y la agregacion con correlacion.
"""

import math
from decimal import Decimal

import pytest

from suite_actuarial.core.validators import ConfiguracionRCSDanos
from suite_actuarial.regulatorio.rcs_danos import RCSDanos

# ------------------------------------------------------------------
# Helpers / local fixtures
# ------------------------------------------------------------------


@pytest.fixture
def rcs_danos(config_rcs_danos):
    """RCSDanos instance from the conftest fixture."""
    return RCSDanos(config_rcs_danos)


@pytest.fixture
def config_single_ramo():
    """Config with a single ramo (no diversification)."""
    return ConfiguracionRCSDanos(
        primas_retenidas_12m=Decimal("100000000"),
        reserva_siniestros=Decimal("50000000"),
        coeficiente_variacion=Decimal("0.20"),
        numero_ramos=1,
    )


@pytest.fixture
def config_many_ramos():
    """Config with 10+ ramos (maximum diversification factor)."""
    return ConfiguracionRCSDanos(
        primas_retenidas_12m=Decimal("100000000"),
        reserva_siniestros=Decimal("50000000"),
        coeficiente_variacion=Decimal("0.20"),
        numero_ramos=12,
    )


# ==================================================================
# 1. RCS prima positive for valid inputs
# ==================================================================


class TestRCSPrima:

    def test_rcs_prima_positive(self, rcs_danos):
        """RCS prima must be strictly positive for nonzero primas."""
        result = rcs_danos.calcular_rcs_prima()
        assert result > Decimal("0")

    def test_rcs_prima_formula_manual(self, config_rcs_danos):
        """Verify RCS prima against hand-calculated value.

        Expected: alpha(3) * primas(20M) * sigma(0.15) * factor_ramos(0.94) = 8,460,000
        factor_ramos for 3 ramos = 1 - (3-1)*0.03 = 0.94
        """
        rcs = RCSDanos(config_rcs_danos)
        result = rcs.calcular_rcs_prima()

        primas = Decimal("20000000")
        alpha = Decimal("3.0")
        sigma = Decimal("0.15")
        factor = Decimal("0.94")  # 1 - 2*0.03
        expected = (primas * alpha * sigma * factor).quantize(Decimal("0.01"))

        assert result == expected

    def test_rcs_prima_returns_decimal(self, rcs_danos):
        """Return type must be Decimal."""
        result = rcs_danos.calcular_rcs_prima()
        assert isinstance(result, Decimal)


# ==================================================================
# 2. RCS reserva positive for valid inputs
# ==================================================================


class TestRCSReserva:

    def test_rcs_reserva_positive(self, rcs_danos):
        """RCS reserva must be strictly positive for nonzero reserva."""
        result = rcs_danos.calcular_rcs_reserva()
        assert result > Decimal("0")

    def test_rcs_reserva_formula_manual(self, config_rcs_danos):
        """Verify RCS reserva against hand-calculated value.

        Expected: beta(2) * reserva(8M) * sqrt(0.15)
        sqrt(0.15) ~ 0.387298
        => 2 * 8_000_000 * 0.387298... = 6_196_773.35 (approx)
        """
        rcs = RCSDanos(config_rcs_danos)
        result = rcs.calcular_rcs_reserva()

        reserva = Decimal("8000000")
        beta = Decimal("2.0")
        sigma_reserva = Decimal(str(math.sqrt(0.15)))
        expected = (reserva * beta * sigma_reserva).quantize(Decimal("0.01"))

        assert result == expected

    def test_rcs_reserva_returns_decimal(self, rcs_danos):
        """Return type must be Decimal."""
        result = rcs_danos.calcular_rcs_reserva()
        assert isinstance(result, Decimal)


# ==================================================================
# 3. Total RCS = sqrt(prima^2 + reserva^2 + 2*rho*prima*reserva)
# ==================================================================


class TestRCSTotalDanos:

    def test_total_structure(self, rcs_danos):
        """calcular_rcs_total_danos returns (Decimal, dict)."""
        rcs_total, desglose = rcs_danos.calcular_rcs_total_danos()

        assert isinstance(rcs_total, Decimal)
        assert isinstance(desglose, dict)
        assert "prima" in desglose
        assert "reserva" in desglose

    def test_total_equals_correlation_formula(self, rcs_danos):
        """Total must match manual variance-covariance formula with rho=0.5."""
        rcs_prima = rcs_danos.calcular_rcs_prima()
        rcs_reserva = rcs_danos.calcular_rcs_reserva()

        rho = Decimal("0.5")
        suma = rcs_prima ** 2 + rcs_reserva ** 2 + 2 * rho * rcs_prima * rcs_reserva
        expected = Decimal(str(math.sqrt(float(suma)))).quantize(Decimal("0.01"))

        rcs_total, _ = rcs_danos.calcular_rcs_total_danos()
        assert rcs_total == expected

    def test_total_less_than_simple_sum(self, rcs_danos):
        """Correlation rho=0.5 < 1 implies total < simple sum of components."""
        rcs_total, desglose = rcs_danos.calcular_rcs_total_danos()
        suma_simple = desglose["prima"] + desglose["reserva"]
        assert rcs_total < suma_simple

    def test_total_greater_than_each_component(self, rcs_danos):
        """Total must exceed each individual component."""
        rcs_total, desglose = rcs_danos.calcular_rcs_total_danos()
        assert rcs_total > desglose["prima"]
        assert rcs_total > desglose["reserva"]


# ==================================================================
# 4. Higher coeficiente_variacion increases RCS
# ==================================================================


class TestCVSensitivity:

    def test_higher_cv_increases_rcs_prima(self):
        """Increasing CV must increase RCS prima (alpha*primas*sigma*factor)."""
        base = ConfiguracionRCSDanos(
            primas_retenidas_12m=Decimal("100000000"),
            reserva_siniestros=Decimal("50000000"),
            coeficiente_variacion=Decimal("0.10"),
            numero_ramos=1,
        )
        high = ConfiguracionRCSDanos(
            primas_retenidas_12m=Decimal("100000000"),
            reserva_siniestros=Decimal("50000000"),
            coeficiente_variacion=Decimal("0.30"),
            numero_ramos=1,
        )

        assert RCSDanos(high).calcular_rcs_prima() > RCSDanos(base).calcular_rcs_prima()

    def test_higher_cv_increases_rcs_reserva(self):
        """Increasing CV must increase RCS reserva (beta*reserva*sqrt(sigma))."""
        base = ConfiguracionRCSDanos(
            primas_retenidas_12m=Decimal("100000000"),
            reserva_siniestros=Decimal("50000000"),
            coeficiente_variacion=Decimal("0.10"),
        )
        high = ConfiguracionRCSDanos(
            primas_retenidas_12m=Decimal("100000000"),
            reserva_siniestros=Decimal("50000000"),
            coeficiente_variacion=Decimal("0.30"),
        )

        assert RCSDanos(high).calcular_rcs_reserva() > RCSDanos(base).calcular_rcs_reserva()


# ==================================================================
# 5. More ramos increase diversification factor (lower RCS)
# ==================================================================


class TestDiversificacion:

    def test_more_ramos_lower_rcs_prima(self, config_single_ramo, config_many_ramos):
        """More ramos must produce a smaller RCS prima (diversification)."""
        rcs_1 = RCSDanos(config_single_ramo).calcular_rcs_prima()
        rcs_many = RCSDanos(config_many_ramos).calcular_rcs_prima()
        assert rcs_many < rcs_1

    def test_factor_ramos_single_is_one(self, config_single_ramo):
        """With 1 ramo the diversification factor must be 1.0."""
        params = RCSDanos(config_single_ramo).obtener_parametros_calculo()
        assert params["factor_diversificacion_ramos"] == Decimal("1.00")

    def test_factor_ramos_above_5_is_075(self, config_many_ramos):
        """With >5 ramos the diversification factor must be 0.75."""
        params = RCSDanos(config_many_ramos).obtener_parametros_calculo()
        assert params["factor_diversificacion_ramos"] == Decimal("0.75")

    def test_factor_ramos_intermediate(self):
        """3 ramos: factor = 1 - 2*0.03 = 0.94."""
        cfg = ConfiguracionRCSDanos(
            primas_retenidas_12m=Decimal("100000000"),
            reserva_siniestros=Decimal("50000000"),
            numero_ramos=3,
        )
        params = RCSDanos(cfg).obtener_parametros_calculo()
        assert params["factor_diversificacion_ramos"] == Decimal("0.94")


# ==================================================================
# 6. Zero reserva edge case
# ==================================================================


class TestZeroReserva:

    def test_zero_reserva_gives_zero_rcs_reserva(self):
        """When reserva_siniestros=0, RCS reserva must be 0."""
        cfg = ConfiguracionRCSDanos(
            primas_retenidas_12m=Decimal("100000000"),
            reserva_siniestros=Decimal("0"),
            coeficiente_variacion=Decimal("0.15"),
        )
        rcs = RCSDanos(cfg)
        assert rcs.calcular_rcs_reserva() == Decimal("0.00")

    def test_zero_reserva_total_equals_prima(self):
        """When reserva=0, total RCS must equal RCS prima."""
        cfg = ConfiguracionRCSDanos(
            primas_retenidas_12m=Decimal("100000000"),
            reserva_siniestros=Decimal("0"),
            coeficiente_variacion=Decimal("0.15"),
        )
        rcs = RCSDanos(cfg)
        rcs_total, desglose = rcs.calcular_rcs_total_danos()
        assert rcs_total == desglose["prima"]


# ==================================================================
# 7. Very large primas (numeric stability)
# ==================================================================


class TestNumericStability:

    def test_large_primas_no_overflow(self):
        """Very large primas should not cause overflow or errors."""
        cfg = ConfiguracionRCSDanos(
            primas_retenidas_12m=Decimal("999999999999"),
            reserva_siniestros=Decimal("500000000000"),
            coeficiente_variacion=Decimal("0.15"),
            numero_ramos=5,
        )
        rcs = RCSDanos(cfg)
        rcs_total, desglose = rcs.calcular_rcs_total_danos()

        assert rcs_total > Decimal("0")
        assert desglose["prima"] > Decimal("0")
        assert desglose["reserva"] > Decimal("0")

    def test_large_values_still_quantized(self):
        """Even with large values, results are quantized to 2 decimals."""
        cfg = ConfiguracionRCSDanos(
            primas_retenidas_12m=Decimal("999999999999"),
            reserva_siniestros=Decimal("500000000000"),
            coeficiente_variacion=Decimal("0.15"),
        )
        rcs = RCSDanos(cfg)
        result = rcs.calcular_rcs_prima()
        # Check it has at most 2 decimal places
        assert result == result.quantize(Decimal("0.01"))


# ==================================================================
# 8. obtener_parametros_calculo
# ==================================================================


class TestParametrosCalculo:

    def test_parametros_keys(self, rcs_danos):
        """obtener_parametros_calculo must return all expected keys."""
        params = rcs_danos.obtener_parametros_calculo()
        expected_keys = {
            "primas_retenidas_12m",
            "reserva_siniestros",
            "coeficiente_variacion",
            "numero_ramos",
            "factor_diversificacion_ramos",
            "sigma_reserva",
            "correlacion_prima_reserva",
        }
        assert set(params.keys()) == expected_keys

    def test_parametros_all_decimal(self, rcs_danos):
        """All values in parametros must be Decimal."""
        params = rcs_danos.obtener_parametros_calculo()
        for key, value in params.items():
            assert isinstance(value, Decimal), f"{key} is not Decimal: {type(value)}"

    def test_correlacion_is_05(self, rcs_danos):
        """Correlation between prima and reserva must be 0.5."""
        params = rcs_danos.obtener_parametros_calculo()
        assert params["correlacion_prima_reserva"] == Decimal("0.5")


# ==================================================================
# 9. __repr__
# ==================================================================


class TestRepr:

    def test_repr_contains_class_name(self, rcs_danos):
        """__repr__ must include class name."""
        assert "RCSDanos" in repr(rcs_danos)

    def test_repr_contains_primas(self, rcs_danos):
        """__repr__ must show primas value."""
        r = repr(rcs_danos)
        assert "primas=" in r
