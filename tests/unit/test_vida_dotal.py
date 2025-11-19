"""
Tests para el producto de Vida Dotal (Endowment)
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
from mexican_insurance.products.vida.dotal import VidaDotal


@pytest.fixture
def tabla_simple():
    """Tabla de mortalidad simplificada para tests"""
    edades = list(range(18, 101))
    datos = []

    for edad in edades:
        qx_h = 0.001 + (edad - 18) * 0.0002
        qx_m = 0.0005 + (edad - 18) * 0.0001
        datos.append({"edad": edad, "sexo": "H", "qx": min(qx_h, 0.99)})
        datos.append({"edad": edad, "sexo": "M", "qx": min(qx_m, 0.99)})

    df = pd.DataFrame(datos)
    return TablaMortalidad(nombre="Simple", datos=df)


@pytest.fixture
def config_dotal_20():
    """Configuración para dotal a 20 años"""
    return ConfiguracionProducto(
        nombre_producto="Dotal Educativo 20 años",
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
        edad=30,
        sexo=Sexo.HOMBRE,
        suma_asegurada=Decimal("500000"),
    )


class TestVidaDotal:
    """Tests para el producto VidaDotal"""

    def test_crear_producto(self, config_dotal_20, tabla_simple):
        """Debe crear el producto correctamente"""
        producto = VidaDotal(config_dotal_20, tabla_simple)

        assert producto.config.nombre_producto == "Dotal Educativo 20 años"
        assert producto.plazo_pago == 20

    def test_calcular_prima_basica(
        self, config_dotal_20, tabla_simple, asegurado_basico
    ):
        """Debe calcular prima correctamente"""
        producto = VidaDotal(config_dotal_20, tabla_simple)
        resultado = producto.calcular_prima(asegurado_basico)

        # Verificaciones básicas
        assert resultado.prima_neta > 0
        assert resultado.prima_total > resultado.prima_neta
        assert resultado.moneda == Moneda.MXN

        # Verificar metadata
        assert resultado.metadata["tipo"] == "vida_dotal"
        assert resultado.metadata["componentes"] == "muerte + supervivencia"
        assert resultado.metadata["edad"] == 30

    def test_prima_dotal_mayor_que_temporal(
        self, config_dotal_20, tabla_simple, asegurado_basico
    ):
        """Prima de dotal debe ser mayor que temporal (pago garantizado)"""
        from mexican_insurance.products.vida.temporal import VidaTemporal

        # Dotal 20 años
        producto_dotal = VidaDotal(config_dotal_20, tabla_simple)
        prima_dotal = producto_dotal.calcular_prima(asegurado_basico).prima_total

        # Temporal 20 años (mismo plazo)
        producto_temp = VidaTemporal(config_dotal_20, tabla_simple)
        prima_temp = producto_temp.calcular_prima(asegurado_basico).prima_total

        # Dotal debe ser más caro (paga muerte O supervivencia vs solo muerte)
        assert prima_dotal > prima_temp

    def test_reserva_inicio_es_cero(
        self, config_dotal_20, tabla_simple, asegurado_basico
    ):
        """La reserva al inicio debe ser cero"""
        producto = VidaDotal(config_dotal_20, tabla_simple)
        reserva = producto.calcular_reserva(asegurado_basico, anio=0)

        assert reserva == Decimal("0")

    def test_reserva_final_es_suma_asegurada(
        self, config_dotal_20, tabla_simple, asegurado_basico
    ):
        """La reserva al vencimiento debe ser exactamente la suma asegurada"""
        producto = VidaDotal(config_dotal_20, tabla_simple)
        reserva_final = producto.calcular_reserva(asegurado_basico, anio=20)

        # Debe ser exactamente la suma asegurada (pago garantizado)
        assert reserva_final == asegurado_basico.suma_asegurada

    def test_reserva_crece_hasta_suma_asegurada(
        self, config_dotal_20, tabla_simple, asegurado_basico
    ):
        """La reserva debe crecer monotónicamente hasta suma asegurada"""
        producto = VidaDotal(config_dotal_20, tabla_simple)

        reservas = []
        for anio in [0, 5, 10, 15, 20]:
            r = producto.calcular_reserva(asegurado_basico, anio=anio)
            reservas.append(float(r))

        # Verificar que crece
        for i in range(len(reservas) - 1):
            assert (
                reservas[i + 1] > reservas[i]
            ), f"Reserva debe crecer entre año {i*5} y {(i+1)*5}"

        # La última debe ser la suma asegurada
        assert reservas[-1] == float(asegurado_basico.suma_asegurada)

    def test_validar_plazo_minimo(self, tabla_simple):
        """No debe aceptar dotales menores a 5 años"""
        config_corto = ConfiguracionProducto(
            nombre_producto="Dotal corto",
            plazo_years=3,  # Muy corto
            tasa_interes_tecnico=Decimal("0.055"),
        )

        producto = VidaDotal(config_corto, tabla_simple)

        asegurado = Asegurado(
            edad=30, sexo=Sexo.HOMBRE, suma_asegurada=Decimal("100000")
        )

        es_asegurable, razon = producto.validar_asegurabilidad(asegurado)

        assert es_asegurable is False
        assert "5 años" in razon

    def test_validar_edad_vencimiento_maxima(self, config_dotal_20, tabla_simple):
        """No debe aceptar edad + plazo > 90"""
        producto = VidaDotal(config_dotal_20, tabla_simple)

        # Edad 75 + plazo 20 = 95 (excede límite)
        asegurado_mayor = Asegurado(
            edad=75, sexo=Sexo.HOMBRE, suma_asegurada=Decimal("500000")
        )

        es_asegurable, razon = producto.validar_asegurabilidad(asegurado_mayor)

        assert es_asegurable is False
        assert "edad" in razon.lower()  # Validación base rechaza edad > 70

    def test_comparar_reservas_dotal_vs_temporal(
        self, config_dotal_20, tabla_simple, asegurado_basico
    ):
        """Reserva del dotal debe ser mayor que temporal en todos los años"""
        from mexican_insurance.products.vida.temporal import VidaTemporal

        producto_dotal = VidaDotal(config_dotal_20, tabla_simple)
        producto_temp = VidaTemporal(config_dotal_20, tabla_simple)

        # Comparar reservas en año 10
        reserva_dotal = producto_dotal.calcular_reserva(asegurado_basico, anio=10)
        reserva_temp = producto_temp.calcular_reserva(asegurado_basico, anio=10)

        # Dotal siempre tiene más reserva (componente de supervivencia)
        assert reserva_dotal > reserva_temp

    def test_prima_frecuencias_diferentes(
        self, config_dotal_20, tabla_simple, asegurado_basico
    ):
        """Debe calcular primas para diferentes frecuencias"""
        producto = VidaDotal(config_dotal_20, tabla_simple)

        prima_anual = producto.calcular_prima(
            asegurado_basico, frecuencia_pago="anual"
        ).prima_total

        prima_mensual = producto.calcular_prima(
            asegurado_basico, frecuencia_pago="mensual"
        ).prima_total

        # Mensual debe ser menor que anual pero mayor que anual/12
        assert prima_mensual < prima_anual
        assert prima_mensual > (prima_anual / Decimal("13"))

    def test_error_plazo_pago_mayor_plazo_seguro(self, tabla_simple):
        """Debe fallar si plazo pago > plazo seguro"""
        config = ConfiguracionProducto(
            nombre_producto="Dotal test",
            plazo_years=20,
            tasa_interes_tecnico=Decimal("0.055"),
        )

        with pytest.raises(ValueError) as exc_info:
            VidaDotal(config, tabla_simple, plazo_pago=25)  # 25 > 20

        assert "mayor" in str(exc_info.value).lower()
