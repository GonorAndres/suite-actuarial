"""
Cross-validation tests: loop-based pricing vs commutation-based pricing.

Verifies that calcular_seguro_vida / calcular_anualidad (loop over ages)
produce the same results as TablaConmutacion.Ax / .ax (commutation columns).
"""

from decimal import Decimal

import pytest

from suite_actuarial.actuarial.pricing.vida_pricing import (
    calcular_anualidad,
    calcular_prima_neta_temporal,
    calcular_seguro_vida,
)
from suite_actuarial.core.validators import Sexo

TASA = Decimal("0.055")
SEXO = Sexo.HOMBRE
REL_TOL = Decimal("1e-6")


def _rel_close(a: Decimal, b: Decimal, tol: Decimal = REL_TOL) -> bool:
    """True when a and b agree within relative tolerance."""
    avg = (abs(a) + abs(b)) / 2
    if avg == 0:
        return a == b
    return abs(a - b) / avg < tol


# ------------------------------------------------------------------
# Insurance A[x:n] cross-validation
# ------------------------------------------------------------------

class TestInsuranceCrossValidation:

    @pytest.mark.parametrize("edad", [25, 35, 50, 65])
    @pytest.mark.parametrize("plazo", [1, 10, 20])
    def test_Axn_loop_vs_commutation(
        self, tabla_emssa09, tabla_conmutacion_hombre, edad, plazo
    ):
        if edad + plazo > tabla_conmutacion_hombre.edad_max:
            pytest.skip("edad + plazo exceeds omega")

        loop_val = calcular_seguro_vida(
            tabla_emssa09, edad, SEXO, plazo, TASA, Decimal("1")
        )
        comm_val = tabla_conmutacion_hombre.Ax(edad, plazo)

        assert _rel_close(loop_val, comm_val), (
            f"A[{edad}:{plazo}] loop={loop_val} comm={comm_val}"
        )

    @pytest.mark.parametrize("edad", [25, 40, 60])
    def test_max_plazo_Ax_loop_vs_commutation(
        self, tabla_emssa09, tabla_conmutacion_hombre, edad
    ):
        """Loop with plazo = omega - edad covers ages [x, omega-1].
        Compare against temporal commutation Ax(x, plazo), not whole-life."""
        omega = tabla_conmutacion_hombre.edad_max
        plazo = omega - edad

        loop_val = calcular_seguro_vida(
            tabla_emssa09, edad, SEXO, plazo, TASA, Decimal("1")
        )
        comm_val = tabla_conmutacion_hombre.Ax(edad, plazo)

        assert _rel_close(loop_val, comm_val), (
            f"A[{edad}:{plazo}] loop={loop_val} comm={comm_val}"
        )

    def test_Ax_single_year(self, tabla_emssa09, tabla_conmutacion_hombre):
        for edad in [30, 50, 80]:
            loop_val = calcular_seguro_vida(
                tabla_emssa09, edad, SEXO, 1, TASA, Decimal("1")
            )
            comm_val = tabla_conmutacion_hombre.Ax(edad, 1)
            assert _rel_close(loop_val, comm_val), (
                f"A[{edad}:1] loop={loop_val} comm={comm_val}"
            )


# ------------------------------------------------------------------
# Annuity a[x:n] cross-validation
# ------------------------------------------------------------------

class TestAnnuityCrossValidation:

    @pytest.mark.parametrize("edad", [25, 35, 50, 65])
    @pytest.mark.parametrize("plazo", [1, 10, 20])
    def test_axn_loop_vs_commutation(
        self, tabla_emssa09, tabla_conmutacion_hombre, edad, plazo
    ):
        if edad + plazo > tabla_conmutacion_hombre.edad_max:
            pytest.skip("edad + plazo exceeds omega")

        loop_val = calcular_anualidad(
            tabla_emssa09, edad, SEXO, plazo, TASA, pago_anticipado=True
        )
        comm_val = tabla_conmutacion_hombre.ax(edad, plazo)

        assert _rel_close(loop_val, comm_val), (
            f"a[{edad}:{plazo}] loop={loop_val} comm={comm_val}"
        )

    @pytest.mark.parametrize("edad", [25, 40, 60])
    def test_max_plazo_ax_loop_vs_commutation(
        self, tabla_emssa09, tabla_conmutacion_hombre, edad
    ):
        """Loop with plazo = omega - edad. Compare against temporal commutation."""
        omega = tabla_conmutacion_hombre.edad_max
        plazo = omega - edad

        loop_val = calcular_anualidad(
            tabla_emssa09, edad, SEXO, plazo, TASA, pago_anticipado=True
        )
        comm_val = tabla_conmutacion_hombre.ax(edad, plazo)

        assert _rel_close(loop_val, comm_val), (
            f"a[{edad}:{plazo}] loop={loop_val} comm={comm_val}"
        )

    def test_annuity_single_year(self, tabla_emssa09, tabla_conmutacion_hombre):
        for edad in [30, 50, 80]:
            loop_val = calcular_anualidad(
                tabla_emssa09, edad, SEXO, 1, TASA, pago_anticipado=True
            )
            comm_val = tabla_conmutacion_hombre.ax(edad, 1)
            assert _rel_close(loop_val, comm_val), (
                f"a[{edad}:1] loop={loop_val} comm={comm_val}"
            )


# ------------------------------------------------------------------
# Insurance-annuity identity: Ax:n + d * ax:n + nEx = 1
# ------------------------------------------------------------------

class TestInsuranceAnnuityIdentity:

    @pytest.mark.parametrize("edad", [25, 35, 50, 65])
    def test_identity_commutation_whole_life(self, tabla_conmutacion_hombre, edad):
        """Whole-life identity via commutation: Ax + d * ax = 1."""
        i = TASA
        d = i / (Decimal("1") + i)

        Ax = tabla_conmutacion_hombre.Ax(edad, None)
        ax = tabla_conmutacion_hombre.ax(edad, None)

        lhs = Ax + d * ax
        assert _rel_close(lhs, Decimal("1")), (
            f"Identity at {edad}: Ax + d*ax = {lhs} (expected 1)"
        )

    @pytest.mark.parametrize("edad", [25, 35, 50, 65])
    @pytest.mark.parametrize("plazo", [10, 20])
    def test_temporal_identity_loop(
        self, tabla_emssa09, tabla_conmutacion_hombre, edad, plazo
    ):
        """Temporal identity via loop: Ax:n + d * ax:n + nEx = 1."""
        if edad + plazo > tabla_conmutacion_hombre.edad_max:
            pytest.skip("edad + plazo exceeds omega")

        i = TASA
        d = i / (Decimal("1") + i)

        Ax_loop = calcular_seguro_vida(
            tabla_emssa09, edad, SEXO, plazo, TASA, Decimal("1")
        )
        ax_loop = calcular_anualidad(
            tabla_emssa09, edad, SEXO, plazo, TASA, pago_anticipado=True
        )
        nEx = tabla_conmutacion_hombre.nEx(edad, plazo)

        lhs = Ax_loop + d * ax_loop + nEx
        assert _rel_close(lhs, Decimal("1"), Decimal("1e-5")), (
            f"Temporal identity at {edad}:{plazo}: "
            f"Ax + d*ax + nEx = {lhs} (expected 1)"
        )

    @pytest.mark.parametrize("edad", [30, 45])
    @pytest.mark.parametrize("plazo", [10, 20])
    def test_temporal_identity_commutation(
        self, tabla_conmutacion_hombre, edad, plazo
    ):
        """Temporal identity via commutation: Ax:n + d * ax:n + nEx = 1."""
        if edad + plazo > tabla_conmutacion_hombre.edad_max:
            pytest.skip("edad + plazo exceeds omega")

        i = TASA
        d = i / (Decimal("1") + i)

        Ax = tabla_conmutacion_hombre.Ax(edad, plazo)
        ax = tabla_conmutacion_hombre.ax(edad, plazo)
        nEx = tabla_conmutacion_hombre.nEx(edad, plazo)

        lhs = Ax + d * ax + nEx
        assert _rel_close(lhs, Decimal("1"), Decimal("1e-5")), (
            f"Temporal identity at {edad}:{plazo}: "
            f"Ax + d*ax + nEx = {lhs} (expected 1)"
        )


# ------------------------------------------------------------------
# Net premium cross-validation
# ------------------------------------------------------------------

class TestNetPremiumCrossValidation:

    @pytest.mark.parametrize("edad", [30, 45])
    @pytest.mark.parametrize("plazo", [10, 20])
    def test_prima_loop_vs_commutation(
        self, tabla_emssa09, tabla_conmutacion_hombre, edad, plazo
    ):
        if edad + plazo > tabla_conmutacion_hombre.edad_max:
            pytest.skip("edad + plazo exceeds omega")

        loop_prima = calcular_prima_neta_temporal(
            tabla_emssa09, edad, SEXO,
            plazo_seguro=plazo, plazo_pago=plazo,
            tasa_interes=TASA, suma_asegurada=Decimal("1"),
        )
        comm_prima = tabla_conmutacion_hombre.Px(edad, plazo)

        assert _rel_close(loop_prima, comm_prima), (
            f"P[{edad}:{plazo}] loop={loop_prima} comm={comm_prima}"
        )


# ------------------------------------------------------------------
# Boundary cases
# ------------------------------------------------------------------

class TestBoundaryCases:

    def test_age_18_long_plazo(self, tabla_emssa09, tabla_conmutacion_hombre):
        edad = 18
        omega = tabla_conmutacion_hombre.edad_max
        plazo = omega - edad

        loop_A = calcular_seguro_vida(
            tabla_emssa09, edad, SEXO, plazo, TASA, Decimal("1")
        )
        comm_A = tabla_conmutacion_hombre.Ax(edad, plazo)
        assert _rel_close(loop_A, comm_A), (
            f"A[18:{plazo}] loop={loop_A} comm={comm_A}"
        )

        loop_a = calcular_anualidad(
            tabla_emssa09, edad, SEXO, plazo, TASA, pago_anticipado=True
        )
        comm_a = tabla_conmutacion_hombre.ax(edad, plazo)
        assert _rel_close(loop_a, comm_a), (
            f"a[18:{plazo}] loop={loop_a} comm={comm_a}"
        )

    def test_age_90_plazo_1(self, tabla_emssa09, tabla_conmutacion_hombre):
        loop_A = calcular_seguro_vida(
            tabla_emssa09, 90, SEXO, 1, TASA, Decimal("1")
        )
        comm_A = tabla_conmutacion_hombre.Ax(90, 1)
        assert _rel_close(loop_A, comm_A), (
            f"A[90:1] loop={loop_A} comm={comm_A}"
        )

    def test_age_90_plazo_10(self, tabla_emssa09, tabla_conmutacion_hombre):
        loop_A = calcular_seguro_vida(
            tabla_emssa09, 90, SEXO, 10, TASA, Decimal("1")
        )
        comm_A = tabla_conmutacion_hombre.Ax(90, 10)
        assert _rel_close(loop_A, comm_A), (
            f"A[90:10] loop={loop_A} comm={comm_A}"
        )

        loop_a = calcular_anualidad(
            tabla_emssa09, 90, SEXO, 10, TASA, pago_anticipado=True
        )
        comm_a = tabla_conmutacion_hombre.ax(90, 10)
        assert _rel_close(loop_a, comm_a), (
            f"a[90:10] loop={loop_a} comm={comm_a}"
        )

    def test_insurance_positive(self, tabla_conmutacion_hombre):
        for edad in [18, 50, 90]:
            val = tabla_conmutacion_hombre.Ax(edad, 10)
            assert val > 0, f"A[{edad}:10] should be positive, got {val}"

    def test_annuity_at_least_one(self, tabla_conmutacion_hombre):
        for edad in [18, 50, 90]:
            val = tabla_conmutacion_hombre.ax(edad, 10)
            assert val >= Decimal("1"), (
                f"a[{edad}:10] due should be >= 1 (first payment certain), got {val}"
            )
