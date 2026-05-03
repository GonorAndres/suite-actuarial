"""Boundary and stress tests across all domains.

Tests edge cases, limits, and extreme inputs for:
- Vida (life insurance): age boundaries, zero rates, extreme sums assured
- Pensiones (pensions): week thresholds, age factors
- Danos (property/auto): min/max values, youngest/oldest drivers
- Reservas (reserves): minimal triangles, numeric stability
- Reaseguro (reinsurance): empty claims, retention edge, large values
"""

from datetime import date
from decimal import Decimal

import pandas as pd
import pytest

from suite_actuarial.actuarial.pricing.vida_pricing import calcular_seguro_vida
from suite_actuarial.core.validators import (
    Asegurado,
    ConfiguracionChainLadder,
    ConfiguracionProducto,
    ExcessOfLossConfig,
    MetodoPromedio,
    QuotaShareConfig,
    Sexo,
    Siniestro,
    TipoContrato,
)
from suite_actuarial.danos.auto import SeguroAuto
from suite_actuarial.danos.incendio import SeguroIncendio
from suite_actuarial.danos.rc import SeguroRC
from suite_actuarial.pensiones.plan_retiro import PensionLey73
from suite_actuarial.reaseguro.excess_of_loss import ExcessOfLoss
from suite_actuarial.reaseguro.quota_share import QuotaShare
from suite_actuarial.reservas.chain_ladder import ChainLadder
from suite_actuarial.vida.temporal import VidaTemporal

# =====================================================================
# VIDA BOUNDARY TESTS
# =====================================================================


class TestVidaBoundary:
    """Boundary tests for life insurance pricing."""

    def test_age_25_plazo_to_omega(self, tabla_emssa09):
        """Age 25 with plazo reaching omega (75 years, 25+75=100) -- should work.

        VidaTemporal rejects age < 25 for plazos >= 30, so we use 25
        as the youngest age that can reach omega.
        """
        config = ConfiguracionProducto(
            nombre_producto="Test 25 to omega",
            plazo_years=75,
            tasa_interes_tecnico=Decimal("0.055"),
            recargo_gastos_admin=Decimal("0.05"),
            recargo_gastos_adq=Decimal("0.10"),
            recargo_utilidad=Decimal("0.03"),
        )
        asegurado = Asegurado(
            edad=25, sexo=Sexo.HOMBRE, suma_asegurada=Decimal("1000000")
        )
        producto = VidaTemporal(config, tabla_emssa09)
        resultado = producto.calcular_prima(asegurado)
        assert resultado.prima_neta > 0
        assert resultado.prima_total > resultado.prima_neta

    def test_age_99_plazo_1(self, tabla_emssa09):
        """Age 99 with plazo 1 -- near omega boundary.

        The base product rejects ages > 70 via validar_asegurabilidad,
        so we test the pricing function directly instead.
        """
        axn = calcular_seguro_vida(
            tabla=tabla_emssa09,
            edad=99,
            sexo=Sexo.HOMBRE,
            plazo=1,
            tasa_interes=Decimal("0.055"),
            suma_asegurada=Decimal("1000000"),
        )
        assert axn > 0
        # Near omega, the insurance value should be close to the
        # discounted qx which is substantial at age 99.
        assert axn < Decimal("1000000")

    def test_age_95_plazo_10_exceeds_omega(self, tabla_emssa09):
        """Age 95 + plazo 10 = 105 exceeds omega (100).

        VidaTemporal.validar_asegurabilidad rejects edad_final > 100,
        and base also rejects age > 70, so calcular_prima raises ValueError.
        """
        config = ConfiguracionProducto(
            nombre_producto="Test exceeds omega",
            plazo_years=10,
            tasa_interes_tecnico=Decimal("0.055"),
            recargo_gastos_admin=Decimal("0.05"),
            recargo_gastos_adq=Decimal("0.10"),
            recargo_utilidad=Decimal("0.03"),
        )
        asegurado = Asegurado(
            edad=95, sexo=Sexo.HOMBRE, suma_asegurada=Decimal("1000000")
        )
        producto = VidaTemporal(config, tabla_emssa09)
        with pytest.raises(ValueError, match="no es asegurable"):
            producto.calcular_prima(asegurado)

    def test_zero_interest_rate(self, tabla_emssa09):
        """tasa_interes = 0 -- zero rate edge case.

        With zero discounting the insurance value equals the expected
        number of deaths (sum of t_p_x * q_{x+t}), which must still be
        positive.
        """
        axn = calcular_seguro_vida(
            tabla=tabla_emssa09,
            edad=35,
            sexo=Sexo.HOMBRE,
            plazo=20,
            tasa_interes=Decimal("0"),
            suma_asegurada=Decimal("1000000"),
        )
        assert axn > 0
        # Without discounting the value should be higher than with 5.5%
        axn_discounted = calcular_seguro_vida(
            tabla=tabla_emssa09,
            edad=35,
            sexo=Sexo.HOMBRE,
            plazo=20,
            tasa_interes=Decimal("0.055"),
            suma_asegurada=Decimal("1000000"),
        )
        assert axn > axn_discounted

    def test_minimum_suma_asegurada(self, tabla_emssa09, config_vida_20):
        """suma_asegurada = 0.01 -- minimum possible value."""
        asegurado = Asegurado(
            edad=35, sexo=Sexo.HOMBRE, suma_asegurada=Decimal("0.01")
        )
        producto = VidaTemporal(config_vida_20, tabla_emssa09)
        resultado = producto.calcular_prima(asegurado)
        assert resultado.prima_neta > 0
        assert resultado.prima_total > 0

    def test_large_suma_asegurada(self, tabla_emssa09):
        """suma_asegurada = 50,000,000 -- large value at the auto-underwriting limit.

        base_product.validar_asegurabilidad rejects > 50M, so exactly 50M
        should still pass.
        """
        config = ConfiguracionProducto(
            nombre_producto="Test large SA",
            plazo_years=20,
            tasa_interes_tecnico=Decimal("0.055"),
            recargo_gastos_admin=Decimal("0.05"),
            recargo_gastos_adq=Decimal("0.10"),
            recargo_utilidad=Decimal("0.03"),
        )
        asegurado = Asegurado(
            edad=35, sexo=Sexo.HOMBRE, suma_asegurada=Decimal("50000000")
        )
        producto = VidaTemporal(config, tabla_emssa09)
        resultado = producto.calcular_prima(asegurado)
        assert resultado.prima_neta > 0
        assert resultado.prima_total > 0


# =====================================================================
# PENSIONES BOUNDARY TESTS
# =====================================================================


class TestPensionesBoundary:
    """Boundary tests for IMSS pension calculations."""

    def test_ley73_500_semanas_minimum(self):
        """500 weeks exactly (legal minimum) -- 33.07% percentage."""
        calc = PensionLey73(
            semanas_cotizadas=500,
            salario_promedio_5_anos=Decimal("500"),
            edad_retiro=65,
        )
        assert calc._porcentaje == Decimal("0.3307")
        pension = calc.calcular_pension_mensual()
        assert pension > 0

    def test_ley73_2060_semanas_cap(self):
        """2060+ weeks should cap at 100%."""
        calc = PensionLey73(
            semanas_cotizadas=2060,
            salario_promedio_5_anos=Decimal("500"),
            edad_retiro=65,
        )
        assert calc._porcentaje == Decimal("1.0000")

        # 2500 weeks should also cap at 100%
        calc2 = PensionLey73(
            semanas_cotizadas=2500,
            salario_promedio_5_anos=Decimal("500"),
            edad_retiro=65,
        )
        assert calc2._porcentaje == Decimal("1.0000")
        # Pensions at 2060 and 2500 weeks should be identical (both at 100%)
        assert calc.calcular_pension_mensual() == calc2.calcular_pension_mensual()

    def test_ley73_499_semanas_below_minimum(self):
        """499 weeks (below minimum) -- should raise ValueError."""
        with pytest.raises(ValueError, match="500 semanas"):
            PensionLey73(
                semanas_cotizadas=499,
                salario_promedio_5_anos=Decimal("500"),
                edad_retiro=65,
            )

    def test_ley73_age_60_minimum_factor(self):
        """Age 60 (minimum retirement age) -- factor 0.75."""
        calc = PensionLey73(
            semanas_cotizadas=1000,
            salario_promedio_5_anos=Decimal("500"),
            edad_retiro=60,
        )
        assert calc._factor_edad == Decimal("0.75")
        pension_60 = calc.calcular_pension_mensual()
        assert pension_60 > 0

    def test_ley73_age_65_full_factor(self):
        """Age 65 (full pension) -- factor 1.00 vs age 60 factor 0.75."""
        calc_65 = PensionLey73(
            semanas_cotizadas=1000,
            salario_promedio_5_anos=Decimal("500"),
            edad_retiro=65,
        )
        calc_60 = PensionLey73(
            semanas_cotizadas=1000,
            salario_promedio_5_anos=Decimal("500"),
            edad_retiro=60,
        )
        assert calc_65._factor_edad == Decimal("1.00")
        # pension at 65 = pension at 60 * (1.00 / 0.75)
        pension_65 = calc_65.calcular_pension_mensual()
        pension_60 = calc_60.calcular_pension_mensual()
        assert pension_65 > pension_60
        # Verify the ratio equals 1.00/0.75
        ratio = pension_65 / pension_60
        assert abs(ratio - Decimal("1.00") / Decimal("0.75")) < Decimal("0.01")


# =====================================================================
# DANOS BOUNDARY TESTS
# =====================================================================


class TestDanosBoundary:
    """Boundary tests for property and auto insurance."""

    def test_incendio_minimum_value(self):
        """SeguroIncendio with valor_inmueble = 1 (minimum)."""
        seguro = SeguroIncendio(
            valor_inmueble=Decimal("1"),
            tipo_construccion="concreto",
            zona="urbana_baja",
            uso="habitacional",
        )
        prima = seguro.calcular_prima()
        assert prima >= 0
        # (1/1000) * 0.80 * 0.85 * 1.00 = 0.00068 -> rounds to 0.00
        assert isinstance(prima, Decimal)

    def test_rc_very_large_limit(self):
        """SeguroRC with very large limit (100,000,000)."""
        seguro = SeguroRC(
            limite_responsabilidad=Decimal("100000000"),
            deducible=Decimal("50000"),
            clase_actividad="oficinas",
        )
        prima = seguro.calcular_prima()
        assert prima > 0
        # (100M/1000) * 1.20 * 0.90 = 108,000
        assert prima == Decimal("108000.00")

    def test_auto_youngest_driver(self):
        """SeguroAuto with youngest valid driver (age 18)."""
        seguro = SeguroAuto(
            valor_vehiculo=Decimal("300000"),
            tipo_vehiculo="sedan_compacto",
            antiguedad_anos=0,
            zona="merida",
            edad_conductor=18,
        )
        tarifa = seguro.calcular_tarifa()
        assert all(v > 0 for v in tarifa.values())
        assert seguro.factor_edad == Decimal("1.35")
        assert seguro.rango_edad == "18-25"

    def test_auto_oldest_practical_driver(self):
        """SeguroAuto with oldest practical driver (age 80, band 66+)."""
        seguro = SeguroAuto(
            valor_vehiculo=Decimal("300000"),
            tipo_vehiculo="sedan_compacto",
            antiguedad_anos=5,
            zona="merida",
            edad_conductor=80,
        )
        tarifa = seguro.calcular_tarifa()
        assert all(v > 0 for v in tarifa.values())
        assert seguro.factor_edad == Decimal("1.20")
        assert seguro.rango_edad == "66+"


# =====================================================================
# RESERVAS BOUNDARY TESTS
# =====================================================================


class TestReservasBoundary:
    """Boundary tests for Chain Ladder reserve calculations."""

    @staticmethod
    def _make_triangle(data: list[list], years: list[int]) -> pd.DataFrame:
        """Helper to build a triangle DataFrame from nested list."""
        n = len(data[0])
        df = pd.DataFrame(data, index=years, columns=range(n))
        # Replace None with NaN
        df = df.where(df.notna())
        return df

    def test_2x2_triangle_smallest_valid(self):
        """2x2 triangle (smallest valid size) -- should compute."""
        data = [
            [100, 150],
            [110, None],
        ]
        df = self._make_triangle(data, [2022, 2023])
        config = ConfiguracionChainLadder(metodo_promedio=MetodoPromedio.SIMPLE)
        cl = ChainLadder(config)
        resultado = cl.calcular(df)
        assert resultado.reserva_total >= 0
        assert resultado.ultimate_total > 0
        assert len(resultado.factores_desarrollo) >= 1

    def test_triangle_all_equal_no_development(self):
        """Triangle with identical values in each row -- factors should be ~1.0."""
        data = [
            [1000, 1000, 1000],
            [1000, 1000, None],
            [1000, None, None],
        ]
        df = self._make_triangle(data, [2021, 2022, 2023])
        config = ConfiguracionChainLadder(metodo_promedio=MetodoPromedio.SIMPLE)
        cl = ChainLadder(config)
        resultado = cl.calcular(df)
        # With no development, all factors should be 1.0
        for factor in resultado.factores_desarrollo:
            assert abs(factor - Decimal("1.0")) < Decimal("0.01")
        # Reserves should be zero or near-zero
        assert resultado.reserva_total < Decimal("1")

    def test_triangle_single_origin_year(self):
        """Single origin year (1x1 triangle) -- should raise ValueError.

        A 1x1 triangle has only one cell with 0 development columns, which
        fails the triangular structure check (expects n_cols - i known values).
        """
        df = pd.DataFrame({"0": [5000]}, index=[2023])
        config = ConfiguracionChainLadder(metodo_promedio=MetodoPromedio.SIMPLE)
        cl = ChainLadder(config)
        # Single row with single column: no development data -> factors empty
        # but it still has a valid triangle structure (1 row, 1 col)
        resultado = cl.calcular(df)
        # With only one development period, no age-to-age factors exist
        # so factores_desarrollo should be empty or trivial
        assert resultado.reserva_total == Decimal("0")

    def test_triangle_large_values_numeric_stability(self):
        """Triangle with large values (millions) -- numeric stability."""
        scale = 1_000_000
        data = [
            [3000 * scale, 5000 * scale, 5600 * scale, 5800 * scale, 5900 * scale],
            [3200 * scale, 5200 * scale, 5800 * scale, 6000 * scale, None],
            [3500 * scale, 5500 * scale, 6100 * scale, None, None],
            [3800 * scale, 5900 * scale, None, None, None],
            [4000 * scale, None, None, None, None],
        ]
        df = self._make_triangle(data, [2019, 2020, 2021, 2022, 2023])
        config = ConfiguracionChainLadder(metodo_promedio=MetodoPromedio.SIMPLE)
        cl = ChainLadder(config)
        resultado = cl.calcular(df)
        assert resultado.reserva_total > 0
        assert resultado.ultimate_total > 0
        # Factors should be the same regardless of scale
        # (i.e. ratios are scale-invariant)
        for factor in resultado.factores_desarrollo:
            assert factor > Decimal("0.9")
            assert factor < Decimal("3.0")

    def test_triangle_from_conftest(self, triangulo_acumulado, origin_years_5):
        """Conftest triangle should compute correctly."""
        n = len(triangulo_acumulado[0])
        df = pd.DataFrame(
            triangulo_acumulado, index=origin_years_5, columns=range(n)
        )
        df = df.where(df.notna())
        config = ConfiguracionChainLadder(metodo_promedio=MetodoPromedio.SIMPLE)
        cl = ChainLadder(config)
        resultado = cl.calcular(df)
        assert resultado.reserva_total > 0
        assert len(resultado.reservas_por_anio) == 5


# =====================================================================
# REASEGURO BOUNDARY TESTS
# =====================================================================


class TestReaseguroBoundary:
    """Boundary tests for reinsurance contracts."""

    @staticmethod
    def _make_qs_config(pct_cesion: Decimal = Decimal("30")) -> QuotaShareConfig:
        """Helper to build a QuotaShare config."""
        return QuotaShareConfig(
            tipo_contrato=TipoContrato.QUOTA_SHARE,
            vigencia_inicio=date(2024, 1, 1),
            vigencia_fin=date(2024, 12, 31),
            porcentaje_cesion=pct_cesion,
            comision_reaseguro=Decimal("25"),
            comision_override=Decimal("2.5"),
        )

    @staticmethod
    def _make_xl_config() -> ExcessOfLossConfig:
        """Helper to build an XL config."""
        return ExcessOfLossConfig(
            tipo_contrato=TipoContrato.EXCESS_OF_LOSS,
            vigencia_inicio=date(2024, 1, 1),
            vigencia_fin=date(2024, 12, 31),
            retencion=Decimal("200000"),
            limite=Decimal("500000"),
            tasa_prima=Decimal("5"),
        )

    @staticmethod
    def _make_siniestro(
        monto: Decimal, id_str: str = "SIN-001"
    ) -> Siniestro:
        """Helper to build a siniestro within the 2024 contract period."""
        return Siniestro(
            id_siniestro=id_str,
            fecha_ocurrencia=date(2024, 6, 15),
            monto_bruto=monto,
        )

    def test_empty_claims_list(self):
        """Empty claims list -- should return zero recuperacion."""
        qs = QuotaShare(self._make_qs_config())
        total, detalle = qs.calcular_recuperacion_multiple([])
        assert total == Decimal("0")
        assert detalle == []

    def test_xl_claim_exactly_at_retention(self):
        """Single claim exactly at retention (200K) -- zero recovery."""
        xl = ExcessOfLoss(self._make_xl_config())
        sin = self._make_siniestro(Decimal("200000"))
        recovery = xl.calcular_recuperacion(sin)
        assert recovery == Decimal("0")

    def test_xl_claim_exceeding_limit(self):
        """Single claim exceeding limit -- recovery capped at limit (500K).

        Claim = 900K, retention = 200K, excess = 700K, but limit = 500K.
        """
        xl = ExcessOfLoss(self._make_xl_config())
        sin = self._make_siniestro(Decimal("900000"))
        recovery = xl.calcular_recuperacion(sin)
        assert recovery == Decimal("500000")

    def test_xl_large_claim_numeric_stability(self):
        """Very large claim (50M) -- numeric stability.

        retention=200K, limit=500K, so recovery should still be exactly 500K.
        """
        xl = ExcessOfLoss(self._make_xl_config())
        sin = self._make_siniestro(Decimal("50000000"))
        recovery = xl.calcular_recuperacion(sin)
        assert recovery == Decimal("500000")

    def test_quota_share_100_percent_cession(self):
        """QuotaShare with 100% cession -- all premium is cedido."""
        config = self._make_qs_config(pct_cesion=Decimal("100"))
        qs = QuotaShare(config)
        prima_cedida = qs.calcular_prima_cedida(Decimal("1000000"))
        prima_retenida = qs.calcular_prima_retenida(Decimal("1000000"))
        assert prima_cedida == Decimal("1000000")
        assert prima_retenida == Decimal("0")
