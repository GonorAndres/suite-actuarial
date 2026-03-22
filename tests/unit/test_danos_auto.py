"""
Tests para el producto de seguro de auto con tarificacion AMIS.

~30 tests cubriendo:
- Calculo de tarifa para distintos vehiculos y zonas
- Transiciones BMS (sin siniestros, 1 siniestro, multiples)
- Aplicacion de factores de deducible
- Cotizacion completa
- Seleccion de coberturas
"""

from decimal import Decimal

import pytest

from suite_actuarial.danos.auto import Cobertura, SeguroAuto, COBERTURAS_BASICAS
from suite_actuarial.danos.tablas_amis import (
    FACTOR_DEDUCIBLE,
    FACTOR_EDAD_CONDUCTOR,
    GRUPOS_VEHICULO,
    TASAS_BASE,
    ZONAS_RIESGO,
    obtener_depreciacion,
    obtener_grupo,
    obtener_zona,
    rango_edad_conductor,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def auto_compacto():
    """Sedan compacto nuevo en CDMX, conductor joven."""
    return SeguroAuto(
        valor_vehiculo=Decimal("350000"),
        tipo_vehiculo="sedan_compacto",
        antiguedad_anos=0,
        zona="cdmx_norte",
        edad_conductor=22,
        deducible_pct=Decimal("0.05"),
    )


@pytest.fixture
def auto_lujo():
    """SUV de lujo de 3 anos en Monterrey, conductor adulto."""
    return SeguroAuto(
        valor_vehiculo=Decimal("1200000"),
        tipo_vehiculo="suv_lujo",
        antiguedad_anos=3,
        zona="monterrey",
        edad_conductor=42,
        deducible_pct=Decimal("0.05"),
    )


@pytest.fixture
def moto():
    """Motocicleta nueva en Merida, conductor joven."""
    return SeguroAuto(
        valor_vehiculo=Decimal("80000"),
        tipo_vehiculo="motocicleta",
        antiguedad_anos=0,
        zona="merida",
        edad_conductor=25,
        deducible_pct=Decimal("0.05"),
    )


# ---------------------------------------------------------------------------
# Tests de construccion
# ---------------------------------------------------------------------------

class TestConstruccion:
    def test_crear_auto_compacto(self, auto_compacto):
        assert auto_compacto.grupo == 1
        assert auto_compacto.factor_zona == Decimal("1.40")
        assert auto_compacto.valor_asegurado == Decimal("350000.00")

    def test_crear_auto_lujo(self, auto_lujo):
        assert auto_lujo.grupo == 8
        assert auto_lujo.factor_depreciacion == Decimal("0.62")
        assert auto_lujo.valor_asegurado == Decimal("744000.00")

    def test_valor_vehiculo_negativo(self):
        with pytest.raises(ValueError, match="positivo"):
            SeguroAuto(Decimal("-100"), "sedan_compacto", 0, "cdmx_norte", 25)

    def test_tipo_vehiculo_invalido(self):
        with pytest.raises(ValueError, match="desconocido"):
            SeguroAuto(Decimal("100000"), "tanque", 0, "cdmx_norte", 25)

    def test_zona_invalida(self):
        with pytest.raises(ValueError, match="desconocida"):
            SeguroAuto(Decimal("100000"), "sedan_compacto", 0, "marte", 25)

    def test_edad_menor(self):
        with pytest.raises(ValueError, match="18"):
            SeguroAuto(Decimal("100000"), "sedan_compacto", 0, "cdmx_norte", 16)

    def test_deducible_invalido(self):
        with pytest.raises(ValueError, match="Deducible"):
            SeguroAuto(
                Decimal("100000"), "sedan_compacto", 0, "cdmx_norte", 25,
                deducible_pct=Decimal("0.50"),
            )


# ---------------------------------------------------------------------------
# Tests de tarificacion
# ---------------------------------------------------------------------------

class TestTarificacion:
    def test_tarifa_todas_coberturas(self, auto_compacto):
        tarifas = auto_compacto.calcular_tarifa()
        assert len(tarifas) == len(Cobertura)
        for cob, prima in tarifas.items():
            assert isinstance(prima, Decimal)
            assert prima > 0

    def test_tarifa_sedan_vs_suv_lujo(self, auto_compacto, auto_lujo):
        """SUV lujo debe tener primas mas altas en danos materiales."""
        t_compacto = auto_compacto.calcular_tarifa()
        t_lujo = auto_lujo.calcular_tarifa()
        # Considerando que el valor asegurado del lujo es mayor
        assert t_lujo[Cobertura.DANOS_MATERIALES] > t_compacto[Cobertura.DANOS_MATERIALES]

    def test_zona_alto_riesgo_mayor(self):
        """CDMX norte (1.40) vs Merida (0.85): misma config, zona diferente."""
        auto_cdmx = SeguroAuto(
            Decimal("300000"), "sedan_compacto", 0, "cdmx_norte", 30
        )
        auto_merida = SeguroAuto(
            Decimal("300000"), "sedan_compacto", 0, "merida", 30
        )
        assert auto_cdmx.calcular_prima_total() > auto_merida.calcular_prima_total()

    def test_edad_joven_mayor_prima(self):
        """Conductor joven (18-25) paga mas que adulto (36-50)."""
        auto_joven = SeguroAuto(
            Decimal("300000"), "sedan_compacto", 0, "queretaro", 20
        )
        auto_adulto = SeguroAuto(
            Decimal("300000"), "sedan_compacto", 0, "queretaro", 40
        )
        assert auto_joven.calcular_prima_total() > auto_adulto.calcular_prima_total()

    def test_depreciacion_reduce_prima(self):
        """Vehiculo viejo tiene prima menor (menor valor asegurado)."""
        auto_nuevo = SeguroAuto(
            Decimal("400000"), "sedan_mediano", 0, "guadalajara", 35
        )
        auto_5anos = SeguroAuto(
            Decimal("400000"), "sedan_mediano", 5, "guadalajara", 35
        )
        assert auto_nuevo.calcular_prima_total() > auto_5anos.calcular_prima_total()


# ---------------------------------------------------------------------------
# Tests de deducible
# ---------------------------------------------------------------------------

class TestDeducible:
    def test_deducible_bajo_mas_caro(self):
        """Deducible 3% = mas caro que 5%."""
        auto_3 = SeguroAuto(
            Decimal("300000"), "sedan_compacto", 0, "queretaro", 30,
            deducible_pct=Decimal("0.03"),
        )
        auto_5 = SeguroAuto(
            Decimal("300000"), "sedan_compacto", 0, "queretaro", 30,
            deducible_pct=Decimal("0.05"),
        )
        assert auto_3.calcular_prima_total() > auto_5.calcular_prima_total()

    def test_deducible_alto_descuento(self):
        """Deducible 20% = descuento significativo."""
        auto_5 = SeguroAuto(
            Decimal("300000"), "sedan_compacto", 0, "queretaro", 30,
            deducible_pct=Decimal("0.05"),
        )
        auto_20 = SeguroAuto(
            Decimal("300000"), "sedan_compacto", 0, "queretaro", 30,
            deducible_pct=Decimal("0.20"),
        )
        assert auto_20.calcular_prima_total() < auto_5.calcular_prima_total()

    def test_deducible_solo_afecta_propias(self):
        """Deducible solo afecta danos materiales y robo, no RC."""
        auto_3 = SeguroAuto(
            Decimal("300000"), "sedan_compacto", 0, "queretaro", 30,
            deducible_pct=Decimal("0.03"),
        )
        auto_20 = SeguroAuto(
            Decimal("300000"), "sedan_compacto", 0, "queretaro", 30,
            deducible_pct=Decimal("0.20"),
        )
        t3 = auto_3.calcular_tarifa()
        t20 = auto_20.calcular_tarifa()
        # RC bienes no se afecta por deducible
        assert t3[Cobertura.RC_BIENES] == t20[Cobertura.RC_BIENES]
        # Danos materiales si se afecta
        assert t3[Cobertura.DANOS_MATERIALES] != t20[Cobertura.DANOS_MATERIALES]


# ---------------------------------------------------------------------------
# Tests de Bonus-Malus
# ---------------------------------------------------------------------------

class TestBonusMalus:
    def test_sin_siniestros_descuento(self, auto_compacto):
        """3 anos sin siniestros = descuento."""
        prima_base = auto_compacto.calcular_prima_total()
        prima_bms = auto_compacto.aplicar_bonus_malus([0, 0, 0])
        assert prima_bms < prima_base

    def test_con_siniestro_recargo(self, auto_compacto):
        """1 siniestro = recargo."""
        prima_base = auto_compacto.calcular_prima_total()
        prima_bms = auto_compacto.aplicar_bonus_malus([1])
        assert prima_bms > prima_base

    def test_multiples_siniestros(self, auto_compacto):
        """Multiples siniestros = recargo mas alto."""
        prima_1 = auto_compacto.aplicar_bonus_malus([1])
        prima_2 = auto_compacto.aplicar_bonus_malus([2])
        assert prima_2 > prima_1


# ---------------------------------------------------------------------------
# Tests de seleccion de coberturas
# ---------------------------------------------------------------------------

class TestSeleccionCoberturas:
    def test_solo_rc(self, auto_compacto):
        """Solo coberturas basicas (RC)."""
        prima_rc = auto_compacto.calcular_prima_total(COBERTURAS_BASICAS)
        prima_total = auto_compacto.calcular_prima_total()
        assert prima_rc < prima_total

    def test_cobertura_individual(self, auto_compacto):
        """Prima de una sola cobertura."""
        prima = auto_compacto.calcular_prima_total([Cobertura.DANOS_MATERIALES])
        assert prima > 0

    def test_todas_coberturas(self, auto_compacto):
        """Todas las coberturas = prima total."""
        prima_todas = auto_compacto.calcular_prima_total(list(Cobertura))
        prima_default = auto_compacto.calcular_prima_total()
        assert prima_todas == prima_default


# ---------------------------------------------------------------------------
# Tests de cotizacion completa
# ---------------------------------------------------------------------------

class TestCotizacion:
    def test_cotizacion_estructura(self, auto_compacto):
        cot = auto_compacto.generar_cotizacion()
        assert "vehiculo" in cot
        assert "conductor" in cot
        assert "zona" in cot
        assert "deducible" in cot
        assert "coberturas" in cot
        assert "subtotal" in cot
        assert "bonus_malus" in cot
        assert "prima_total" in cot

    def test_cotizacion_vehiculo_info(self, auto_compacto):
        cot = auto_compacto.generar_cotizacion()
        assert cot["vehiculo"]["tipo"] == "sedan_compacto"
        assert cot["vehiculo"]["grupo"] == 1
        assert cot["vehiculo"]["valor_original"] == Decimal("350000")

    def test_cotizacion_con_bms(self, auto_compacto):
        cot = auto_compacto.generar_cotizacion(historial_siniestros=[0, 0, 0])
        assert cot["bonus_malus"]["factor"] < Decimal("1.00")
        assert cot["prima_total"] < cot["subtotal"]

    def test_cotizacion_deducible_pesos(self, auto_compacto):
        cot = auto_compacto.generar_cotizacion()
        # 5% de 350000 = 17500
        assert cot["deducible"]["pesos"] == Decimal("17500.00")

    def test_cotizacion_coberturas_seleccionadas(self, auto_compacto):
        cot = auto_compacto.generar_cotizacion(
            coberturas=[Cobertura.DANOS_MATERIALES, Cobertura.ROBO_TOTAL]
        )
        assert len(cot["coberturas"]) == 2
        assert "danos_materiales" in cot["coberturas"]
        assert "robo_total" in cot["coberturas"]


# ---------------------------------------------------------------------------
# Tests de tablas AMIS auxiliares
# ---------------------------------------------------------------------------

class TestTablasAMIS:
    def test_obtener_grupo_valido(self):
        assert obtener_grupo("sedan_compacto") == 1
        assert obtener_grupo("deportivo") == 9

    def test_obtener_grupo_invalido(self):
        with pytest.raises(ValueError):
            obtener_grupo("helicoptero")

    def test_obtener_zona_valida(self):
        assert obtener_zona("cdmx_norte") == Decimal("1.40")

    def test_depreciacion_nuevo(self):
        assert obtener_depreciacion(0) == Decimal("1.00")

    def test_depreciacion_10_plus(self):
        """Vehiculos de 15 anos usan el factor de 10."""
        assert obtener_depreciacion(15) == Decimal("0.29")

    def test_rango_edad(self):
        assert rango_edad_conductor(20) == "18-25"
        assert rango_edad_conductor(30) == "26-35"
        assert rango_edad_conductor(45) == "36-50"
        assert rango_edad_conductor(60) == "51-65"
        assert rango_edad_conductor(70) == "66+"
