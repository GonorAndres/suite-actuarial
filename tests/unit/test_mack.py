"""Tests del modelo de Mack (1993) — hallazgo A9a de `docs/AUDIT.md`.

Oráculo principal: el triángulo de Taylor & Ashe (1983), que es el ejemplo
publicado en el propio artículo de Mack. Sus resultados (reserva total
18,680,856 y error estándar 2,447,095) son la referencia con la que se validan
todas las implementaciones del método, así que la prueba contrasta contra una
fuente externa y no contra la fórmula bajo prueba.
"""

from decimal import Decimal

import pandas as pd
import pytest

from suite_actuarial.reservas.mack import calcular_mack

#: Triángulo incremental de Taylor & Ashe (1983), usado por Mack (1993) como
#: ejemplo numérico y reproducido por la literatura posterior.
TAYLOR_ASHE_INCREMENTAL = [
    [357848, 766940, 610542, 482940, 527326, 574398, 146342, 139950, 227229, 67948],
    [352118, 884021, 933894, 1183289, 445745, 320996, 527804, 266172, 425046, None],
    [290507, 1001799, 926219, 1016654, 750816, 146923, 495992, 280405, None, None],
    [310608, 1108250, 776189, 1562400, 272482, 352053, 206286, None, None, None],
    [443160, 693190, 991983, 769488, 504851, 470639, None, None, None, None],
    [396132, 937085, 847498, 805037, 705960, None, None, None, None, None],
    [440832, 847631, 1131398, 1063269, None, None, None, None, None, None],
    [359480, 1061648, 1443370, None, None, None, None, None, None, None],
    [376686, 986608, None, None, None, None, None, None, None, None],
    [344014, None, None, None, None, None, None, None, None, None],
]

#: Error estándar por año de origen publicado para este triángulo (1981-1990).
SE_PUBLICADO = {
    1981: 0,
    1982: 75_535,
    1983: 121_700,
    1984: 133_551,
    1985: 261_412,
    1986: 411_028,
    1987: 558_317,
    1988: 875_328,
    1989: 971_258,
    1990: 1_363_155,
}


@pytest.fixture
def taylor_ashe():
    """Triángulo acumulado de Taylor & Ashe (1983)."""
    acumulado = []
    for fila in TAYLOR_ASHE_INCREMENTAL:
        total = 0.0
        salida = []
        for valor in fila:
            if valor is None:
                salida.append(None)
            else:
                total += valor
                salida.append(total)
        acumulado.append(salida)

    columnas = {j: [acumulado[i][j] for i in range(10)] for j in range(10)}
    return pd.DataFrame(columnas, index=list(range(1981, 1991)))


@pytest.fixture
def triangulo_multiplicativo():
    """Triángulo exactamente multiplicativo: C[i,j] = a[i] * b[j].

    Dentro de cada periodo de desarrollo todas las razones age-to-age son
    idénticas, así que sigma_k = 0 para todo k y el error de predicción es
    exactamente cero.
    """
    a = [1000.0, 1200.0, 1500.0, 1800.0]
    b = [1.0, 1.5, 1.8, 1.9]
    data = {j: [a[i] * b[j] if i + j <= 3 else None for i in range(4)] for j in range(4)}
    return pd.DataFrame(data, index=[2021, 2022, 2023, 2024])


class TestOraculoTaylorAshe:
    """Contraste contra los resultados publicados por Mack (1993)."""

    def test_reserva_total_publicada(self, taylor_ashe):
        """La reserva del Chain Ladder ponderado por volumen: 18,680,856."""
        resultado = calcular_mack(taylor_ashe)

        assert float(resultado.reserva_total) == pytest.approx(18_680_856, abs=1)

    def test_error_estandar_total_publicado(self, taylor_ashe):
        """El error estándar total de Mack: 2,447,095.

        Este número es la prueba decisiva del hallazgo A9a. Requiere sigma_k por
        periodo, el MSEP por año de origen y el término de correlación entre
        años. Cualquiera de los tres omitido lo cambia materialmente: sin el
        término de correlación la raíz de la suma de los MSEP individuales da
        ~2.0M, no 2.45M.
        """
        resultado = calcular_mack(taylor_ashe)

        assert float(resultado.standard_error) == pytest.approx(2_447_095, abs=2)
        assert float(resultado.coefficient_of_variation) == pytest.approx(0.131, abs=0.001)

    def test_error_estandar_por_anio_publicado(self, taylor_ashe):
        """Cada año de origen reproduce su error estándar publicado.

        La tolerancia relativa es 1e-4 (cinco cifras significativas por fila):
        la tabla de referencia circula redondeada y su transcripción no conserva
        más precisión que esa. El total, que sí se contrasta al peso, está en
        `test_error_estandar_total_publicado`.
        """
        resultado = calcular_mack(taylor_ashe)

        for anio, se_esperado in SE_PUBLICADO.items():
            assert float(resultado.se_por_anio[anio]) == pytest.approx(se_esperado, rel=1e-4, abs=1)

    def test_correlacion_hace_el_total_mayor_que_la_raiz_de_la_suma(self, taylor_ashe):
        """El total excede la agregación independiente, y por eso importa.

        Los estimadores f_k son comunes a todos los años de origen, así que sus
        errores están correlacionados positivamente. Agregar como si fueran
        independientes subestima. Esta prueba fija la dirección del sesgo sin
        repetir la fórmula.
        """
        resultado = calcular_mack(taylor_ashe)

        suma_independiente = sum(float(se) ** 2 for se in resultado.se_por_anio.values()) ** 0.5

        assert float(resultado.standard_error) > suma_independiente
        assert suma_independiente == pytest.approx(2_034_000, rel=0.01)

    def test_primer_anio_totalmente_desarrollado_no_tiene_error(self, taylor_ashe):
        """El año más antiguo ya no se proyecta: reserva y error son cero."""
        resultado = calcular_mack(taylor_ashe)

        assert resultado.reservas_por_anio[1981] == Decimal("0")
        assert resultado.se_por_anio[1981] == Decimal("0")


class TestPropiedadesEstructurales:
    """Identidades y límites que el modelo debe satisfacer."""

    def test_ajuste_perfecto_da_error_cero(self, triangulo_multiplicativo):
        """Sobre un triángulo multiplicativo sigma_k = 0, luego SE = 0.

        Este es el oráculo que separa Mack de la banda de dispersión agrupada:
        `banda_dispersion_link_ratios` devuelve un positivo grande sobre este
        mismo triángulo porque mide la variación *entre* periodos.
        """
        resultado = calcular_mack(triangulo_multiplicativo)

        assert all(sigma == Decimal("0") for sigma in resultado.sigmas)
        assert float(resultado.standard_error) == pytest.approx(0.0, abs=1e-9)
        assert float(resultado.reserva_total) > 0

    def test_metodo_reportado_es_mack(self, taylor_ashe):
        resultado = calcular_mack(taylor_ashe)

        assert resultado.method == "mack-1993"

    def test_invarianza_de_escala_del_cv(self, taylor_ashe):
        """Multiplicar el triángulo por 100 multiplica el SE por 100.

        La varianza de Mack es lineal en el volumen (`Var = sigma_k^2 * C`), así
        que el error estándar es homogéneo de grado 1 y el coeficiente de
        variación no cambia. Es una identidad del modelo, no una repetición del
        cálculo.
        """
        base = calcular_mack(taylor_ashe)
        escalado = calcular_mack(taylor_ashe * 100)

        assert float(escalado.standard_error) == pytest.approx(
            100 * float(base.standard_error), rel=1e-9
        )
        assert float(escalado.coefficient_of_variation) == pytest.approx(
            float(base.coefficient_of_variation), rel=1e-9
        )

    def test_ultimate_es_pagado_mas_reserva(self, taylor_ashe):
        """Identidad contable por año de origen."""
        resultado = calcular_mack(taylor_ashe)

        for anio in resultado.ultimates_por_anio:
            fila = taylor_ashe.loc[anio].dropna()
            pagado = Decimal(str(fila.iloc[-1]))
            ultimate = resultado.ultimates_por_anio[anio]
            reserva = resultado.reservas_por_anio[anio]
            assert float(ultimate - pagado - reserva) == pytest.approx(0.0, abs=1e-6)

    def test_rango_es_simetrico_alrededor_de_la_reserva(self, taylor_ashe):
        resultado = calcular_mack(taylor_ashe, confidence_z=Decimal("2"))

        inferior, superior = resultado.reserve_range
        assert float(superior - resultado.reserva_total) == pytest.approx(
            2 * float(resultado.standard_error), abs=1e-6
        )
        assert float(resultado.reserva_total - inferior) == pytest.approx(
            2 * float(resultado.standard_error), abs=1e-6
        )

    def test_triangulo_de_una_columna_falla(self):
        """Sin dos periodos no hay ningún factor que estimar."""
        triangulo = pd.DataFrame({0: [1000.0]}, index=[2024])

        with pytest.raises(ValueError, match="dos periodos"):
            calcular_mack(triangulo)


class TestExtrapolacionDeSigma:
    """El último periodo no tiene grados de libertad."""

    def test_ultimo_sigma_no_excede_los_previos(self, taylor_ashe):
        """La regla de Mack acota el último sigma por los dos anteriores.

        sigma_last^2 = min(sigma_{k-1}^4/sigma_{k-2}^2, min(sigma_{k-1}^2,
        sigma_{k-2}^2)). El resultado nunca puede superar a ninguno de los dos
        anteriores: la varianza extrapolada no puede crecer.
        """
        resultado = calcular_mack(taylor_ashe)

        ultimo = float(resultado.sigmas[-1])
        assert ultimo <= float(resultado.sigmas[-2]) + 1e-9
        assert ultimo <= float(resultado.sigmas[-3]) + 1e-9
        assert ultimo > 0
