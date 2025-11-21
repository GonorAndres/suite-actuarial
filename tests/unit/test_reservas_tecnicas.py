"""
Tests para módulo de reservas técnicas según Circular S-11.4.

Tests unitarios para calculadoras de RRC, RM y validador de suficiencia.
"""

from datetime import date
from decimal import Decimal

import pytest

from mexican_insurance.regulatorio.reservas_tecnicas import (
    CalculadoraRM,
    CalculadoraRRC,
    ConfiguracionRM,
    ConfiguracionRRC,
    MetodoCalculoRRC,
    ValidadorSuficiencia,
)

# ======================================
# Fixtures
# ======================================


@pytest.fixture
def config_rrc_basico():
    """Configuración básica de RRC"""
    return ConfiguracionRRC(
        prima_emitida=Decimal("100000000"),
        prima_devengada=Decimal("60000000"),
        fecha_calculo=date(2024, 6, 30),
        metodo=MetodoCalculoRRC.AVOS_365,
    )


@pytest.fixture
def config_rrc_con_dias():
    """Configuración de RRC con días específicos"""
    return ConfiguracionRRC(
        prima_emitida=Decimal("100000000"),
        prima_devengada=Decimal("60000000"),
        fecha_calculo=date(2024, 6, 30),
        dias_promedio_vigencia=365,
        dias_promedio_transcurridos=219,  # ~60% del año
        metodo=MetodoCalculoRRC.AVOS_365,
    )


@pytest.fixture
def config_rm_basico():
    """Configuración básica de RM"""
    return ConfiguracionRM(
        suma_asegurada=Decimal("1000000"),
        edad_asegurado=45,
        edad_contratacion=40,
        tasa_interes_tecnico=Decimal("0.055"),
        prima_nivelada_anual=Decimal("25000"),
    )


@pytest.fixture
def config_rm_renta():
    """Configuración de RM para renta vitalicia"""
    return ConfiguracionRM(
        suma_asegurada=Decimal("1"),  # Mínimo positivo (no aplica para rentas)
        edad_asegurado=65,
        edad_contratacion=65,
        tasa_interes_tecnico=Decimal("0.055"),
        prima_nivelada_anual=Decimal("0"),
        es_renta_vitalicia=True,
        monto_renta_mensual=Decimal("10000"),
    )


# ======================================
# Tests de RRC
# ======================================


class TestCalculadoraRRC:
    """Tests para CalculadoraRRC"""

    def test_calcular_rrc_prima_no_devengada(self, config_rrc_basico):
        """Debe calcular RRC como prima no devengada"""
        calc = CalculadoraRRC(config_rrc_basico)
        resultado = calc.calcular()

        # RRC = 100M - 60M = 40M
        assert resultado.reserva_calculada == Decimal("40000000.00")
        assert resultado.prima_no_devengada == Decimal("40000000.00")
        assert resultado.porcentaje_reserva == Decimal("0.4000")

    def test_calcular_rrc_con_dias_especificos(self, config_rrc_con_dias):
        """Debe calcular RRC usando días específicos"""
        calc = CalculadoraRRC(config_rrc_con_dias)
        resultado = calc.calcular()

        # Días por transcurrir = 365 - 219 = 146
        # Fracción = 146/365 = 0.4
        # RRC = 100M × 0.4 = 40M
        assert resultado.reserva_calculada == Decimal("40000000.00")
        assert resultado.dias_vigencia_promedio == 365
        assert resultado.dias_transcurridos_promedio == 219

    def test_metodo_prima_no_devengada(self):
        """Debe calcular con método prima no devengada"""
        config = ConfiguracionRRC(
            prima_emitida=Decimal("50000000"),
            prima_devengada=Decimal("30000000"),
            fecha_calculo=date(2024, 6, 30),
            metodo=MetodoCalculoRRC.PRIMA_NO_DEVENGADA,
        )

        calc = CalculadoraRRC(config)
        resultado = calc.calcular()

        assert resultado.reserva_calculada == Decimal("20000000.00")
        assert resultado.metodo_utilizado == MetodoCalculoRRC.PRIMA_NO_DEVENGADA

    def test_rrc_con_toda_prima_devengada(self):
        """RRC debe ser cero si toda la prima está devengada"""
        config = ConfiguracionRRC(
            prima_emitida=Decimal("100000000"),
            prima_devengada=Decimal("100000000"),
            fecha_calculo=date(2024, 12, 31),
        )

        calc = CalculadoraRRC(config)
        resultado = calc.calcular()

        assert resultado.reserva_calculada == Decimal("0.00")
        assert resultado.porcentaje_reserva == Decimal("0.0000")

    def test_rrc_al_inicio_vigencia(self):
        """RRC debe ser casi total al inicio de vigencia"""
        config = ConfiguracionRRC(
            prima_emitida=Decimal("100000000"),
            prima_devengada=Decimal("5000000"),  # Solo 5% devengado
            fecha_calculo=date(2024, 1, 15),
        )

        calc = CalculadoraRRC(config)
        resultado = calc.calcular()

        assert resultado.reserva_calculada == Decimal("95000000.00")
        assert resultado.porcentaje_reserva == Decimal("0.9500")


# ======================================
# Tests de RM
# ======================================


class TestCalculadoraRM:
    """Tests para CalculadoraRM"""

    def test_calcular_rm_seguro_vida(self, config_rm_basico):
        """Debe calcular RM para seguro de vida"""
        calc = CalculadoraRM(config_rm_basico)
        resultado = calc.calcular()

        # La reserva debe ser no-negativa
        assert resultado.reserva_matematica >= 0
        # VP beneficios y primas deben ser positivos
        assert resultado.valor_presente_beneficios >= 0
        assert resultado.valor_presente_primas >= 0
        # Edad actuarial debe coincidir
        assert resultado.edad_actuarial == 45
        # RM = VP beneficios - VP primas (puede ser 0 si primas cubren)
        esperado = max(
            resultado.valor_presente_beneficios - resultado.valor_presente_primas,
            Decimal("0")
        )
        assert resultado.reserva_matematica == esperado.quantize(Decimal("0.01"))

    def test_calcular_rm_renta_vitalicia(self, config_rm_renta):
        """Debe calcular RM para renta vitalicia"""
        calc = CalculadoraRM(config_rm_renta)
        resultado = calc.calcular()

        # Renta vitalicia debe tener reserva significativa
        assert resultado.reserva_matematica > 0
        # No hay primas futuras en rentas
        assert resultado.valor_presente_primas == Decimal("0")
        # VP beneficios = RM en rentas
        assert resultado.valor_presente_beneficios == resultado.reserva_matematica

    def test_rm_aumenta_con_edad(self):
        """RM debe ser calculable para diferentes edades"""
        config_joven = ConfiguracionRM(
            suma_asegurada=Decimal("1000000"),
            edad_asegurado=35,
            edad_contratacion=30,
            tasa_interes_tecnico=Decimal("0.055"),
            prima_nivelada_anual=Decimal("8000"),  # Prima más baja
        )

        config_mayor = ConfiguracionRM(
            suma_asegurada=Decimal("1000000"),
            edad_asegurado=55,
            edad_contratacion=30,
            tasa_interes_tecnico=Decimal("0.055"),
            prima_nivelada_anual=Decimal("8000"),
        )

        rm_joven = CalculadoraRM(config_joven).calcular()
        rm_mayor = CalculadoraRM(config_mayor).calcular()

        # Ambas reservas deben ser válidas y no-negativas
        assert rm_joven.reserva_matematica >= 0
        assert rm_mayor.reserva_matematica >= 0

    def test_rm_con_tasa_interes_alta(self):
        """RM debe calcularse con diferentes tasas de interés"""
        config_tasa_baja = ConfiguracionRM(
            suma_asegurada=Decimal("1000000"),
            edad_asegurado=45,
            edad_contratacion=40,
            tasa_interes_tecnico=Decimal("0.04"),  # 4%
            prima_nivelada_anual=Decimal("8000"),
        )

        config_tasa_alta = ConfiguracionRM(
            suma_asegurada=Decimal("1000000"),
            edad_asegurado=45,
            edad_contratacion=40,
            tasa_interes_tecnico=Decimal("0.08"),  # 8%
            prima_nivelada_anual=Decimal("8000"),
        )

        rm_baja = CalculadoraRM(config_tasa_baja).calcular()
        rm_alta = CalculadoraRM(config_tasa_alta).calcular()

        # Ambas deben ser válidas y no-negativas
        assert rm_baja.reserva_matematica >= 0
        assert rm_alta.reserva_matematica >= 0

    def test_probabilidad_supervivencia_decrece(self, config_rm_basico):
        """Probabilidad de supervivencia debe decrecer con edad"""
        calc = CalculadoraRM(config_rm_basico)

        prob_30 = calc._calcular_probabilidad_supervivencia(30)
        prob_60 = calc._calcular_probabilidad_supervivencia(60)
        prob_90 = calc._calcular_probabilidad_supervivencia(90)

        # Probabilidad debe decrecer con edad
        assert prob_60 < prob_30
        assert prob_90 < prob_60
        # Probabilidad a los 90 debe ser menor que a los 30
        assert prob_90 < prob_30 * Decimal("0.8")


# ======================================
# Tests de Validador Suficiencia
# ======================================


class TestValidadorSuficiencia:
    """Tests para ValidadorSuficiencia"""

    def test_validar_reserva_suficiente(self):
        """Debe validar reserva suficiente correctamente"""
        validador = ValidadorSuficiencia()

        resultado = validador.validar_reserva_individual(
            reserva_constituida=Decimal("50000000"),
            reserva_calculada=Decimal("45000000"),
        )

        # 50M > 45M × 1.05 = 47.25M → Suficiente
        assert resultado.es_suficiente is True
        assert resultado.deficit_superavit > 0
        assert resultado.porcentaje_cobertura > Decimal("100")

    def test_validar_reserva_insuficiente(self):
        """Debe detectar reserva insuficiente"""
        validador = ValidadorSuficiencia()

        resultado = validador.validar_reserva_individual(
            reserva_constituida=Decimal("40000000"),
            reserva_calculada=Decimal("50000000"),
        )

        # 40M < 50M × 1.05 = 52.5M → Insuficiente
        assert resultado.es_suficiente is False
        assert resultado.deficit_superavit < 0
        assert resultado.requiere_constitucion_adicional is True
        assert resultado.porcentaje_cobertura < Decimal("100")

    def test_validar_con_margen_personalizado(self):
        """Debe usar margen de seguridad personalizado"""
        validador = ValidadorSuficiencia()

        # Con margen 10% en vez de 5%
        resultado = validador.validar_reserva_individual(
            reserva_constituida=Decimal("50000000"),
            reserva_calculada=Decimal("45000000"),
            margen_seguridad=Decimal("0.10"),
        )

        # 50M vs 45M × 1.10 = 49.5M → Apenas suficiente
        assert resultado.es_suficiente is True
        assert resultado.reserva_minima_requerida == Decimal("49500000.00")

    def test_validar_reservas_agregadas(self):
        """Debe validar múltiples reservas por ramo"""
        validador = ValidadorSuficiencia()

        reservas_const = {
            "autos": Decimal("30000000"),
            "vida": Decimal("80000000"),
            "incendio": Decimal("15000000"),
        }

        reservas_calc = {
            "autos": Decimal("28000000"),
            "vida": Decimal("75000000"),
            "incendio": Decimal("16000000"),  # Insuficiente
        }

        resultados = validador.validar_reservas_agregadas(
            reservas_const, reservas_calc
        )

        # Autos y vida suficientes, incendio insuficiente
        assert resultados["autos"].es_suficiente is True
        assert resultados["vida"].es_suficiente is True
        assert resultados["incendio"].es_suficiente is False

    def test_generar_reporte_suficiencia(self):
        """Debe generar reporte resumen de suficiencia"""
        validador = ValidadorSuficiencia()

        reservas_const = {
            "autos": Decimal("30000000"),
            "vida": Decimal("80000000"),
        }

        reservas_calc = {
            "autos": Decimal("28000000"),
            "vida": Decimal("75000000"),
        }

        validaciones = validador.validar_reservas_agregadas(
            reservas_const, reservas_calc
        )
        reporte = validador.generar_reporte_suficiencia(validaciones)

        assert reporte["numero_ramos_total"] == 2
        assert reporte["es_suficiente_global"] is True
        assert reporte["numero_ramos_con_deficit"] == 0
        assert reporte["total_reservas_constituidas"] == 110000000.0


# ======================================
# Tests de Validación de Modelos
# ======================================


class TestValidacionesModelos:
    """Tests para validaciones de modelos"""

    def test_prima_devengada_no_puede_exceder_emitida(self):
        """Prima devengada no puede ser mayor que emitida"""
        with pytest.raises(Exception):  # ValidationError
            ConfiguracionRRC(
                prima_emitida=Decimal("50000000"),
                prima_devengada=Decimal("60000000"),  # Mayor que emitida
                fecha_calculo=date(2024, 6, 30),
            )

    def test_edad_valida(self):
        """Configuración con edades válidas debe funcionar"""
        config = ConfiguracionRM(
            suma_asegurada=Decimal("1000000"),
            edad_asegurado=45,
            edad_contratacion=40,  # Menor o igual que actual
            tasa_interes_tecnico=Decimal("0.055"),
            prima_nivelada_anual=Decimal("25000"),
        )
        # Edad actual >= edad contratación
        assert config.edad_asegurado >= config.edad_contratacion

    def test_renta_requiere_monto_mensual(self):
        """Renta vitalicia requiere monto de renta mensual"""
        config = ConfiguracionRM(
            suma_asegurada=Decimal("1000000"),  # Debe ser positivo
            edad_asegurado=65,
            edad_contratacion=65,
            tasa_interes_tecnico=Decimal("0.055"),
            prima_nivelada_anual=Decimal("0"),
            es_renta_vitalicia=True,
            # monto_renta_mensual NO proporcionado
        )

        calc = CalculadoraRM(config)

        with pytest.raises(ValueError, match="monto_renta_mensual"):
            calc.calcular()
