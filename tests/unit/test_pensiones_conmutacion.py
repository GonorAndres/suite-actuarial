"""
Tests para funciones de conmutacion actuarial.

Verifica Dx, Nx, Cx, Mx, ax, Ax, nEx, Px, tVx contra
propiedades matematicas conocidas y la tabla EMSSA-09.
"""

from decimal import Decimal

import pandas as pd
import pytest

from suite_actuarial.actuarial.mortality.tablas import TablaMortalidad
from suite_actuarial.pensiones.conmutacion import TablaConmutacion

# ======================================================================
# Fixtures
# ======================================================================


@pytest.fixture
def tabla_simple():
    """Small synthetic mortality table for deterministic tests."""
    datos = pd.DataFrame(
        {
            "edad": list(range(0, 6)) + list(range(0, 6)),
            "sexo": ["H"] * 6 + ["M"] * 6,
            "qx": [
                0.01,
                0.02,
                0.03,
                0.05,
                0.10,
                1.00,  # H: omega=5
                0.005,
                0.01,
                0.02,
                0.03,
                0.05,
                1.00,  # M: omega=5
            ],
        }
    )
    return TablaMortalidad(nombre="Simple", datos=datos)


@pytest.fixture
def tc_simple(tabla_simple):
    """Commutation table from the simple mortality table at 5%."""
    return TablaConmutacion(tabla_simple, sexo="H", tasa_interes=0.05, raiz=100_000)


@pytest.fixture
def tc_simple_mujer(tabla_simple):
    """Commutation table for women."""
    return TablaConmutacion(tabla_simple, sexo="M", tasa_interes=0.05, raiz=100_000)


@pytest.fixture
def tabla_emssa09():
    """Load EMSSA-09 table."""
    try:
        return TablaMortalidad.cargar_emssa09()
    except FileNotFoundError:
        pytest.skip("EMSSA-09 table not available")


@pytest.fixture
def tc_emssa_h(tabla_emssa09):
    """EMSSA-09, male, 5.5% interest."""
    return TablaConmutacion(tabla_emssa09, sexo="H", tasa_interes=0.055)


@pytest.fixture
def tc_emssa_m(tabla_emssa09):
    """EMSSA-09, female, 5.5% interest."""
    return TablaConmutacion(tabla_emssa09, sexo="M", tasa_interes=0.055)


# ======================================================================
# Tests: basic commutation values
# ======================================================================


class TestCommutationBasic:
    """Verify fundamental commutation function properties."""

    def test_Dx_at_age_zero(self, tc_simple):
        """D0 = l0 * v^0 = l0 = raiz."""
        # v^0 = 1, so D0 = raiz * 1 = 100_000
        d0 = tc_simple.Dx(0)
        assert d0 == Decimal("100000.0")

    def test_Dx_decreases_with_age(self, tc_simple):
        """Dx must decrease with age (fewer survivors + more discounting)."""
        for x in range(tc_simple.edad_min, tc_simple.edad_max):
            assert tc_simple.Dx(x) > tc_simple.Dx(x + 1)

    def test_Nx_is_sum_of_Dx(self, tc_simple):
        """Nx should equal sum of Dx from x to omega."""
        # N0 = D0 + D1 + D2 + D3 + D4 + D5
        suma = sum(float(tc_simple.Dx(x)) for x in range(0, 6))
        n0 = float(tc_simple.Nx(0))
        assert abs(n0 - suma) < 0.01

    def test_Nx_at_omega(self, tc_simple):
        """N(omega) = D(omega) (only one term left)."""
        omega = tc_simple.edad_max
        assert abs(float(tc_simple.Nx(omega)) - float(tc_simple.Dx(omega))) < 0.01

    def test_Cx_positive(self, tc_simple):
        """Cx should be positive (deaths exist at every age)."""
        for x in range(tc_simple.edad_min, tc_simple.edad_max + 1):
            assert tc_simple.Cx(x) >= Decimal("0")

    def test_Mx_is_sum_of_Cx(self, tc_simple):
        """Mx should equal sum of Cx from x to omega."""
        suma = sum(float(tc_simple.Cx(x)) for x in range(0, 6))
        m0 = float(tc_simple.Mx(0))
        assert abs(m0 - suma) < 0.01

    def test_Sx_is_sum_of_Nx(self, tc_simple):
        """Sx should equal sum of Nx from x to omega."""
        suma = sum(float(tc_simple.Nx(x)) for x in range(0, 6))
        s0 = float(tc_simple.Sx(0))
        assert abs(s0 - suma) < 0.01

    def test_Rx_is_sum_of_Mx(self, tc_simple):
        """Rx should equal sum of Mx from x to omega."""
        suma = sum(float(tc_simple.Mx(x)) for x in range(0, 6))
        r0 = float(tc_simple.Rx(0))
        assert abs(r0 - suma) < 0.01

    def test_Dx_returns_decimal(self, tc_simple):
        """All accessors should return Decimal."""
        assert isinstance(tc_simple.Dx(0), Decimal)
        assert isinstance(tc_simple.Nx(0), Decimal)
        assert isinstance(tc_simple.Cx(0), Decimal)
        assert isinstance(tc_simple.Mx(0), Decimal)
        assert isinstance(tc_simple.Sx(0), Decimal)
        assert isinstance(tc_simple.Rx(0), Decimal)


class TestCommutationBoundaries:
    """Test boundary conditions."""

    def test_age_below_range_raises(self, tc_emssa_h):
        """Accessing age below table range should raise ValueError."""
        with pytest.raises(ValueError, match="fuera del rango"):
            tc_emssa_h.Dx(5)

    def test_age_above_range_raises(self, tc_emssa_h):
        """Accessing age above table range should raise ValueError."""
        with pytest.raises(ValueError, match="fuera del rango"):
            tc_emssa_h.Dx(101)

    def test_edad_min_max_properties(self, tc_emssa_h):
        """edad_min and edad_max should match EMSSA-09 range."""
        assert tc_emssa_h.edad_min == 18
        assert tc_emssa_h.edad_max == 100

    def test_omega_age_Dx_small(self, tc_emssa_h):
        """D(omega) should be very small but positive."""
        d_omega = tc_emssa_h.Dx(100)
        assert d_omega > 0
        assert d_omega < tc_emssa_h.Dx(18)


# ======================================================================
# Tests: annuity (ax)
# ======================================================================


class TestAnnuity:
    """Test ax (annuity) calculations."""

    def test_ax_whole_life_positive(self, tc_emssa_h):
        """Whole-life annuity should be positive and reasonable."""
        ax = tc_emssa_h.ax(35)
        assert ax > Decimal("0")
        # At age 35, 5.5%, whole-life annuity should be roughly 12-18
        assert Decimal("5") < ax < Decimal("25")

    def test_ax_temporal_less_than_whole_life(self, tc_emssa_h):
        """Temporary annuity should be less than whole-life."""
        ax_whole = tc_emssa_h.ax(35)
        ax_temp = tc_emssa_h.ax(35, n=10)
        assert ax_temp < ax_whole

    def test_ax_temporal_increases_with_n(self, tc_emssa_h):
        """Longer temporary annuity should be larger."""
        ax_5 = tc_emssa_h.ax(35, n=5)
        ax_10 = tc_emssa_h.ax(35, n=10)
        ax_20 = tc_emssa_h.ax(35, n=20)
        assert ax_5 < ax_10 < ax_20

    def test_ax_zero_term(self, tc_emssa_h):
        """Annuity with n=0 should be 0."""
        assert tc_emssa_h.ax(35, n=0) == Decimal("0")

    def test_ax_n_exceeds_omega_equals_whole_life(self, tc_emssa_h):
        """If x+n > omega, temporal annuity = whole life annuity."""
        ax_whole = tc_emssa_h.ax(90)
        ax_huge = tc_emssa_h.ax(90, n=50)
        assert abs(float(ax_whole) - float(ax_huge)) < 0.001

    def test_ax_women_greater_than_men(self, tc_emssa_h, tc_emssa_m):
        """Women live longer, so annuity factor should be higher."""
        ax_h = tc_emssa_h.ax(35)
        ax_m = tc_emssa_m.ax(35)
        assert ax_m > ax_h


# ======================================================================
# Tests: insurance (Ax)
# ======================================================================


class TestInsurance:
    """Test Ax (insurance) calculations."""

    def test_Ax_whole_life_in_range(self, tc_emssa_h):
        """Whole-life insurance value at age 35 should be between 0 and 1."""
        ax = tc_emssa_h.Ax(35)
        assert Decimal("0") < ax < Decimal("1")

    def test_Ax_increases_with_age(self, tc_emssa_h):
        """Insurance value should increase with age (more likely to die)."""
        a35 = tc_emssa_h.Ax(35)
        a50 = tc_emssa_h.Ax(50)
        a65 = tc_emssa_h.Ax(65)
        assert a35 < a50 < a65

    def test_Ax_temporal_less_than_whole_life(self, tc_emssa_h):
        """Temporary insurance should be less than whole life."""
        ax_whole = tc_emssa_h.Ax(35)
        ax_temp = tc_emssa_h.Ax(35, n=10)
        assert ax_temp < ax_whole


# ======================================================================
# Tests: pure endowment (nEx)
# ======================================================================


class TestPureEndowment:
    """Test nEx (pure endowment) calculations."""

    def test_nEx_at_zero_term(self, tc_emssa_h):
        """0Ex = D(x)/D(x) = 1."""
        # nEx with n=0 would be D(x)/D(x) = 1
        # Our implementation: nEx(x, 0) -> Dx(x)/Dx(x) = 1
        nex = tc_emssa_h.nEx(35, 0)
        assert abs(float(nex) - 1.0) < 0.001

    def test_nEx_decreases_with_n(self, tc_emssa_h):
        """Longer deferral = smaller pure endowment (more discounting)."""
        e5 = tc_emssa_h.nEx(35, 5)
        e10 = tc_emssa_h.nEx(35, 10)
        e20 = tc_emssa_h.nEx(35, 20)
        assert e5 > e10 > e20

    def test_nEx_between_zero_and_one(self, tc_emssa_h):
        """nEx should be between 0 and 1."""
        for n in [1, 5, 10, 20, 30]:
            nex = tc_emssa_h.nEx(35, n)
            assert Decimal("0") < nex <= Decimal("1"), f"nEx(35,{n})={nex}"

    def test_nEx_beyond_omega_is_zero(self, tc_emssa_h):
        """If x+n > omega, nEx = 0 (nobody survives)."""
        nex = tc_emssa_h.nEx(35, 100)
        assert nex == Decimal("0")


# ======================================================================
# Tests: net level premium and reserve
# ======================================================================


class TestPremiumAndReserve:
    """Test Px (premium) and tVx (reserve) calculations."""

    def test_Px_positive(self, tc_emssa_h):
        """Net level premium should be positive."""
        px = tc_emssa_h.Px(35, n=20)
        assert px > Decimal("0")

    def test_Px_increases_with_age(self, tc_emssa_h):
        """Premium should increase with age at issue."""
        p35 = tc_emssa_h.Px(35, n=20)
        p45 = tc_emssa_h.Px(45, n=20)
        assert p45 > p35

    def test_tVx_zero_at_boundaries(self, tc_emssa_h):
        """Reserve should be 0 at t=0 and t=n."""
        assert tc_emssa_h.tVx(35, 20, 0) == Decimal("0")
        assert tc_emssa_h.tVx(35, 20, 20) == Decimal("0")

    def test_tVx_positive_midterm(self, tc_emssa_h):
        """Reserve should be positive in the middle of the term."""
        v10 = tc_emssa_h.tVx(35, 20, 10)
        assert v10 > Decimal("0")

    def test_tVx_out_of_range_raises(self, tc_emssa_h):
        """Reserve at invalid time should raise ValueError."""
        with pytest.raises(ValueError, match="fuera de rango"):
            tc_emssa_h.tVx(35, 20, -1)
        with pytest.raises(ValueError, match="fuera de rango"):
            tc_emssa_h.tVx(35, 20, 21)

    def test_identity_Ax_plus_d_ax_equals_one(self, tc_emssa_h):
        """Actuarial identity: Ax + d*ax = 1 (whole life).
        Where d = i/(1+i)."""
        x = 35
        ax_val = float(tc_emssa_h.ax(x))
        Ax_val = float(tc_emssa_h.Ax(x))
        i = tc_emssa_h.tasa_interes
        d = i / (1 + i)
        # Ax + d*ax should be close to 1
        total = Ax_val + d * ax_val
        assert abs(total - 1.0) < 0.01, f"Ax + d*ax = {total}, expected ~1.0"


class TestCommutationRepr:
    """Test string representation."""

    def test_repr(self, tc_simple):
        r = repr(tc_simple)
        assert "TablaConmutacion" in r
        assert "Simple" in r
        assert "H" in r


class TestEsperanzaDeVida:
    """Esperanza de vida abreviada `e_x` — hallazgo A5 de `docs/AUDIT.md`.

    `e_x` cuenta años por vivir; `ax` descuenta cada pago por interés. Son
    cantidades distintas y usar una por la otra sesga cualquier reparto de
    saldo. Estas pruebas fijan la diferencia con una identidad exacta.
    """

    def test_valor_calculado_a_mano(self, tc_simple):
        """e_0 sobre la tabla sintética, sumando lx a mano.

        qx = 0.01, 0.02, 0.03, 0.05, 0.10 con raíz 100,000 da
        lx = 100000, 99000, 97020, 94109.4, 89403.93, 80463.537, así que
        e_0 = (99000 + 97020 + 94109.4 + 89403.93 + 80463.537) / 100000.
        """
        esperado = (99000 + 97020 + 94109.4 + 89403.93 + 80463.537) / 100000

        assert float(tc_simple.ex(0)) == pytest.approx(esperado, rel=1e-9)
        assert float(tc_simple.ex(0)) == pytest.approx(4.59996867, rel=1e-9)

    def test_recursion_de_la_esperanza(self, tc_emssa_h):
        """Identidad: e_x = p_x * (1 + e_{x+1}).

        Es la recursión estándar de la esperanza abreviada. Contrasta el
        resultado contra una ruta distinta del mismo cálculo, así que detecta
        un error de indexado o de truncamiento en la suma.
        """
        for x in (30, 50, 65, 80):
            p_x = 1 - float(tc_emssa_h.tabla_mortalidad.obtener_qx(x, "H"))
            esperado = p_x * (1 + float(tc_emssa_h.ex(x + 1)))
            assert float(tc_emssa_h.ex(x)) == pytest.approx(esperado, rel=1e-9)

    def test_a_interes_cero_la_anualidad_es_uno_mas_la_esperanza(self, tabla_emssa09):
        """Identidad exacta: con i = 0, `ax = 1 + e_x`.

        La anualidad anticipada suma `v^t * t_p_x`; sin descuento, `v = 1`, así
        que se reduce a `1 + suma t_p_x = 1 + e_x`. Esta identidad separa las
        dos cantidades sin ambigüedad: coinciden solo cuando el interés se
        anula, y es lo que hace incorrecto usar `ax` como esperanza de vida.
        """
        sin_interes = TablaConmutacion(tabla_emssa09, sexo="H", tasa_interes=0.0)

        for x in (40, 65, 85):
            assert float(sin_interes.ax(x)) == pytest.approx(1 + float(sin_interes.ex(x)), rel=1e-9)

    def test_con_interes_positivo_la_anualidad_subestima_la_esperanza(self, tc_emssa_h):
        """Con i > 0 el descuento hace `ax` estrictamente menor que `e_x`.

        A 65 años la tabla da e_65 ≈ 17.2 contra ax ≈ 11.6: repartir un saldo
        entre 11 años en vez de 17 sobreestima el retiro en más de 45%. Ese
        era el defecto A5.
        """
        x = 65
        ax_val = float(tc_emssa_h.ax(x))
        ex_val = float(tc_emssa_h.ex(x))

        assert ex_val > ax_val
        assert ex_val == pytest.approx(17.2, abs=0.3)
        assert ax_val < 12.5

    def test_es_decreciente_con_la_edad(self, tc_emssa_h):
        """A mayor edad, menos años por vivir."""
        valores = [float(tc_emssa_h.ex(x)) for x in range(30, 90, 5)]

        assert valores == sorted(valores, reverse=True)

    def test_edad_terminal_no_tiene_esperanza(self, tc_simple):
        """En omega no quedan años por vivir."""
        assert tc_simple.ex(tc_simple.edad_max) == Decimal("0")

    def test_lx_expone_la_tabla_de_sobrevivientes(self, tc_simple):
        """`lx` es la raíz a la edad mínima y decrece."""
        assert float(tc_simple.lx(0)) == pytest.approx(100_000)
        assert float(tc_simple.lx(1)) == pytest.approx(99_000)
        assert tc_simple.lx(5) < tc_simple.lx(4)
