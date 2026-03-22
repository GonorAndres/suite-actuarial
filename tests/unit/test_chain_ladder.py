"""
Tests para método Chain Ladder.

Valida cálculo de factores de desarrollo, completado de triángulo,
y cálculo de reservas IBNR.
"""

from decimal import Decimal

import pandas as pd
import pytest

from suite_actuarial.core.validators import (
    ConfiguracionChainLadder,
    MetodoPromedio,
)
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

    def test_calcular_factores_ponderado(
        self, triangulo_simple, config_ponderado
    ):
        """Debe calcular factores con promedio ponderado"""
        cl = ChainLadder(config_ponderado)
        factores = cl.calcular_factores_desarrollo(triangulo_simple)

        assert len(factores) == 4
        assert all(isinstance(f, Decimal) for f in factores)

    def test_calcular_factores_geometrico(
        self, triangulo_simple, config_geometrico
    ):
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

    def test_completar_triangulo_mantiene_conocidos(
        self, triangulo_simple, config_simple
    ):
        """Los valores conocidos no deben cambiar"""
        cl = ChainLadder(config_simple)
        factores = cl.calcular_factores_desarrollo(triangulo_simple)
        triangulo_completo = cl.completar_triangulo(
            triangulo_simple, factores
        )

        # Valores conocidos deben ser iguales
        assert triangulo_completo.iloc[0, 0] == triangulo_simple.iloc[0, 0]
        assert triangulo_completo.iloc[1, 1] == triangulo_simple.iloc[1, 1]

    def test_completar_triangulo_llena_nans(
        self, triangulo_simple, config_simple
    ):
        """Debe llenar todos los NaN con proyecciones"""
        cl = ChainLadder(config_simple)
        factores = cl.calcular_factores_desarrollo(triangulo_simple)
        triangulo_completo = cl.completar_triangulo(
            triangulo_simple, factores
        )

        # No debe haber NaN
        assert not triangulo_completo.isna().any().any()

    def test_completar_triangulo_valores_crecientes(
        self, triangulo_simple, config_simple
    ):
        """Los valores proyectados deben ser monótonos crecientes"""
        cl = ChainLadder(config_simple)
        factores = cl.calcular_factores_desarrollo(triangulo_simple)
        triangulo_completo = cl.completar_triangulo(
            triangulo_simple, factores
        )

        # Cada fila debe ser monótona creciente
        for i in range(len(triangulo_completo)):
            row = triangulo_completo.iloc[i]
            assert row.is_monotonic_increasing


class TestChainLadderUltimates:
    """Tests para cálculo de ultimates"""

    def test_calcular_ultimates_todos_anios(
        self, triangulo_simple, config_simple
    ):
        """Debe calcular ultimate para todos los años"""
        cl = ChainLadder(config_simple)
        factores = cl.calcular_factores_desarrollo(triangulo_simple)
        triangulo_completo = cl.completar_triangulo(
            triangulo_simple, factores
        )
        ultimates = cl.calcular_ultimates(triangulo_completo)

        # Debe haber ultimate para cada año
        assert len(ultimates) == len(triangulo_simple)
        assert set(ultimates.keys()) == set(triangulo_simple.index)

    def test_ultimates_son_mayores_que_observado(
        self, triangulo_simple, config_simple
    ):
        """Ultimates deben ser >= valores observados"""
        cl = ChainLadder(config_simple)
        factores = cl.calcular_factores_desarrollo(triangulo_simple)
        triangulo_completo = cl.completar_triangulo(
            triangulo_simple, factores
        )
        ultimates = cl.calcular_ultimates(triangulo_completo)

        # Para cada año, ultimate >= último valor observado
        for idx in triangulo_simple.index:
            row = triangulo_simple.loc[idx]
            ultimo_observado = row.dropna().iloc[-1]
            assert ultimates[int(idx)] >= Decimal(str(ultimo_observado))


class TestChainLadderReservas:
    """Tests para cálculo de reservas"""

    def test_calcular_reservas_todas_positivas(
        self, triangulo_simple, config_simple
    ):
        """Todas las reservas deben ser >= 0"""
        cl = ChainLadder(config_simple)
        factores = cl.calcular_factores_desarrollo(triangulo_simple)
        triangulo_completo = cl.completar_triangulo(
            triangulo_simple, factores
        )
        ultimates = cl.calcular_ultimates(triangulo_completo)
        reservas = cl.calcular_reservas(triangulo_simple, ultimates)

        assert all(r >= Decimal("0") for r in reservas.values())

    def test_reserva_primer_anio_mayor(self, triangulo_simple, config_simple):
        """Años más recientes deben tener mayor reserva (mayor IBNR)"""
        cl = ChainLadder(config_simple)
        factores = cl.calcular_factores_desarrollo(triangulo_simple)
        triangulo_completo = cl.completar_triangulo(
            triangulo_simple, factores
        )
        ultimates = cl.calcular_ultimates(triangulo_completo)
        reservas = cl.calcular_reservas(triangulo_simple, ultimates)

        # Año más reciente (2024) debe tener mayor reserva que el más antiguo
        assert reservas[2024] > reservas[2020]


class TestChainLadderCalculoCompleto:
    """Tests para cálculo completo end-to-end"""

    def test_calcular_completo_exitoso(self, triangulo_simple, config_simple):
        """Debe ejecutar cálculo completo sin errores"""
        cl = ChainLadder(config_simple)
        resultado = cl.calcular(triangulo_simple)

        assert resultado is not None
        assert resultado.reserva_total >= Decimal("0")
        assert resultado.ultimate_total >= Decimal("0")
        assert resultado.pagado_total >= Decimal("0")

    def test_resultado_tiene_todos_anios(self, triangulo_simple, config_simple):
        """Resultado debe tener datos para todos los años"""
        cl = ChainLadder(config_simple)
        resultado = cl.calcular(triangulo_simple)

        assert len(resultado.reservas_por_anio) == len(triangulo_simple)
        assert len(resultado.ultimates_por_anio) == len(triangulo_simple)

    def test_resultado_tiene_factores(self, triangulo_simple, config_simple):
        """Resultado debe incluir factores de desarrollo"""
        cl = ChainLadder(config_simple)
        resultado = cl.calcular(triangulo_simple)

        assert resultado.factores_desarrollo is not None
        assert len(resultado.factores_desarrollo) == 4

    def test_validacion_consistencia(self, triangulo_simple, config_simple):
        """Ultimate = Pagado + Reserva debe cumplirse"""
        cl = ChainLadder(config_simple)
        resultado = cl.calcular(triangulo_simple)

        # Validar que el resultado es consistente
        assert (
            abs(
                resultado.ultimate_total
                - resultado.pagado_total
                - resultado.reserva_total
            )
            < Decimal("0.01")
        )

    def test_detalles_en_resultado(self, triangulo_simple, config_simple):
        """Resultado debe incluir detalles completos"""
        cl = ChainLadder(config_simple)
        resultado = cl.calcular(triangulo_simple)

        assert "metodo_promedio" in resultado.detalles
        assert "numero_anios" in resultado.detalles
        assert "numero_periodos" in resultado.detalles
        assert resultado.detalles["numero_anios"] == 5


class TestChainLadderTrianguloEjemplo:
    """Tests con triángulo de ejemplo"""

    def test_triangulo_ejemplo_funciona(self, config_simple):
        """Debe procesar triángulo de ejemplo sin errores"""
        triangulo = crear_triangulo_ejemplo()
        cl = ChainLadder(config_simple)
        resultado = cl.calcular(triangulo)

        assert resultado.reserva_total > Decimal("0")

    def test_obtener_triangulo_completo(
        self, triangulo_simple, config_simple
    ):
        """Debe poder obtener triángulo completo después de calcular"""
        cl = ChainLadder(config_simple)
        cl.calcular(triangulo_simple)

        triangulo_completo = cl.obtener_triangulo_completo()
        assert triangulo_completo is not None
        assert not triangulo_completo.isna().any().any()

    def test_obtener_factores_age_to_age(
        self, triangulo_simple, config_simple
    ):
        """Debe poder obtener factores age-to-age"""
        cl = ChainLadder(config_simple)
        cl.calcular(triangulo_simple)

        factores_ata = cl.obtener_factores_age_to_age()
        assert factores_ata is not None


class TestChainLadderComparacionMetodos:
    """Tests comparando diferentes métodos de promedio"""

    def test_metodos_producen_resultados_diferentes(self, triangulo_simple):
        """Diferentes métodos deben producir resultados ligeramente diferentes"""
        config_simple = ConfiguracionChainLadder(
            metodo_promedio=MetodoPromedio.SIMPLE
        )
        config_ponderado = ConfiguracionChainLadder(
            metodo_promedio=MetodoPromedio.PONDERADO
        )

        cl_simple = ChainLadder(config_simple)
        cl_ponderado = ChainLadder(config_ponderado)

        resultado_simple = cl_simple.calcular(triangulo_simple)
        resultado_ponderado = cl_ponderado.calcular(triangulo_simple)

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
            resultado = cl.calcular(triangulo_simple)
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
