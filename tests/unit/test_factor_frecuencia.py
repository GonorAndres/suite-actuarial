"""
Tests for UDD frequency factors and the shared _obtener_factor_frecuencia dispatcher.

Covers:
- UDD formula correctness (annual, mensual, edge cases)
- Boundary comparison between UDD and traditional factors
- Zero-rate degeneration to 1/m
- Backward-compatible default (traditional method)
"""

from decimal import Decimal

import pytest

from suite_actuarial.actuarial.pricing.vida_pricing import (
    _FACTORES_TRADICIONALES,
    _FRECUENCIA_A_M,
    _obtener_factor_frecuencia,
    factor_frecuencia_udd,
)


class TestFactorUDD:
    """Tests for the pure UDD formula."""

    def test_factor_udd_anual_is_one(self):
        """Annual payment (m=1) must always return exactly 1."""
        assert factor_frecuencia_udd(1, Decimal("0.055")) == Decimal("1")
        assert factor_frecuencia_udd(1, Decimal("0")) == Decimal("1")
        assert factor_frecuencia_udd(1, Decimal("0.10")) == Decimal("1")

    def test_factor_udd_mensual_matches_formula(self):
        """At i=5.5%, monthly UDD factor should be approximately 0.08527.

        Manual calculation:
            i = 0.055
            i^(12) = 12 * ((1.055)^(1/12) - 1) = 12 * 0.004472 = 0.053665
            factor = (1/12) * (0.055 / 0.053665) = 0.08333 * 1.02488 = 0.08541
        The exact value depends on floating-point precision, so we check
        it is within a tight tolerance.
        """
        factor = factor_frecuencia_udd(12, Decimal("0.055"))
        assert abs(float(factor) - 0.0854) < 0.001

    def test_factor_udd_vs_tradicional_bounded(self):
        """UDD factor should be within 0.01 of traditional factor for all frequencies."""
        tasa = Decimal("0.055")
        for freq, m in _FRECUENCIA_A_M.items():
            udd_val = float(factor_frecuencia_udd(m, tasa))
            trad_val = float(_FACTORES_TRADICIONALES[freq])
            diff = abs(udd_val - trad_val)
            assert diff < 0.01, (
                f"Frequency '{freq}' (m={m}): UDD={udd_val:.5f}, "
                f"traditional={trad_val:.5f}, diff={diff:.5f}"
            )

    def test_factor_udd_zero_rate_degenerates(self):
        """At i=0 the UDD factor must degenerate to exactly 1/m."""
        for m in [1, 2, 4, 12]:
            factor = factor_frecuencia_udd(m, Decimal("0"))
            expected = Decimal(str(1.0 / m))
            assert factor == expected, (
                f"m={m}: expected {expected}, got {factor}"
            )


class TestObtenerFactorFrecuencia:
    """Tests for the dispatcher function."""

    def test_tradicional_is_default(self):
        """Default method must return the old hardcoded values (backward compat)."""
        for freq, expected in _FACTORES_TRADICIONALES.items():
            result = _obtener_factor_frecuencia(freq)
            assert result == expected, (
                f"Default for '{freq}': expected {expected}, got {result}"
            )

    def test_udd_method_returns_decimal(self):
        """UDD method must return a Decimal."""
        result = _obtener_factor_frecuencia("mensual", Decimal("0.055"), metodo="udd")
        assert isinstance(result, Decimal)

    def test_invalid_frecuencia_raises(self):
        """Unknown frequency must raise ValueError."""
        with pytest.raises(ValueError, match="no soportada"):
            _obtener_factor_frecuencia("bimestral")

    def test_invalid_metodo_raises(self):
        """Unknown method must raise ValueError."""
        with pytest.raises(ValueError, match="no soportado"):
            _obtener_factor_frecuencia("anual", metodo="woolhouse")
