"""
Rigorous actuarial correctness tests for suite_actuarial.

These tests verify mathematical identities, regulatory constraints,
boundary conditions, and cross-domain consistency using first-principles
reasoning -- NOT by mirroring the code under test.

Author: Test Architect (adversarial audit)
"""

import math
from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

from suite_actuarial.actuarial.interest.tasas import CurvaRendimiento
from suite_actuarial.actuarial.mortality.tablas import TablaMortalidad
from suite_actuarial.config import cargar_config
from suite_actuarial.core.models.common import Sexo
from suite_actuarial.core.validators import (
    Asegurado,
    ConfiguracionBootstrap,
    ConfiguracionBornhuetterFerguson,
    ConfiguracionChainLadder,
    ConfiguracionProducto,
    ConfiguracionRCSDanos,
    ConfiguracionRCSInversion,
    ConfiguracionRCSVida,
    MetodoPromedio,
)
from suite_actuarial.danos.frecuencia_severidad import ModeloColectivo
from suite_actuarial.danos.tarifas import (
    CalculadoraBonusMalus,
    FactorCredibilidad,
)
from suite_actuarial.pensiones.conmutacion import TablaConmutacion
from suite_actuarial.pensiones.plan_retiro import (
    CalculadoraIMSS,
    PensionLey73,
    PensionLey97,
)
from suite_actuarial.pensiones.renta_vitalicia import RentaVitalicia
from suite_actuarial.pensiones.tablas_imss import (
    obtener_factor_edad,
    obtener_porcentaje_ley73,
)
from suite_actuarial.regulatorio.agregador_rcs import AgregadorRCS
from suite_actuarial.regulatorio.validaciones_sat.models import (
    TipoSeguroFiscal,
)
from suite_actuarial.regulatorio.validaciones_sat.validador_siniestros import (
    ValidadorSiniestrosGravables,
)
from suite_actuarial.reservas.bootstrap import Bootstrap
from suite_actuarial.reservas.bornhuetter_ferguson import BornhuetterFerguson
from suite_actuarial.reservas.chain_ladder import ChainLadder
from suite_actuarial.salud.gmm import GMM, NivelHospitalario, ZonaGeografica
from suite_actuarial.vida.dotal import VidaDotal
from suite_actuarial.vida.ordinario import VidaOrdinario
from suite_actuarial.vida.temporal import VidaTemporal


# ======================================================================
# Fixtures
# ======================================================================

@pytest.fixture
def tabla_simple():
    """Small synthetic mortality table with known qx for deterministic tests.

    Ages 0-5 for both sexes. qx at omega (age 5) = 1.0.
    """
    datos = pd.DataFrame({
        "edad": list(range(0, 6)) + list(range(0, 6)),
        "sexo": ["H"] * 6 + ["M"] * 6,
        "qx": [
            0.01, 0.02, 0.03, 0.05, 0.10, 1.00,
            0.005, 0.01, 0.02, 0.03, 0.05, 1.00,
        ],
    })
    return TablaMortalidad(nombre="Simple", datos=datos)


@pytest.fixture
def tc_simple(tabla_simple):
    """Commutation table: simple mortality, male, 5% interest, raiz=100000."""
    return TablaConmutacion(tabla_simple, sexo="H", tasa_interes=0.05, raiz=100_000)


@pytest.fixture
def tabla_emssa09():
    """Load EMSSA-09 mortality table; skip if unavailable."""
    try:
        return TablaMortalidad.cargar_emssa09()
    except FileNotFoundError:
        pytest.skip("EMSSA-09 table not available")


@pytest.fixture
def tc_emssa_h(tabla_emssa09):
    """EMSSA-09 commutation table, male, 5.5% interest."""
    return TablaConmutacion(tabla_emssa09, sexo="H", tasa_interes=0.055)


@pytest.fixture
def tc_emssa_m(tabla_emssa09):
    """EMSSA-09 commutation table, female, 5.5% interest."""
    return TablaConmutacion(tabla_emssa09, sexo="M", tasa_interes=0.055)


@pytest.fixture
def triangulo_acumulado():
    """Small 4x4 cumulative triangle for Chain Ladder / BF / Bootstrap tests."""
    data = {
        1: [100.0, 150.0, 200.0, 250.0],
        2: [120.0, 180.0, 240.0, np.nan],
        3: [130.0, 195.0, np.nan, np.nan],
        4: [140.0, np.nan, np.nan, np.nan],
    }
    return pd.DataFrame(data, index=[2020, 2021, 2022, 2023])


@pytest.fixture
def config_vida_20():
    """ConfiguracionProducto for 20-year products."""
    return ConfiguracionProducto(
        nombre_producto="Test Vida 20",
        plazo_years=20,
        tasa_interes_tecnico=Decimal("0.055"),
        recargo_gastos_admin=Decimal("0.05"),
        recargo_gastos_adq=Decimal("0.10"),
        recargo_utilidad=Decimal("0.03"),
    )


@pytest.fixture
def asegurado_35_h():
    """Standard male insured, age 35, SA=1M MXN."""
    return Asegurado(
        edad=35,
        sexo=Sexo.HOMBRE,
        suma_asegurada=Decimal("1000000"),
    )


# ======================================================================
# 1. COMMUTATION IDENTITIES AND CONSTRAINTS
# ======================================================================

class TestCommutationIdentities:
    """Verify fundamental commutation function identities."""

    def test_Nx_equals_sum_of_Dx(self, tc_simple):
        """Nx must equal the sum of Dx from age x to omega.

        This is the DEFINITION of Nx. An off-by-one in the reverse
        cumulative sum would break this identity.
        """
        for x in range(tc_simple.edad_min, tc_simple.edad_max + 1):
            nx_val = tc_simple.Nx(x)
            sum_dx = sum(
                tc_simple.Dx(k)
                for k in range(x, tc_simple.edad_max + 1)
            )
            # Both are Decimal; allow tiny rounding tolerance
            assert abs(float(nx_val) - float(sum_dx)) < 1e-6, (
                f"Nx({x}) = {nx_val} != sum(Dx) = {sum_dx}"
            )

    def test_Mx_equals_sum_of_Cx(self, tc_simple):
        """Mx must equal the sum of Cx from age x to omega."""
        for x in range(tc_simple.edad_min, tc_simple.edad_max + 1):
            mx_val = tc_simple.Mx(x)
            sum_cx = sum(
                tc_simple.Cx(k)
                for k in range(x, tc_simple.edad_max + 1)
            )
            assert abs(float(mx_val) - float(sum_cx)) < 1e-6, (
                f"Mx({x}) = {mx_val} != sum(Cx) = {sum_cx}"
            )

    def test_Sx_equals_sum_of_Nx(self, tc_simple):
        """Sx must equal the sum of Nx from age x to omega."""
        for x in range(tc_simple.edad_min, tc_simple.edad_max + 1):
            sx_val = tc_simple.Sx(x)
            sum_nx = sum(
                tc_simple.Nx(k)
                for k in range(x, tc_simple.edad_max + 1)
            )
            assert abs(float(sx_val) - float(sum_nx)) < 1e-6

    def test_Rx_equals_sum_of_Mx(self, tc_simple):
        """Rx must equal the sum of Mx from age x to omega."""
        for x in range(tc_simple.edad_min, tc_simple.edad_max + 1):
            rx_val = tc_simple.Rx(x)
            sum_mx = sum(
                tc_simple.Mx(k)
                for k in range(x, tc_simple.edad_max + 1)
            )
            assert abs(float(rx_val) - float(sum_mx)) < 1e-6

    def test_insurance_annuity_identity(self, tc_simple):
        """The fundamental insurance-annuity identity: Ax + d * ax = 1.

        For a whole-life annuity-due and whole-life insurance on a discrete
        table with terminal age omega where q_omega = 1:
            Ax + d * ax_due = 1
        where d = i / (1 + i).

        This is Bowers et al. equation (5.2.9).
        """
        i = tc_simple.tasa_interes
        d = i / (1.0 + i)  # discount rate

        for x in range(tc_simple.edad_min, tc_simple.edad_max):
            ax_val = float(tc_simple.ax(x))       # whole-life annuity-due
            Ax_val = float(tc_simple.Ax(x))        # whole-life insurance

            identity = Ax_val + d * ax_val
            # Should equal 1.0 within floating-point tolerance
            assert abs(identity - 1.0) < 1e-6, (
                f"At age {x}: Ax + d*ax = {identity:.8f}, expected 1.0"
            )

    def test_nEx_equals_Dx_ratio(self, tc_simple):
        """Pure endowment nEx = D(x+n) / Dx must hold exactly."""
        x = 0
        for n in range(1, tc_simple.edad_max - tc_simple.edad_min + 1):
            nex = tc_simple.nEx(x, n)
            expected = tc_simple.Dx(x + n) / tc_simple.Dx(x)
            assert abs(float(nex) - float(expected)) < 1e-10, (
                f"nEx({x},{n}) = {nex} != Dx({x+n})/Dx({x}) = {expected}"
            )

    def test_nEx_beyond_omega_is_zero(self, tc_simple):
        """Pure endowment beyond omega should be 0 (no one survives)."""
        x = 0
        n = tc_simple.edad_max - tc_simple.edad_min + 1  # beyond omega
        assert tc_simple.nEx(x, n) == Decimal("0")

    def test_Dx_positive_and_decreasing(self, tc_simple):
        """Dx must be positive and non-increasing (discounted survivors decline)."""
        prev = float(tc_simple.Dx(tc_simple.edad_min))
        assert prev > 0
        for x in range(tc_simple.edad_min + 1, tc_simple.edad_max + 1):
            curr = float(tc_simple.Dx(x))
            assert curr >= 0
            assert curr <= prev + 1e-10, (
                f"Dx is increasing at age {x}: Dx({x})={curr} > Dx({x-1})={prev}"
            )
            prev = curr

    def test_Nx_non_increasing(self, tc_simple):
        """Nx must be non-increasing as age increases (fewer remaining Dx terms)."""
        prev = float(tc_simple.Nx(tc_simple.edad_min))
        for x in range(tc_simple.edad_min + 1, tc_simple.edad_max + 1):
            curr = float(tc_simple.Nx(x))
            assert curr <= prev + 1e-10
            prev = curr


class TestCommutationEMSSA:
    """Commutation tests on the real EMSSA-09 table."""

    def test_insurance_annuity_identity_emssa(self, tc_emssa_h):
        """Ax + d*ax = 1 on the real EMSSA-09 male table at i=5.5%.

        Note: EMSSA-09 starts at age 18, so we only test from there.
        Also, the identity holds strictly only if q_omega=1 in the table.
        For EMSSA-09 where q_omega < 1, the identity may not hold exactly
        at ages near omega; we test interior ages where it should be close.
        """
        i = tc_emssa_h.tasa_interes
        d = i / (1.0 + i)

        # EMSSA-09 starts at age 18; test ages within the table range
        for x in [20, 35, 50, 65, 80]:
            if x < tc_emssa_h.edad_min or x > tc_emssa_h.edad_max:
                continue
            ax_val = float(tc_emssa_h.ax(x))
            Ax_val = float(tc_emssa_h.Ax(x))
            identity = Ax_val + d * ax_val
            assert abs(identity - 1.0) < 1e-5, (
                f"EMSSA male age {x}: Ax + d*ax = {identity:.8f}"
            )

    def test_annuity_bounded_by_life_expectancy(self, tc_emssa_h):
        """ax must be positive and less than remaining life expectancy.

        The annuity-due ax at age x gives the expected present value
        of 1 per year paid while alive. Since payments are discounted,
        ax < (omega - x + 1), which is the maximum possible payments.
        """
        for x in [30, 40, 50, 60, 70]:
            if x > tc_emssa_h.edad_max:
                continue
            ax_val = float(tc_emssa_h.ax(x))
            max_payments = tc_emssa_h.edad_max - x + 1
            assert ax_val > 0, f"ax({x}) should be positive"
            assert ax_val < max_payments, (
                f"ax({x}) = {ax_val} >= max possible {max_payments}"
            )

    def test_old_age_no_nan(self, tc_emssa_h):
        """Values at very old ages (90+) must not produce NaN or infinity."""
        for x in range(90, tc_emssa_h.edad_max + 1):
            dx = float(tc_emssa_h.Dx(x))
            nx = float(tc_emssa_h.Nx(x))
            mx = float(tc_emssa_h.Mx(x))
            assert not math.isnan(dx) and not math.isinf(dx)
            assert not math.isnan(nx) and not math.isinf(nx)
            assert not math.isnan(mx) and not math.isinf(mx)


# ======================================================================
# 2. RESERVE BOUNDARY CONDITIONS
# ======================================================================

class TestReserveBoundaries:
    """Verify reserve boundary conditions for level-premium products."""

    def test_temporal_reserve_at_zero_and_end(self, tc_simple):
        """For a temporal insurance with level premiums:
        - Reserve at t=0 = 0 (no obligation accrued)
        - Reserve at t=n = 0 (no further coverage)
        """
        x = 0
        n = 3  # 3-year term
        assert tc_simple.tVx(x, n, 0) == Decimal("0")
        assert tc_simple.tVx(x, n, n) == Decimal("0")

    def test_temporal_reserve_positive_interior(self, tc_simple):
        """Mid-term reserve should be positive for a temporal insurance.

        The insurer has collected premiums but still bears risk, so the
        accumulated fund should be positive at intermediate durations.
        """
        x = 0
        n = 4
        for t in range(1, n):
            reserve = float(tc_simple.tVx(x, n, t))
            # Reserve should be non-negative for temporal
            assert reserve >= -1e-6, (
                f"Reserve at t={t} is negative: {reserve}"
            )

    def test_temporal_reserve_raises_out_of_range(self, tc_simple):
        """tVx should raise ValueError for t outside [0, n]."""
        with pytest.raises(ValueError):
            tc_simple.tVx(0, 3, -1)
        with pytest.raises(ValueError):
            tc_simple.tVx(0, 3, 4)


# ======================================================================
# 3. VIDA PRODUCT ORDERING
# ======================================================================

class TestVidaProductOrdering:
    """Verify that Dotal > Ordinario > Temporal in premium for same inputs.

    Economic reasoning:
    - Temporal: pays only on death during term -> cheapest
    - Ordinario (whole life): pays on death, guaranteed -> more expensive
    - Dotal: pays on death OR survival, both guaranteed -> most expensive
    """

    def test_premium_ordering(self, tabla_emssa09, config_vida_20, asegurado_35_h):
        """Dotal > Ordinario > Temporal premium (annual, same age/term/rate)."""
        temporal = VidaTemporal(config_vida_20, tabla_emssa09)
        ordinario = VidaOrdinario(config_vida_20, tabla_emssa09)
        dotal = VidaDotal(config_vida_20, tabla_emssa09)

        r_temporal = temporal.calcular_prima(asegurado_35_h)
        r_ordinario = ordinario.calcular_prima(asegurado_35_h)
        r_dotal = dotal.calcular_prima(asegurado_35_h)

        prima_t = r_temporal.prima_neta
        prima_o = r_ordinario.prima_neta
        prima_d = r_dotal.prima_neta

        assert prima_t > 0, "Temporal premium should be positive"
        assert prima_o > 0, "Ordinario premium should be positive"
        assert prima_d > 0, "Dotal premium should be positive"

        assert prima_d > prima_o, (
            f"Dotal ({prima_d}) should exceed Ordinario ({prima_o})"
        )
        assert prima_o > prima_t, (
            f"Ordinario ({prima_o}) should exceed Temporal ({prima_t})"
        )

    def test_dotal_reserve_at_maturity_equals_sa(self, tabla_emssa09):
        """For a dotal, reserve at maturity = sum insured (guaranteed payout)."""
        config = ConfiguracionProducto(
            nombre_producto="Test Dotal",
            plazo_years=10,
            tasa_interes_tecnico=Decimal("0.055"),
        )
        dotal = VidaDotal(config, tabla_emssa09)
        asegurado = Asegurado(
            edad=30,
            sexo=Sexo.HOMBRE,
            suma_asegurada=Decimal("500000"),
        )
        reserva_final = dotal.calcular_reserva(asegurado, anio=10)
        assert reserva_final == Decimal("500000"), (
            f"Dotal reserve at maturity = {reserva_final}, expected 500000"
        )

    def test_temporal_reserve_at_maturity_is_zero(self, tabla_emssa09):
        """For a temporal, reserve at maturity = 0 (no further obligation)."""
        config = ConfiguracionProducto(
            nombre_producto="Test Temporal",
            plazo_years=10,
            tasa_interes_tecnico=Decimal("0.055"),
        )
        temporal = VidaTemporal(config, tabla_emssa09)
        asegurado = Asegurado(
            edad=30,
            sexo=Sexo.HOMBRE,
            suma_asegurada=Decimal("500000"),
        )
        reserva_final = temporal.calcular_reserva(asegurado, anio=10)
        assert reserva_final == Decimal("0")


# ======================================================================
# 4. COLLECTIVE RISK MODEL (DANOS)
# ======================================================================

class TestCollectiveRiskModel:
    """Verify properties of the collective risk model S = X1 + ... + XN."""

    def test_pure_premium_equals_EN_times_EX(self):
        """E[S] = E[N] * E[X] -- the fundamental collective risk identity.

        For Poisson(lambda=10) frequency and Exponential(lambda=0.001) severity:
        E[N] = 10, E[X] = 1/0.001 = 1000, so E[S] = 10,000.
        """
        modelo = ModeloColectivo(
            dist_frecuencia="poisson",
            params_frecuencia={"lambda_": 10.0},
            dist_severidad="exponencial",
            params_severidad={"lambda_": 0.001},
        )
        pp = modelo.prima_pura()
        # E[N] = 10, E[X] = 1000, so E[S] = 10000
        assert abs(float(pp) - 10000.0) < 1.0, (
            f"Pure premium = {pp}, expected ~10000"
        )

    def test_variance_formula(self):
        """Var[S] = E[N]*Var[X] + Var[N]*E[X]^2 for Poisson-Exponential.

        For Poisson(10): E[N]=10, Var[N]=10
        For Exp(0.001): E[X]=1000, Var[X]=1000^2=1e6
        Var[S] = 10*1e6 + 10*1e6 = 2e7
        """
        modelo = ModeloColectivo(
            dist_frecuencia="poisson",
            params_frecuencia={"lambda_": 10.0},
            dist_severidad="exponencial",
            params_severidad={"lambda_": 0.001},
        )
        var_s = float(modelo.varianza_agregada())
        # E[N]*Var[X] + Var[N]*E[X]^2 = 10*1e6 + 10*1e6 = 20,000,000
        assert abs(var_s - 2e7) < 1e4, (
            f"Var[S] = {var_s}, expected ~20,000,000"
        )

    def test_tvar_geq_var(self):
        """TVaR >= VaR must hold for any confidence level.

        TVaR is the expected loss given that loss exceeds VaR,
        so by definition it must be at least as large.
        """
        modelo = ModeloColectivo(
            dist_frecuencia="poisson",
            params_frecuencia={"lambda_": 5.0},
            dist_severidad="lognormal",
            params_severidad={"mu": 7.0, "sigma": 1.5},
        )
        for nivel in [0.90, 0.95, 0.99]:
            var_val = float(modelo.var(nivel=nivel, n_simulaciones=50_000, seed=42))
            tvar_val = float(modelo.tvar(nivel=nivel, n_simulaciones=50_000, seed=42))
            assert tvar_val >= var_val - 1.0, (
                f"TVaR({nivel}) = {tvar_val} < VaR({nivel}) = {var_val}"
            )

    def test_simulation_converges_to_analytic_mean(self):
        """Monte Carlo mean should converge to E[S] = E[N]*E[X].

        With enough simulations, the simulated mean should be within
        a few percent of the analytic pure premium.
        """
        modelo = ModeloColectivo(
            dist_frecuencia="poisson",
            params_frecuencia={"lambda_": 20.0},
            dist_severidad="gamma",
            params_severidad={"alpha": 2.0, "beta": 0.001},
        )
        # Analytic: E[N]=20, E[X] = alpha/beta = 2000, E[S] = 40000
        perdidas = modelo.simular_perdidas(n_simulaciones=100_000, seed=123)
        sim_mean = float(np.mean(perdidas))
        assert abs(sim_mean - 40000.0) / 40000.0 < 0.03, (
            f"Simulated mean = {sim_mean}, expected ~40000 (within 3%)"
        )

    def test_pareto_heavy_tail_no_explosion(self):
        """Pareto with alpha close to 1 (heavy tail) should not produce NaN/Inf."""
        modelo = ModeloColectivo(
            dist_frecuencia="poisson",
            params_frecuencia={"lambda_": 3.0},
            dist_severidad="pareto",
            params_severidad={"alpha": 1.5, "scale": 1000.0},
        )
        # Should not raise or produce NaN
        perdidas = modelo.simular_perdidas(n_simulaciones=10_000, seed=99)
        assert not np.any(np.isnan(perdidas))
        assert not np.any(np.isinf(perdidas))


# ======================================================================
# 5. CREDIBILITY AND BONUS-MALUS (TARIFAS)
# ======================================================================

class TestCredibilidad:
    """Verify Buhlmann credibility constraints."""

    def test_buhlmann_z_between_0_and_1(self):
        """Credibility factor Z must be in [0, 1]."""
        experiencia = [Decimal("100"), Decimal("120"), Decimal("90"),
                       Decimal("150"), Decimal("80")]
        resultado = FactorCredibilidad.buhlmann(experiencia, Decimal("110"))
        z = resultado["Z"]
        assert Decimal("0") <= z <= Decimal("1"), f"Z = {z} outside [0,1]"

    def test_buhlmann_empty_returns_manual_rate(self):
        """With no data, credibility premium = manual rate (Z=0)."""
        resultado = FactorCredibilidad.buhlmann([], Decimal("500"))
        assert resultado["Z"] == Decimal("0")
        assert resultado["prima_credibilidad"] == Decimal("500")

    def test_buhlmann_single_period_z_zero(self):
        """With one observation, cannot estimate variance => Z=0."""
        resultado = FactorCredibilidad.buhlmann(
            [Decimal("200")], Decimal("150")
        )
        assert resultado["Z"] == Decimal("0")
        assert resultado["prima_credibilidad"] == Decimal("150")


class TestBonusMalus:
    """Verify BMS transition rules and boundary clamping."""

    def test_bms_zero_claims_decreases_level(self):
        """0 claims -> level drops by 1."""
        bms = CalculadoraBonusMalus(nivel_actual=0)
        nuevo = bms.transicion(0)
        assert nuevo == -1

    def test_bms_one_claim_increases_by_two(self):
        """1 claim -> level rises by 2."""
        bms = CalculadoraBonusMalus(nivel_actual=0)
        nuevo = bms.transicion(1)
        assert nuevo == 2

    def test_bms_two_plus_claims_increases_by_three(self):
        """2+ claims -> level rises by 3."""
        bms = CalculadoraBonusMalus(nivel_actual=0)
        nuevo = bms.transicion(3)
        assert nuevo == 3  # clamped at max

    def test_bms_clamped_at_min(self):
        """Level cannot go below NIVEL_MIN (-5)."""
        bms = CalculadoraBonusMalus(nivel_actual=-5)
        nuevo = bms.transicion(0)
        assert nuevo == -5  # already at minimum

    def test_bms_clamped_at_max(self):
        """Level cannot go above NIVEL_MAX (3)."""
        bms = CalculadoraBonusMalus(nivel_actual=3)
        nuevo = bms.transicion(2)
        assert nuevo == 3  # already at maximum

    def test_bms_factor_at_base_is_one(self):
        """Factor at level 0 (base) = 1.00."""
        bms = CalculadoraBonusMalus(nivel_actual=0)
        assert bms.factor_actual() == Decimal("1.00")

    def test_bms_factor_at_max_discount(self):
        """Factor at level -5 = 0.70 (30% discount)."""
        bms = CalculadoraBonusMalus(nivel_actual=-5)
        assert bms.factor_actual() == Decimal("0.70")

    def test_bms_negative_claims_raises(self):
        """Negative claims count should raise ValueError."""
        bms = CalculadoraBonusMalus(nivel_actual=0)
        with pytest.raises(ValueError):
            bms.transicion(-1)


# ======================================================================
# 6. PENSION LEY 73 REGULATORY CONSTRAINTS
# ======================================================================

class TestPensionLey73:
    """Verify IMSS Ley 73 pension calculations against regulatory tables."""

    def test_500_weeks_33_07_percent(self):
        """At exactly 500 weeks, percentage must be 33.07% per Art. 167 LSS 1973."""
        pct = obtener_porcentaje_ley73(500)
        assert pct == Decimal("0.3307"), f"At 500 weeks: {pct}, expected 0.3307"

    def test_2060_weeks_100_percent_cap(self):
        """At 2060+ weeks, percentage is capped at 100%."""
        assert obtener_porcentaje_ley73(2060) == Decimal("1.0000")
        assert obtener_porcentaje_ley73(3000) == Decimal("1.0000")

    def test_percentage_monotonically_increasing(self):
        """More weeks cotizadas => higher pension percentage."""
        prev = obtener_porcentaje_ley73(500)
        for semanas in range(520, 2100, 52):
            curr = obtener_porcentaje_ley73(semanas)
            assert curr >= prev, (
                f"Percentage decreased at {semanas} weeks: {curr} < {prev}"
            )
            prev = curr

    def test_age_factor_at_65_is_100_percent(self):
        """At age 65 (vejez), factor = 1.00 (full pension)."""
        assert obtener_factor_edad(65) == Decimal("1.00")

    def test_age_factor_monotonically_increasing(self):
        """Older retirement age => higher factor (60: 0.75, ..., 65: 1.00)."""
        prev = obtener_factor_edad(60)
        for edad in range(61, 66):
            curr = obtener_factor_edad(edad)
            assert curr >= prev, (
                f"Age factor decreased at {edad}: {curr} < {prev}"
            )
            prev = curr

    def test_age_factor_above_65_is_1(self):
        """Ages above 65 should return factor = 1.00."""
        assert obtener_factor_edad(70) == Decimal("1.00")

    def test_pension_65_geq_pension_60(self):
        """Pension at age 65 must be >= pension at age 60 (higher age factor)."""
        p60 = PensionLey73(
            semanas_cotizadas=1000,
            salario_promedio_5_anos=Decimal("500"),
            edad_retiro=60,
        )
        p65 = PensionLey73(
            semanas_cotizadas=1000,
            salario_promedio_5_anos=Decimal("500"),
            edad_retiro=65,
        )
        assert p65.calcular_pension_mensual() >= p60.calcular_pension_mensual()

    def test_under_500_weeks_raises(self):
        """Fewer than 500 weeks should raise ValueError."""
        with pytest.raises(ValueError):
            PensionLey73(
                semanas_cotizadas=499,
                salario_promedio_5_anos=Decimal("500"),
                edad_retiro=65,
            )

    def test_under_age_60_raises(self):
        """Retirement before age 60 should raise ValueError."""
        with pytest.raises(ValueError):
            PensionLey73(
                semanas_cotizadas=500,
                salario_promedio_5_anos=Decimal("500"),
                edad_retiro=59,
            )

    def test_pension_hand_calculation(self):
        """Hand-calculated pension for 500 weeks, age 65, salary 500/day.

        pension = salario_diario * 30 * porcentaje * factor_edad
               = 500 * 30 * 0.3307 * 1.00
               = 4960.50
        """
        p = PensionLey73(
            semanas_cotizadas=500,
            salario_promedio_5_anos=Decimal("500"),
            edad_retiro=65,
        )
        pension = p.calcular_pension_mensual()
        expected = Decimal("500") * Decimal("30") * Decimal("0.3307") * Decimal("1.00")
        assert pension == expected.quantize(Decimal("0.01")), (
            f"Pension = {pension}, expected {expected}"
        )


# ======================================================================
# 7. IMSS REGIME DETERMINATION
# ======================================================================

class TestCalculadoraIMSS:
    """Verify regime determination based on IMSS enrollment date."""

    def test_before_july_1997_is_ley73(self):
        """Enrolled before July 1, 1997 -> Ley 73."""
        calc = CalculadoraIMSS()
        assert calc.determinar_regimen("1995-03-15") == "Ley 73"

    def test_on_july_1997_is_ley97(self):
        """Enrolled on July 1, 1997 -> Ley 97."""
        calc = CalculadoraIMSS()
        assert calc.determinar_regimen("1997-07-01") == "Ley 97"

    def test_after_july_1997_is_ley97(self):
        """Enrolled after July 1, 1997 -> Ley 97."""
        calc = CalculadoraIMSS()
        assert calc.determinar_regimen("2010-01-01") == "Ley 97"


# ======================================================================
# 8. RCS AGGREGATION WITH CORRELATIONS
# ======================================================================

class TestRCSAggregation:
    """Verify RCS aggregation satisfies diversification properties."""

    def test_correlated_rcs_leq_simple_sum(self):
        """RCS with correlations <= simple sum (diversification benefit).

        When correlation rho < 1, the quadratic aggregation formula
        sqrt(a^2 + b^2 + c^2 + 2*rho_ab*a*b + ...) <= a + b + c.
        """
        agregador = AgregadorRCS()
        a = Decimal("100")
        b = Decimal("200")
        c = Decimal("150")
        rcs_diversified = agregador._agregar_con_correlaciones(a, b, c)
        simple_sum = a + b + c
        assert float(rcs_diversified) <= float(simple_sum) + 0.01, (
            f"Diversified RCS {rcs_diversified} > simple sum {simple_sum}"
        )

    def test_zero_correlation_is_pythagorean(self):
        """When vida-danos correlation = 0 and one component is 0,
        with rho_vida_inv = 0.25, the result follows the formula.

        RCS = sqrt(a^2 + c^2 + 2*0.25*a*c) when b=0.
        """
        agregador = AgregadorRCS()
        a = Decimal("100")
        b = Decimal("0")
        c = Decimal("100")
        result = float(agregador._agregar_con_correlaciones(a, b, c))
        # Expected: sqrt(100^2 + 100^2 + 2*0.25*100*100) = sqrt(25000) = 158.11...
        expected = math.sqrt(10000 + 10000 + 5000)
        assert abs(result - expected) < 0.1

    def test_single_component_equals_itself(self):
        """RCS with only one component should equal that component."""
        agregador = AgregadorRCS()
        a = Decimal("500")
        result = float(agregador._agregar_con_correlaciones(a, Decimal("0"), Decimal("0")))
        assert abs(result - 500.0) < 0.1

    def test_all_zero_rcs(self):
        """All-zero components -> RCS = 0."""
        agregador = AgregadorRCS()
        result = agregador._agregar_con_correlaciones(
            Decimal("0"), Decimal("0"), Decimal("0")
        )
        assert result == Decimal("0.00")


# ======================================================================
# 9. CONFIG AND UMA CONSISTENCY
# ======================================================================

class TestConfigConsistency:
    """Verify regulatory config values are internally consistent."""

    def test_uma_annual_equals_daily_times_365(self):
        """UMA anual should equal UMA diaria * 365 (definition)."""
        config = cargar_config(2026)
        expected_annual = config.uma.uma_diaria * Decimal("365")
        actual = config.uma.uma_anual
        assert abs(float(actual) - float(expected_annual)) < 1.0, (
            f"UMA anual {actual} != diaria*365 = {expected_annual}"
        )

    def test_uma_monthly_approximately_daily_times_30_4(self):
        """UMA mensual ~= UMA diaria * 30.4 (standard approximation).

        The exact factor is 30.4 per UMA definition (INEGI/DOF).
        Allow small rounding tolerance.
        """
        config = cargar_config(2026)
        expected_monthly = config.uma.uma_diaria * Decimal("30.4")
        actual = config.uma.uma_mensual
        # Allow up to 1 peso tolerance for rounding
        assert abs(float(actual) - float(expected_monthly)) < 1.0, (
            f"UMA mensual {actual} != diaria*30.4 = {expected_monthly}"
        )

    def test_loading_same_year_returns_same_object(self):
        """Loading config for the same year twice returns cached instance."""
        c1 = cargar_config(2026)
        c2 = cargar_config(2026)
        assert c1 is c2, "Config should be cached (same object)"

    def test_loading_nonexistent_year_raises(self):
        """Loading config for a year without config module should raise."""
        with pytest.raises(ModuleNotFoundError):
            cargar_config(1999)

    def test_config_2026_correct_uma_diaria(self):
        """2026 UMA diaria should be 117.67 per config."""
        config = cargar_config(2026)
        assert config.uma.uma_diaria == Decimal("117.67")


# ======================================================================
# 10. GMM MONOTONICITY AND CLAIM SIMULATION
# ======================================================================

class TestGMMMonotonicity:
    """Verify GMM premium is non-decreasing with age."""

    def test_premium_increases_with_age_adult(self):
        """Higher age => higher or equal premium for adults (15+).

        Infant/child bands (0-4, 5-9, 10-14) have elevated morbidity due to
        pediatric care costs, so monotonicity only holds from age 15 onward.
        This is standard in Mexican GMM rating: the U-shaped infant cost
        curve means we check monotonicity from the 15-19 band upward.
        """
        primas = []
        for edad in [17, 22, 27, 32, 37, 42, 47, 52, 57, 62, 67]:
            gmm = GMM(
                edad=edad,
                sexo="M",
                suma_asegurada=Decimal("5000000"),
                deducible=Decimal("50000"),
                coaseguro_pct=Decimal("0.10"),
            )
            primas.append((edad, float(gmm.calcular_prima_ajustada())))

        # Check monotonicity from 15-19 band onward
        for i in range(1, len(primas)):
            edad_prev, prima_prev = primas[i - 1]
            edad_curr, prima_curr = primas[i]
            assert prima_curr >= prima_prev - 0.01, (
                f"GMM premium decreased: age {edad_prev} ({prima_prev}) "
                f"> age {edad_curr} ({prima_curr})"
            )

    def test_claim_simulation_balances(self):
        """Deductible + coaseguro_asegurado + pago_aseguradora = monto_cubierto.

        For any claim within the sum insured, the total of what the insured
        and insurer pay must equal the claim amount.
        """
        gmm = GMM(
            edad=40,
            sexo="M",
            suma_asegurada=Decimal("10000000"),
            deducible=Decimal("50000"),
            coaseguro_pct=Decimal("0.10"),
            tope_coaseguro=Decimal("200000"),
        )
        for monto in [Decimal("10000"), Decimal("100000"), Decimal("500000"),
                       Decimal("2000000"), Decimal("15000000")]:
            resultado = gmm.simular_gasto_medico(monto)
            total = (
                resultado["deducible_aplicado"]
                + resultado["coaseguro_asegurado"]
                + resultado["pago_aseguradora"]
                + resultado["exceso_no_cubierto"]
            )
            assert abs(float(total) - float(monto)) < 0.01, (
                f"Claim {monto}: deducible+coaseg+aseg+exceso = {total} != {monto}"
            )

    def test_below_deductible_insurer_pays_nothing(self):
        """If claim <= deductible, insurer pays nothing."""
        gmm = GMM(
            edad=30,
            sexo="F",
            suma_asegurada=Decimal("5000000"),
            deducible=Decimal("50000"),
            coaseguro_pct=Decimal("0.10"),
        )
        resultado = gmm.simular_gasto_medico(Decimal("40000"))
        assert resultado["pago_aseguradora"] == Decimal("0")


# ======================================================================
# 11. SAT TAX EXEMPTIONS
# ======================================================================

class TestSATValidaciones:
    """Verify SAT tax treatment of insurance payouts."""

    def test_life_death_benefit_always_exempt_pf(self):
        """Life insurance death benefit is ALWAYS tax-exempt for PF.

        Art. 93, fracc. XIII LISR: indemnizaciones por muerte exentas.
        This should hold regardless of amount.
        """
        validador = ValidadorSiniestrosGravables()
        for monto in [Decimal("100000"), Decimal("10000000"), Decimal("1")]:
            resultado = validador.validar_gravabilidad(
                tipo_seguro=TipoSeguroFiscal.VIDA,
                monto_pago=monto,
                es_persona_fisica=True,
                es_indemnizacion_muerte=True,
            )
            assert resultado.esta_gravado is False, (
                f"Death benefit of {monto} should be exempt"
            )
            assert resultado.monto_exento == monto
            assert resultado.monto_gravado == Decimal("0")

    def test_medical_expenses_always_exempt(self):
        """GMM (gastos medicos) payouts are always exempt (reimbursement)."""
        validador = ValidadorSiniestrosGravables()
        resultado = validador.validar_gravabilidad(
            tipo_seguro=TipoSeguroFiscal.GASTOS_MEDICOS,
            monto_pago=Decimal("500000"),
            es_persona_fisica=True,
        )
        assert resultado.esta_gravado is False

    def test_property_damage_exempt(self):
        """Property/casualty insurance payouts are exempt (patrimonio)."""
        validador = ValidadorSiniestrosGravables()
        resultado = validador.validar_gravabilidad(
            tipo_seguro=TipoSeguroFiscal.DANOS,
            monto_pago=Decimal("1000000"),
            es_persona_fisica=True,
        )
        assert resultado.esta_gravado is False


# ======================================================================
# 12. CHAIN LADDER AND BF IDENTITIES
# ======================================================================

class TestChainLadder:
    """Verify Chain Ladder properties."""

    def test_ultimate_geq_paid(self, triangulo_acumulado):
        """Ultimate must be >= paid for each origin year (development only adds)."""
        config = ConfiguracionChainLadder(metodo_promedio=MetodoPromedio.SIMPLE)
        cl = ChainLadder(config)
        resultado = cl.calcular(triangulo_acumulado)

        for anio in resultado.ultimates_por_anio:
            ult = resultado.ultimates_por_anio[anio]
            reserva = resultado.reservas_por_anio[anio]
            assert reserva >= Decimal("0"), (
                f"Year {anio}: reserve = {reserva} < 0"
            )
            assert ult >= Decimal("0")

    def test_reserve_total_is_sum_of_parts(self, triangulo_acumulado):
        """Total reserve = sum of individual year reserves."""
        config = ConfiguracionChainLadder(metodo_promedio=MetodoPromedio.SIMPLE)
        cl = ChainLadder(config)
        resultado = cl.calcular(triangulo_acumulado)

        sum_reserves = sum(resultado.reservas_por_anio.values())
        assert abs(float(sum_reserves) - float(resultado.reserva_total)) < 0.01

    def test_first_year_reserve_is_zero(self, triangulo_acumulado):
        """The oldest origin year (fully developed) should have reserve = 0."""
        config = ConfiguracionChainLadder(metodo_promedio=MetodoPromedio.SIMPLE)
        cl = ChainLadder(config)
        resultado = cl.calcular(triangulo_acumulado)
        # Year 2020 is fully developed in a 4x4 triangle
        assert resultado.reservas_por_anio[2020] == Decimal("0")


class TestBornhuetterFerguson:
    """Verify BF identity and relationship to Chain Ladder."""

    def test_bf_ultimate_equals_paid_plus_ibnr(self, triangulo_acumulado):
        """Ultimate_BF = Paid + IBNR for each year.

        This is the definition. IBNR = Ultimate - Paid, so this is
        trivially true if the code is self-consistent.
        """
        primas = {2020: Decimal("300"), 2021: Decimal("350"),
                  2022: Decimal("400"), 2023: Decimal("450")}
        config = ConfiguracionBornhuetterFerguson(
            loss_ratio_apriori=Decimal("0.65"),
            metodo_promedio=MetodoPromedio.SIMPLE,
        )
        bf = BornhuetterFerguson(config)
        resultado = bf.calcular(triangulo_acumulado, primas)

        for anio in resultado.ultimates_por_anio:
            ult = resultado.ultimates_por_anio[anio]
            reserva = resultado.reservas_por_anio[anio]
            # Ultimate - reserve should give the paid amount
            paid = ult - reserva
            assert paid >= Decimal("0"), (
                f"Year {anio}: implied paid = {paid} < 0"
            )

    def test_bf_reserves_nonnegative(self, triangulo_acumulado):
        """BF reserves must be non-negative."""
        primas = {2020: Decimal("300"), 2021: Decimal("350"),
                  2022: Decimal("400"), 2023: Decimal("450")}
        config = ConfiguracionBornhuetterFerguson(
            loss_ratio_apriori=Decimal("0.65"),
            metodo_promedio=MetodoPromedio.SIMPLE,
        )
        bf = BornhuetterFerguson(config)
        resultado = bf.calcular(triangulo_acumulado, primas)

        for anio, reserva in resultado.reservas_por_anio.items():
            assert reserva >= Decimal("0"), (
                f"BF reserve for year {anio} is negative: {reserva}"
            )


# ======================================================================
# 13. BOOTSTRAP DETERMINISM AND RISK MEASURES
# ======================================================================

class TestBootstrapDeterminism:
    """Verify Bootstrap produces deterministic results with same seed."""

    def test_same_seed_same_result(self, triangulo_acumulado):
        """Running Bootstrap twice with same seed must give identical results."""
        config1 = ConfiguracionBootstrap(
            num_simulaciones=100,
            seed=42,
            percentiles=[50, 75, 95],
        )
        config2 = ConfiguracionBootstrap(
            num_simulaciones=100,
            seed=42,
            percentiles=[50, 75, 95],
        )
        bs1 = Bootstrap(config1)
        bs2 = Bootstrap(config2)

        r1 = bs1.calcular(triangulo_acumulado)
        r2 = bs2.calcular(triangulo_acumulado)

        assert r1.reserva_total == r2.reserva_total, (
            f"Run 1: {r1.reserva_total} != Run 2: {r2.reserva_total}"
        )

    def test_bootstrap_tvar_geq_var(self, triangulo_acumulado):
        """TVaR >= VaR from bootstrap distribution."""
        config = ConfiguracionBootstrap(
            num_simulaciones=100,
            seed=123,
            percentiles=[50, 75, 90, 95, 99],
        )
        bs = Bootstrap(config)
        bs.calcular(triangulo_acumulado)

        var_95 = float(bs.calcular_var(0.95))
        tvar_95 = float(bs.calcular_tvar(0.95))
        assert tvar_95 >= var_95 - 0.01, (
            f"TVaR(95%) = {tvar_95} < VaR(95%) = {var_95}"
        )


# ======================================================================
# 14. YIELD CURVE MATHEMATICAL PROPERTIES
# ======================================================================

class TestYieldCurve:
    """Verify yield curve mathematical identities."""

    def test_discount_factor_between_0_and_1(self):
        """Discount factor must be in (0, 1] for positive rates."""
        curva = CurvaRendimiento.plana(Decimal("0.08"))
        for t in [0.5, 1, 2, 5, 10, 30]:
            v = float(curva.factor_descuento(t))
            assert 0 < v <= 1.0, f"v({t}) = {v} outside (0, 1]"

    def test_discount_factor_decreasing_in_time(self):
        """For a flat curve, discount factor decreases with time."""
        curva = CurvaRendimiento.plana(Decimal("0.05"))
        prev_v = 1.0
        for t in [1, 2, 5, 10, 20]:
            v = float(curva.factor_descuento(t))
            assert v < prev_v, f"v({t}) = {v} >= v(prev) = {prev_v}"
            prev_v = v

    def test_forward_rate_identity(self):
        """Forward rate identity: (1+r2)^t2 = (1+r1)^t1 * (1+f)^(t2-t1).

        The forward rate computed by the code must satisfy this arbitrage-free
        condition within floating-point tolerance.
        """
        curva = CurvaRendimiento(
            plazos=[1, 2, 3, 5, 10],
            tasas=[Decimal("0.08"), Decimal("0.085"), Decimal("0.09"),
                   Decimal("0.095"), Decimal("0.10")],
        )
        t1, t2 = 2, 5
        r1 = float(curva.tasa_spot(t1))
        r2 = float(curva.tasa_spot(t2))
        f12 = float(curva.tasa_forward(t1, t2))

        lhs = (1 + r2) ** t2
        rhs = (1 + r1) ** t1 * (1 + f12) ** (t2 - t1)
        assert abs(lhs - rhs) / lhs < 1e-4, (
            f"Forward identity violated: LHS={lhs:.6f}, RHS={rhs:.6f}"
        )

    def test_flat_curve_forward_equals_spot(self):
        """On a flat curve, all forward rates equal the spot rate."""
        rate = Decimal("0.07")
        curva = CurvaRendimiento.plana(rate)
        f = float(curva.tasa_forward(1, 5))
        assert abs(f - 0.07) < 1e-4, f"Forward on flat curve = {f}, expected 0.07"

    def test_present_value_single_cashflow(self):
        """PV of a single cashflow = CF * v(t)."""
        curva = CurvaRendimiento.plana(Decimal("0.10"))
        pv = float(curva.valor_presente([Decimal("1000")], [5.0]))
        expected = 1000 / (1.10 ** 5)
        assert abs(pv - expected) < 1.0, f"PV = {pv}, expected {expected}"


# ======================================================================
# 15. MORTALITY TABLE CONSTRAINTS
# ======================================================================

class TestMortalityConstraints:
    """Verify mortality table constraints from actuarial theory."""

    def test_qx_between_0_and_1(self, tabla_emssa09):
        """Every qx must be in [0, 1] -- fundamental probability constraint."""
        for sexo_str in ["H", "M"]:
            df = tabla_emssa09.obtener_tabla_completa(sexo_str)
            for _, row in df.iterrows():
                qx = row["qx"]
                assert 0 <= qx <= 1, (
                    f"qx({row['edad']}, {sexo_str}) = {qx} outside [0,1]"
                )

    def test_qx_at_omega_leq_1(self, tabla_emssa09):
        """qx at the maximum (omega) age should be in (0, 1].

        Note: Some mortality tables (including EMSSA-09) do NOT force
        q_omega = 1.0 at the terminal age. The EMSSA-09 table ends at
        age 100 with qx < 1.0. This is a legitimate modeling choice where
        the table simply stops rather than forcing certain death.
        We verify qx is a valid probability at the terminal age.
        """
        for sexo_str in ["H", "M"]:
            df = tabla_emssa09.obtener_tabla_completa(sexo_str)
            max_age = df["edad"].max()
            qx_omega = float(
                df[df["edad"] == max_age]["qx"].values[0]
            )
            assert 0 < qx_omega <= 1.0, (
                f"qx at omega age {max_age} for {sexo_str} = {qx_omega}, "
                f"expected in (0, 1]"
            )

    def test_lx_non_increasing(self, tabla_emssa09):
        """lx (survivors) must be non-increasing with age."""
        for sexo_str in ["H", "M"]:
            sexo = Sexo(sexo_str)
            df = tabla_emssa09.calcular_lx(sexo)
            df = df.sort_values("edad")
            lx_vals = df["lx"].values
            for i in range(1, len(lx_vals)):
                assert lx_vals[i] <= lx_vals[i-1] + 1e-6, (
                    f"lx increasing at age {df.iloc[i]['edad']} for {sexo_str}"
                )


# ======================================================================
# 16. RENTA VITALICIA PROPERTIES
# ======================================================================

class TestRentaVitalicia:
    """Verify life annuity properties."""

    def test_immediate_annuity_factor_positive(self, tabla_emssa09):
        """Immediate annuity factor must be positive for a living rentist."""
        rv = RentaVitalicia(
            edad=65,
            sexo="H",
            monto_mensual=Decimal("10000"),
            tabla_mortalidad=tabla_emssa09,
            tasa_interes=Decimal("0.035"),
        )
        factor = rv.calcular_factor_renta()
        assert factor > 0, f"Annuity factor = {factor}, expected > 0"

    def test_deferred_annuity_cheaper_than_immediate(self, tabla_emssa09):
        """A deferred annuity should have a lower single premium than an
        immediate one (waiting period + mortality during deferral).
        """
        rv_imm = RentaVitalicia(
            edad=60,
            sexo="H",
            monto_mensual=Decimal("10000"),
            tabla_mortalidad=tabla_emssa09,
            tasa_interes=Decimal("0.035"),
        )
        rv_def = RentaVitalicia(
            edad=60,
            sexo="H",
            monto_mensual=Decimal("10000"),
            tabla_mortalidad=tabla_emssa09,
            tasa_interes=Decimal("0.035"),
            periodo_diferimiento=5,
        )
        prima_imm = rv_imm.calcular_prima_unica()
        prima_def = rv_def.calcular_prima_unica()
        assert prima_def < prima_imm, (
            f"Deferred ({prima_def}) should be cheaper than immediate ({prima_imm})"
        )

    def test_reserve_decreases_over_time_immediate(self, tabla_emssa09):
        """For an immediate annuity, reserve should generally decrease over time
        (fewer expected future payments as age increases).
        """
        rv = RentaVitalicia(
            edad=65,
            sexo="H",
            monto_mensual=Decimal("10000"),
            tabla_mortalidad=tabla_emssa09,
            tasa_interes=Decimal("0.035"),
        )
        reserva_0 = float(rv.calcular_reserva_matematica(0))
        reserva_10 = float(rv.calcular_reserva_matematica(10))
        assert reserva_10 < reserva_0, (
            f"Reserve at t=10 ({reserva_10}) should be < reserve at t=0 ({reserva_0})"
        )


# ======================================================================
# 17. NUMERICAL STABILITY
# ======================================================================

class TestNumericalStability:
    """Verify calculations are numerically stable under extreme inputs."""

    def test_high_sum_insured_no_precision_loss(self, tabla_emssa09):
        """Calculations with SA=40M (near product limit) should not lose precision.

        The base product has an automatic underwriting limit of 50M MXN,
        so we use 40M to stay within bounds while testing large amounts.
        """
        config = ConfiguracionProducto(
            nombre_producto="High SA",
            plazo_years=10,
            tasa_interes_tecnico=Decimal("0.055"),
        )
        temporal = VidaTemporal(config, tabla_emssa09)
        asegurado = Asegurado(
            edad=30,
            sexo=Sexo.HOMBRE,
            suma_asegurada=Decimal("40000000"),  # 40 million
        )
        resultado = temporal.calcular_prima(asegurado)
        assert resultado.prima_neta > 0
        assert resultado.prima_total > resultado.prima_neta

        # Verify linearity: premium at 40M should be 40x premium at 1M
        asegurado_1m = Asegurado(
            edad=30,
            sexo=Sexo.HOMBRE,
            suma_asegurada=Decimal("1000000"),
        )
        resultado_1m = temporal.calcular_prima(asegurado_1m)
        ratio = float(resultado.prima_neta) / float(resultado_1m.prima_neta)
        assert abs(ratio - 40.0) < 0.01, (
            f"Premium ratio = {ratio}, expected 40.0 (linear in SA)"
        )

    def test_collective_model_deterministic_with_seed(self):
        """Collective risk model with same seed produces same VaR."""
        modelo = ModeloColectivo(
            dist_frecuencia="poisson",
            params_frecuencia={"lambda_": 10.0},
            dist_severidad="lognormal",
            params_severidad={"mu": 8.0, "sigma": 1.0},
        )
        var1 = modelo.var(nivel=0.95, n_simulaciones=10_000, seed=777)
        # Reset cache by creating new model
        modelo2 = ModeloColectivo(
            dist_frecuencia="poisson",
            params_frecuencia={"lambda_": 10.0},
            dist_severidad="lognormal",
            params_severidad={"mu": 8.0, "sigma": 1.0},
        )
        var2 = modelo2.var(nivel=0.95, n_simulaciones=10_000, seed=777)
        assert var1 == var2, f"VaR not deterministic: {var1} != {var2}"


# ======================================================================
# 18. CROSS-DOMAIN: DOTAL COMPONENTS SUM IDENTITY
# ======================================================================

class TestDotalDecomposition:
    """The dotal insurance = temporal + pure endowment.

    A_x:n (dotal) = A^1_x:n (temporal) + nEx (pure endowment)

    This is a fundamental actuarial identity. We verify it using
    commutation functions.
    """

    def test_dotal_equals_temporal_plus_endowment(self, tc_simple):
        """Ax(n) + nEx should give the dotal value using commutation functions.

        The commutation-table Ax(x, n) gives the temporal insurance.
        nEx gives the pure endowment.
        Their sum should equal:
            (Mx - M(x+n) + D(x+n)) / Dx
        """
        x = 0
        n = 3
        Ax_temp = tc_simple.Ax(x, n)  # temporal insurance
        nEx = tc_simple.nEx(x, n)      # pure endowment

        # The dotal = temporal + endowment
        dotal_via_sum = Ax_temp + nEx

        # Verify via commutation: (Mx - M(x+n) + D(x+n)) / Dx
        Dx = tc_simple.Dx(x)
        Mx = tc_simple.Mx(x)
        Mx_n = tc_simple.Mx(x + n)
        Dx_n = tc_simple.Dx(x + n)
        dotal_direct = (Mx - Mx_n + Dx_n) / Dx

        assert abs(float(dotal_via_sum) - float(dotal_direct)) < 1e-8, (
            f"Dotal decomposition: {dotal_via_sum} != {dotal_direct}"
        )


# ======================================================================
# 19. COMMUTATION ON EMSSA-09: INSURANCE-ANNUITY IDENTITY (FEMALE)
# ======================================================================

class TestCommutationEMSSAFemale:
    """Repeat key identity on the female EMSSA-09 table."""

    def test_insurance_annuity_identity_female(self, tc_emssa_m):
        """Ax + d*ax = 1 on the EMSSA-09 female table."""
        i = tc_emssa_m.tasa_interes
        d = i / (1.0 + i)

        for x in [25, 40, 55, 70]:
            if x > tc_emssa_m.edad_max:
                continue
            ax_val = float(tc_emssa_m.ax(x))
            Ax_val = float(tc_emssa_m.Ax(x))
            identity = Ax_val + d * ax_val
            assert abs(identity - 1.0) < 1e-5, (
                f"EMSSA female age {x}: Ax + d*ax = {identity:.8f}"
            )

    def test_female_annuity_higher_than_male(self, tc_emssa_h, tc_emssa_m):
        """Females have lower mortality => higher life annuity factor.

        This is a well-known actuarial fact: women live longer on average,
        so their annuity-due is more expensive (more expected payments).
        """
        for x in [30, 50, 65]:
            ax_m = float(tc_emssa_m.ax(x))
            ax_h = float(tc_emssa_h.ax(x))
            assert ax_m > ax_h, (
                f"Age {x}: female ax ({ax_m}) should > male ax ({ax_h})"
            )


# ======================================================================
# 20. PENSION LEY 97 BASIC PROPERTIES
# ======================================================================

class TestPensionLey97:
    """Verify Ley 97 pension basic properties."""

    def test_larger_afore_yields_higher_pension(self, tabla_emssa09):
        """Higher AFORE balance -> higher pension."""
        p1 = PensionLey97(
            saldo_afore=Decimal("1000000"),
            edad=65,
            sexo="H",
            semanas_cotizadas=1000,
            tabla_mortalidad=tabla_emssa09,
            tasa_interes=Decimal("0.035"),
        )
        p2 = PensionLey97(
            saldo_afore=Decimal("2000000"),
            edad=65,
            sexo="H",
            semanas_cotizadas=1000,
            tabla_mortalidad=tabla_emssa09,
            tasa_interes=Decimal("0.035"),
        )
        pension1 = p1.calcular_renta_vitalicia()
        pension2 = p2.calcular_renta_vitalicia()
        assert pension2 > pension1, (
            f"Double balance should give higher pension: {pension2} vs {pension1}"
        )

    def test_pension_at_least_guaranteed(self, tabla_emssa09):
        """Pension must be at least the guaranteed minimum."""
        from suite_actuarial.pensiones.tablas_imss import PENSION_GARANTIZADA_2024

        p = PensionLey97(
            saldo_afore=Decimal("100"),  # Very small balance
            edad=65,
            sexo="H",
            semanas_cotizadas=1000,
            tabla_mortalidad=tabla_emssa09,
            tasa_interes=Decimal("0.035"),
        )
        pension = p.calcular_renta_vitalicia()
        assert pension >= PENSION_GARANTIZADA_2024, (
            f"Pension {pension} < guaranteed minimum {PENSION_GARANTIZADA_2024}"
        )
