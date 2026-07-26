"""La validación estructural del triángulo debe atrapar lo que antes pasaba.

`validar_triangulo` contaba las celdas observadas por fila y aceptaba cualquier
distribución de los huecos. Dos entradas malformadas pasaban esa cuenta:

1. Una fila con un hueco en medio y valores a su derecha. El conteo cuadraba,
   pero `incrementar_triangulo` aplica `dropna()`, lo que corre los valores
   hacia la izquierda y resta contra periodos que no corresponden.
2. Un año de origen entero sin observaciones. Cuando hay más filas que
   columnas, el conteo esperado de la última fila da 0, y una fila vacía
   satisface `0 == 0`. Después reventaba adentro con un traceback interno.
"""

import pandas as pd
import pytest

from suite_actuarial.core.models.reservas import (
    ConfiguracionBootstrap,
    ConfiguracionChainLadder,
)
from suite_actuarial.core.validators import TipoTriangulo
from suite_actuarial.reservas.bootstrap import Bootstrap
from suite_actuarial.reservas.chain_ladder import ChainLadder
from suite_actuarial.reservas.mack import calcular_mack
from suite_actuarial.reservas.triangulo import incrementar_triangulo, validar_triangulo


def _triangulo_valido() -> pd.DataFrame:
    return pd.DataFrame(
        {0: [1000.0, 1200.0, 1100.0], 1: [1500.0, 1800.0, None], 2: [1800.0, None, None]},
        index=[2020, 2021, 2022],
    )


class TestHuecosIntermedios:
    """Los huecos deben quedar al final de la fila, no en medio."""

    @staticmethod
    def _con_hueco_en_medio() -> pd.DataFrame:
        """2021 no tiene periodo 2 pero sí periodo 3; el conteo por fila cuadra."""
        return pd.DataFrame(
            {
                0: [1000.0, 1200.0, 1100.0],
                1: [1500.0, 1800.0, None],
                2: [1800.0, None, 1950.0],
                3: [1950.0, 2100.0, None],
            },
            index=[2020, 2021, 2022],
        )

    def test_se_rechaza_nombrando_el_periodo_faltante(self):
        with pytest.raises(ValueError, match="huecos deben quedar al final"):
            validar_triangulo(self._con_hueco_en_medio(), TipoTriangulo.ACUMULADO)

    def test_el_conteo_por_si_solo_no_lo_detectaba(self):
        """Cada fila tiene exactamente las celdas que el conteo esperaba."""
        df = self._con_hueco_en_medio()
        n_cols = df.shape[1]
        for i in range(df.shape[0]):
            assert int(df.iloc[i].notna().sum()) == n_cols - i

    def test_incrementar_ya_no_puede_mezclar_acumulado_con_incrementos(self):
        """Antes devolvía [1200, 600, 300, 2100.0]: el 2100 quedaba sin tocar."""
        with pytest.raises(ValueError, match="huecos deben quedar al final"):
            incrementar_triangulo(self._con_hueco_en_medio())

    def test_un_triangulo_bien_formado_pasa(self):
        assert validar_triangulo(_triangulo_valido(), TipoTriangulo.ACUMULADO)


class TestAnioSinObservaciones:
    """Un año de origen sin datos se rechaza al entrar, no adentro del método."""

    @staticmethod
    def _con_anio_vacio() -> pd.DataFrame:
        """4 filas x 3 columnas: la fila 2023 queda entera en NaN."""
        return pd.DataFrame(
            {
                0: [1000.0, 1200.0, 1100.0, None],
                1: [1500.0, 1800.0, None, None],
                2: [1800.0, None, None, None],
            },
            index=[2020, 2021, 2022, 2023],
        )

    def test_se_rechaza_nombrando_el_anio(self):
        with pytest.raises(ValueError, match="2023 no tiene ninguna observación"):
            validar_triangulo(self._con_anio_vacio(), TipoTriangulo.ACUMULADO)

    def test_chain_ladder_ya_no_lanza_keyerror(self):
        """Antes: KeyError 2023, sin explicación."""
        with pytest.raises(ValueError, match="no tiene ninguna observación"):
            ChainLadder(ConfiguracionChainLadder()).calcular(
                self._con_anio_vacio(), TipoTriangulo.ACUMULADO
            )

    def test_mack_ya_no_lanza_invalidoperation(self):
        """Antes: decimal.InvalidOperation, aún menos explicativo."""
        with pytest.raises(ValueError, match="no tiene ninguna observación"):
            calcular_mack(self._con_anio_vacio())

    def test_el_permiso_de_desarrollo_negativo_no_lo_deja_pasar(self):
        """Es un defecto de estructura, no de signo: el permiso no aplica."""
        with pytest.raises(ValueError, match="no tiene ninguna observación"):
            validar_triangulo(
                self._con_anio_vacio(),
                TipoTriangulo.ACUMULADO,
                permitir_desarrollo_negativo=True,
            )


class TestDesarrolloNegativoEnMackYBootstrap:
    """El permiso de desarrollo negativo debe llegar completo a Mack y al bootstrap.

    `permitir_desarrollo_negativo` se verificó para Chain Ladder y B-F, donde la
    aritmética es directa. Estas pruebas cubren los dos métodos estadísticos,
    donde el permiso deja pasar datos cuyas consecuencias no eran obvias.
    """

    @staticmethod
    def _con_recuperaciones() -> pd.DataFrame:
        """5x5 con descenso real en las columnas de cola."""
        return pd.DataFrame(
            {
                0: [1000.0, 1100.0, 900.0, 1050.0, 980.0],
                1: [1300.0, 1500.0, 1150.0, 1400.0, None],
                2: [1450.0, 1620.0, 1280.0, None, None],
                3: [1390.0, 1580.0, None, None, None],
                4: [1405.0, None, None, None, None],
            },
            index=[2018, 2019, 2020, 2021, 2022],
        )

    @staticmethod
    def _con_celdas_negativas() -> pd.DataFrame:
        """Recuperaciones que llevan el acumulado por debajo de cero."""
        return pd.DataFrame(
            {
                0: [1000.0, 1100.0, 900.0, 1050.0],
                1: [1200.0, 1300.0, 1150.0, None],
                2: [-50.0, -40.0, None, None],
                3: [-60.0, None, None, None],
            },
            index=[2019, 2020, 2021, 2022],
        )

    def test_mack_acepta_lo_mismo_que_chain_ladder(self):
        """Mack revalidaba con el flag por omisión y rechazaba lo que CL aceptaba.

        El mensaje pedía activar `permitir_desarrollo_negativo`, una bandera que
        `calcular_mack` no recibía: el usuario ya la tenía puesta.
        """
        config = ConfiguracionChainLadder(permitir_desarrollo_negativo=True)
        cl = ChainLadder(config)
        triangulo = self._con_celdas_negativas()

        cl.calcular(triangulo, TipoTriangulo.ACUMULADO)  # no debe levantar
        resultado = cl.calcular_mack(triangulo, TipoTriangulo.ACUMULADO)  # tampoco
        assert resultado.standard_error >= 0

    def test_mack_sigue_rechazando_sin_declararlo(self):
        cl = ChainLadder(ConfiguracionChainLadder())
        with pytest.raises(ValueError, match="permitir_desarrollo_negativo"):
            cl.calcular_mack(self._con_celdas_negativas(), TipoTriangulo.ACUMULADO)

    def test_mack_devuelve_error_estandar_finito_y_no_negativo(self):
        """El estimador se mantiene sano bajo descenso moderado."""
        import math

        config = ConfiguracionChainLadder(permitir_desarrollo_negativo=True)
        resultado = ChainLadder(config).calcular_mack(
            self._con_recuperaciones(), TipoTriangulo.ACUMULADO
        )
        assert math.isfinite(float(resultado.standard_error))
        assert float(resultado.standard_error) >= 0
        for se in resultado.se_por_anio.values():
            assert math.isfinite(float(se))
            assert float(se) >= 0

    def test_el_bootstrap_avisa_de_las_celdas_sin_varianza_de_proceso(self):
        """Una fracción material de celdas sin varianza estrecha la banda.

        Estaba reportado solo como un conteo crudo en `detalles`, donde nada
        obliga a mirarlo. La cifra debe venir con su advertencia.
        """
        config = ConfiguracionBootstrap(
            num_simulaciones=200, seed=7, permitir_desarrollo_negativo=True
        )
        resultado = Bootstrap(config).calcular(self._con_recuperaciones(), TipoTriangulo.ACUMULADO)

        assert resultado.detalles["celdas_sin_varianza_proceso"] > 0
        avisos = resultado.calculation_metadata.warnings
        assert any("SIN varianza de proceso" in a for a in avisos), avisos
        assert any("subestiman la dispersion" in a for a in avisos), avisos

    def test_un_triangulo_creciente_no_recibe_ese_aviso(self):
        """El aviso no debe ensuciar el caso normal."""
        creciente = pd.DataFrame(
            {
                0: [1000.0, 1100.0, 900.0, 1050.0, 980.0],
                1: [1300.0, 1500.0, 1150.0, 1400.0, None],
                2: [1450.0, 1620.0, 1280.0, None, None],
                3: [1520.0, 1700.0, None, None, None],
                4: [1560.0, None, None, None, None],
            },
            index=[2018, 2019, 2020, 2021, 2022],
        )
        resultado = Bootstrap(ConfiguracionBootstrap(num_simulaciones=200, seed=7)).calcular(
            creciente, TipoTriangulo.ACUMULADO
        )
        avisos = resultado.calculation_metadata.warnings
        assert not any("SIN varianza de proceso" in a for a in avisos), avisos
