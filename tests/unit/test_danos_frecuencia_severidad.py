"""
Tests para el modelo colectivo de riesgo (frecuencia-severidad).

~35 tests cubriendo:
- Prima pura con parametros conocidos
- Formula de varianza
- VaR y TVaR de simulacion
- Cada distribucion de frecuencia (poisson, negbinom, binomial)
- Cada distribucion de severidad (lognormal, pareto, gamma, weibull, exponencial)
- Casos borde (cero siniestros, severidad muy alta)
"""

from decimal import Decimal

import numpy as np
import pytest

from suite_actuarial.danos.frecuencia_severidad import ModeloColectivo

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def modelo_poisson_lognormal():
    """Poisson(lambda=10) + Lognormal(mu=8, sigma=1.5) -- caso clasico."""
    return ModeloColectivo(
        dist_frecuencia="poisson",
        params_frecuencia={"lambda_": 10},
        dist_severidad="lognormal",
        params_severidad={"mu": 8, "sigma": 1.5},
    )


@pytest.fixture
def modelo_negbinom_gamma():
    """NegBin(n=5, p=0.3) + Gamma(alpha=2, beta=0.001)."""
    return ModeloColectivo(
        dist_frecuencia="negbinom",
        params_frecuencia={"n": 5, "p": 0.3},
        dist_severidad="gamma",
        params_severidad={"alpha": 2, "beta": 0.001},
    )


@pytest.fixture
def modelo_binomial_exponencial():
    """Binomial(n=20, p=0.1) + Exponencial(lambda=0.0001)."""
    return ModeloColectivo(
        dist_frecuencia="binomial",
        params_frecuencia={"n": 20, "p": 0.1},
        dist_severidad="exponencial",
        params_severidad={"lambda_": 0.0001},
    )


# ---------------------------------------------------------------------------
# Tests de construccion
# ---------------------------------------------------------------------------

class TestConstruccion:
    def test_crear_modelo_basico(self, modelo_poisson_lognormal):
        m = modelo_poisson_lognormal
        assert m.dist_frecuencia_nombre == "poisson"
        assert m.dist_severidad_nombre == "lognormal"

    def test_frecuencia_invalida(self):
        with pytest.raises(ValueError, match="frecuencia no soportada"):
            ModeloColectivo("uniforme", {"a": 1}, "lognormal", {"mu": 1, "sigma": 1})

    def test_severidad_invalida(self):
        with pytest.raises(ValueError, match="severidad no soportada"):
            ModeloColectivo("poisson", {"lambda_": 5}, "normal", {"mu": 0, "sigma": 1})


# ---------------------------------------------------------------------------
# Tests de prima pura: E[S] = E[N] * E[X]
# ---------------------------------------------------------------------------

class TestPrimaPura:
    def test_poisson_lognormal_prima_pura(self, modelo_poisson_lognormal):
        """E[N]=10, E[X]=e^(8+1.5^2/2) para lognormal."""
        pp = modelo_poisson_lognormal.prima_pura()
        assert isinstance(pp, Decimal)
        assert pp > 0

    def test_prima_pura_poisson_exponencial(self):
        """E[N]=5, E[X]=1/0.01=100 => E[S]=500."""
        m = ModeloColectivo(
            "poisson", {"lambda_": 5},
            "exponencial", {"lambda_": 0.01},
        )
        pp = m.prima_pura()
        assert pp == Decimal("500.00")

    def test_prima_pura_binomial_exponencial(self, modelo_binomial_exponencial):
        """E[N]=20*0.1=2, E[X]=1/0.0001=10000 => E[S]=20000."""
        pp = modelo_binomial_exponencial.prima_pura()
        assert pp == Decimal("20000.00")

    def test_prima_pura_negbinom(self, modelo_negbinom_gamma):
        """E[N] para NegBin(n=5, p=0.3) = n*(1-p)/p = 5*0.7/0.3."""
        pp = modelo_negbinom_gamma.prima_pura()
        assert pp > 0

    def test_prima_pura_positiva_siempre(self, modelo_poisson_lognormal):
        assert modelo_poisson_lognormal.prima_pura() > 0


# ---------------------------------------------------------------------------
# Tests de varianza: Var[S] = E[N]*Var[X] + Var[N]*E[X]^2
# ---------------------------------------------------------------------------

class TestVarianza:
    def test_varianza_positiva(self, modelo_poisson_lognormal):
        var = modelo_poisson_lognormal.varianza_agregada()
        assert isinstance(var, Decimal)
        assert var > 0

    def test_varianza_poisson_exponencial(self):
        """
        Poisson(5) + Exp(0.01):
        E[N]=5, Var[N]=5, E[X]=100, Var[X]=10000
        Var[S] = 5*10000 + 5*100^2 = 50000 + 50000 = 100000
        """
        m = ModeloColectivo(
            "poisson", {"lambda_": 5},
            "exponencial", {"lambda_": 0.01},
        )
        var = m.varianza_agregada()
        assert var == Decimal("100000.00")

    def test_desviacion_estandar(self, modelo_poisson_lognormal):
        de = modelo_poisson_lognormal.desviacion_estandar()
        var = modelo_poisson_lognormal.varianza_agregada()
        # de^2 ~ var
        assert abs(float(de) ** 2 - float(var)) / float(var) < 0.01


# ---------------------------------------------------------------------------
# Tests de simulacion
# ---------------------------------------------------------------------------

class TestSimulacion:
    def test_simular_devuelve_array(self, modelo_poisson_lognormal):
        perdidas = modelo_poisson_lognormal.simular_perdidas(n_simulaciones=1000, seed=42)
        assert isinstance(perdidas, np.ndarray)
        assert len(perdidas) == 1000

    def test_simular_reproducible(self, modelo_poisson_lognormal):
        p1 = modelo_poisson_lognormal.simular_perdidas(n_simulaciones=500, seed=123)
        # Limpiar cache para forzar recalculo
        modelo_poisson_lognormal._cache_sim = None
        p2 = modelo_poisson_lognormal.simular_perdidas(n_simulaciones=500, seed=123)
        np.testing.assert_array_equal(p1, p2)

    def test_simular_no_negativos(self, modelo_poisson_lognormal):
        perdidas = modelo_poisson_lognormal.simular_perdidas(n_simulaciones=5000, seed=42)
        assert (perdidas >= 0).all()

    def test_simular_cache(self, modelo_poisson_lognormal):
        p1 = modelo_poisson_lognormal.simular_perdidas(n_simulaciones=500, seed=99)
        p2 = modelo_poisson_lognormal.simular_perdidas(n_simulaciones=500, seed=99)
        assert p1 is p2  # Misma referencia (cache)

    def test_media_simulada_cercana_a_prima_pura(self):
        """Con muchas simulaciones, la media debe aproximar E[S]."""
        m = ModeloColectivo(
            "poisson", {"lambda_": 5},
            "exponencial", {"lambda_": 0.01},
        )
        perdidas = m.simular_perdidas(n_simulaciones=50_000, seed=42)
        media_sim = float(perdidas.mean())
        prima_teorica = 500.0  # E[N]*E[X] = 5*100
        assert abs(media_sim - prima_teorica) / prima_teorica < 0.05


# ---------------------------------------------------------------------------
# Tests de VaR y TVaR
# ---------------------------------------------------------------------------

class TestMedidasRiesgo:
    def test_var_es_decimal(self, modelo_poisson_lognormal):
        var = modelo_poisson_lognormal.var(nivel=0.95, n_simulaciones=5000, seed=42)
        assert isinstance(var, Decimal)

    def test_var_mayor_que_media(self):
        m = ModeloColectivo(
            "poisson", {"lambda_": 10},
            "exponencial", {"lambda_": 0.001},
        )
        var95 = m.var(nivel=0.95, n_simulaciones=10_000, seed=42)
        pp = m.prima_pura()
        assert var95 > pp

    def test_var99_mayor_que_var95(self):
        m = ModeloColectivo(
            "poisson", {"lambda_": 10},
            "exponencial", {"lambda_": 0.001},
        )
        var95 = m.var(nivel=0.95, n_simulaciones=50_000, seed=42)
        var99 = m.var(nivel=0.99, n_simulaciones=50_000, seed=42)
        assert var99 >= var95

    def test_tvar_mayor_que_var(self):
        m = ModeloColectivo(
            "poisson", {"lambda_": 10},
            "exponencial", {"lambda_": 0.001},
        )
        var95 = m.var(nivel=0.95, n_simulaciones=50_000, seed=42)
        tvar95 = m.tvar(nivel=0.95, n_simulaciones=50_000, seed=42)
        assert tvar95 >= var95

    def test_tvar_es_decimal(self, modelo_poisson_lognormal):
        tvar = modelo_poisson_lognormal.tvar(nivel=0.95, n_simulaciones=5000, seed=42)
        assert isinstance(tvar, Decimal)


# ---------------------------------------------------------------------------
# Tests de prima de riesgo
# ---------------------------------------------------------------------------

class TestPrimaRiesgo:
    def test_prima_riesgo_mayor_o_igual_prima_pura(self, modelo_poisson_lognormal):
        pr = modelo_poisson_lognormal.prima_riesgo(
            nivel_confianza=0.95, n_simulaciones=10_000, seed=42
        )
        pp = modelo_poisson_lognormal.prima_pura()
        assert pr >= pp


# ---------------------------------------------------------------------------
# Tests por distribucion de frecuencia
# ---------------------------------------------------------------------------

class TestDistribucionesFrecuencia:
    def test_poisson(self):
        m = ModeloColectivo(
            "poisson", {"lambda_": 3},
            "exponencial", {"lambda_": 0.01},
        )
        assert m.prima_pura() == Decimal("300.00")

    def test_negbinom(self):
        m = ModeloColectivo(
            "negbinom", {"n": 2, "p": 0.5},
            "exponencial", {"lambda_": 0.01},
        )
        # E[N] para NegBin(n=2, p=0.5) = 2*(1-0.5)/0.5 = 2
        pp = m.prima_pura()
        assert pp == Decimal("200.00")

    def test_binomial(self):
        m = ModeloColectivo(
            "binomial", {"n": 10, "p": 0.2},
            "exponencial", {"lambda_": 0.01},
        )
        # E[N] = 10*0.2 = 2
        pp = m.prima_pura()
        assert pp == Decimal("200.00")


# ---------------------------------------------------------------------------
# Tests por distribucion de severidad
# ---------------------------------------------------------------------------

class TestDistribucionesSeveridad:
    def test_lognormal(self):
        m = ModeloColectivo(
            "poisson", {"lambda_": 1},
            "lognormal", {"mu": 0, "sigma": 1},
        )
        # E[X] = e^(0 + 1/2) = e^0.5 ~ 1.6487
        pp = m.prima_pura()
        assert abs(float(pp) - np.exp(0.5)) < 0.01

    def test_pareto(self):
        m = ModeloColectivo(
            "poisson", {"lambda_": 1},
            "pareto", {"alpha": 3, "scale": 1000},
        )
        # Pareto(b=3, scale=1000): E[X] = b*scale/(b-1) = 3*1000/2 = 1500
        # With Poisson(lambda=1), E[S] = E[N]*E[X] = 1 * 1500 = 1500
        pp = m.prima_pura()
        assert pp == Decimal("1500.00")

    def test_gamma(self):
        m = ModeloColectivo(
            "poisson", {"lambda_": 1},
            "gamma", {"alpha": 2, "beta": 0.5},
        )
        # E[X] = alpha/beta = 2/0.5 = 4
        pp = m.prima_pura()
        assert pp == Decimal("4.00")

    def test_weibull(self):
        m = ModeloColectivo(
            "poisson", {"lambda_": 1},
            "weibull", {"c": 2, "scale": 100},
        )
        pp = m.prima_pura()
        assert pp > 0

    def test_exponencial(self):
        m = ModeloColectivo(
            "poisson", {"lambda_": 1},
            "exponencial", {"lambda_": 0.01},
        )
        # E[X] = 1/0.01 = 100
        pp = m.prima_pura()
        assert pp == Decimal("100.00")


# ---------------------------------------------------------------------------
# Tests de casos borde
# ---------------------------------------------------------------------------

class TestCasosBorde:
    def test_frecuencia_muy_baja(self):
        """Lambda muy pequeno: la mayoria de simulaciones dan 0 siniestros."""
        m = ModeloColectivo(
            "poisson", {"lambda_": 0.01},
            "exponencial", {"lambda_": 0.001},
        )
        perdidas = m.simular_perdidas(n_simulaciones=1000, seed=42)
        # La mayoria debe ser cero
        ceros = (perdidas == 0).sum()
        assert ceros > 900

    def test_severidad_alta(self):
        """Severidad con cola pesada (Pareto alpha bajo)."""
        m = ModeloColectivo(
            "poisson", {"lambda_": 5},
            "pareto", {"alpha": 1.5, "scale": 10000},
        )
        perdidas = m.simular_perdidas(n_simulaciones=5000, seed=42)
        assert perdidas.max() > perdidas.mean() * 5  # Cola pesada

    def test_estadisticas_completas(self):
        m = ModeloColectivo(
            "poisson", {"lambda_": 5},
            "exponencial", {"lambda_": 0.01},
        )
        stats = m.estadisticas(n_simulaciones=10_000, seed=42)
        assert "prima_pura" in stats
        assert "varianza_agregada" in stats
        assert "var_95" in stats
        assert "tvar_95" in stats
        assert "var_99" in stats
        assert "tvar_99" in stats
        assert "asimetria" in stats
        assert stats["simulaciones"] == 10_000

    def test_estadisticas_valores_razonables(self):
        m = ModeloColectivo(
            "poisson", {"lambda_": 5},
            "exponencial", {"lambda_": 0.01},
        )
        stats = m.estadisticas(n_simulaciones=20_000, seed=42)
        assert stats["var_99"] >= stats["var_95"]
        assert stats["tvar_99"] >= stats["tvar_95"]
        assert stats["minimo"] >= Decimal("0")
