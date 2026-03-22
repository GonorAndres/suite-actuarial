"""
Tests para CurvaRendimiento (yield curve).

~20 tests cubriendo:
- Curva plana (todas las tasas iguales)
- Interpolacion de tasas spot
- Calculo de tasas forward
- Consistencia de factores de descuento
- Valor presente de flujo unico
- Valor presente de multiples flujos
- Curva de referencia CETES
- Casos extremos (plazos largos, tasa cero)
"""

from decimal import Decimal

import pytest

from suite_actuarial.actuarial.interest.tasas import CurvaRendimiento


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def curva_plana():
    """Curva plana al 8%."""
    return CurvaRendimiento.plana(Decimal("0.08"))


@pytest.fixture
def curva_normal():
    """Curva normal (creciente) tipica."""
    return CurvaRendimiento(
        plazos=[1, 2, 3, 5, 10, 20, 30],
        tasas=[
            Decimal("0.08"),
            Decimal("0.085"),
            Decimal("0.09"),
            Decimal("0.095"),
            Decimal("0.10"),
            Decimal("0.105"),
            Decimal("0.11"),
        ],
    )


@pytest.fixture
def curva_cetes():
    """Curva CETES de referencia."""
    return CurvaRendimiento.cetes_referencia()


# ---------------------------------------------------------------------------
# Tests de curva plana
# ---------------------------------------------------------------------------

class TestCurvaPlana:
    def test_plana_tasa_constante(self, curva_plana):
        """Todas las tasas spot deben ser iguales en una curva plana."""
        for plazo in [1, 5, 10, 25, 50]:
            assert curva_plana.tasa_spot(plazo) == Decimal("0.08")

    def test_plana_forward_igual_spot(self, curva_plana):
        """Forward en curva plana = spot rate."""
        fwd = curva_plana.tasa_forward(1, 5)
        assert abs(fwd - Decimal("0.08")) < Decimal("0.0001")

    def test_plana_factor_descuento_1_ano(self, curva_plana):
        """v(1) = 1/1.08 ~ 0.925926."""
        v1 = curva_plana.factor_descuento(1)
        expected = Decimal("1") / Decimal("1.08")
        assert abs(v1 - expected) < Decimal("0.000001")

    def test_plana_longitud(self):
        """Curva plana con plazo_max=30 tiene 30 puntos."""
        c = CurvaRendimiento.plana(Decimal("0.10"), plazo_max=30)
        assert len(c.plazos) == 30


# ---------------------------------------------------------------------------
# Tests de interpolacion spot
# ---------------------------------------------------------------------------

class TestInterpolacionSpot:
    def test_punto_exacto(self, curva_normal):
        """Plazo exacto retorna tasa sin interpolar."""
        assert curva_normal.tasa_spot(1) == Decimal("0.08")
        assert curva_normal.tasa_spot(5) == Decimal("0.095")

    def test_interpolacion_lineal(self, curva_normal):
        """Plazo 2.5 entre 2 (8.5%) y 3 (9.0%) => 8.75%."""
        tasa = curva_normal.tasa_spot(2.5)
        assert tasa == Decimal("0.087500")

    def test_extrapolacion_corta(self, curva_normal):
        """Plazo menor al minimo usa primera tasa."""
        tasa = curva_normal.tasa_spot(0.5)
        assert tasa == Decimal("0.08")

    def test_extrapolacion_larga(self, curva_normal):
        """Plazo mayor al maximo usa ultima tasa."""
        tasa = curva_normal.tasa_spot(50)
        assert tasa == Decimal("0.11")

    def test_plazo_no_positivo_error(self, curva_normal):
        with pytest.raises(ValueError, match="positivo"):
            curva_normal.tasa_spot(0)

    def test_plazo_negativo_error(self, curva_normal):
        with pytest.raises(ValueError, match="positivo"):
            curva_normal.tasa_spot(-1)


# ---------------------------------------------------------------------------
# Tests de tasas forward
# ---------------------------------------------------------------------------

class TestTasasForward:
    def test_forward_basico(self, curva_normal):
        """Forward entre 1 y 2 anos.
        (1.085)^2 = (1.08)^1 * (1+f)^1
        f = (1.085)^2 / 1.08 - 1 ~ 0.09002315
        """
        fwd = curva_normal.tasa_forward(1, 2)
        # Manual: (1.085^2) / 1.08 - 1 = 1.177225 / 1.08 - 1 = 0.090024
        assert abs(fwd - Decimal("0.090023")) < Decimal("0.001")

    def test_forward_t2_menor_t1_error(self, curva_normal):
        with pytest.raises(ValueError, match="mayor"):
            curva_normal.tasa_forward(5, 2)

    def test_forward_igual_error(self, curva_normal):
        with pytest.raises(ValueError, match="mayor"):
            curva_normal.tasa_forward(5, 5)

    def test_forward_positivo(self, curva_normal):
        """Forward rates should be positive for upward sloping curve."""
        fwd = curva_normal.tasa_forward(1, 10)
        assert fwd > 0

    def test_forward_plazo_cero_error(self, curva_normal):
        with pytest.raises(ValueError, match="positivo"):
            curva_normal.tasa_forward(0, 5)


# ---------------------------------------------------------------------------
# Tests de factor de descuento
# ---------------------------------------------------------------------------

class TestFactorDescuento:
    def test_factor_descuento_menor_que_1(self, curva_normal):
        """Discount factor must be < 1 for positive rates."""
        for plazo in [1, 5, 10, 30]:
            v = curva_normal.factor_descuento(plazo)
            assert v < Decimal("1")
            assert v > Decimal("0")

    def test_factor_descuento_decrece(self, curva_normal):
        """Longer tenors have smaller discount factors."""
        v1 = curva_normal.factor_descuento(1)
        v5 = curva_normal.factor_descuento(5)
        v10 = curva_normal.factor_descuento(10)
        assert v1 > v5 > v10

    def test_consistencia_spot_descuento(self, curva_normal):
        """v(t) = 1/(1+r(t))^t should hold."""
        for plazo in [1, 3, 10]:
            r = curva_normal.tasa_spot(plazo)
            v = curva_normal.factor_descuento(plazo)
            expected = Decimal("1") / ((Decimal("1") + r) ** Decimal(str(plazo)))
            expected = expected.quantize(Decimal("0.000001"))
            assert v == expected


# ---------------------------------------------------------------------------
# Tests de valor presente
# ---------------------------------------------------------------------------

class TestValorPresente:
    def test_pv_flujo_unico(self, curva_plana):
        """PV of 1,000,000 at year 1 with 8% ~ 925,926."""
        pv = curva_plana.valor_presente(
            flujos=[Decimal("1000000")],
            plazos=[1.0],
        )
        # factor_descuento rounds to 6 decimals, so use same path
        v1 = curva_plana.factor_descuento(1)
        expected = (Decimal("1000000") * v1).quantize(Decimal("0.01"))
        assert pv == expected

    def test_pv_multiples_flujos(self, curva_plana):
        """PV of 100k at years 1, 2, 3 with flat 8%."""
        flujos = [Decimal("100000")] * 3
        plazos = [1.0, 2.0, 3.0]
        pv = curva_plana.valor_presente(flujos, plazos)
        # Manual: 100k/1.08 + 100k/1.08^2 + 100k/1.08^3
        v = Decimal("1") / Decimal("1.08")
        expected = Decimal("100000") * (v + v**2 + v**3)
        expected = expected.quantize(Decimal("0.01"))
        assert pv == expected

    def test_pv_longitudes_distintas_error(self, curva_plana):
        with pytest.raises(ValueError, match="longitud"):
            curva_plana.valor_presente(
                flujos=[Decimal("100"), Decimal("200")],
                plazos=[1.0],
            )


# ---------------------------------------------------------------------------
# Tests de curva CETES referencia
# ---------------------------------------------------------------------------

class TestCETES:
    def test_cetes_tiene_7_puntos(self, curva_cetes):
        assert len(curva_cetes.plazos) == 7

    def test_cetes_tasas_positivas(self, curva_cetes):
        for tasa in curva_cetes.tasas:
            assert tasa > 0

    def test_cetes_invertida(self, curva_cetes):
        """CETES curve is inverted (shorter tenors have higher rates)."""
        assert curva_cetes.tasa_spot(1) > curva_cetes.tasa_spot(30)

    def test_cetes_factor_descuento(self, curva_cetes):
        v1 = curva_cetes.factor_descuento(1)
        # With ~10.8% rate, v(1) ~ 0.9025
        assert Decimal("0.89") < v1 < Decimal("0.92")


# ---------------------------------------------------------------------------
# Tests de casos extremos
# ---------------------------------------------------------------------------

class TestCasosExtremos:
    def test_tasa_cero(self):
        """Tasa cero: factor de descuento = 1, PV = sum of cashflows."""
        c = CurvaRendimiento.plana(Decimal("0.00"))
        assert c.factor_descuento(10) == Decimal("1.000000")
        pv = c.valor_presente(
            flujos=[Decimal("1000"), Decimal("2000")],
            plazos=[5.0, 10.0],
        )
        assert pv == Decimal("3000.00")

    def test_constructor_vacio_error(self):
        with pytest.raises(ValueError, match="al menos"):
            CurvaRendimiento([], [])

    def test_longitudes_distintas_error(self):
        with pytest.raises(ValueError, match="longitud"):
            CurvaRendimiento([1, 2], [Decimal("0.05")])

    def test_plazos_negativos_error(self):
        with pytest.raises(ValueError, match="positivos"):
            CurvaRendimiento([-1, 2], [Decimal("0.05"), Decimal("0.06")])

    def test_tasas_negativas_error(self):
        with pytest.raises(ValueError, match="negativas"):
            CurvaRendimiento([1, 2], [Decimal("-0.05"), Decimal("0.06")])
