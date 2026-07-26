"""Tests de la estimación de cola por curva de potencia inversa (A10).

Oráculo principal: si los factores observados provienen exactamente de la curva
`f_k = 1 + a*k^(-b)`, el ajuste debe recuperar `a` y `b`, y la cola debe ser el
producto analítico de los factores extrapolados. Ese producto se calcula en la
prueba de forma independiente, con los parámetros conocidos de antemano, así que
no se está repitiendo la fórmula bajo prueba con sus propias estimaciones.
"""

import math
from decimal import Decimal

import pytest

from suite_actuarial.core.warnings import ExperimentalModelWarning
from suite_actuarial.reservas.cola import (
    HORIZONTE_POR_OMISION,
    estimar_tail_sherman,
)


def curva(a: float, b: float, k: int) -> float:
    """Factor age-to-age teórico del periodo k."""
    return 1.0 + a * float(k**-b)


class TestOraculoCurvaConocida:
    """Recuperación exacta de una curva generada a propósito."""

    def test_recupera_los_parametros_de_la_curva(self):
        """Con datos exactos de la curva, el ajuste log-log es exacto."""
        a, b = 0.8, 2.5
        factores = [Decimal(str(curva(a, b, k))) for k in range(1, 7)]

        ajuste = estimar_tail_sherman(factores)

        assert float(ajuste.a) == pytest.approx(a, rel=1e-9)
        assert float(ajuste.b) == pytest.approx(b, rel=1e-9)
        assert float(ajuste.r_cuadrado) == pytest.approx(1.0, abs=1e-12)

    def test_la_cola_es_el_producto_analitico_extrapolado(self):
        """La cola coincide con el producto calculado a mano.

        El valor esperado se construye desde los parámetros conocidos de la
        curva, no desde los ajustados, así que la prueba contrasta contra un
        cálculo independiente.
        """
        a, b = 0.8, 2.5
        periodos_observados = 6
        horizonte = 50
        factores = [Decimal(str(curva(a, b, k))) for k in range(1, periodos_observados + 1)]

        esperado = math.prod(
            curva(a, b, k)
            for k in range(periodos_observados + 1, periodos_observados + horizonte + 1)
        )
        ajuste = estimar_tail_sherman(factores, horizonte=horizonte)

        assert float(ajuste.tail) == pytest.approx(esperado, rel=1e-9)
        assert ajuste.metodo == "sherman_curva_potencia_inversa"

    def test_la_cola_no_es_comparable_con_el_ultimo_factor_observado(self):
        """La cola cubre todos los periodos restantes, no solo el siguiente.

        `docs/AUDIT.md` (A10) afirmaba que una estimación de cola sobre factores
        decrecientes debía quedar por debajo del último factor observado. Es
        falso, y esta prueba lo demuestra en las dos direcciones: la cola es el
        producto de infinitos factores, así que con decaimiento lento supera al
        último observado y con decaimiento rápido queda por debajo. Repetir el
        último factor no yerra "sistemáticamente al alza": yerra en la dirección
        que le toque, porque no es una estimación.
        """
        lento = estimar_tail_sherman([Decimal(str(curva(0.5, 1.5, k))) for k in range(1, 6)])
        rapido = estimar_tail_sherman([Decimal(str(curva(0.5, 6.0, k))) for k in range(1, 6)])

        ultimo_lento = curva(0.5, 1.5, 5)
        ultimo_rapido = curva(0.5, 6.0, 5)

        assert float(lento.tail) > ultimo_lento
        assert float(rapido.tail) < ultimo_rapido
        assert float(rapido.tail) > 1.0

    def test_un_decaimiento_mas_rapido_produce_una_cola_menor(self):
        """Monotonía en b: a mayor decaimiento, menos desarrollo remanente.

        Es una propiedad del modelo, no una repetición del cálculo: si el
        exceso decae más rápido, la suma de los excesos restantes es menor y el
        producto también.
        """
        colas = [
            float(estimar_tail_sherman([Decimal(str(curva(0.5, b, k))) for k in range(1, 6)]).tail)
            for b in (1.5, 2.0, 3.0, 4.0)
        ]

        assert colas == sorted(colas, reverse=True)
        assert all(cola > 1.0 for cola in colas)


class TestConvergencia:
    """La serie converge solo si b > 1."""

    def test_serie_convergente_no_avisa_y_se_marca_convergente(self):
        factores = [Decimal(str(curva(0.6, 2.0, k))) for k in range(1, 6)]

        ajuste = estimar_tail_sherman(factores)

        assert ajuste.converge is True

    def test_serie_divergente_avisa_y_declara_el_horizonte(self):
        """Con b <= 1 la cola depende del truncamiento, y hay que decirlo.

        La prueba además demuestra la dependencia: duplicar el horizonte cambia
        materialmente el resultado, cosa que no ocurre con una serie que
        converge rápido.
        """
        factores = [Decimal(str(curva(0.4, 0.7, k))) for k in range(1, 6)]

        with pytest.warns(ExperimentalModelWarning, match="no converge"):
            corto = estimar_tail_sherman(factores, horizonte=50)
        with pytest.warns(ExperimentalModelWarning):
            largo = estimar_tail_sherman(factores, horizonte=100)

        assert corto.converge is False
        assert float(largo.tail) > float(corto.tail) * 1.05
        assert corto.horizonte == 50


class TestNegativaAEstimar:
    """Cuando el patrón no sostiene una extrapolación, no se inventa una."""

    def test_factores_crecientes_no_se_extrapolan(self):
        """Un patrón creciente daría b <= 0: fabricaría desarrollo al alza."""
        factores = [Decimal("1.05"), Decimal("1.20"), Decimal("1.50")]

        with pytest.raises(ValueError, match="no decrecen"):
            estimar_tail_sherman(factores)

    def test_pocos_factores_utiles_no_se_extrapolan(self):
        """Con menos de tres factores > 1 no hay curva que ajustar."""
        factores = [Decimal("1.0"), Decimal("1.30"), Decimal("1.10")]

        with pytest.raises(ValueError, match="al menos 3 factores"):
            estimar_tail_sherman(factores)

    def test_sin_factores_falla(self):
        with pytest.raises(ValueError, match="No hay factores"):
            estimar_tail_sherman([])

    def test_horizonte_invalido_falla(self):
        factores = [Decimal(str(curva(0.5, 2.0, k))) for k in range(1, 5)]

        with pytest.raises(ValueError, match="al menos 1 periodo"):
            estimar_tail_sherman(factores, horizonte=0)


class TestDesarrolloTerminado:
    """Reconocer que ya no hay desarrollo es parte de estimar la cola."""

    def test_ultimo_factor_unitario_da_cola_uno(self):
        factores = [Decimal("1.5"), Decimal("1.2"), Decimal("1.0")]

        ajuste = estimar_tail_sherman(factores)

        assert ajuste.tail == Decimal("1")
        assert ajuste.metodo == "sin_desarrollo_residual"
        assert ajuste.periodos_ajustados == 0
        assert ajuste.horizonte == HORIZONTE_POR_OMISION
