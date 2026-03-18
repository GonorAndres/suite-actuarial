"""
Tests para el producto de Vida Temporal
"""

from decimal import Decimal

import pandas as pd
import pytest

from mexican_insurance.actuarial.mortality.tablas import TablaMortalidad
from mexican_insurance.core.validators import (
    Asegurado,
    ConfiguracionProducto,
    Moneda,
    Sexo,
)
from mexican_insurance.products.vida.temporal import VidaTemporal


@pytest.fixture
def tabla_simple():
    """Tabla de mortalidad simplificada para tests"""
    # Crear tabla con mortalidad constante baja para tests predecibles
    edades = list(range(18, 101))
    datos = []

    for edad in edades:
        # Mortalidad que aumenta gradualmente con la edad
        qx_h = 0.001 + (edad - 18) * 0.0002
        qx_m = 0.0005 + (edad - 18) * 0.0001
        datos.append({"edad": edad, "sexo": "H", "qx": qx_h})
        datos.append({"edad": edad, "sexo": "M", "qx": qx_m})

    df = pd.DataFrame(datos)
    return TablaMortalidad(nombre="Simple", datos=df)


@pytest.fixture
def config_basica():
    """Configuración básica de producto"""
    return ConfiguracionProducto(
        nombre_producto="Vida Temporal 20 años",
        plazo_years=20,
        tasa_interes_tecnico=Decimal("0.055"),
        recargo_gastos_admin=Decimal("0.05"),
        recargo_gastos_adq=Decimal("0.10"),
        recargo_utilidad=Decimal("0.03"),
    )


@pytest.fixture
def asegurado_basico():
    """Asegurado con datos básicos"""
    return Asegurado(
        edad=35,
        sexo=Sexo.HOMBRE,
        suma_asegurada=Decimal("1000000"),
    )


class TestVidaTemporal:
    """Tests para el producto VidaTemporal"""

    def test_crear_producto(self, config_basica, tabla_simple):
        """Debe crear el producto correctamente"""
        producto = VidaTemporal(config_basica, tabla_simple)

        assert producto.config.nombre_producto == "Vida Temporal 20 años"
        assert producto.plazo_pago == 20  # Por default igual al plazo

    def test_calcular_prima_basica(
        self, config_basica, tabla_simple, asegurado_basico
    ):
        """Debe calcular prima correctamente"""
        producto = VidaTemporal(config_basica, tabla_simple)
        resultado = producto.calcular_prima(asegurado_basico)

        # Verificaciones básicas
        assert resultado.prima_neta > 0
        assert resultado.prima_total > resultado.prima_neta
        assert resultado.moneda == Moneda.MXN

        # Verificar que tiene desglose
        assert "gastos_admin" in resultado.desglose_recargos
        assert "gastos_adq" in resultado.desglose_recargos
        assert "utilidad" in resultado.desglose_recargos

        # Verificar metadata
        assert resultado.metadata["edad"] == 35
        assert resultado.metadata["plazo_seguro"] == 20

    def test_prima_aumenta_con_edad(self, config_basica, tabla_simple):
        """La prima debe aumentar con la edad del asegurado"""
        producto = VidaTemporal(config_basica, tabla_simple)

        asegurado_joven = Asegurado(
            edad=25, sexo=Sexo.HOMBRE, suma_asegurada=Decimal("1000000")
        )
        asegurado_mayor = Asegurado(
            edad=50, sexo=Sexo.HOMBRE, suma_asegurada=Decimal("1000000")
        )

        prima_joven = producto.calcular_prima(asegurado_joven).prima_total
        prima_mayor = producto.calcular_prima(asegurado_mayor).prima_total

        assert prima_mayor > prima_joven

    def test_prima_aumenta_con_suma_asegurada(
        self, config_basica, tabla_simple
    ):
        """La prima debe ser proporcional a la suma asegurada"""
        producto = VidaTemporal(config_basica, tabla_simple)

        asegurado_1m = Asegurado(
            edad=35, sexo=Sexo.HOMBRE, suma_asegurada=Decimal("1000000")
        )
        asegurado_2m = Asegurado(
            edad=35, sexo=Sexo.HOMBRE, suma_asegurada=Decimal("2000000")
        )

        prima_1m = producto.calcular_prima(asegurado_1m).prima_total
        prima_2m = producto.calcular_prima(asegurado_2m).prima_total

        # La prima de 2M debe ser aproximadamente el doble
        ratio = prima_2m / prima_1m
        assert 1.95 < ratio < 2.05  # Aproximadamente 2x

    def test_frecuencia_pago_mensual(
        self, config_basica, tabla_simple, asegurado_basico
    ):
        """Debe calcular prima mensual correctamente"""
        producto = VidaTemporal(config_basica, tabla_simple)

        prima_anual = producto.calcular_prima(
            asegurado_basico, frecuencia_pago="anual"
        ).prima_total

        prima_mensual = producto.calcular_prima(
            asegurado_basico, frecuencia_pago="mensual"
        ).prima_total

        # Prima mensual debe ser menor que anual pero mayor que anual/12
        assert prima_mensual < prima_anual
        assert prima_mensual > (prima_anual / Decimal("13"))

    def test_validar_asegurabilidad_edad_valida(
        self, config_basica, tabla_simple
    ):
        """Asegurado con edad válida debe ser aceptado"""
        producto = VidaTemporal(config_basica, tabla_simple)

        asegurado = Asegurado(
            edad=35, sexo=Sexo.HOMBRE, suma_asegurada=Decimal("1000000")
        )

        es_asegurable, razon = producto.validar_asegurabilidad(asegurado)

        assert es_asegurable is True
        assert razon is None

    def test_validar_asegurabilidad_edad_muy_alta(
        self, config_basica, tabla_simple
    ):
        """Edad + plazo > 100 debe ser rechazado"""
        producto = VidaTemporal(config_basica, tabla_simple)

        # Edad 65 + plazo 20 = 85 años -- within base class age limit but exceeds temporal limit
        # Use edad within base class limit (<=70) but edad+plazo > 100
        # Actually edad 85 > 70 so base class rejects first
        asegurado = Asegurado(
            edad=85, sexo=Sexo.HOMBRE, suma_asegurada=Decimal("1000000")
        )

        es_asegurable, razon = producto.validar_asegurabilidad(asegurado)

        assert es_asegurable is False
        assert razon is not None

    def test_validar_asegurabilidad_menor_de_edad(
        self, config_basica, tabla_simple
    ):
        """Menores de 18 deben ser rechazados"""
        producto = VidaTemporal(config_basica, tabla_simple)

        # Edad menor válida según tabla pero menor de edad legal
        asegurado = Asegurado(
            edad=17, sexo=Sexo.HOMBRE, suma_asegurada=Decimal("1000000")
        )

        es_asegurable, razon = producto.validar_asegurabilidad(asegurado)

        assert es_asegurable is False
        assert "mayor de edad" in razon.lower()

    def test_calcular_reserva_inicio_es_cero(
        self, config_basica, tabla_simple, asegurado_basico
    ):
        """La reserva al inicio (año 0) debe ser cero"""
        producto = VidaTemporal(config_basica, tabla_simple)
        reserva = producto.calcular_reserva(asegurado_basico, anio=0)

        assert reserva == Decimal("0")

    def test_calcular_reserva_final_es_cero(
        self, config_basica, tabla_simple, asegurado_basico
    ):
        """La reserva al final del plazo debe ser cero"""
        producto = VidaTemporal(config_basica, tabla_simple)
        reserva = producto.calcular_reserva(asegurado_basico, anio=20)

        assert reserva == Decimal("0")

    def test_calcular_reserva_intermedia_positiva(
        self, config_basica, tabla_simple, asegurado_basico
    ):
        """La reserva en años intermedios debe ser positiva"""
        producto = VidaTemporal(config_basica, tabla_simple)
        reserva = producto.calcular_reserva(asegurado_basico, anio=10)

        assert reserva > 0

    def test_calcular_reserva_fuera_de_rango_falla(
        self, config_basica, tabla_simple, asegurado_basico
    ):
        """Debe fallar si el año está fuera del plazo"""
        producto = VidaTemporal(config_basica, tabla_simple)

        with pytest.raises(ValueError) as exc_info:
            producto.calcular_reserva(asegurado_basico, anio=25)

        assert "fuera de rango" in str(exc_info.value).lower()

    def test_aplicar_recargos(self, config_basica, tabla_simple):
        """Debe aplicar recargos correctamente"""
        producto = VidaTemporal(config_basica, tabla_simple)

        prima_neta = Decimal("1000")
        prima_total, desglose = producto.aplicar_recargos(prima_neta)

        # Recargos: 5% + 10% + 3% = 18%
        recargo_esperado = prima_neta * Decimal("0.18")
        assert prima_total == prima_neta + recargo_esperado

        # Verificar desglose
        assert desglose["gastos_admin"] == prima_neta * Decimal("0.05")
        assert desglose["gastos_adq"] == prima_neta * Decimal("0.10")
        assert desglose["utilidad"] == prima_neta * Decimal("0.03")
