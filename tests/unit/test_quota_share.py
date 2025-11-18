"""
Tests para contrato Quota Share (Cuota Parte).

Valida el cálculo de primas cedidas, comisiones y recuperaciones.
"""

from datetime import date
from decimal import Decimal

import pytest

from mexican_insurance.core.validators import (
    Moneda,
    QuotaShareConfig,
    Siniestro,
    TipoContrato,
    TipoSiniestro,
)
from mexican_insurance.reinsurance.quota_share import QuotaShare


@pytest.fixture
def config_qs_30pct():
    """Quota share 30% con comisión 25%"""
    return QuotaShareConfig(
        tipo_contrato=TipoContrato.QUOTA_SHARE,
        vigencia_inicio=date(2024, 1, 1),
        vigencia_fin=date(2024, 12, 31),
        moneda=Moneda.MXN,
        porcentaje_cesion=Decimal("30"),
        comision_reaseguro=Decimal("25"),
        comision_override=Decimal("2.5"),
    )


@pytest.fixture
def config_qs_50pct():
    """Quota share 50% con comisión 20%"""
    return QuotaShareConfig(
        tipo_contrato=TipoContrato.QUOTA_SHARE,
        vigencia_inicio=date(2024, 1, 1),
        vigencia_fin=date(2024, 12, 31),
        moneda=Moneda.MXN,
        porcentaje_cesion=Decimal("50"),
        comision_reaseguro=Decimal("20"),
        comision_override=Decimal("0"),
    )


@pytest.fixture
def siniestro_100k():
    """Siniestro de $100,000"""
    return Siniestro(
        id_siniestro="SIN-001",
        fecha_ocurrencia=date(2024, 6, 15),
        monto_bruto=Decimal("100000"),
        tipo=TipoSiniestro.INDIVIDUAL,
        id_poliza="POL-001",
    )


@pytest.fixture
def siniestro_250k():
    """Siniestro de $250,000"""
    return Siniestro(
        id_siniestro="SIN-002",
        fecha_ocurrencia=date(2024, 7, 20),
        monto_bruto=Decimal("250000"),
        tipo=TipoSiniestro.INDIVIDUAL,
        id_poliza="POL-002",
    )


@pytest.fixture
def siniestro_fuera_vigencia():
    """Siniestro fuera de vigencia"""
    return Siniestro(
        id_siniestro="SIN-003",
        fecha_ocurrencia=date(2025, 1, 15),
        monto_bruto=Decimal("50000"),
        tipo=TipoSiniestro.INDIVIDUAL,
    )


class TestQuotaShareCreacion:
    """Tests para la creación de contratos Quota Share"""

    def test_crear_quota_share_valido(self, config_qs_30pct):
        """Debe crear un contrato QS válido"""
        qs = QuotaShare(config_qs_30pct)
        assert qs.config.porcentaje_cesion == Decimal("30")
        assert qs.config.comision_reaseguro == Decimal("25")

    def test_porcentaje_cesion_invalido_mayor_100(self):
        """No debe permitir cesión > 100%"""
        with pytest.raises(ValueError):
            QuotaShareConfig(
                tipo_contrato=TipoContrato.QUOTA_SHARE,
                vigencia_inicio=date(2024, 1, 1),
                vigencia_fin=date(2024, 12, 31),
                porcentaje_cesion=Decimal("101"),
                comision_reaseguro=Decimal("25"),
            )

    def test_porcentaje_cesion_invalido_cero(self):
        """No debe permitir cesión = 0%"""
        with pytest.raises(ValueError):
            QuotaShareConfig(
                tipo_contrato=TipoContrato.QUOTA_SHARE,
                vigencia_inicio=date(2024, 1, 1),
                vigencia_fin=date(2024, 12, 31),
                porcentaje_cesion=Decimal("0"),
                comision_reaseguro=Decimal("25"),
            )

    def test_comision_excesiva(self):
        """No debe permitir comisión > 50%"""
        with pytest.raises(ValueError):
            QuotaShareConfig(
                tipo_contrato=TipoContrato.QUOTA_SHARE,
                vigencia_inicio=date(2024, 1, 1),
                vigencia_fin=date(2024, 12, 31),
                porcentaje_cesion=Decimal("30"),
                comision_reaseguro=Decimal("51"),
            )


class TestQuotaShareCalculoPrimas:
    """Tests para cálculo de primas cedidas y comisiones"""

    def test_calcular_prima_cedida_30pct(self, config_qs_30pct):
        """30% de $1,000,000 = $300,000"""
        qs = QuotaShare(config_qs_30pct)
        prima_bruta = Decimal("1000000")
        prima_cedida = qs.calcular_prima_cedida(prima_bruta)

        assert prima_cedida == Decimal("300000")

    def test_calcular_prima_retenida_30pct(self, config_qs_30pct):
        """70% de $1,000,000 = $700,000"""
        qs = QuotaShare(config_qs_30pct)
        prima_bruta = Decimal("1000000")
        prima_retenida = qs.calcular_prima_retenida(prima_bruta)

        assert prima_retenida == Decimal("700000")

    def test_calcular_prima_cedida_50pct(self, config_qs_50pct):
        """50% de $500,000 = $250,000"""
        qs = QuotaShare(config_qs_50pct)
        prima_bruta = Decimal("500000")
        prima_cedida = qs.calcular_prima_cedida(prima_bruta)

        assert prima_cedida == Decimal("250000")

    def test_calcular_comision_con_override(self, config_qs_30pct):
        """Comisión 27.5% (25% + 2.5%) sobre $300,000 = $82,500"""
        qs = QuotaShare(config_qs_30pct)
        prima_cedida = Decimal("300000")
        comision = qs.calcular_comision(prima_cedida)

        # 25% + 2.5% = 27.5% de 300,000 = 82,500
        assert comision == Decimal("82500")

    def test_calcular_comision_sin_override(self, config_qs_50pct):
        """Comisión 20% sobre $250,000 = $50,000"""
        qs = QuotaShare(config_qs_50pct)
        prima_cedida = Decimal("250000")
        comision = qs.calcular_comision(prima_cedida)

        assert comision == Decimal("50000")


class TestQuotaShareRecuperacion:
    """Tests para cálculo de recuperaciones de siniestros"""

    def test_recuperacion_siniestro_30pct(
        self, config_qs_30pct, siniestro_100k
    ):
        """30% de $100,000 = $30,000"""
        qs = QuotaShare(config_qs_30pct)
        recuperacion = qs.calcular_recuperacion(siniestro_100k)

        assert recuperacion == Decimal("30000")

    def test_recuperacion_siniestro_50pct(
        self, config_qs_50pct, siniestro_250k
    ):
        """50% de $250,000 = $125,000"""
        qs = QuotaShare(config_qs_50pct)
        recuperacion = qs.calcular_recuperacion(siniestro_250k)

        assert recuperacion == Decimal("125000")

    def test_siniestro_fuera_vigencia(
        self, config_qs_30pct, siniestro_fuera_vigencia
    ):
        """No debe procesar siniestros fuera de vigencia"""
        qs = QuotaShare(config_qs_30pct)

        with pytest.raises(ValueError, match="fuera de vigencia"):
            qs.calcular_recuperacion(siniestro_fuera_vigencia)

    def test_recuperacion_multiple(
        self, config_qs_30pct, siniestro_100k, siniestro_250k
    ):
        """Debe calcular recuperación de múltiples siniestros"""
        qs = QuotaShare(config_qs_30pct)
        siniestros = [siniestro_100k, siniestro_250k]

        recuperacion_total, detalle = qs.calcular_recuperacion_multiple(
            siniestros
        )

        # 30% de (100,000 + 250,000) = 30% de 350,000 = 105,000
        assert recuperacion_total == Decimal("105000")
        assert len(detalle) == 2
        assert detalle[0][1] == Decimal("30000")  # 30% de 100k
        assert detalle[1][1] == Decimal("75000")  # 30% de 250k


class TestQuotaShareResultadoNeto:
    """Tests para cálculo del resultado neto completo"""

    def test_resultado_neto_con_ganancia(
        self, config_qs_30pct, siniestro_100k
    ):
        """Debe calcular correctamente con siniestralidad baja"""
        qs = QuotaShare(config_qs_30pct)

        # Prima: $1,000,000
        # Siniestro: $100,000
        # Ratio siniestralidad: 10%

        resultado = qs.calcular_resultado_neto(
            prima_bruta=Decimal("1000000"),
            siniestros=[siniestro_100k],
        )

        # Prima cedida: $300,000
        # Prima retenida: $700,000
        # Comisión: $82,500 (27.5% de 300k)
        # Siniestro cedido: $30,000
        # Siniestro retenido: $70,000
        # Resultado neto: 700,000 + 82,500 - 70,000 = 712,500

        assert resultado.monto_cedido == Decimal("300000")
        assert resultado.monto_retenido == Decimal("700000")
        assert resultado.comision_recibida == Decimal("82500")
        assert resultado.recuperacion_reaseguro == Decimal("30000")
        assert resultado.ratio_cesion == Decimal("30")

    def test_resultado_neto_con_perdida(
        self, config_qs_30pct, siniestro_100k, siniestro_250k
    ):
        """Debe calcular correctamente con siniestralidad alta"""
        qs = QuotaShare(config_qs_30pct)

        # Prima: $300,000
        # Siniestros: $350,000 (100k + 250k)
        # Ratio siniestralidad: 116.7%

        resultado = qs.calcular_resultado_neto(
            prima_bruta=Decimal("300000"),
            siniestros=[siniestro_100k, siniestro_250k],
        )

        # Prima cedida: $90,000
        # Prima retenida: $210,000
        # Comisión: $24,750 (27.5% de 90k)
        # Siniestros cedidos: $105,000 (30% de 350k)
        # Siniestros retenidos: $245,000
        # Resultado neto: 210,000 + 24,750 - 245,000 = -10,250

        assert resultado.monto_cedido == Decimal("90000")
        assert resultado.recuperacion_reaseguro == Decimal("105000")
        # Resultado negativo (pérdida)
        assert resultado.resultado_neto_cedente < 0

    def test_resultado_sin_siniestros(self, config_qs_30pct):
        """Debe calcular correctamente sin siniestros"""
        qs = QuotaShare(config_qs_30pct)

        resultado = qs.calcular_resultado_neto(
            prima_bruta=Decimal("1000000"),
            siniestros=[],
        )

        # Prima retenida: $700,000
        # Comisión: $82,500
        # Siniestros: $0
        # Resultado: 700,000 + 82,500 = 782,500

        assert resultado.recuperacion_reaseguro == Decimal("0")
        assert resultado.resultado_neto_cedente == Decimal("782500")

    def test_cesion_100_porciento(self):
        """Debe manejar cesión del 100%"""
        config = QuotaShareConfig(
            tipo_contrato=TipoContrato.QUOTA_SHARE,
            vigencia_inicio=date(2024, 1, 1),
            vigencia_fin=date(2024, 12, 31),
            porcentaje_cesion=Decimal("100"),
            comision_reaseguro=Decimal("30"),
        )

        qs = QuotaShare(config)

        resultado = qs.calcular_resultado_neto(
            prima_bruta=Decimal("100000"),
            siniestros=[],
        )

        # Todo se cede
        assert resultado.monto_cedido == Decimal("100000")
        assert resultado.monto_retenido == Decimal("0")
        assert resultado.ratio_cesion == Decimal("100")

    def test_detalles_en_resultado(self, config_qs_30pct, siniestro_100k):
        """Debe incluir detalles en el resultado"""
        qs = QuotaShare(config_qs_30pct)

        resultado = qs.calcular_resultado_neto(
            prima_bruta=Decimal("1000000"),
            siniestros=[siniestro_100k],
        )

        assert "porcentaje_cesion" in resultado.detalles
        assert "comision_pct" in resultado.detalles
        assert "detalle_siniestros" in resultado.detalles
        assert resultado.detalles["numero_siniestros"] == 1
