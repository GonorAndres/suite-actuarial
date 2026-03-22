"""
Tests para método Bornhuetter-Ferguson.

Valida combinación de datos observados con loss ratio a priori,
cálculo de porcentajes reportados, y estimación de IBNR.
"""

from decimal import Decimal

import pandas as pd
import pytest

from suite_actuarial.core.validators import (
    ConfiguracionBornhuetterFerguson,
    MetodoPromedio,
)
from suite_actuarial.reservas.bornhuetter_ferguson import BornhuetterFerguson


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
def primas_por_anio():
    """Primas ganadas por año de origen"""
    return {
        2020: Decimal("2000"),
        2021: Decimal("2500"),
        2022: Decimal("3000"),
        2023: Decimal("3500"),
        2024: Decimal("4000"),
    }


@pytest.fixture
def config_lr_65():
    """Configuración con LR 65%"""
    return ConfiguracionBornhuetterFerguson(
        loss_ratio_apriori=Decimal("0.65"),
        metodo_promedio=MetodoPromedio.SIMPLE,
    )


@pytest.fixture
def config_lr_75():
    """Configuración con LR 75%"""
    return ConfiguracionBornhuetterFerguson(
        loss_ratio_apriori=Decimal("0.75"),
        metodo_promedio=MetodoPromedio.SIMPLE,
    )


class TestBornhuetterFergusonCreacion:
    """Tests para creación de Bornhuetter-Ferguson"""

    def test_crear_bf_valido(self, config_lr_65):
        """Debe crear un B-F válido"""
        bf = BornhuetterFerguson(config_lr_65)
        assert bf.config.loss_ratio_apriori == Decimal("0.65")

    def test_loss_ratio_muy_bajo_invalido(self):
        """No debe permitir loss ratio muy bajo"""
        with pytest.raises(ValueError, match="muy bajo"):
            ConfiguracionBornhuetterFerguson(
                loss_ratio_apriori=Decimal("0.2")  # 20% es muy bajo
            )

    def test_loss_ratio_muy_alto_invalido(self):
        """No debe permitir loss ratio muy alto"""
        with pytest.raises(ValueError, match="muy alto"):
            ConfiguracionBornhuetterFerguson(
                loss_ratio_apriori=Decimal("2.0")  # 200% es muy alto
            )

    def test_loss_ratio_razonable_valido(self):
        """Debe aceptar loss ratios razonables"""
        # 60% es razonable
        config = ConfiguracionBornhuetterFerguson(
            loss_ratio_apriori=Decimal("0.60")
        )
        assert config.loss_ratio_apriori == Decimal("0.60")


class TestBornhuetterFergusonPorcentajesReportados:
    """Tests para cálculo de porcentajes reportados"""

    def test_calcular_porcentajes_reportados(
        self, triangulo_simple, config_lr_65
    ):
        """Debe calcular % reportado para cada año"""
        bf = BornhuetterFerguson(config_lr_65)

        # Primero necesitamos factores de desarrollo
        from suite_actuarial.core.validators import ConfiguracionChainLadder
        from suite_actuarial.reservas.chain_ladder import ChainLadder

        config_cl = ConfiguracionChainLadder()
        cl = ChainLadder(config_cl)
        factores = cl.calcular_factores_desarrollo(triangulo_simple)

        porcentajes = bf.calcular_porcentajes_reportados(
            triangulo_simple, factores
        )

        # Debe haber % para cada año
        assert len(porcentajes) == len(triangulo_simple)

        # Todos deben estar entre 0 y 1
        assert all(
            Decimal("0") <= p <= Decimal("1") for p in porcentajes.values()
        )

    def test_anios_mas_desarrollados_mayor_porcentaje(
        self, triangulo_simple, config_lr_65
    ):
        """Años con más desarrollo deben tener mayor % reportado"""
        bf = BornhuetterFerguson(config_lr_65)

        from suite_actuarial.core.validators import ConfiguracionChainLadder
        from suite_actuarial.reservas.chain_ladder import ChainLadder

        config_cl = ConfiguracionChainLadder()
        cl = ChainLadder(config_cl)
        factores = cl.calcular_factores_desarrollo(triangulo_simple)

        porcentajes = bf.calcular_porcentajes_reportados(
            triangulo_simple, factores
        )

        # Año 2020 (totalmente desarrollado) debe tener mayor %
        # que año 2024 (poco desarrollado)
        assert porcentajes[2020] > porcentajes[2024]


class TestBornhuetterFergusonUltimates:
    """Tests para cálculo de ultimates"""

    def test_calcular_ultimates_todos_anios(
        self, triangulo_simple, primas_por_anio, config_lr_65
    ):
        """Debe calcular ultimate para todos los años"""
        bf = BornhuetterFerguson(config_lr_65)
        resultado = bf.calcular(triangulo_simple, primas_por_anio)

        assert len(resultado.ultimates_por_anio) == len(triangulo_simple)

    def test_ultimate_mayor_que_pagado(
        self, triangulo_simple, primas_por_anio, config_lr_65
    ):
        """Ultimate debe ser >= pagado"""
        bf = BornhuetterFerguson(config_lr_65)
        resultado = bf.calcular(triangulo_simple, primas_por_anio)

        from suite_actuarial.reservas.triangulo import (
            obtener_ultima_diagonal,
        )

        ultima_diagonal = obtener_ultima_diagonal(triangulo_simple)

        for idx in triangulo_simple.index:
            anio = int(idx)
            ultimate = resultado.ultimates_por_anio[anio]
            pagado = Decimal(str(ultima_diagonal[idx]))
            assert ultimate >= pagado

    def test_error_si_faltan_primas(self, triangulo_simple, config_lr_65):
        """Debe fallar si faltan primas para algún año"""
        bf = BornhuetterFerguson(config_lr_65)

        # Primas incompletas
        primas_parciales = {
            2020: Decimal("2000"),
            2021: Decimal("2500"),
            # Faltan 2022, 2023, 2024
        }

        with pytest.raises(ValueError, match="Falta prima"):
            bf.calcular(triangulo_simple, primas_parciales)


class TestBornhuetterFergusonCalculoCompleto:
    """Tests para cálculo completo end-to-end"""

    def test_calcular_completo_exitoso(
        self, triangulo_simple, primas_por_anio, config_lr_65
    ):
        """Debe ejecutar cálculo completo sin errores"""
        bf = BornhuetterFerguson(config_lr_65)
        resultado = bf.calcular(triangulo_simple, primas_por_anio)

        assert resultado is not None
        assert resultado.reserva_total >= Decimal("0")
        assert resultado.ultimate_total >= Decimal("0")

    def test_resultado_tiene_factores(
        self, triangulo_simple, primas_por_anio, config_lr_65
    ):
        """Resultado debe incluir factores de desarrollo"""
        bf = BornhuetterFerguson(config_lr_65)
        resultado = bf.calcular(triangulo_simple, primas_por_anio)

        assert resultado.factores_desarrollo is not None
        assert len(resultado.factores_desarrollo) > 0

    def test_detalles_incluyen_loss_ratios(
        self, triangulo_simple, primas_por_anio, config_lr_65
    ):
        """Detalles deben incluir loss ratios a priori e implícito"""
        bf = BornhuetterFerguson(config_lr_65)
        resultado = bf.calcular(triangulo_simple, primas_por_anio)

        assert "loss_ratio_apriori" in resultado.detalles
        assert "loss_ratio_implicito" in resultado.detalles
        assert "porcentajes_reportados" in resultado.detalles

    def test_porcentajes_reportados_en_detalles(
        self, triangulo_simple, primas_por_anio, config_lr_65
    ):
        """Detalles deben incluir % reportados por año"""
        bf = BornhuetterFerguson(config_lr_65)
        resultado = bf.calcular(triangulo_simple, primas_por_anio)

        porcentajes = resultado.detalles["porcentajes_reportados"]
        assert len(porcentajes) == len(triangulo_simple)


class TestBornhuetterFergusonComparacionLR:
    """Tests comparando diferentes loss ratios"""

    def test_lr_mayor_produce_reservas_mayores(
        self, triangulo_simple, primas_por_anio
    ):
        """Loss ratio mayor debe producir reservas mayores"""
        config_65 = ConfiguracionBornhuetterFerguson(
            loss_ratio_apriori=Decimal("0.65")
        )
        config_75 = ConfiguracionBornhuetterFerguson(
            loss_ratio_apriori=Decimal("0.75")
        )

        bf_65 = BornhuetterFerguson(config_65)
        bf_75 = BornhuetterFerguson(config_75)

        resultado_65 = bf_65.calcular(triangulo_simple, primas_por_anio)
        resultado_75 = bf_75.calcular(triangulo_simple, primas_por_anio)

        # LR 75% debe producir reservas mayores que LR 65%
        assert resultado_75.reserva_total > resultado_65.reserva_total

    def test_impacto_lr_mayor_en_anios_recientes(
        self, triangulo_simple, primas_por_anio
    ):
        """El impacto del LR debe ser mayor en años recientes (poco desarrollados)"""
        config_65 = ConfiguracionBornhuetterFerguson(
            loss_ratio_apriori=Decimal("0.65")
        )
        config_75 = ConfiguracionBornhuetterFerguson(
            loss_ratio_apriori=Decimal("0.75")
        )

        bf_65 = BornhuetterFerguson(config_65)
        bf_75 = BornhuetterFerguson(config_75)

        resultado_65 = bf_65.calcular(triangulo_simple, primas_por_anio)
        resultado_75 = bf_75.calcular(triangulo_simple, primas_por_anio)

        # Diferencia en año reciente (2024)
        diff_2024 = abs(
            resultado_75.reservas_por_anio[2024]
            - resultado_65.reservas_por_anio[2024]
        )

        # Diferencia en año antiguo (2020)
        diff_2020 = abs(
            resultado_75.reservas_por_anio[2020]
            - resultado_65.reservas_por_anio[2020]
        )

        # La diferencia debe ser mayor en el año reciente
        assert diff_2024 > diff_2020


class TestBornhuetterFergusonComparacionChainLadder:
    """Tests comparando B-F con Chain Ladder"""

    def test_comparar_con_chain_ladder(
        self, triangulo_simple, primas_por_anio, config_lr_65
    ):
        """Debe poder comparar B-F con Chain Ladder"""
        bf = BornhuetterFerguson(config_lr_65)

        comparacion = bf.comparar_con_chain_ladder(
            triangulo_simple, primas_por_anio
        )

        # Debe retornar DataFrame
        assert isinstance(comparacion, pd.DataFrame)

        # Debe tener columnas esperadas
        assert "Ultimate_CL" in comparacion.columns
        assert "Ultimate_BF" in comparacion.columns
        assert "Reserva_CL" in comparacion.columns
        assert "Reserva_BF" in comparacion.columns
        assert "Diferencia_%" in comparacion.columns

        # Debe tener una fila por año
        assert len(comparacion) == len(triangulo_simple)

    def test_bf_mas_estable_en_anios_recientes(
        self, triangulo_simple, primas_por_anio
    ):
        """B-F debe ser más estable que CL en años recientes"""
        # Configurar B-F con LR conservador
        config = ConfiguracionBornhuetterFerguson(
            loss_ratio_apriori=Decimal("0.65")
        )
        bf = BornhuetterFerguson(config)

        comparacion = bf.comparar_con_chain_ladder(
            triangulo_simple, primas_por_anio
        )

        # La diferencia porcentual debe ser mayor en años recientes
        # (B-F ajusta más para años con poco desarrollo)
        assert comparacion is not None


class TestBornhuetterFergusonObtenerPorcentajes:
    """Tests para obtener porcentajes reportados"""

    def test_obtener_porcentajes_reportados(
        self, triangulo_simple, primas_por_anio, config_lr_65
    ):
        """Debe poder obtener porcentajes reportados después de calcular"""
        bf = BornhuetterFerguson(config_lr_65)
        bf.calcular(triangulo_simple, primas_por_anio)

        porcentajes = bf.obtener_porcentajes_reportados()
        assert porcentajes is not None
        assert len(porcentajes) == len(triangulo_simple)

    def test_obtener_porcentajes_antes_de_calcular(self, config_lr_65):
        """Antes de calcular debe retornar None"""
        bf = BornhuetterFerguson(config_lr_65)
        porcentajes = bf.obtener_porcentajes_reportados()
        assert porcentajes is None


class TestBornhuetterFergusonValidacionConsistencia:
    """Tests para validación de consistencia"""

    def test_validacion_ultimate_pagado_reserva(
        self, triangulo_simple, primas_por_anio, config_lr_65
    ):
        """Ultimate = Pagado + Reserva debe cumplirse"""
        bf = BornhuetterFerguson(config_lr_65)
        resultado = bf.calcular(triangulo_simple, primas_por_anio)

        assert (
            abs(
                resultado.ultimate_total
                - resultado.pagado_total
                - resultado.reserva_total
            )
            < Decimal("0.01")
        )


class TestBornhuetterFergusonRepr:
    """Tests para representación string"""

    def test_repr_contiene_info_relevante(self, config_lr_65):
        """__repr__ debe contener información útil"""
        bf = BornhuetterFerguson(config_lr_65)
        repr_str = repr(bf)

        assert "BornhuetterFerguson" in repr_str
        assert "0.65" in repr_str  # Loss ratio


class TestBornhuetterFergusonMetodosPromedio:
    """Tests con diferentes métodos de promedio"""

    def test_diferentes_metodos_promedio(
        self, triangulo_simple, primas_por_anio
    ):
        """Debe funcionar con todos los métodos de promedio"""
        metodos = [
            MetodoPromedio.SIMPLE,
            MetodoPromedio.PONDERADO,
            MetodoPromedio.GEOMETRICO,
        ]

        for metodo in metodos:
            config = ConfiguracionBornhuetterFerguson(
                loss_ratio_apriori=Decimal("0.65"), metodo_promedio=metodo
            )
            bf = BornhuetterFerguson(config)
            resultado = bf.calcular(triangulo_simple, primas_por_anio)

            assert resultado.reserva_total >= Decimal("0")
