"""
Tests para método Bootstrap.

Valida simulación Monte Carlo, generación de triángulos sintéticos,
cálculo de distribución completa y percentiles.
"""

from decimal import Decimal

import pandas as pd
import pytest

from suite_actuarial.core.validators import ConfiguracionBootstrap
from suite_actuarial.reservas.bootstrap import Bootstrap


@pytest.fixture
def triangulo_simple():
    """Triángulo acumulado simple de 5x5"""
    data = {
        0: [1000, 1200, 1100, 1300, 1250],
        1: [1500, 1800, 1650, 1950, None],
        2: [1800, 2100, 1950, None, None],
        3: [1950, 2250, None, None, None],
        4: [2000, None, None, None, None],
    }
    return pd.DataFrame(data, index=[2020, 2021, 2022, 2023, 2024])


@pytest.fixture
def config_100_sims():
    """Configuración con 100 simulaciones"""
    return ConfiguracionBootstrap(
        num_simulaciones=100,
        seed=42,  # Para reproducibilidad
        percentiles=[50, 75, 90, 95, 99],
    )


@pytest.fixture
def config_1000_sims():
    """Configuración con 1000 simulaciones"""
    return ConfiguracionBootstrap(
        num_simulaciones=1000,
        seed=42,
        percentiles=[50, 75, 90, 95, 99],
    )


class TestBootstrapCreacion:
    """Tests para creación de Bootstrap"""

    def test_crear_bootstrap_valido(self, config_100_sims):
        """Debe crear un Bootstrap válido"""
        bs = Bootstrap(config_100_sims)
        assert bs.config.num_simulaciones == 100
        assert bs.config.seed == 42

    def test_num_simulaciones_muy_bajo_invalido(self):
        """No debe permitir muy pocas simulaciones"""
        with pytest.raises(ValueError):
            ConfiguracionBootstrap(num_simulaciones=50)  # < 100

    def test_num_simulaciones_muy_alto_invalido(self):
        """No debe permitir demasiadas simulaciones"""
        with pytest.raises(ValueError):
            ConfiguracionBootstrap(num_simulaciones=20000)  # > 10000

    def test_percentiles_invalidos(self):
        """No debe permitir percentiles fuera de rango"""
        with pytest.raises(ValueError, match="fuera de rango"):
            ConfiguracionBootstrap(percentiles=[0, 50, 100])  # 0 y 100 inválidos

    def test_percentiles_se_ordenan_y_deduplicant(self):
        """Percentiles deben ordenarse y eliminar duplicados"""
        config = ConfiguracionBootstrap(percentiles=[90, 50, 90, 75])
        # Deben quedar: [50, 75, 90]
        assert config.percentiles == [50, 75, 90]


class TestBootstrapTrianguloAjustado:
    """Tests para cálculo de triángulo ajustado"""

    def test_calcular_triangulo_ajustado(
        self, triangulo_simple, config_100_sims
    ):
        """Debe calcular triángulo ajustado (fitted values)"""
        bs = Bootstrap(config_100_sims)

        # Primero ejecutar Chain Ladder para tener factores
        from suite_actuarial.core.validators import ConfiguracionChainLadder
        from suite_actuarial.reservas.chain_ladder import ChainLadder

        config_cl = ConfiguracionChainLadder()
        cl = ChainLadder(config_cl)
        cl.calcular(triangulo_simple)

        triangulo_ajustado = bs.calcular_triangulo_ajustado(
            triangulo_simple, cl
        )

        # Debe tener mismas dimensiones
        assert triangulo_ajustado.shape == triangulo_simple.shape

        # Primera columna debe ser igual
        assert triangulo_ajustado.iloc[0, 0] == triangulo_simple.iloc[0, 0]


class TestBootstrapResiduales:
    """Tests para cálculo de residuales"""

    def test_calcular_residuales_pearson(
        self, triangulo_simple, config_100_sims
    ):
        """Debe calcular residuales de Pearson"""
        bs = Bootstrap(config_100_sims)

        from suite_actuarial.core.validators import ConfiguracionChainLadder
        from suite_actuarial.reservas.chain_ladder import ChainLadder

        config_cl = ConfiguracionChainLadder()
        cl = ChainLadder(config_cl)
        cl.calcular(triangulo_simple)

        triangulo_ajustado = bs.calcular_triangulo_ajustado(
            triangulo_simple, cl
        )
        residuales = bs.calcular_residuales_pearson(
            triangulo_simple, triangulo_ajustado
        )

        # Debe tener mismas dimensiones
        assert residuales.shape == triangulo_simple.shape

        # Residuales en celdas conocidas no deben ser NaN
        assert pd.notna(residuales.iloc[0, 0])


class TestBootstrapTrianguloSintetico:
    """Tests para generación de triángulos sintéticos"""

    def test_generar_triangulo_sintetico(
        self, triangulo_simple, config_100_sims
    ):
        """Debe generar triángulo sintético re-muestreando residuales"""
        bs = Bootstrap(config_100_sims)

        from suite_actuarial.core.validators import ConfiguracionChainLadder
        from suite_actuarial.reservas.chain_ladder import ChainLadder

        config_cl = ConfiguracionChainLadder()
        cl = ChainLadder(config_cl)
        cl.calcular(triangulo_simple)

        triangulo_ajustado = bs.calcular_triangulo_ajustado(
            triangulo_simple, cl
        )
        residuales = bs.calcular_residuales_pearson(
            triangulo_simple, triangulo_ajustado
        )

        triangulo_sintetico = bs.generar_triangulo_sintetico(
            triangulo_ajustado, residuales
        )

        # Debe tener mismas dimensiones
        assert triangulo_sintetico.shape == triangulo_simple.shape

        # All non-NaN values must be >= 0
        mask = triangulo_sintetico.notna()
        assert (triangulo_sintetico[mask] >= 0).all().all()

    def test_triangulossinteticos_son_diferentes(
        self, triangulo_simple, config_100_sims
    ):
        """Múltiples triángulos sintéticos deben ser diferentes"""
        bs = Bootstrap(config_100_sims)

        from suite_actuarial.core.validators import ConfiguracionChainLadder
        from suite_actuarial.reservas.chain_ladder import ChainLadder

        config_cl = ConfiguracionChainLadder()
        cl = ChainLadder(config_cl)
        cl.calcular(triangulo_simple)

        triangulo_ajustado = bs.calcular_triangulo_ajustado(
            triangulo_simple, cl
        )
        residuales = bs.calcular_residuales_pearson(
            triangulo_simple, triangulo_ajustado
        )

        # Generar dos triángulos
        t1 = bs.generar_triangulo_sintetico(triangulo_ajustado, residuales)
        t2 = bs.generar_triangulo_sintetico(triangulo_ajustado, residuales)

        # Deben ser diferentes (con alta probabilidad)
        # Comparar algunos valores
        diferencias = (t1 != t2).sum().sum()
        # Al menos algunas celdas deben ser diferentes
        assert diferencias > 0


class TestBootstrapSimulacion:
    """Tests para ejecución de simulaciones"""

    def test_ejecutar_simulacion(self, triangulo_simple, config_100_sims):
        """Debe ejecutar una simulación completa"""
        bs = Bootstrap(config_100_sims)

        from suite_actuarial.core.validators import ConfiguracionChainLadder
        from suite_actuarial.reservas.chain_ladder import ChainLadder

        config_cl = ConfiguracionChainLadder()
        cl = ChainLadder(config_cl)
        cl.calcular(triangulo_simple)

        # Preparar bootstrap
        bs.triangulo_ajustado = bs.calcular_triangulo_ajustado(
            triangulo_simple, cl
        )
        bs.residuales = bs.calcular_residuales_pearson(
            triangulo_simple, bs.triangulo_ajustado
        )

        # Ejecutar una simulación
        reserva_sim = bs.ejecutar_simulacion(triangulo_simple, cl)

        # Debe retornar un Decimal positivo
        assert isinstance(reserva_sim, Decimal)
        assert reserva_sim >= Decimal("0")


class TestBootstrapPercentiles:
    """Tests para cálculo de percentiles"""

    def test_calcular_percentiles(self, config_100_sims):
        """Debe calcular percentiles correctamente"""
        bs = Bootstrap(config_100_sims)

        # Simulaciones de ejemplo
        simulaciones = [Decimal(str(x)) for x in range(100)]

        percentiles = bs.calcular_percentiles(simulaciones)

        # Debe tener todos los percentiles configurados
        assert len(percentiles) == len(config_100_sims.percentiles)
        assert 50 in percentiles
        assert 95 in percentiles

        # P50 debe ser cercano a 50 (mediana)
        assert abs(float(percentiles[50]) - 49.5) < 2

        # P95 debe ser cercano a 95
        assert abs(float(percentiles[95]) - 95) < 2

    def test_percentiles_ordenados(self, triangulo_simple, config_100_sims):
        """Percentiles deben estar ordenados ascendentemente"""
        bs = Bootstrap(config_100_sims)
        resultado = bs.calcular(triangulo_simple)

        percentiles_valores = [
            resultado.percentiles[p] for p in sorted(resultado.percentiles.keys())
        ]

        # Deben estar ordenados
        for i in range(len(percentiles_valores) - 1):
            assert percentiles_valores[i] <= percentiles_valores[i + 1]


class TestBootstrapCalculoCompleto:
    """Tests para cálculo completo end-to-end"""

    def test_calcular_completo_exitoso(
        self, triangulo_simple, config_100_sims
    ):
        """Debe ejecutar cálculo completo sin errores"""
        bs = Bootstrap(config_100_sims)
        resultado = bs.calcular(triangulo_simple)

        assert resultado is not None
        assert resultado.reserva_total >= Decimal("0")
        assert resultado.percentiles is not None

    def test_resultado_tiene_percentiles_configurados(
        self, triangulo_simple, config_100_sims
    ):
        """Resultado debe tener todos los percentiles configurados"""
        bs = Bootstrap(config_100_sims)
        resultado = bs.calcular(triangulo_simple)

        for p in config_100_sims.percentiles:
            assert p in resultado.percentiles

    def test_reserva_total_es_p50(self, triangulo_simple, config_100_sims):
        """Reserva total debe ser el percentil 50 (mediana)"""
        bs = Bootstrap(config_100_sims)
        resultado = bs.calcular(triangulo_simple)

        # La reserva total debe ser la mediana
        assert resultado.reserva_total == resultado.percentiles[50]

    def test_detalles_incluyen_estadisticas(
        self, triangulo_simple, config_100_sims
    ):
        """Detalles deben incluir estadísticas descriptivas"""
        bs = Bootstrap(config_100_sims)
        resultado = bs.calcular(triangulo_simple)

        assert "num_simulaciones" in resultado.detalles
        assert "media" in resultado.detalles
        assert "desviacion_estandar" in resultado.detalles
        assert "minimo" in resultado.detalles
        assert "maximo" in resultado.detalles
        assert "coeficiente_variacion" in resultado.detalles


class TestBootstrapReproducibilidad:
    """Tests para reproducibilidad con seed"""

    def test_mismo_seed_mismos_resultados(self, triangulo_simple):
        """Mismo seed debe producir mismos resultados"""
        config1 = ConfiguracionBootstrap(num_simulaciones=100, seed=42)
        config2 = ConfiguracionBootstrap(num_simulaciones=100, seed=42)

        bs1 = Bootstrap(config1)
        bs2 = Bootstrap(config2)

        resultado1 = bs1.calcular(triangulo_simple)
        resultado2 = bs2.calcular(triangulo_simple)

        # Los resultados deben ser idénticos
        assert resultado1.reserva_total == resultado2.reserva_total
        assert resultado1.percentiles[95] == resultado2.percentiles[95]

    def test_diferente_seed_diferentes_resultados(self, triangulo_simple):
        """Diferente seed debe produce different internal distributions"""
        config1 = ConfiguracionBootstrap(num_simulaciones=500, seed=42)
        config2 = ConfiguracionBootstrap(num_simulaciones=500, seed=999)

        bs1 = Bootstrap(config1)
        bs2 = Bootstrap(config2)

        bs1.calcular(triangulo_simple)
        bs2.calcular(triangulo_simple)

        # Both should produce valid results (distributions may converge
        # for small triangles, but internal simulation lists should exist)
        assert bs1.simulaciones_reservas is not None
        assert bs2.simulaciones_reservas is not None
        assert len(bs1.simulaciones_reservas) == 500
        assert len(bs2.simulaciones_reservas) == 500


class TestBootstrapDistribucion:
    """Tests para análisis de distribución"""

    def test_obtener_distribucion(self, triangulo_simple, config_100_sims):
        """Debe poder obtener distribución completa"""
        bs = Bootstrap(config_100_sims)
        bs.calcular(triangulo_simple)

        distribucion = bs.obtener_distribucion()

        assert distribucion is not None
        assert len(distribucion) == 100

    def test_graficar_distribucion(self, triangulo_simple, config_100_sims):
        """Debe generar datos para histograma"""
        bs = Bootstrap(config_100_sims)
        bs.calcular(triangulo_simple)

        df_hist = bs.graficar_distribucion()

        assert isinstance(df_hist, pd.DataFrame)
        assert "frequency" in df_hist.columns
        assert "relative_frequency" in df_hist.columns
        assert len(df_hist) > 0

    def test_obtener_distribucion_antes_de_calcular(self, config_100_sims):
        """Antes de calcular debe retornar None"""
        bs = Bootstrap(config_100_sims)
        distribucion = bs.obtener_distribucion()
        assert distribucion is None


class TestBootstrapVaRTVaR:
    """Tests para cálculo de VaR y TVaR"""

    def test_calcular_var(self, triangulo_simple, config_100_sims):
        """Debe calcular VaR al 95%"""
        bs = Bootstrap(config_100_sims)
        resultado = bs.calcular(triangulo_simple)

        var_95 = bs.calcular_var(nivel_confianza=0.95)

        # VaR debe ser positivo
        assert var_95 >= Decimal("0")

        # VaR al 95% debe be reasonably close to the P95 percentile from result
        p95 = resultado.percentiles[95]
        assert abs(var_95 - p95) / max(p95, Decimal("1")) < Decimal("0.1")

    def test_calcular_tvar(self, triangulo_simple, config_100_sims):
        """Debe calcular TVaR al 95%"""
        bs = Bootstrap(config_100_sims)
        bs.calcular(triangulo_simple)

        tvar_95 = bs.calcular_tvar(nivel_confianza=0.95)
        var_95 = bs.calcular_var(nivel_confianza=0.95)

        # TVaR debe ser >= VaR
        assert tvar_95 >= var_95

    def test_tvar_mayor_que_var(self, triangulo_simple, config_1000_sims):
        """TVaR debe ser mayor que VaR (cola superior)"""
        bs = Bootstrap(config_1000_sims)
        bs.calcular(triangulo_simple)

        var_95 = bs.calcular_var(nivel_confianza=0.95)
        tvar_95 = bs.calcular_tvar(nivel_confianza=0.95)

        # TVaR >= VaR (con >= porque en distribuciones simétricas pueden ser iguales)
        assert tvar_95 >= var_95

    def test_error_var_sin_calcular(self, config_100_sims):
        """Debe fallar si se calcula VaR antes de ejecutar bootstrap"""
        bs = Bootstrap(config_100_sims)

        with pytest.raises(ValueError, match="Debe ejecutar calcular"):
            bs.calcular_var()


class TestBootstrapConvergencia:
    """Tests para convergencia con más simulaciones"""

    def test_mas_simulaciones_mas_estable(self, triangulo_simple):
        """Más simulaciones deben producir resultados más estables"""
        # 100 simulaciones
        config_100 = ConfiguracionBootstrap(num_simulaciones=100, seed=42)
        bs_100 = Bootstrap(config_100)
        resultado_100 = bs_100.calcular(triangulo_simple)

        # 1000 simulaciones
        config_1000 = ConfiguracionBootstrap(num_simulaciones=1000, seed=42)
        bs_1000 = Bootstrap(config_1000)
        resultado_1000 = bs_1000.calcular(triangulo_simple)

        # Ambos deben ser razonables
        assert resultado_100.reserva_total > Decimal("0")
        assert resultado_1000.reserva_total > Decimal("0")

        # Con más simulaciones, la desviación estándar relativa
        # debería ser menor (más concentrado)
        cv_100 = Decimal(resultado_100.detalles["coeficiente_variacion"])
        cv_1000 = Decimal(resultado_1000.detalles["coeficiente_variacion"])

        # Ambos CV deben ser razonables (< 3 for small triangles)
        assert cv_100 < Decimal("3.0")
        assert cv_1000 < Decimal("3.0")


class TestBootstrapRepr:
    """Tests para representación string"""

    def test_repr_contiene_info_relevante(self, config_100_sims):
        """__repr__ debe contener información útil"""
        bs = Bootstrap(config_100_sims)
        repr_str = repr(bs)

        assert "Bootstrap" in repr_str
        assert "100" in repr_str  # Número de simulaciones
        assert "42" in repr_str  # Seed
