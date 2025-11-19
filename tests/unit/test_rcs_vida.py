"""
Tests para RCS Vida.

Valida cálculo de requerimiento de capital de solvencia para riesgos
de suscripción en seguros de vida.
"""

from decimal import Decimal

import pytest

from mexican_insurance.core.validators import ConfiguracionRCSVida
from mexican_insurance.regulatorio.rcs_vida import RCSVida


@pytest.fixture
def config_vida_basico():
    """Configuración básica de RCS vida"""
    return ConfiguracionRCSVida(
        suma_asegurada_total=Decimal("500000000"),  # 500M
        reserva_matematica=Decimal("350000000"),  # 350M
        edad_promedio_asegurados=45,
        duracion_promedio_polizas=15,
        numero_asegurados=10000,
    )


@pytest.fixture
def config_vida_cartera_joven():
    """Configuración con cartera joven"""
    return ConfiguracionRCSVida(
        suma_asegurada_total=Decimal("200000000"),
        reserva_matematica=Decimal("100000000"),
        edad_promedio_asegurados=30,
        duracion_promedio_polizas=20,
        numero_asegurados=5000,
    )


@pytest.fixture
def config_vida_cartera_madura():
    """Configuración con cartera madura (edad avanzada)"""
    return ConfiguracionRCSVida(
        suma_asegurada_total=Decimal("300000000"),
        reserva_matematica=Decimal("250000000"),
        edad_promedio_asegurados=65,
        duracion_promedio_polizas=10,
        numero_asegurados=15000,
    )


class TestRCSVidaCreacion:
    """Tests para creación de RCS Vida"""

    def test_crear_rcs_vida_valido(self, config_vida_basico):
        """Debe crear RCS Vida válido"""
        rcs = RCSVida(config_vida_basico)
        assert rcs.config.suma_asegurada_total == Decimal("500000000")

    def test_repr_contiene_info(self, config_vida_basico):
        """__repr__ debe contener información útil"""
        rcs = RCSVida(config_vida_basico)
        repr_str = repr(rcs)
        assert "RCSVida" in repr_str
        assert ("500000000" in repr_str or "500,000,000" in repr_str)


class TestRCSMortalidad:
    """Tests para RCS de mortalidad"""

    def test_calcular_rcs_mortalidad_positivo(self, config_vida_basico):
        """RCS mortalidad debe ser positivo"""
        rcs = RCSVida(config_vida_basico)
        rcs_mort = rcs.calcular_rcs_mortalidad()
        assert rcs_mort > Decimal("0")

    def test_mortalidad_mayor_en_edad_avanzada(
        self, config_vida_cartera_joven, config_vida_cartera_madura
    ):
        """RCS mortalidad debe ser mayor para cartera de mayor edad"""
        rcs_joven = RCSVida(config_vida_cartera_joven)
        rcs_madura = RCSVida(config_vida_cartera_madura)

        mort_joven = rcs_joven.calcular_rcs_mortalidad()
        mort_madura = rcs_madura.calcular_rcs_mortalidad()

        # Cartera madura debe tener mayor RCS mortalidad
        # (ajustado por suma asegurada)
        ratio_joven = (
            mort_joven / config_vida_cartera_joven.suma_asegurada_total
        )
        ratio_madura = (
            mort_madura / config_vida_cartera_madura.suma_asegurada_total
        )

        assert ratio_madura > ratio_joven

    def test_mortalidad_escala_con_suma_asegurada(self):
        """RCS mortalidad debe escalar con suma asegurada"""
        config_pequeña = ConfiguracionRCSVida(
            suma_asegurada_total=Decimal("100000000"),
            reserva_matematica=Decimal("70000000"),
            edad_promedio_asegurados=40,
            duracion_promedio_polizas=15,
            numero_asegurados=10000,
        )

        config_grande = ConfiguracionRCSVida(
            suma_asegurada_total=Decimal("200000000"),
            reserva_matematica=Decimal("140000000"),
            edad_promedio_asegurados=40,
            duracion_promedio_polizas=15,
            numero_asegurados=10000,
        )

        rcs_pequeña = RCSVida(config_pequeña).calcular_rcs_mortalidad()
        rcs_grande = RCSVida(config_grande).calcular_rcs_mortalidad()

        # Debe escalar aproximadamente proporcional
        ratio = rcs_grande / rcs_pequeña
        assert Decimal("1.8") < ratio < Decimal("2.2")


class TestRCSLongevidad:
    """Tests para RCS de longevidad"""

    def test_calcular_rcs_longevidad_positivo(self, config_vida_basico):
        """RCS longevidad debe ser positivo"""
        rcs = RCSVida(config_vida_basico)
        rcs_long = rcs.calcular_rcs_longevidad()
        assert rcs_long > Decimal("0")

    def test_longevidad_escala_con_reserva(self):
        """RCS longevidad debe escalar con reserva matemática"""
        config_1 = ConfiguracionRCSVida(
            suma_asegurada_total=Decimal("500000000"),
            reserva_matematica=Decimal("200000000"),
            edad_promedio_asegurados=50,
            duracion_promedio_polizas=15,
        )

        config_2 = ConfiguracionRCSVida(
            suma_asegurada_total=Decimal("500000000"),
            reserva_matematica=Decimal("400000000"),
            edad_promedio_asegurados=50,
            duracion_promedio_polizas=15,
        )

        long_1 = RCSVida(config_1).calcular_rcs_longevidad()
        long_2 = RCSVida(config_2).calcular_rcs_longevidad()

        # Mayor reserva debe dar mayor RCS
        assert long_2 > long_1


class TestRCSInvalidez:
    """Tests para RCS de invalidez"""

    def test_calcular_rcs_invalidez_positivo(self, config_vida_basico):
        """RCS invalidez debe ser positivo"""
        rcs = RCSVida(config_vida_basico)
        rcs_inv = rcs.calcular_rcs_invalidez()
        assert rcs_inv > Decimal("0")

    def test_invalidez_menor_que_mortalidad(self, config_vida_basico):
        """RCS invalidez típicamente menor que mortalidad"""
        rcs = RCSVida(config_vida_basico)
        rcs_inv = rcs.calcular_rcs_invalidez()
        rcs_mort = rcs.calcular_rcs_mortalidad()

        # Invalidez debería ser menor (es menos frecuente)
        assert rcs_inv < rcs_mort


class TestRCSGastos:
    """Tests para RCS de gastos"""

    def test_calcular_rcs_gastos_positivo(self, config_vida_basico):
        """RCS gastos debe ser positivo"""
        rcs = RCSVida(config_vida_basico)
        rcs_gastos = rcs.calcular_rcs_gastos()
        assert rcs_gastos > Decimal("0")

    def test_gastos_economias_escala(self):
        """Cartera más grande debe tener menor RCS gastos relativo"""
        config_pequeña = ConfiguracionRCSVida(
            suma_asegurada_total=Decimal("100000000"),
            reserva_matematica=Decimal("70000000"),
            edad_promedio_asegurados=40,
            duracion_promedio_polizas=15,
            numero_asegurados=1000,
        )

        config_grande = ConfiguracionRCSVida(
            suma_asegurada_total=Decimal("100000000"),
            reserva_matematica=Decimal("70000000"),
            edad_promedio_asegurados=40,
            duracion_promedio_polizas=15,
            numero_asegurados=50000,
        )

        gastos_pequeña = RCSVida(config_pequeña).calcular_rcs_gastos()
        gastos_grande = RCSVida(config_grande).calcular_rcs_gastos()

        # Economías de escala: más asegurados = menor gasto relativo
        assert gastos_grande < gastos_pequeña


class TestRCSTotalVida:
    """Tests para RCS total vida"""

    def test_calcular_rcs_total_vida(self, config_vida_basico):
        """Debe calcular RCS total vida"""
        rcs = RCSVida(config_vida_basico)
        rcs_total, desglose = rcs.calcular_rcs_total_vida()

        assert rcs_total > Decimal("0")
        assert "mortalidad" in desglose
        assert "longevidad" in desglose
        assert "invalidez" in desglose
        assert "gastos" in desglose

    def test_rcs_total_menor_que_suma_componentes(self, config_vida_basico):
        """RCS total debe ser menor que suma simple (por correlación)"""
        rcs = RCSVida(config_vida_basico)
        rcs_total, desglose = rcs.calcular_rcs_total_vida()

        suma_simple = sum(desglose.values())

        # Agregación con raíz cuadrada debe ser menor que suma
        assert rcs_total < suma_simple

    def test_desglose_suma_coherente(self, config_vida_basico):
        """Desglose debe tener valores coherentes"""
        rcs = RCSVida(config_vida_basico)
        rcs_total, desglose = rcs.calcular_rcs_total_vida()

        # Todos los componentes deben ser positivos
        for nombre, valor in desglose.items():
            assert valor > Decimal("0"), f"{nombre} debe ser positivo"

        # Mortalidad típicamente es el mayor componente
        assert desglose["mortalidad"] >= desglose["gastos"]


class TestFactoresAplicados:
    """Tests para obtener factores aplicados"""

    def test_obtener_factores_aplicados(self, config_vida_basico):
        """Debe obtener factores intermedios"""
        rcs = RCSVida(config_vida_basico)
        factores = rcs.obtener_factores_aplicados()

        assert "factor_edad_mortalidad" in factores
        assert "factor_diversificacion" in factores
        assert "numero_asegurados" in factores

        # Factores deben estar en rangos razonables
        assert factores["factor_edad_mortalidad"] > Decimal("0")
        assert factores["factor_diversificacion"] > Decimal("0")


class TestValidacionesConfiguracion:
    """Tests para validaciones de configuración"""

    def test_suma_asegurada_debe_ser_positiva(self):
        """Suma asegurada debe ser positiva"""
        with pytest.raises(ValueError):
            ConfiguracionRCSVida(
                suma_asegurada_total=Decimal("0"),
                reserva_matematica=Decimal("100000"),
                edad_promedio_asegurados=40,
                duracion_promedio_polizas=10,
            )

    def test_reserva_muy_alta_vs_suma_asegurada(self):
        """Reserva no debería exceder mucho la suma asegurada"""
        with pytest.raises(ValueError, match="muy alta"):
            ConfiguracionRCSVida(
                suma_asegurada_total=Decimal("100000000"),
                reserva_matematica=Decimal(
                    "300000000"
                ),  # 3x suma asegurada
                edad_promedio_asegurados=40,
                duracion_promedio_polizas=10,
            )

    def test_edad_en_rango_valido(self):
        """Edad debe estar en rango válido"""
        with pytest.raises(ValueError):
            ConfiguracionRCSVida(
                suma_asegurada_total=Decimal("100000000"),
                reserva_matematica=Decimal("70000000"),
                edad_promedio_asegurados=150,  # Inválido
                duracion_promedio_polizas=10,
            )


class TestCasosEspeciales:
    """Tests para casos especiales"""

    def test_cartera_muy_pequeña(self):
        """Cartera con pocos asegurados debe tener RCS alto"""
        config = ConfiguracionRCSVida(
            suma_asegurada_total=Decimal("10000000"),
            reserva_matematica=Decimal("7000000"),
            edad_promedio_asegurados=40,
            duracion_promedio_polizas=15,
            numero_asegurados=100,  # Muy pocos
        )

        rcs = RCSVida(config)
        rcs_mort = rcs.calcular_rcs_mortalidad()

        # RCS relativo debe ser alto para carteras pequeñas
        ratio = rcs_mort / config.suma_asegurada_total
        assert ratio > Decimal("0.005")  # > 0.5%

    def test_duracion_muy_larga(self):
        """Duración muy larga debe aumentar RCS longevidad"""
        config_corta = ConfiguracionRCSVida(
            suma_asegurada_total=Decimal("100000000"),
            reserva_matematica=Decimal("70000000"),
            edad_promedio_asegurados=50,
            duracion_promedio_polizas=5,
        )

        config_larga = ConfiguracionRCSVida(
            suma_asegurada_total=Decimal("100000000"),
            reserva_matematica=Decimal("70000000"),
            edad_promedio_asegurados=50,
            duracion_promedio_polizas=30,
        )

        long_corta = RCSVida(config_corta).calcular_rcs_longevidad()
        long_larga = RCSVida(config_larga).calcular_rcs_longevidad()

        assert long_larga > long_corta
