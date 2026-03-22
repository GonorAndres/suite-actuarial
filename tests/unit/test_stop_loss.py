"""
Tests para contrato Stop Loss (Limitación de Pérdidas).

Valida el cálculo de siniestralidad agregada y recuperaciones.
"""

from datetime import date
from decimal import Decimal

import pytest

from suite_actuarial.core.validators import (
    Moneda,
    Siniestro,
    StopLossConfig,
    TipoContrato,
    TipoSiniestro,
)
from suite_actuarial.reaseguro.stop_loss import StopLoss


@pytest.fixture
def config_sl_80_xs_20():
    """Stop Loss 80% xs 20% sobre $10M"""
    return StopLossConfig(
        tipo_contrato=TipoContrato.STOP_LOSS,
        vigencia_inicio=date(2024, 1, 1),
        vigencia_fin=date(2024, 12, 31),
        moneda=Moneda.MXN,
        attachment_point=Decimal("80"),  # Se activa en 80%
        limite_cobertura=Decimal("20"),  # Cubre hasta 20% adicional (100% total)
        primas_sujetas=Decimal("10000000"),  # $10M
    )


@pytest.fixture
def config_sl_100_xs_30():
    """Stop Loss 100% xs 30% sobre $5M"""
    return StopLossConfig(
        tipo_contrato=TipoContrato.STOP_LOSS,
        vigencia_inicio=date(2024, 1, 1),
        vigencia_fin=date(2024, 12, 31),
        attachment_point=Decimal("100"),
        limite_cobertura=Decimal("30"),
        primas_sujetas=Decimal("5000000"),
    )


@pytest.fixture
def siniestros_bajos():
    """Varios siniestros que suman $7M (70% de $10M)"""
    return [
        Siniestro(
            id_siniestro=f"SIN-{i}",
            fecha_ocurrencia=date(2024, i, 15),
            monto_bruto=Decimal("1000000"),
            tipo=TipoSiniestro.INDIVIDUAL,
        )
        for i in range(1, 8)
    ]


@pytest.fixture
def siniestros_altos():
    """Varios siniestros que suman $9M (90% de $10M)"""
    return [
        Siniestro(
            id_siniestro=f"SIN-{i}",
            fecha_ocurrencia=date(2024, i, 15),
            monto_bruto=Decimal("1000000"),
            tipo=TipoSiniestro.INDIVIDUAL,
        )
        for i in range(1, 10)
    ]


@pytest.fixture
def siniestros_extremos():
    """Varios siniestros que suman $11M (110% de $10M)"""
    return [
        Siniestro(
            id_siniestro=f"SIN-{i}",
            fecha_ocurrencia=date(2024, (i % 12) + 1, 15),
            monto_bruto=Decimal("1000000"),
            tipo=TipoSiniestro.INDIVIDUAL,
        )
        for i in range(11)
    ]


class TestStopLossCreacion:
    """Tests para la creación de contratos Stop Loss"""

    def test_crear_stop_loss_valido(self, config_sl_80_xs_20):
        """Debe crear un contrato Stop Loss válido"""
        sl = StopLoss(config_sl_80_xs_20)
        assert sl.config.attachment_point == Decimal("80")
        assert sl.config.limite_cobertura == Decimal("20")
        assert sl.config.primas_sujetas == Decimal("10000000")

    def test_attachment_invalido_muy_bajo(self):
        """No debe permitir attachment < 50%"""
        with pytest.raises(ValueError):
            StopLossConfig(
                tipo_contrato=TipoContrato.STOP_LOSS,
                vigencia_inicio=date(2024, 1, 1),
                vigencia_fin=date(2024, 12, 31),
                attachment_point=Decimal("40"),  # Muy bajo
                limite_cobertura=Decimal("20"),
                primas_sujetas=Decimal("10000000"),
            )

    def test_primas_sujetas_cero(self):
        """No debe permitir primas sujetas = 0"""
        with pytest.raises(ValueError):
            StopLossConfig(
                tipo_contrato=TipoContrato.STOP_LOSS,
                vigencia_inicio=date(2024, 1, 1),
                vigencia_fin=date(2024, 12, 31),
                attachment_point=Decimal("80"),
                limite_cobertura=Decimal("20"),
                primas_sujetas=Decimal("0"),
            )


class TestStopLossCalculoSiniestralidad:
    """Tests para cálculo de siniestralidad"""

    def test_calcular_siniestralidad_70pct(self, config_sl_80_xs_20):
        """$7M siniestros / $10M primas = 70%"""
        sl = StopLoss(config_sl_80_xs_20)
        siniestralidad = sl.calcular_siniestralidad(
            siniestros_totales=Decimal("7000000"),
            primas_totales=Decimal("10000000"),
        )
        assert siniestralidad == Decimal("70")

    def test_calcular_siniestralidad_90pct(self, config_sl_80_xs_20):
        """$9M siniestros / $10M primas = 90%"""
        sl = StopLoss(config_sl_80_xs_20)
        siniestralidad = sl.calcular_siniestralidad(
            siniestros_totales=Decimal("9000000"),
            primas_totales=Decimal("10000000"),
        )
        assert siniestralidad == Decimal("90")

    def test_calcular_siniestralidad_110pct(self, config_sl_80_xs_20):
        """$11M siniestros / $10M primas = 110%"""
        sl = StopLoss(config_sl_80_xs_20)
        siniestralidad = sl.calcular_siniestralidad(
            siniestros_totales=Decimal("11000000"),
            primas_totales=Decimal("10000000"),
        )
        assert siniestralidad == Decimal("110")

    def test_primas_cero_error(self, config_sl_80_xs_20):
        """No debe permitir calcular con primas = 0"""
        sl = StopLoss(config_sl_80_xs_20)
        with pytest.raises(ValueError, match="primas totales no pueden ser cero"):
            sl.calcular_siniestralidad(
                siniestros_totales=Decimal("1000000"),
                primas_totales=Decimal("0"),
            )


class TestStopLossRecuperacion:
    """Tests para cálculo de recuperaciones"""

    def test_siniestralidad_bajo_attachment(
        self, config_sl_80_xs_20, siniestros_bajos
    ):
        """70% < 80% → No activa → recuperación $0"""
        sl = StopLoss(config_sl_80_xs_20)

        recuperacion = sl.calcular_recuperacion(
            siniestros_totales=Decimal("7000000"),
            primas_totales=Decimal("10000000"),
        )

        assert recuperacion == Decimal("0")

    def test_siniestralidad_exactamente_attachment(self, config_sl_80_xs_20):
        """80% = 80% → No activa (límite es exclusivo) → recuperación $0"""
        sl = StopLoss(config_sl_80_xs_20)

        recuperacion = sl.calcular_recuperacion(
            siniestros_totales=Decimal("8000000"),
            primas_totales=Decimal("10000000"),
        )

        assert recuperacion == Decimal("0")

    def test_siniestralidad_excede_attachment(self, config_sl_80_xs_20):
        """90% > 80% → Activa → recuperación = 10% de $10M = $1M"""
        sl = StopLoss(config_sl_80_xs_20)

        recuperacion = sl.calcular_recuperacion(
            siniestros_totales=Decimal("9000000"),
            primas_totales=Decimal("10000000"),
        )

        # Exceso: 90% - 80% = 10%
        # Recuperación: 10% de $10M = $1M
        assert recuperacion == Decimal("1000000")

    def test_siniestralidad_excede_limite_total(self, config_sl_80_xs_20):
        """110% > 100% (80% + 20%) → recuperación limitada a 20% = $2M"""
        sl = StopLoss(config_sl_80_xs_20)

        recuperacion = sl.calcular_recuperacion(
            siniestros_totales=Decimal("11000000"),
            primas_totales=Decimal("10000000"),
        )

        # Exceso: 110% - 80% = 30%
        # Pero límite es solo 20%
        # Recuperación: 20% de $10M = $2M
        assert recuperacion == Decimal("2000000")

    def test_calcular_recuperacion_maxima(self, config_sl_80_xs_20):
        """Siniestralidad extrema → recuperación limitada al máximo"""
        sl = StopLoss(config_sl_80_xs_20)

        recuperacion = sl.calcular_recuperacion(
            siniestros_totales=Decimal("15000000"),  # 150%
            primas_totales=Decimal("10000000"),
        )

        # Exceso: 150% - 80% = 70%
        # Límite: 20%
        # Recuperación máxima: $2M
        assert recuperacion == Decimal("2000000")


class TestStopLossSiniestralidadNeta:
    """Tests para siniestralidad neta después de reaseguro"""

    def test_siniestralidad_neta_con_recuperacion(self, config_sl_80_xs_20):
        """Siniestralidad neta debe reflejar la recuperación"""
        sl = StopLoss(config_sl_80_xs_20)

        # Siniestralidad bruta: 90%
        # Recuperación: $1M (10%)
        # Siniestralidad neta: 80%

        siniestralidad_neta = sl.calcular_siniestralidad_neta(
            siniestros_totales=Decimal("9000000"),
            primas_totales=Decimal("10000000"),
            recuperacion=Decimal("1000000"),
        )

        assert siniestralidad_neta == Decimal("80")

    def test_siniestralidad_neta_sin_recuperacion(self, config_sl_80_xs_20):
        """Sin recuperación, siniestralidad neta = bruta"""
        sl = StopLoss(config_sl_80_xs_20)

        siniestralidad_neta = sl.calcular_siniestralidad_neta(
            siniestros_totales=Decimal("7000000"),
            primas_totales=Decimal("10000000"),
            recuperacion=Decimal("0"),
        )

        assert siniestralidad_neta == Decimal("70")


class TestStopLossPrima:
    """Tests para cálculo de prima"""

    def test_calcular_prima_reaseguro(self, config_sl_80_xs_20):
        """Prima = 3% de primas sujetas (método simplificado)"""
        sl = StopLoss(config_sl_80_xs_20)
        prima = sl.calcular_prima_reaseguro()

        # 3% de $10M = $300K
        assert prima == Decimal("300000")


class TestStopLossResultadoNeto:
    """Tests para resultado neto del contrato"""

    def test_resultado_sin_activacion(
        self, config_sl_80_xs_20, siniestros_bajos
    ):
        """Siniestralidad 70% → no activa → solo se paga prima"""
        sl = StopLoss(config_sl_80_xs_20)

        resultado = sl.calcular_resultado_neto(
            primas_totales=Decimal("10000000"),
            siniestros=siniestros_bajos,
        )

        # No hay recuperación
        assert resultado.recuperacion_reaseguro == Decimal("0")
        # Solo se paga la prima
        assert resultado.prima_reaseguro_pagada == Decimal("300000")
        # Resultado negativo (solo costo de prima)
        assert resultado.resultado_neto_cedente == Decimal("-300000")
        assert resultado.detalles["contrato_activado"] is False

    def test_resultado_con_activacion(
        self, config_sl_80_xs_20, siniestros_altos
    ):
        """Siniestralidad 90% → activa → recuperación $1M"""
        sl = StopLoss(config_sl_80_xs_20)

        resultado = sl.calcular_resultado_neto(
            primas_totales=Decimal("10000000"),
            siniestros=siniestros_altos,
        )

        # Recuperación: $1M (10% de $10M)
        assert resultado.recuperacion_reaseguro == Decimal("1000000")
        # Prima: $300K
        assert resultado.prima_reaseguro_pagada == Decimal("300000")
        # Resultado neto: $1M - $300K = $700K
        assert resultado.resultado_neto_cedente == Decimal("700000")
        assert resultado.detalles["contrato_activado"] is True

    def test_resultado_con_activacion_maxima(
        self, config_sl_80_xs_20, siniestros_extremos
    ):
        """Siniestralidad 110% → recuperación limitada a $2M"""
        sl = StopLoss(config_sl_80_xs_20)

        resultado = sl.calcular_resultado_neto(
            primas_totales=Decimal("10000000"),
            siniestros=siniestros_extremos,
        )

        # Recuperación máxima: $2M (20% de $10M)
        assert resultado.recuperacion_reaseguro == Decimal("2000000")
        # Prima: $300K
        assert resultado.prima_reaseguro_pagada == Decimal("300000")
        # Resultado neto: $2M - $300K = $1.7M
        assert resultado.resultado_neto_cedente == Decimal("1700000")

    def test_detalles_en_resultado(
        self, config_sl_80_xs_20, siniestros_altos
    ):
        """Debe incluir detalles completos en el resultado"""
        sl = StopLoss(config_sl_80_xs_20)

        resultado = sl.calcular_resultado_neto(
            primas_totales=Decimal("10000000"),
            siniestros=siniestros_altos,
        )

        assert "siniestralidad_bruta" in resultado.detalles
        assert "siniestralidad_neta" in resultado.detalles
        assert "contrato_activado" in resultado.detalles
        assert resultado.detalles["numero_siniestros"] == 9
        assert resultado.detalles["siniestralidad_bruta"] == "90.00%"
        assert resultado.detalles["siniestralidad_neta"] == "80.00%"

    def test_sin_siniestros(self, config_sl_80_xs_20):
        """Sin siniestros → siniestralidad 0% → no activa"""
        sl = StopLoss(config_sl_80_xs_20)

        resultado = sl.calcular_resultado_neto(
            primas_totales=Decimal("10000000"),
            siniestros=[],
        )

        assert resultado.recuperacion_reaseguro == Decimal("0")
        assert resultado.resultado_neto_cedente == Decimal("-300000")

    def test_siniestralidad_extrema(self, config_sl_80_xs_20):
        """Siniestralidad > 200% → recuperación limitada"""
        sl = StopLoss(config_sl_80_xs_20)

        # Siniestros de $25M (250%)
        siniestros_extremos_250 = [
            Siniestro(
                id_siniestro=f"SIN-{i}",
                fecha_ocurrencia=date(2024, (i % 12) + 1, 15),
                monto_bruto=Decimal("1000000"),
                tipo=TipoSiniestro.INDIVIDUAL,
            )
            for i in range(25)
        ]

        resultado = sl.calcular_resultado_neto(
            primas_totales=Decimal("10000000"),
            siniestros=siniestros_extremos_250,
        )

        # Recuperación máxima sigue siendo $2M
        assert resultado.recuperacion_reaseguro == Decimal("2000000")
