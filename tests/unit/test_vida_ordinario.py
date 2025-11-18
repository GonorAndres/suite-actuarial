"""
Tests para el producto de Vida Ordinario
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
from mexican_insurance.products.vida.ordinario import VidaOrdinario


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
def config_pago_limitado():
    """Configuración para vida ordinario con pago limitado 20 años"""
    return ConfiguracionProducto(
        nombre_producto="Vida Ordinario - Pago 20 años",
        plazo_years=20,  # Paga prima 20 años
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


class TestVidaOrdinario:
    """Tests para el producto VidaOrdinario"""

    def test_crear_producto_pago_limitado(self, config_pago_limitado, tabla_simple):
        """Debe crear producto con pago limitado correctamente"""
        producto = VidaOrdinario(
            config_pago_limitado,
            tabla_simple,
            plazo_pago_vitalicio=False,
        )

        assert producto.plazo_pago == 20
        assert producto.edad_omega == 100
        assert not producto.plazo_pago_vitalicio

    def test_crear_producto_pago_vitalicio(self, config_pago_limitado, tabla_simple):
        """Debe crear producto con pago vitalicio correctamente"""
        producto = VidaOrdinario(
            config_pago_limitado,
            tabla_simple,
            plazo_pago_vitalicio=True,
        )

        assert producto.plazo_pago is None
        assert producto.plazo_pago_vitalicio

    def test_calcular_prima_basica(
        self, config_pago_limitado, tabla_simple, asegurado_basico
    ):
        """Debe calcular prima correctamente"""
        producto = VidaOrdinario(config_pago_limitado, tabla_simple)
        resultado = producto.calcular_prima(asegurado_basico)

        # Verificaciones básicas
        assert resultado.prima_neta > 0
        assert resultado.prima_total > resultado.prima_neta
        assert resultado.moneda == Moneda.MXN

        # Verificar metadata
        assert resultado.metadata["tipo"] == "vida_ordinario"
        assert resultado.metadata["edad"] == 35
        assert resultado.metadata["edad_omega"] == 100

    def test_prima_ordinario_mayor_que_temporal(
        self, config_pago_limitado, tabla_simple, asegurado_basico
    ):
        """Prima de ordinario debe ser mayor que temporal (beneficio garantizado)"""
        from mexican_insurance.products.vida.temporal import VidaTemporal

        # Ordinario con pago 20 años
        producto_ord = VidaOrdinario(config_pago_limitado, tabla_simple)
        prima_ord = producto_ord.calcular_prima(asegurado_basico).prima_total

        # Temporal 20 años (mismo plazo de pago)
        producto_temp = VidaTemporal(config_pago_limitado, tabla_simple)
        prima_temp = producto_temp.calcular_prima(asegurado_basico).prima_total

        # Ordinario debe ser más caro (cobertura vitalicia vs 20 años)
        assert prima_ord > prima_temp

    def test_reserva_inicio_es_cero(
        self, config_pago_limitado, tabla_simple, asegurado_basico
    ):
        """La reserva al inicio debe ser cero"""
        producto = VidaOrdinario(config_pago_limitado, tabla_simple)
        reserva = producto.calcular_reserva(asegurado_basico, anio=0)

        assert reserva == Decimal("0")

    def test_reserva_final_es_suma_asegurada(
        self, config_pago_limitado, tabla_simple, asegurado_basico
    ):
        """La reserva en edad omega debe ser la suma asegurada"""
        producto = VidaOrdinario(config_pago_limitado, tabla_simple, edad_omega=100)

        # Años hasta omega
        plazo_total = 100 - asegurado_basico.edad  # 65 años

        reserva_final = producto.calcular_reserva(asegurado_basico, anio=plazo_total)

        # Debe ser exactamente la suma asegurada
        assert reserva_final == asegurado_basico.suma_asegurada

    def test_reserva_crece_monotonamente(
        self, config_pago_limitado, tabla_simple, asegurado_basico
    ):
        """La reserva debe crecer año con año"""
        producto = VidaOrdinario(config_pago_limitado, tabla_simple)

        reservas = []
        for anio in [0, 5, 10, 15, 20]:
            r = producto.calcular_reserva(asegurado_basico, anio=anio)
            reservas.append(r)

        # Verificar que crece
        for i in range(len(reservas) - 1):
            assert reservas[i + 1] > reservas[i], f"Reserva debe crecer entre año {i*5} y {(i+1)*5}"

    def test_validar_edad_maxima_emision(
        self, config_pago_limitado, tabla_simple
    ):
        """No debe aceptar asegurados mayores de 75 años"""
        producto = VidaOrdinario(config_pago_limitado, tabla_simple)

        asegurado_mayor = Asegurado(
            edad=76, sexo=Sexo.HOMBRE, suma_asegurada=Decimal("1000000")
        )

        es_asegurable, razon = producto.validar_asegurabilidad(asegurado_mayor)

        assert es_asegurable is False
        assert "75" in razon

    def test_validar_edad_cercana_omega(self, config_pago_limitado, tabla_simple):
        """No debe aceptar edades muy cercanas a omega"""
        producto = VidaOrdinario(
            config_pago_limitado, tabla_simple, edad_omega=100
        )

        # Edad 96 está a solo 4 años de omega
        asegurado_cercano = Asegurado(
            edad=96, sexo=Sexo.HOMBRE, suma_asegurada=Decimal("1000000")
        )

        es_asegurable, razon = producto.validar_asegurabilidad(asegurado_cercano)

        assert es_asegurable is False
        assert "omega" in razon.lower()

    def test_error_edad_mayor_omega(
        self, config_pago_limitado, tabla_simple
    ):
        """Debe fallar si edad >= omega"""
        producto = VidaOrdinario(
            config_pago_limitado, tabla_simple, edad_omega=100
        )

        asegurado_omega = Asegurado(
            edad=100, sexo=Sexo.HOMBRE, suma_asegurada=Decimal("1000000")
        )

        with pytest.raises(ValueError) as exc_info:
            producto.calcular_prima(asegurado_omega)

        assert "omega" in str(exc_info.value).lower()
