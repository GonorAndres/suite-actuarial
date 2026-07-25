"""Tests del bootstrap ODP de England-Verrall — hallazgo A2 de `docs/AUDIT.md`.

Oráculos independientes que sostienen estas pruebas:

1. **Triángulo de Taylor & Ashe (1983).** El parámetro de dispersión publicado
   para el modelo ODP sobre este triángulo es phi ≈ 52,601, y el error de
   predicción del bootstrap (CV ≈ 16%) queda por encima del error estándar de
   Mack (CV ≈ 13%), como reporta la literatura. Ninguna de las dos cifras sale
   de la fórmula bajo prueba.
2. **Propiedad del estimador máximo-verosímil del ODP.** Los incrementales
   ajustados reproducen exactamente las sumas por fila y por columna del
   triángulo observado. Es una identidad algebraica del método, verificable sin
   simular nada.
3. **Ajuste perfecto.** Sobre un triángulo exactamente multiplicativo todos los
   residuales de Pearson son cero, phi es cero y la distribución colapsa en un
   punto. La versión anterior inyectaba ruido `N(0, 0.05)` justo ahí y fabricaba
   un CV del 5-15%.
"""

from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

from suite_actuarial.core.validators import ConfiguracionBootstrap
from suite_actuarial.reservas.bootstrap import Bootstrap
from suite_actuarial.reservas.mack import calcular_mack

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
def triangulo_simple():
    """Triángulo acumulado simple de 5x5."""
    data = {
        0: [1000, 1200, 1100, 1300, 1250],
        1: [1500, 1800, 1650, 1950, None],
        2: [1800, 2100, 1950, None, None],
        3: [1950, 2250, None, None, None],
        4: [2000, None, None, None, None],
    }
    return pd.DataFrame(data, index=[2020, 2021, 2022, 2023, 2024])


@pytest.fixture
def triangulo_multiplicativo():
    """Triángulo exactamente multiplicativo: C[i,j] = a[i] * b[j].

    Cada razón age-to-age es idéntica en toda la columna, así que Chain Ladder
    ajusta el triángulo sin error y todos los residuales de Pearson son cero por
    construcción. Es el caso límite que separa un remuestreo honesto de uno que
    fabrica dispersión.

    Se usa un triángulo de 6x6: el modelo ODP tiene `I + J - 1` parámetros, así
    que hacen falta más celdas que eso para tener grados de libertad.
    """
    a = [1000.0, 1200.0, 1500.0, 1800.0, 2000.0, 2200.0]
    b = [1.0, 1.5, 1.8, 1.9, 1.95, 1.97]
    data = {j: [a[i] * b[j] if i + j <= 5 else None for i in range(6)] for j in range(6)}
    return pd.DataFrame(data, index=[2019, 2020, 2021, 2022, 2023, 2024])


@pytest.fixture
def config_100_sims():
    return ConfiguracionBootstrap(num_simulaciones=100, seed=42, percentiles=[50, 75, 90, 95, 99])


@pytest.fixture
def config_1000_sims():
    return ConfiguracionBootstrap(num_simulaciones=1000, seed=42, percentiles=[50, 75, 90, 95, 99])


class TestAjusteODP:
    """El ajuste hacia atrás y sus identidades algebraicas."""

    def test_los_ajustados_reproducen_las_sumas_por_fila_y_columna(self, taylor_ashe):
        """Identidad del estimador máximo-verosímil del ODP.

        El modelo ODP ajustado por máxima verosimilitud reproduce exactamente
        los totales marginales del triángulo observado, y su estimador coincide
        con Chain Ladder. Es una identidad algebraica: se verifica sin simular.

        El ajuste anterior construía los valores hacia adelante desde la primera
        columna, así que ni siquiera reproducía la diagonal observada (A2).
        """
        bootstrap = Bootstrap(ConfiguracionBootstrap(num_simulaciones=100, seed=1))
        observados, ajustados = bootstrap.ajustar_incrementales(taylor_ashe)

        assert np.allclose(np.nansum(observados, axis=1), np.nansum(ajustados, axis=1))
        assert np.allclose(np.nansum(observados, axis=0), np.nansum(ajustados, axis=0))

    def test_la_diagonal_ajustada_reproduce_la_observada(self, taylor_ashe):
        """El ajuste hacia atrás parte del ultimate, así que cierra en la diagonal."""
        bootstrap = Bootstrap(ConfiguracionBootstrap(num_simulaciones=100, seed=1))
        bootstrap.ajustar_incrementales(taylor_ashe)

        acumulado_ajustado = np.nancumsum(
            np.where(
                np.isnan(bootstrap.incrementales_ajustados),
                0.0,
                bootstrap.incrementales_ajustados,
            ),
            axis=1,
        )
        observado = taylor_ashe.to_numpy(dtype=float)

        for i in range(observado.shape[0]):
            ultima = int(np.where(~np.isnan(observado[i]))[0][-1])
            assert acumulado_ajustado[i, ultima] == pytest.approx(observado[i, ultima], rel=1e-9)

    def test_phi_reproduce_el_valor_publicado(self, taylor_ashe):
        """phi ≈ 52,601 para el triángulo de Taylor & Ashe.

        El parámetro de dispersión es el que gobierna la varianza de proceso
        (`Var = phi * media`). Reproducirlo exige que estén bien el ajuste hacia
        atrás, los residuales sobre incrementales y los grados de libertad
        `n - p` con `p = I + J - 1`. Cualquiera de los tres mal cambia el valor.
        """
        bootstrap = Bootstrap(ConfiguracionBootstrap(num_simulaciones=100, seed=1))
        observados, ajustados = bootstrap.ajustar_incrementales(taylor_ashe)
        bootstrap.calcular_residuales_pearson(observados, ajustados)

        assert bootstrap.phi == pytest.approx(52_601, rel=1e-3)
        assert bootstrap.celdas_utilizables == 55
        assert bootstrap.parametros_modelo == 19  # I + J - 1 = 10 + 10 - 1
        assert bootstrap.grados_libertad == 36

    def test_sin_grados_de_libertad_falla(self):
        """Un triángulo diminuto no permite estimar la dispersión."""
        triangulo = pd.DataFrame({0: [1000.0, 1200.0], 1: [1500.0, None]}, index=[2023, 2024])
        bootstrap = Bootstrap(ConfiguracionBootstrap(num_simulaciones=100, seed=1))

        with pytest.raises(ValueError, match="grados de libertad"):
            bootstrap.calcular(triangulo)


class TestDistribucionPredictiva:
    """Contraste de la distribución contra referencias externas."""

    def test_la_media_concilia_con_chain_ladder(self, taylor_ashe, config_1000_sims):
        """La media de las réplicas queda a ~1% de la reserva Chain Ladder.

        Reconciliar era el criterio de salida del hallazgo A2: la versión
        anterior usaba la mediana y quedaba 2.5x por encima. La diferencia
        residual no es ruido de Monte Carlo — la reserva es convexa en los
        factores de desarrollo, así que remuestrearlos eleva la media
        (desigualdad de Jensen). Por eso se acota, se reporta y no se afirma
        que sea cero.
        """
        bootstrap = Bootstrap(config_1000_sims)
        resultado = bootstrap.calcular(taylor_ashe)

        reserva_cl = Decimal(resultado.detalles["reserva_base_cl"])
        relativa = Decimal(resultado.detalles["conciliacion_cl_relativa"])

        assert float(reserva_cl) == pytest.approx(18_680_856, abs=1)
        assert relativa < Decimal("0.02")
        assert resultado.detalles["estimador_central"] == "media"

    def test_el_error_de_prediccion_supera_al_de_mack(self, taylor_ashe, config_1000_sims):
        """El bootstrap ODP es más disperso que Mack sobre el mismo triángulo.

        Ambos miden error de predicción condicionado al Chain Ladder, pero bajo
        supuestos de varianza distintos: Mack supone `Var = sigma_k^2 * C`, el
        ODP supone `Var = phi * m`. Para este triángulo la literatura reporta
        CV ≈ 16% para el bootstrap contra 13.1% de Mack. Que ambos queden en el
        mismo orden de magnitud, con el bootstrap por encima, es la prueba
        cruzada entre dos métodos independientes.
        """
        bootstrap = Bootstrap(config_1000_sims)
        resultado = bootstrap.calcular(taylor_ashe)
        mack = calcular_mack(taylor_ashe)

        error_bootstrap = float(resultado.detalles["error_prediccion"])
        cv_bootstrap = float(resultado.detalles["coeficiente_variacion"])

        assert error_bootstrap > float(mack.standard_error)
        assert error_bootstrap < 2 * float(mack.standard_error)
        assert cv_bootstrap == pytest.approx(0.16, abs=0.02)

    def test_la_varianza_de_proceso_agrega_dispersion(self, taylor_ashe, config_1000_sims):
        """Apagar el paso de proceso reduce el error de predicción.

        Las dos fuentes se componen: error de estimación (remuestreo de
        residuales) y error de proceso (Gamma con `Var = phi*m`). Si el segundo
        no aportara nada, el paso no estaría haciendo su trabajo.
        """
        bootstrap = Bootstrap(config_1000_sims)
        resultado = bootstrap.calcular(taylor_ashe)
        con_proceso = float(resultado.detalles["error_prediccion"])

        bootstrap.phi = 0.0  # desactiva la simulación de proceso
        rng = np.random.default_rng(config_1000_sims.seed)
        solo_estimacion = np.array(
            [
                float(bootstrap.ejecutar_replica(rng))
                for _ in range(config_1000_sims.num_simulaciones)
            ]
        )

        assert con_proceso > float(solo_estimacion.std(ddof=1))

    def test_percentiles_ordenados_y_completos(self, triangulo_simple, config_1000_sims):
        bootstrap = Bootstrap(config_1000_sims)
        resultado = bootstrap.calcular(triangulo_simple)

        assert set(resultado.percentiles.keys()) == {50, 75, 90, 95, 99}
        valores = [resultado.percentiles[p] for p in sorted(resultado.percentiles)]
        assert valores == sorted(valores)

    def test_identidad_contable_del_resultado(self, triangulo_simple, config_100_sims):
        """ultimate = pagado + reserva, con la reserva igual a la media."""
        bootstrap = Bootstrap(config_100_sims)
        resultado = bootstrap.calcular(triangulo_simple)

        assert resultado.ultimate_total == resultado.pagado_total + resultado.reserva_total
        assert resultado.reserva_total == Decimal(resultado.detalles["media"])


class TestAjustePerfecto:
    """Sin dispersión observada no puede haber dispersión simulada."""

    def test_triangulo_multiplicativo_produce_banda_de_ancho_cero(
        self, triangulo_multiplicativo, config_100_sims
    ):
        """Todos los residuales son cero, luego phi es cero y la banda colapsa.

        Este es el oráculo decisivo del hallazgo A2: la implementación anterior
        inyectaba `N(0, 0.05)` exactamente aquí y fabricaba un CV del 5-15% a
        partir de un triángulo sin ninguna variabilidad.
        """
        bootstrap = Bootstrap(config_100_sims)
        resultado = bootstrap.calcular(triangulo_multiplicativo)

        assert bootstrap.phi == pytest.approx(0.0, abs=1e-12)
        assert np.allclose(bootstrap.residuales, 0.0)

        # Las réplicas coinciden hasta el ruido de punto flotante (~1e-12
        # relativo): no queda nada que remuestrear.
        simulaciones = np.array([float(s) for s in bootstrap.simulaciones_reservas])
        assert np.ptp(simulaciones) / simulaciones.mean() < 1e-9
        assert float(resultado.detalles["error_prediccion"]) == pytest.approx(0.0, abs=1e-6)

    def test_el_ajuste_perfecto_concilia_exactamente_con_chain_ladder(
        self, triangulo_multiplicativo, config_100_sims
    ):
        """Sin variabilidad no hay convexidad que sesgue la media."""
        bootstrap = Bootstrap(config_100_sims)
        resultado = bootstrap.calcular(triangulo_multiplicativo)

        conciliacion = float(resultado.detalles["conciliacion_cl"])
        assert conciliacion == pytest.approx(0.0, abs=1e-6)


class TestSinSesgoPorDescarte:
    """Perturbar incrementales elimina la causa raíz del sesgo por selección."""

    def test_ninguna_replica_se_descarta(self, triangulo_simple, config_1000_sims):
        """Todas las réplicas configuradas llegan a la distribución.

        La versión anterior sumaba residuales a valores ACUMULADOS, así que
        ~9% de los intentos quedaban no monótonos y se descartaban, sesgando la
        banda por selección. Aquí se perturban incrementales y se recumula: no
        hay nada que descartar, y el conteo lo demuestra.
        """
        bootstrap = Bootstrap(config_1000_sims)
        bootstrap.calcular(triangulo_simple)

        assert len(bootstrap.simulaciones_reservas) == config_1000_sims.num_simulaciones

    def test_no_hay_masa_puntual_en_la_reserva_base(self, triangulo_simple, config_1000_sims):
        """Ningún valor concentra una fracción anómala de las réplicas.

        La versión anterior sustituía las réplicas fallidas por la reserva base
        de Chain Ladder, lo que apilaba una masa puntual y producía los
        percentiles bimodales que documenta A2.
        """
        bootstrap = Bootstrap(config_1000_sims)
        bootstrap.calcular(triangulo_simple)

        valores = [round(float(s), 6) for s in bootstrap.simulaciones_reservas]
        repeticion_maxima = max(valores.count(v) for v in set(valores))

        assert repeticion_maxima / len(valores) < 0.01


class TestReproducibilidad:
    """La semilla fija la distribución completa."""

    def test_misma_semilla_mismos_resultados(self, triangulo_simple):
        config = ConfiguracionBootstrap(num_simulaciones=200, seed=7)

        primera = Bootstrap(config).calcular(triangulo_simple)
        segunda = Bootstrap(config).calcular(triangulo_simple)

        assert primera.reserva_total == segunda.reserva_total
        assert primera.percentiles == segunda.percentiles

    def test_distinta_semilla_distintos_resultados(self, triangulo_simple):
        una = Bootstrap(ConfiguracionBootstrap(num_simulaciones=200, seed=7)).calcular(
            triangulo_simple
        )
        otra = Bootstrap(ConfiguracionBootstrap(num_simulaciones=200, seed=8)).calcular(
            triangulo_simple
        )

        assert una.reserva_total != otra.reserva_total


class TestInvarianzaDeEscala:
    """El modelo ODP tiene una estructura de escala conocida."""

    def test_escalar_el_triangulo_escala_reserva_y_error(self, triangulo_simple):
        """Multiplicar por 100 multiplica reserva y error por 100; phi también.

        En el modelo ODP `Var = phi * m`, así que al escalar los montos por `c`
        la media escala por `c`, la varianza por `c^2` y por tanto `phi` por `c`.
        El coeficiente de variación queda invariante. Es una identidad del
        modelo, no una repetición del cálculo.
        """
        config = ConfiguracionBootstrap(num_simulaciones=300, seed=11)

        base = Bootstrap(config)
        resultado_base = base.calcular(triangulo_simple)
        escalado = Bootstrap(config)
        resultado_escalado = escalado.calcular(triangulo_simple * 100)

        assert escalado.phi == pytest.approx(100 * base.phi, rel=1e-9)
        assert float(resultado_escalado.reserva_total) == pytest.approx(
            100 * float(resultado_base.reserva_total), rel=1e-9
        )
        assert float(resultado_escalado.detalles["coeficiente_variacion"]) == pytest.approx(
            float(resultado_base.detalles["coeficiente_variacion"]), rel=1e-9
        )


class TestMetadatosYAlcance:
    """Lo que el resultado declara sobre sí mismo."""

    def test_declara_el_metodo_y_su_alcance(self, triangulo_simple, config_100_sims):
        resultado = Bootstrap(config_100_sims).calcular(triangulo_simple)

        assert resultado.detalles["metodo"] == "bootstrap-odp-england-verrall"
        assert resultado.calculation_metadata.validation_tier == "supported"
        assert any(
            "CONDICIONAL al modelo" in aviso for aviso in resultado.calculation_metadata.warnings
        )

    def test_reporta_los_diagnosticos_del_ajuste(self, taylor_ashe, config_100_sims):
        """phi, grados de libertad y celdas excluidas viajan con el resultado."""
        resultado = Bootstrap(config_100_sims).calcular(taylor_ashe)

        assert float(resultado.detalles["phi_dispersion"]) == pytest.approx(52_601, rel=1e-3)
        assert resultado.detalles["grados_libertad"] == 36
        assert resultado.detalles["parametros_modelo"] == 19
        assert float(resultado.detalles["ajuste_grados_libertad"]) == pytest.approx(
            (55 / 36) ** 0.5, rel=1e-9
        )


class TestVaRTVaR:
    """Lecturas de cola de la distribución predictiva."""

    def test_tvar_no_es_menor_que_var(self, triangulo_simple, config_1000_sims):
        """El TVaR promedia la cola que empieza en el VaR."""
        bootstrap = Bootstrap(config_1000_sims)
        bootstrap.calcular(triangulo_simple)

        var = bootstrap.calcular_var(0.95)
        tvar = bootstrap.calcular_tvar(0.95)

        assert tvar >= var

    def test_var_creciente_en_el_nivel_de_confianza(self, triangulo_simple, config_1000_sims):
        bootstrap = Bootstrap(config_1000_sims)
        bootstrap.calcular(triangulo_simple)

        assert bootstrap.calcular_var(0.99) >= bootstrap.calcular_var(0.95)
        assert bootstrap.calcular_var(0.95) >= bootstrap.calcular_var(0.75)

    def test_var_antes_de_calcular_falla(self, config_100_sims):
        with pytest.raises(ValueError, match="antes de calcular"):
            Bootstrap(config_100_sims).calcular_var()


class TestSalidasAuxiliares:
    """Distribución y datos de graficación."""

    def test_obtener_distribucion(self, triangulo_simple, config_100_sims):
        bootstrap = Bootstrap(config_100_sims)
        bootstrap.calcular(triangulo_simple)

        distribucion = bootstrap.obtener_distribucion()
        assert distribucion is not None
        assert len(distribucion) == 100

    def test_obtener_distribucion_antes_de_calcular(self, config_100_sims):
        assert Bootstrap(config_100_sims).obtener_distribucion() is None

    def test_graficar_distribucion(self, triangulo_simple, config_100_sims):
        bootstrap = Bootstrap(config_100_sims)
        bootstrap.calcular(triangulo_simple)

        histograma = bootstrap.graficar_distribucion()
        assert len(histograma) == 50
        assert histograma["relative_frequency"].sum() == pytest.approx(1.0)

    def test_graficar_antes_de_calcular_falla(self, config_100_sims):
        with pytest.raises(ValueError, match="antes de graficar"):
            Bootstrap(config_100_sims).graficar_distribucion()

    def test_repr_contiene_info_relevante(self, config_100_sims):
        texto = repr(Bootstrap(config_100_sims))

        assert "Bootstrap" in texto
        assert "100" in texto


class TestConfiguracion:
    """Validación de la configuración."""

    def test_num_simulaciones_muy_bajo_invalido(self):
        with pytest.raises(ValueError):
            ConfiguracionBootstrap(num_simulaciones=50)

    def test_num_simulaciones_muy_alto_invalido(self):
        with pytest.raises(ValueError):
            ConfiguracionBootstrap(num_simulaciones=50000)

    def test_percentiles_invalidos(self):
        with pytest.raises(ValueError):
            ConfiguracionBootstrap(percentiles=[50, 150])

    def test_percentiles_se_ordenan_y_deduplican(self):
        config = ConfiguracionBootstrap(percentiles=[95, 50, 95, 75])

        assert config.percentiles == [50, 75, 95]
