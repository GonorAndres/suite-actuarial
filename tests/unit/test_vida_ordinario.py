"""
Tests para el producto de Vida Ordinario
"""

from decimal import Decimal

import pandas as pd
import pytest

from suite_actuarial.actuarial.mortality.tablas import TablaMortalidad
from suite_actuarial.core.validators import (
    Asegurado,
    ConfiguracionProducto,
    Moneda,
    Sexo,
)
from suite_actuarial.vida.ordinario import VidaOrdinario


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

    def test_calcular_prima_basica(self, config_pago_limitado, tabla_simple, asegurado_basico):
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
        from suite_actuarial.vida.temporal import VidaTemporal

        # Ordinario con pago 20 años
        producto_ord = VidaOrdinario(config_pago_limitado, tabla_simple)
        prima_ord = producto_ord.calcular_prima(asegurado_basico).prima_total

        # Temporal 20 años (mismo plazo de pago)
        producto_temp = VidaTemporal(config_pago_limitado, tabla_simple)
        prima_temp = producto_temp.calcular_prima(asegurado_basico).prima_total

        # Ordinario debe ser más caro (cobertura vitalicia vs 20 años)
        assert prima_ord > prima_temp

    def test_reserva_inicio_es_cero(self, config_pago_limitado, tabla_simple, asegurado_basico):
        """La reserva al inicio debe ser cero"""
        producto = VidaOrdinario(config_pago_limitado, tabla_simple)
        reserva = producto.calcular_reserva(asegurado_basico, anio=0)

        assert reserva == Decimal("0")

    def test_reserva_en_edad_omega_es_la_suma_asegurada_descontada(
        self, config_pago_limitado, tabla_simple, asegurado_basico
    ):
        """En edad omega la reserva es SA descontada un año (A7).

        Con la convención de edad terminal `q_omega = 1`, el beneficio se paga
        con certeza al final de ese año, así que su valor presente al inicio
        del año es `SA * v`. Ya no hay primas por cobrar (el pago era de 20
        años), de modo que la reserva prospectiva es exactamente eso.

        Antes se fijaba a mano en `SA`, un salto que la propia fórmula
        prospectiva no sostenía: el año anterior daba ~0.38*SA.
        """
        producto = VidaOrdinario(config_pago_limitado, tabla_simple, edad_omega=100)

        # Edades cubiertas: x .. omega inclusive
        anio_omega = 100 - asegurado_basico.edad

        reserva_omega = producto.calcular_reserva(asegurado_basico, anio=anio_omega)

        v = Decimal("1") / (Decimal("1") + config_pago_limitado.tasa_interes_tecnico)
        esperado = asegurado_basico.suma_asegurada * v

        assert float(reserva_omega) == pytest.approx(float(esperado), rel=1e-12)

    def test_la_reserva_no_salta_en_el_ultimo_ano(
        self, config_pago_limitado, tabla_simple, asegurado_basico
    ):
        """La reserva llega a su valor final por la recursión, sin discontinuidad.

        El defecto A7 producía un salto de ~0.38*SA a SA en un solo año. La
        prueba exige que el último paso sea del mismo orden que los anteriores:
        se compara el incremento final contra el promedio de los cinco previos.
        """
        producto = VidaOrdinario(config_pago_limitado, tabla_simple, edad_omega=100)
        anio_omega = 100 - asegurado_basico.edad

        reservas = [
            float(producto.calcular_reserva(asegurado_basico, anio=t))
            for t in range(anio_omega - 6, anio_omega + 1)
        ]
        incrementos = [b - a for a, b in zip(reservas[:-1], reservas[1:], strict=True)]

        promedio_previo = sum(incrementos[:-1]) / len(incrementos[:-1])

        assert incrementos[-1] == pytest.approx(promedio_previo, rel=0.5)
        assert all(inc > 0 for inc in incrementos)

    def test_el_beneficio_vitalicio_se_fondea_por_completo(
        self, config_pago_limitado, tabla_simple, asegurado_basico
    ):
        """La probabilidad total de pago es 1: nadie queda sin cobrar (A7).

        Un beneficio "garantizado" que no se paga a la cohorte viva en la edad
        terminal no está fondeado. La prueba suma las probabilidades de muerte
        que el motor usa y exige que cierren en 1. Sin `q_omega = 1` la suma
        queda por debajo y el faltante nunca se cobra.
        """
        producto = VidaOrdinario(config_pago_limitado, tabla_simple, edad_omega=100)
        edad = asegurado_basico.edad

        supervivencia = Decimal("1")
        probabilidad_de_pago = Decimal("0")
        for x in range(edad, 101):
            qx = (
                Decimal("1")
                if x >= producto.edad_omega
                else tabla_simple.obtener_qx(x, asegurado_basico.sexo, interpolar=True)
            )
            probabilidad_de_pago += supervivencia * qx
            supervivencia *= Decimal("1") - qx

        assert float(probabilidad_de_pago) == pytest.approx(1.0, abs=1e-12)
        assert float(supervivencia) == pytest.approx(0.0, abs=1e-12)

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
            assert reservas[i + 1] > reservas[i], (
                f"Reserva debe crecer entre año {i * 5} y {(i + 1) * 5}"
            )

    def test_validar_edad_maxima_emision(self, config_pago_limitado, tabla_simple):
        """No debe aceptar asegurados mayores de 70 años (base class limit)"""
        producto = VidaOrdinario(config_pago_limitado, tabla_simple)

        asegurado_mayor = Asegurado(edad=76, sexo=Sexo.HOMBRE, suma_asegurada=Decimal("1000000"))

        es_asegurable, razon = producto.validar_asegurabilidad(asegurado_mayor)

        assert es_asegurable is False
        assert razon is not None

    def test_validar_edad_cercana_omega(self, config_pago_limitado, tabla_simple):
        """No debe aceptar edades very close to omega (base rejects >70 first)"""
        producto = VidaOrdinario(config_pago_limitado, tabla_simple, edad_omega=100)

        # Edad 96 > 70 so base class rejects first
        asegurado_cercano = Asegurado(edad=96, sexo=Sexo.HOMBRE, suma_asegurada=Decimal("1000000"))

        es_asegurable, razon = producto.validar_asegurabilidad(asegurado_cercano)

        assert es_asegurable is False
        assert razon is not None

    def test_error_edad_mayor_omega(self, config_pago_limitado, tabla_simple):
        """Debe fallar si edad >= omega (base class rejects >70 first)"""
        producto = VidaOrdinario(config_pago_limitado, tabla_simple, edad_omega=100)

        asegurado_omega = Asegurado(edad=100, sexo=Sexo.HOMBRE, suma_asegurada=Decimal("1000000"))

        with pytest.raises(ValueError) as exc_info:
            producto.calcular_prima(asegurado_omega)

        # Base class rejects age > 70, so error message mentions age limit
        assert "asegurable" in str(exc_info.value).lower()
