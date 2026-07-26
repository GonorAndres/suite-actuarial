"""
Tests para método Chain Ladder.

Valida cálculo de factores de desarrollo, completado de triángulo,
y cálculo de reservas IBNR.
"""

import math
from decimal import Decimal

import pandas as pd
import pytest
from pydantic import ValidationError

from suite_actuarial.core.validators import (
    ConfiguracionChainLadder,
    MetodoPromedio,
    MetodoReserva,
    ResultadoReserva,
    TipoTriangulo,
)
from suite_actuarial.core.warnings import ExperimentalModelWarning
from suite_actuarial.reservas.chain_ladder import ChainLadder
from suite_actuarial.reservas.triangulo import crear_triangulo_ejemplo


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
def config_simple():
    """Configuración básica de Chain Ladder"""
    return ConfiguracionChainLadder(
        metodo_promedio=MetodoPromedio.SIMPLE,
        calcular_tail_factor=False,
    )


@pytest.fixture
def config_ponderado():
    """Configuración con promedio ponderado"""
    return ConfiguracionChainLadder(
        metodo_promedio=MetodoPromedio.PONDERADO,
        calcular_tail_factor=False,
    )


@pytest.fixture
def config_geometrico():
    """Configuración con promedio geométrico"""
    return ConfiguracionChainLadder(
        metodo_promedio=MetodoPromedio.GEOMETRICO,
        calcular_tail_factor=False,
    )


@pytest.fixture
def config_con_tail():
    """Configuración con tail factor"""
    return ConfiguracionChainLadder(
        metodo_promedio=MetodoPromedio.SIMPLE,
        calcular_tail_factor=True,
    )


class TestChainLadderCreacion:
    """Tests para creación de Chain Ladder"""

    def test_crear_chain_ladder_valido(self, config_simple):
        """Debe crear un Chain Ladder válido"""
        cl = ChainLadder(config_simple)
        assert cl.config.metodo_promedio == MetodoPromedio.SIMPLE
        assert cl.config.calcular_tail_factor is False

    def test_crear_con_tail_factor_manual(self):
        """Debe aceptar tail factor manual"""
        config = ConfiguracionChainLadder(
            metodo_promedio=MetodoPromedio.SIMPLE,
            tail_factor=Decimal("1.05"),
        )
        cl = ChainLadder(config)
        assert cl.config.tail_factor == Decimal("1.05")


class TestChainLadderFactoresDesarrollo:
    """Tests para cálculo de factores de desarrollo"""

    def test_calcular_factores_simple(self, triangulo_simple, config_simple):
        """Debe calcular factores con promedio simple"""
        cl = ChainLadder(config_simple)
        factores = cl.calcular_factores_desarrollo(triangulo_simple)

        # Debe haber 4 factores (para 5 columnas)
        assert len(factores) == 4

        # Todos deben ser Decimal
        assert all(isinstance(f, Decimal) for f in factores)

        # Todos deben ser >= 1 (triángulo acumulado)
        assert all(f >= Decimal("1.0") for f in factores)

    def test_calcular_factores_ponderado(self, triangulo_simple, config_ponderado):
        """Debe calcular factores con promedio ponderado"""
        cl = ChainLadder(config_ponderado)
        factores = cl.calcular_factores_desarrollo(triangulo_simple)

        assert len(factores) == 4
        assert all(isinstance(f, Decimal) for f in factores)

    def test_calcular_factores_geometrico(self, triangulo_simple, config_geometrico):
        """Debe calcular factores con promedio geométrico"""
        cl = ChainLadder(config_geometrico)
        factores = cl.calcular_factores_desarrollo(triangulo_simple)

        assert len(factores) == 4
        assert all(isinstance(f, Decimal) for f in factores)

    def test_factores_con_tail(self, triangulo_simple, config_con_tail):
        """Debe agregar tail factor si está configurado"""
        cl = ChainLadder(config_con_tail)
        factores = cl.calcular_factores_desarrollo(triangulo_simple)

        # Debe tener un factor extra (tail)
        assert len(factores) == 5


class TestChainLadderCompletarTriangulo:
    """Tests para completar triángulo"""

    def test_completar_triangulo_mantiene_conocidos(self, triangulo_simple, config_simple):
        """Los valores conocidos no deben cambiar"""
        cl = ChainLadder(config_simple)
        factores = cl.calcular_factores_desarrollo(triangulo_simple)
        triangulo_completo = cl.completar_triangulo(triangulo_simple, factores)

        # Valores conocidos deben ser iguales
        assert triangulo_completo.iloc[0, 0] == triangulo_simple.iloc[0, 0]
        assert triangulo_completo.iloc[1, 1] == triangulo_simple.iloc[1, 1]

    def test_completar_triangulo_llena_nans(self, triangulo_simple, config_simple):
        """Debe llenar todos los NaN con proyecciones"""
        cl = ChainLadder(config_simple)
        factores = cl.calcular_factores_desarrollo(triangulo_simple)
        triangulo_completo = cl.completar_triangulo(triangulo_simple, factores)

        # No debe haber NaN
        assert not triangulo_completo.isna().any().any()

    def test_completar_triangulo_valores_crecientes(self, triangulo_simple, config_simple):
        """Los valores proyectados deben ser monótonos crecientes"""
        cl = ChainLadder(config_simple)
        factores = cl.calcular_factores_desarrollo(triangulo_simple)
        triangulo_completo = cl.completar_triangulo(triangulo_simple, factores)

        # Cada fila debe ser monótona creciente
        for i in range(len(triangulo_completo)):
            row = triangulo_completo.iloc[i]
            assert row.is_monotonic_increasing


class TestChainLadderUltimates:
    """Tests para cálculo de ultimates"""

    def test_calcular_ultimates_todos_anios(self, triangulo_simple, config_simple):
        """Debe calcular ultimate para todos los años"""
        cl = ChainLadder(config_simple)
        factores = cl.calcular_factores_desarrollo(triangulo_simple)
        triangulo_completo = cl.completar_triangulo(triangulo_simple, factores)
        ultimates = cl.calcular_ultimates(triangulo_completo)

        # Debe haber ultimate para cada año
        assert len(ultimates) == len(triangulo_simple)
        assert set(ultimates.keys()) == set(triangulo_simple.index)

    def test_ultimates_son_mayores_que_observado(self, triangulo_simple, config_simple):
        """Ultimates deben ser >= valores observados"""
        cl = ChainLadder(config_simple)
        factores = cl.calcular_factores_desarrollo(triangulo_simple)
        triangulo_completo = cl.completar_triangulo(triangulo_simple, factores)
        ultimates = cl.calcular_ultimates(triangulo_completo)

        # Para cada año, ultimate >= último valor observado
        for idx in triangulo_simple.index:
            row = triangulo_simple.loc[idx]
            ultimo_observado = row.dropna().iloc[-1]
            assert ultimates[int(idx)] >= Decimal(str(ultimo_observado))


class TestChainLadderReservas:
    """Tests para cálculo de reservas"""

    def test_calcular_reservas_todas_positivas(self, triangulo_simple, config_simple):
        """Todas las reservas deben ser >= 0"""
        cl = ChainLadder(config_simple)
        factores = cl.calcular_factores_desarrollo(triangulo_simple)
        triangulo_completo = cl.completar_triangulo(triangulo_simple, factores)
        ultimates = cl.calcular_ultimates(triangulo_completo)
        reservas = cl.calcular_reservas(triangulo_simple, ultimates)

        assert all(r >= Decimal("0") for r in reservas.values())

    def test_reserva_primer_anio_mayor(self, triangulo_simple, config_simple):
        """Años más recientes deben tener mayor reserva (mayor IBNR)"""
        cl = ChainLadder(config_simple)
        factores = cl.calcular_factores_desarrollo(triangulo_simple)
        triangulo_completo = cl.completar_triangulo(triangulo_simple, factores)
        ultimates = cl.calcular_ultimates(triangulo_completo)
        reservas = cl.calcular_reservas(triangulo_simple, ultimates)

        # Año más reciente (2024) debe tener mayor reserva que el más antiguo
        assert reservas[2024] > reservas[2020]


class TestChainLadderCalculoCompleto:
    """Tests para cálculo completo end-to-end"""

    def test_calcular_completo_exitoso(self, triangulo_simple, config_simple):
        """Debe ejecutar cálculo completo sin errores"""
        cl = ChainLadder(config_simple)
        resultado = cl.calcular(triangulo_simple, TipoTriangulo.ACUMULADO)

        assert resultado is not None
        assert resultado.reserva_total >= Decimal("0")
        assert resultado.ultimate_total >= Decimal("0")
        assert resultado.pagado_total >= Decimal("0")

    def test_resultado_tiene_todos_anios(self, triangulo_simple, config_simple):
        """Resultado debe tener datos para todos los años"""
        cl = ChainLadder(config_simple)
        resultado = cl.calcular(triangulo_simple, TipoTriangulo.ACUMULADO)

        assert len(resultado.reservas_por_anio) == len(triangulo_simple)
        assert len(resultado.ultimates_por_anio) == len(triangulo_simple)

    def test_resultado_tiene_factores(self, triangulo_simple, config_simple):
        """Resultado debe incluir factores de desarrollo"""
        cl = ChainLadder(config_simple)
        resultado = cl.calcular(triangulo_simple, TipoTriangulo.ACUMULADO)

        assert resultado.factores_desarrollo is not None
        assert len(resultado.factores_desarrollo) == 4

    def test_validacion_consistencia(self, triangulo_simple, config_simple):
        """Ultimate = Pagado + Reserva debe cumplirse"""
        cl = ChainLadder(config_simple)
        resultado = cl.calcular(triangulo_simple, TipoTriangulo.ACUMULADO)

        # Validar que el resultado es consistente
        assert abs(
            resultado.ultimate_total - resultado.pagado_total - resultado.reserva_total
        ) < Decimal("0.01")

    def test_detalles_en_resultado(self, triangulo_simple, config_simple):
        """Resultado debe incluir detalles completos"""
        cl = ChainLadder(config_simple)
        resultado = cl.calcular(triangulo_simple, TipoTriangulo.ACUMULADO)

        assert "metodo_promedio" in resultado.detalles
        assert "numero_anios" in resultado.detalles
        assert "numero_periodos" in resultado.detalles
        assert resultado.detalles["numero_anios"] == 5


class TestChainLadderTailFactor:
    """El factor de cola debe afectar ultimates y reservas"""

    def test_tail_factor_manual_incrementa_ultimates(self, triangulo_simple, config_simple):
        """Un tail manual de 1.05 debe escalar cada ultimate en 5%"""
        base = ChainLadder(config_simple).calcular(triangulo_simple, TipoTriangulo.ACUMULADO)
        config_tail = ConfiguracionChainLadder(
            metodo_promedio=MetodoPromedio.SIMPLE,
            tail_factor=Decimal("1.05"),
        )
        con_tail = ChainLadder(config_tail).calcular(triangulo_simple, TipoTriangulo.ACUMULADO)

        for anio, ultimate_base in base.ultimates_por_anio.items():
            esperado = ultimate_base * Decimal("1.05")
            assert abs(con_tail.ultimates_por_anio[anio] - esperado) < Decimal("0.01")
        assert con_tail.reserva_total > base.reserva_total

    def test_tail_factor_calculado_incrementa_reserva(
        self, triangulo_simple, config_simple, config_con_tail
    ):
        """calcular_tail_factor=True debe producir reserva mayor que sin cola.

        Nota: esto solo comprueba que la cola fabricada se aplique; no valida
        que el valor de la cola sea correcto — no lo es (hallazgo A10). Debe
        reemplazarse en la fase 2 por una prueba contra una cola estimada.
        """
        base = ChainLadder(config_simple).calcular(triangulo_simple, TipoTriangulo.ACUMULADO)
        con_tail = ChainLadder(config_con_tail).calcular(triangulo_simple, TipoTriangulo.ACUMULADO)

        assert con_tail.reserva_total > base.reserva_total
        # El ultimate nunca puede quedar por debajo de lo pagado
        ultima_diagonal = {
            int(anio): Decimal(str(triangulo_simple.loc[anio].dropna().iloc[-1]))
            for anio in triangulo_simple.index
        }
        for anio, ultimate in con_tail.ultimates_por_anio.items():
            assert ultimate >= ultima_diagonal[anio]


class TestChainLadderTrianguloEjemplo:
    """Tests con triángulo de ejemplo"""

    def test_triangulo_ejemplo_funciona(self, config_simple):
        """Debe procesar triángulo de ejemplo sin errores"""
        triangulo = crear_triangulo_ejemplo()
        cl = ChainLadder(config_simple)
        resultado = cl.calcular(triangulo, TipoTriangulo.ACUMULADO)

        assert resultado.reserva_total > Decimal("0")

    def test_obtener_triangulo_completo(self, triangulo_simple, config_simple):
        """Debe poder obtener triángulo completo después de calcular"""
        cl = ChainLadder(config_simple)
        cl.calcular(triangulo_simple, TipoTriangulo.ACUMULADO)

        triangulo_completo = cl.obtener_triangulo_completo()
        assert triangulo_completo is not None
        assert not triangulo_completo.isna().any().any()

    def test_obtener_factores_age_to_age(self, triangulo_simple, config_simple):
        """Debe poder obtener factores age-to-age"""
        cl = ChainLadder(config_simple)
        cl.calcular(triangulo_simple, TipoTriangulo.ACUMULADO)

        factores_ata = cl.obtener_factores_age_to_age()
        assert factores_ata is not None


class TestChainLadderComparacionMetodos:
    """Tests comparando diferentes métodos de promedio"""

    def test_metodos_producen_resultados_diferentes(self, triangulo_simple):
        """Diferentes métodos deben producir resultados ligeramente diferentes"""
        config_simple = ConfiguracionChainLadder(metodo_promedio=MetodoPromedio.SIMPLE)
        config_ponderado = ConfiguracionChainLadder(metodo_promedio=MetodoPromedio.PONDERADO)

        cl_simple = ChainLadder(config_simple)
        cl_ponderado = ChainLadder(config_ponderado)

        resultado_simple = cl_simple.calcular(triangulo_simple, TipoTriangulo.ACUMULADO)
        resultado_ponderado = cl_ponderado.calcular(triangulo_simple, TipoTriangulo.ACUMULADO)

        # Los resultados pueden ser diferentes (no siempre, depende del triángulo)
        # Pero ambos deben ser válidos
        assert resultado_simple.reserva_total >= Decimal("0")
        assert resultado_ponderado.reserva_total >= Decimal("0")

    def test_todos_metodos_convergen_razonablemente(self, triangulo_simple):
        """Todos los métodos deben producir resultados razonables"""
        metodos = [
            MetodoPromedio.SIMPLE,
            MetodoPromedio.PONDERADO,
            MetodoPromedio.GEOMETRICO,
        ]

        resultados = []
        for metodo in metodos:
            config = ConfiguracionChainLadder(metodo_promedio=metodo)
            cl = ChainLadder(config)
            resultado = cl.calcular(triangulo_simple, TipoTriangulo.ACUMULADO)
            resultados.append(float(resultado.reserva_total))

        # Todos deben estar en un rango razonable (diferencia < 50%)
        min_res = min(resultados)
        max_res = max(resultados)

        if min_res > 0:
            variacion = (max_res - min_res) / min_res
            assert variacion < 0.5  # Máximo 50% de diferencia


class TestChainLadderRepr:
    """Tests para representación string"""

    def test_repr_contiene_info_relevante(self, config_simple):
        """__repr__ debe contener información útil"""
        cl = ChainLadder(config_simple)
        repr_str = repr(cl)

        assert "ChainLadder" in repr_str
        assert "simple" in repr_str.lower()


class TestColaEstimada:
    """El factor de cola se estima con la curva de Sherman (1984).

    Cierre del hallazgo A10 (docs/AUDIT.md): antes se repetía el último factor
    age-to-age, lo que fabricaba un periodo de desarrollo sin base empírica.
    """

    @pytest.fixture
    def triangulo_decreciente(self):
        """Factores age-to-age estrictamente decrecientes hacia 1.

        Construido para que las razones sean exactamente 1.5, 1.2 y 1.05 en
        cada columna: el último factor observado es 1.05 y una cola estimada
        por una curva decreciente tiene que quedar por debajo.
        """
        base = [1000.0, 1200.0, 1500.0, 1800.0]
        acum = [1.0, 1.5, 1.8, 1.89]  # razones 1.5, 1.2, 1.05
        data = {j: [base[i] * acum[j] if i + j <= 3 else None for i in range(4)] for j in range(4)}
        return pd.DataFrame(data, index=[2021, 2022, 2023, 2024])

    def test_la_cola_es_el_producto_extrapolado_de_la_curva_ajustada(self, triangulo_decreciente):
        """La cola cubre todo el desarrollo restante, no un periodo más.

        Con razones 1.5, 1.2 y 1.05 la curva ajustada es `1 + 0.5689*k^-2.0126`
        (r² = 0.93). El valor esperado se reconstruye aquí multiplicando esos
        factores desde el periodo 4, de forma independiente del código bajo
        prueba.

        Nota: `docs/AUDIT.md` (A10) pedía `tail < 1.05` para este triángulo. Esa
        expectativa era incorrecta — trata la cola como si fuera el siguiente
        factor, cuando es el producto de todos los restantes. El desarrollo
        remanente real de este patrón es 1.163, así que repetir 1.05 lo
        *subestimaba*.
        """
        config = ConfiguracionChainLadder(calcular_tail_factor=True)
        with pytest.warns(ExperimentalModelWarning, match="EXTRAPOLACION"):
            resultado = ChainLadder(config).calcular(triangulo_decreciente, TipoTriangulo.ACUMULADO)

        a, b = 0.5689, 2.0126
        esperado = math.prod(1 + a * k**-b for k in range(4, 104))

        tail = float(resultado.factores_desarrollo[-1])
        assert tail == pytest.approx(esperado, rel=1e-3)
        assert tail > 1.05, "repetir el ultimo factor subestimaba este patron"
        assert resultado.detalles["tail_factor_metodo"] == "sherman_curva_potencia_inversa"

    def test_reporta_el_diagnostico_del_ajuste(self, triangulo_decreciente):
        """Sin r², horizonte y parámetros la cola no sería auditable."""
        config = ConfiguracionChainLadder(calcular_tail_factor=True)
        with pytest.warns(ExperimentalModelWarning):
            resultado = ChainLadder(config).calcular(triangulo_decreciente, TipoTriangulo.ACUMULADO)

        detalles = resultado.detalles
        assert Decimal(detalles["tail_ajuste_r2"]) > Decimal("0.9")
        assert Decimal(detalles["tail_ajuste_b"]) > Decimal("0")
        assert detalles["tail_horizonte"] == 100
        assert detalles["tail_periodos_ajustados"] == 3
        assert resultado.calculation_metadata.validation_tier == "supported"

    def test_chain_ladder_sin_cola_automatica_no_emite_el_aviso(self, triangulo_decreciente):
        """El aviso de extrapolación es exclusivo de la ruta estimada."""
        for config, metodo in [
            (ConfiguracionChainLadder(), "ninguno"),
            (ConfiguracionChainLadder(tail_factor=Decimal("1.02")), "manual"),
        ]:
            resultado = ChainLadder(config).calcular(triangulo_decreciente, TipoTriangulo.ACUMULADO)
            assert resultado.calculation_metadata.validation_tier == "supported"
            assert resultado.detalles["tail_factor_metodo"] == metodo
            assert "tail_ajuste_r2" not in resultado.detalles

    def test_triangulo_ya_desarrollado_no_fabrica_cola(self):
        """Con desarrollo terminado la cola es 1, y por la razón correcta.

        Con razones 1.5, 1.0 y 1.0 el último factor no aporta desarrollo. El
        método lo reconoce y devuelve 1 sin ajustar curva alguna, en vez de
        llegar a 1 por accidente repitiendo el último factor.
        """
        base = [1000.0, 1200.0, 1500.0, 1800.0]
        acum = [1.0, 1.5, 1.5, 1.5]  # razones 1.5, 1.0, 1.0
        data = {j: [base[i] * acum[j] if i + j <= 3 else None for i in range(4)] for j in range(4)}
        triangulo = pd.DataFrame(data, index=[2021, 2022, 2023, 2024])

        config = ConfiguracionChainLadder(calcular_tail_factor=True)
        with pytest.warns(ExperimentalModelWarning):
            resultado = ChainLadder(config).calcular(triangulo, TipoTriangulo.ACUMULADO)

        assert float(resultado.factores_desarrollo[-1]) == pytest.approx(1.0)
        assert resultado.detalles["tail_factor_metodo"] == "sin_desarrollo_residual"
        assert resultado.detalles["tail_periodos_ajustados"] == 0


class TestTipoTrianguloDeclarado:
    """El tipo de triángulo se declara; no se infiere de los valores.

    Antes se deducía comparando la monotonía del primer renglón: si crecía, se
    asumía acumulado. Un triángulo incremental cuyo primer año de origen crece
    -patrón normal en ramos de reporte lento- caía en esa trampa y se usaba sin
    acumular, con lo que la reserva salía menor a la correcta sin error ni
    advertencia.
    """

    @staticmethod
    def _incremental_con_primer_renglon_creciente() -> pd.DataFrame:
        """Incremental cuyo renglón 2020 es [100, 150, 200]: monótono creciente."""
        return pd.DataFrame(
            {0: [100.0, 90.0, 80.0], 1: [150.0, 140.0, None], 2: [200.0, None, None]},
            index=[2020, 2021, 2022],
        )

    def test_declarar_incremental_acumula_antes_de_los_factores(self):
        """Reserva a mano: acumulado = 100,250,450 / 90,230 / 80.

        f1 = promedio(250/100, 230/90) = promedio(2.5, 2.5556) = 2.527778
        f2 = 450/250 = 1.8
        ultimates = 450, 230*1.8 = 414, 80*2.527778*1.8 = 364
        reservas  =   0,       184,                       284  -> total 468
        """
        triangulo = self._incremental_con_primer_renglon_creciente()
        config = ConfiguracionChainLadder(metodo_promedio=MetodoPromedio.SIMPLE)

        resultado = ChainLadder(config).calcular(triangulo, TipoTriangulo.INCREMENTAL)

        assert float(resultado.reserva_total) == pytest.approx(468.0)
        assert float(resultado.reservas_por_anio[2020]) == pytest.approx(0.0)
        assert float(resultado.reservas_por_anio[2021]) == pytest.approx(184.0)
        assert float(resultado.reservas_por_anio[2022]) == pytest.approx(284.0)
        assert float(resultado.factores_desarrollo[0]) == pytest.approx(2.527778, abs=1e-6)
        assert float(resultado.factores_desarrollo[1]) == pytest.approx(1.8)

    def test_declararlo_acumulado_da_un_resultado_distinto(self):
        """El mismo triángulo leído como acumulado da 129.63, no 468.

        Es la cifra que producía la heurística. Se fija aquí para que la
        diferencia entre declarar bien y declarar mal quede medida, no supuesta.
        """
        triangulo = self._incremental_con_primer_renglon_creciente()
        config = ConfiguracionChainLadder(metodo_promedio=MetodoPromedio.SIMPLE)

        como_acumulado = ChainLadder(config).calcular(triangulo, TipoTriangulo.ACUMULADO)
        como_incremental = ChainLadder(config).calcular(triangulo, TipoTriangulo.INCREMENTAL)

        assert float(como_acumulado.reserva_total) == pytest.approx(129.6296, abs=1e-4)
        assert como_incremental.reserva_total > como_acumulado.reserva_total * 3

    def test_el_tipo_es_obligatorio(self):
        """Omitirlo es un TypeError, no una suposición silenciosa."""
        config = ConfiguracionChainLadder(metodo_promedio=MetodoPromedio.SIMPLE)
        with pytest.raises(TypeError):
            ChainLadder(config).calcular(  # type: ignore[call-arg]
                self._incremental_con_primer_renglon_creciente()
            )


class TestDesarrolloNegativo:
    """Un triángulo puede bajar por razones reales, y hay que poder valuarlo.

    Un triángulo de pagados baja con salvamento o subrogación; uno de incurridos
    baja al liberar reserva de un siniestro menos grave de lo estimado. El caso
    corriente sigue siendo el creciente, así que el permiso se declara: aceptar
    todo en silencio dejaría pasar un triángulo mal capturado.
    """

    @staticmethod
    def _acumulado_con_recuperacion() -> pd.DataFrame:
        """La fila 2020 baja de 1200 a 1150: hubo una recuperación en el periodo 3."""
        return pd.DataFrame(
            {0: [1000.0, 1100.0, 1200.0], 1: [1200.0, 1300.0, None], 2: [1150.0, None, None]},
            index=[2020, 2021, 2022],
        )

    def test_por_omision_se_rechaza_y_se_dice_como_permitirlo(self):
        config = ConfiguracionChainLadder(metodo_promedio=MetodoPromedio.SIMPLE)
        with pytest.raises(ValueError, match="permitir_desarrollo_negativo"):
            ChainLadder(config).calcular(
                self._acumulado_con_recuperacion(), TipoTriangulo.ACUMULADO
            )

    def test_declarandolo_se_valua(self):
        config = ConfiguracionChainLadder(
            metodo_promedio=MetodoPromedio.SIMPLE,
            permitir_desarrollo_negativo=True,
        )
        resultado = ChainLadder(config).calcular(
            self._acumulado_con_recuperacion(), TipoTriangulo.ACUMULADO
        )
        assert resultado.reserva_total >= 0
        # El factor 1->2 es 1150/1200 < 1: el periodo devuelve dinero.
        assert float(resultado.factores_desarrollo[1]) == pytest.approx(1150 / 1200)

    def test_un_incremental_con_recuperacion_se_acumula(self):
        """Incremental [1000, 200, -50] acumula a [1000, 1200, 1150]."""
        incremental = pd.DataFrame(
            {0: [1000.0, 1100.0, 1200.0], 1: [200.0, 200.0, None], 2: [-50.0, None, None]},
            index=[2020, 2021, 2022],
        )
        config = ConfiguracionChainLadder(
            metodo_promedio=MetodoPromedio.SIMPLE,
            permitir_desarrollo_negativo=True,
        )
        resultado = ChainLadder(config).calcular(incremental, TipoTriangulo.INCREMENTAL)
        assert float(resultado.factores_desarrollo[1]) == pytest.approx(1150 / 1200)

    def test_el_triangulo_creciente_normal_no_cambia(self):
        """Activar el permiso no altera un triángulo que ya era monótono."""
        triangulo = crear_triangulo_ejemplo(TipoTriangulo.ACUMULADO)
        estricto = ChainLadder(
            ConfiguracionChainLadder(metodo_promedio=MetodoPromedio.SIMPLE)
        ).calcular(triangulo, TipoTriangulo.ACUMULADO)
        permisivo = ChainLadder(
            ConfiguracionChainLadder(
                metodo_promedio=MetodoPromedio.SIMPLE, permitir_desarrollo_negativo=True
            )
        ).calcular(triangulo, TipoTriangulo.ACUMULADO)
        assert estricto.reserva_total == permisivo.reserva_total


class TestReservaAgregadaNegativa:
    """El caso que motiva el permiso: la reserva NETA del ramo sale negativa.

    Los totales estaban declarados con `ge=0` en `ResultadoReserva`, así que el
    escenario más propio del permiso -una cartera con salvamento o subrogación
    fuertes cuya reserva agregada resulta negativa- era irrepresentable: el
    cálculo llegaba a la cifra correcta y el modelo se negaba a envolverla. El
    router traducía ese fallo a un 400, como si el triángulo fuera inválido.
    """

    @staticmethod
    def _con_recuperacion_fuerte() -> pd.DataFrame:
        """La última diagonal se desploma de 1100 a 50: recuperación mayor que lo pagado."""
        return pd.DataFrame(
            {0: [1000.0, 1000.0, 1000.0], 1: [1100.0, 1100.0, None], 2: [50.0, None, None]},
            index=[2020, 2021, 2022],
        )

    def test_la_reserva_agregada_puede_ser_negativa(self):
        config = ConfiguracionChainLadder(permitir_desarrollo_negativo=True)
        resultado = ChainLadder(config).calcular(
            self._con_recuperacion_fuerte(), TipoTriangulo.ACUMULADO
        )
        assert resultado.reserva_total < 0
        assert resultado.permite_desarrollo_negativo is True

    def test_la_identidad_contable_se_mantiene(self):
        """ultimate = pagado + reserva, también cuando la reserva es negativa."""
        config = ConfiguracionChainLadder(permitir_desarrollo_negativo=True)
        r = ChainLadder(config).calcular(self._con_recuperacion_fuerte(), TipoTriangulo.ACUMULADO)
        assert r.ultimate_total == r.pagado_total + r.reserva_total

    def test_sin_declararlo_un_total_negativo_se_rechaza(self):
        """El piso sigue protegiendo los caminos normales."""
        with pytest.raises(ValidationError, match="sin haber declarado"):
            ResultadoReserva(
                metodo=MetodoReserva.CHAIN_LADDER,
                reserva_total=Decimal("-100"),
                ultimate_total=Decimal("900"),
                pagado_total=Decimal("1000"),
            )

    def test_declarandolo_el_mismo_total_se_acepta(self):
        r = ResultadoReserva(
            metodo=MetodoReserva.CHAIN_LADDER,
            permite_desarrollo_negativo=True,
            reserva_total=Decimal("-100"),
            ultimate_total=Decimal("900"),
            pagado_total=Decimal("1000"),
        )
        assert r.reserva_total == Decimal("-100")
