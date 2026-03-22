"""
Tests para contrato Excess of Loss (Exceso de Pérdida).

Valida el cálculo de recuperaciones, límites y reinstatements.
"""

from datetime import date
from decimal import Decimal

import pytest

from suite_actuarial.core.validators import (
    ExcessOfLossConfig,
    ModalidadXL,
    Moneda,
    Siniestro,
    TipoContrato,
    TipoSiniestro,
)
from suite_actuarial.reaseguro.excess_of_loss import ExcessOfLoss


@pytest.fixture
def config_xl_500_xs_200():
    """XL 500 xs 200 (límite 500K, retención 200K)"""
    return ExcessOfLossConfig(
        tipo_contrato=TipoContrato.EXCESS_OF_LOSS,
        vigencia_inicio=date(2024, 1, 1),
        vigencia_fin=date(2024, 12, 31),
        moneda=Moneda.MXN,
        retencion=Decimal("200000"),
        limite=Decimal("500000"),
        modalidad=ModalidadXL.POR_RIESGO,
        numero_reinstatements=2,
        tasa_prima=Decimal("5"),
    )


@pytest.fixture
def config_xl_1m_xs_500k():
    """XL 1M xs 500K (límite 1M, retención 500K)"""
    return ExcessOfLossConfig(
        tipo_contrato=TipoContrato.EXCESS_OF_LOSS,
        vigencia_inicio=date(2024, 1, 1),
        vigencia_fin=date(2024, 12, 31),
        retencion=Decimal("500000"),
        limite=Decimal("1000000"),
        modalidad=ModalidadXL.POR_EVENTO,
        numero_reinstatements=1,
        tasa_prima=Decimal("4"),
    )


@pytest.fixture
def siniestro_pequeño():
    """Siniestro de $150K (bajo retención típica)"""
    return Siniestro(
        id_siniestro="SIN-SMALL",
        fecha_ocurrencia=date(2024, 3, 15),
        monto_bruto=Decimal("150000"),
        tipo=TipoSiniestro.INDIVIDUAL,
    )


@pytest.fixture
def siniestro_medio():
    """Siniestro de $400K (excede retención 200K)"""
    return Siniestro(
        id_siniestro="SIN-MED",
        fecha_ocurrencia=date(2024, 6, 20),
        monto_bruto=Decimal("400000"),
        tipo=TipoSiniestro.INDIVIDUAL,
    )


@pytest.fixture
def siniestro_grande():
    """Siniestro de $800K (excede límite)"""
    return Siniestro(
        id_siniestro="SIN-LARGE",
        fecha_ocurrencia=date(2024, 9, 10),
        monto_bruto=Decimal("800000"),
        tipo=TipoSiniestro.INDIVIDUAL,
    )


class TestExcessOfLossCreacion:
    """Tests para la creación de contratos XL"""

    def test_crear_xl_valido(self, config_xl_500_xs_200):
        """Debe crear un contrato XL válido"""
        xl = ExcessOfLoss(config_xl_500_xs_200)
        assert xl.config.retencion == Decimal("200000")
        assert xl.config.limite == Decimal("500000")
        assert xl.limite_disponible == Decimal("500000")

    def test_limite_menor_retencion_invalido(self):
        """No debe permitir límite <= retención"""
        with pytest.raises(ValueError):
            ExcessOfLossConfig(
                tipo_contrato=TipoContrato.EXCESS_OF_LOSS,
                vigencia_inicio=date(2024, 1, 1),
                vigencia_fin=date(2024, 12, 31),
                retencion=Decimal("500000"),
                limite=Decimal("400000"),  # Menor que retención
                tasa_prima=Decimal("5"),
            )

    def test_retencion_negativa_invalida(self):
        """No debe permitir retención negativa"""
        with pytest.raises(ValueError):
            ExcessOfLossConfig(
                tipo_contrato=TipoContrato.EXCESS_OF_LOSS,
                vigencia_inicio=date(2024, 1, 1),
                vigencia_fin=date(2024, 12, 31),
                retencion=Decimal("-100000"),
                limite=Decimal("500000"),
                tasa_prima=Decimal("5"),
            )


class TestExcessOfLossRecuperacion:
    """Tests para cálculo de recuperaciones"""

    def test_siniestro_bajo_retencion(
        self, config_xl_500_xs_200, siniestro_pequeño
    ):
        """Siniestro $150K < retención $200K → recuperación $0"""
        xl = ExcessOfLoss(config_xl_500_xs_200)
        recuperacion = xl.calcular_recuperacion(siniestro_pequeño)

        assert recuperacion == Decimal("0")
        assert xl.limite_disponible == Decimal("500000")  # No se consume

    def test_siniestro_exactamente_retencion(self, config_xl_500_xs_200):
        """Siniestro = retención → recuperación $0"""
        xl = ExcessOfLoss(config_xl_500_xs_200)

        siniestro = Siniestro(
            id_siniestro="SIN-EXACT",
            fecha_ocurrencia=date(2024, 5, 1),
            monto_bruto=Decimal("200000"),  # Exactamente la retención
            tipo=TipoSiniestro.INDIVIDUAL,
        )

        recuperacion = xl.calcular_recuperacion(siniestro)
        assert recuperacion == Decimal("0")

    def test_siniestro_dentro_limite(
        self, config_xl_500_xs_200, siniestro_medio
    ):
        """Siniestro $400K → exceso $200K → recuperación $200K"""
        xl = ExcessOfLoss(config_xl_500_xs_200)
        recuperacion = xl.calcular_recuperacion(siniestro_medio)

        # Exceso = 400K - 200K = 200K
        assert recuperacion == Decimal("200000")
        # Límite se consume
        assert xl.limite_disponible == Decimal("300000")

    def test_siniestro_excede_limite(
        self, config_xl_500_xs_200, siniestro_grande
    ):
        """Siniestro $800K → exceso $600K → recuperación limitada a $500K"""
        xl = ExcessOfLoss(config_xl_500_xs_200)
        recuperacion = xl.calcular_recuperacion(siniestro_grande)

        # Exceso = 800K - 200K = 600K
        # Pero límite es solo 500K
        assert recuperacion == Decimal("500000")
        assert xl.limite_disponible == Decimal("0")  # Límite agotado

    def test_multiples_siniestros_agotan_limite(
        self, config_xl_500_xs_200, siniestro_medio
    ):
        """Múltiples siniestros pueden agotar el límite"""
        xl = ExcessOfLoss(config_xl_500_xs_200)

        # Primer siniestro: $400K → recuperación $200K
        recup1 = xl.calcular_recuperacion(siniestro_medio)
        assert recup1 == Decimal("200000")
        assert xl.limite_disponible == Decimal("300000")

        # Segundo siniestro: $400K → exceso $200K, pero solo quedan $300K
        siniestro2 = Siniestro(
            id_siniestro="SIN-2",
            fecha_ocurrencia=date(2024, 7, 1),
            monto_bruto=Decimal("400000"),
            tipo=TipoSiniestro.INDIVIDUAL,
        )
        recup2 = xl.calcular_recuperacion(siniestro2)
        assert recup2 == Decimal("200000")
        assert xl.limite_disponible == Decimal("100000")

        # Tercer siniestro: $400K → exceso $200K, pero solo quedan $100K
        siniestro3 = Siniestro(
            id_siniestro="SIN-3",
            fecha_ocurrencia=date(2024, 8, 1),
            monto_bruto=Decimal("400000"),
            tipo=TipoSiniestro.INDIVIDUAL,
        )
        recup3 = xl.calcular_recuperacion(siniestro3)
        assert recup3 == Decimal("100000")  # Solo lo que queda
        assert xl.limite_disponible == Decimal("0")

    def test_siniestro_fuera_vigencia(self, config_xl_500_xs_200):
        """No debe procesar siniestros fuera de vigencia"""
        xl = ExcessOfLoss(config_xl_500_xs_200)

        siniestro_futuro = Siniestro(
            id_siniestro="SIN-FUTURE",
            fecha_ocurrencia=date(2025, 3, 1),
            monto_bruto=Decimal("500000"),
            tipo=TipoSiniestro.INDIVIDUAL,
        )

        with pytest.raises(ValueError, match="fuera de vigencia"):
            xl.calcular_recuperacion(siniestro_futuro)


class TestExcessOfLossReinstatements:
    """Tests para reinstatements"""

    def test_reinstatement_primer_uso(self, config_xl_500_xs_200):
        """Debe aplicar reinstatement correctamente"""
        xl = ExcessOfLoss(config_xl_500_xs_200)

        # Consumir parte del límite
        monto_usado = Decimal("300000")
        xl.limite_disponible = Decimal("200000")  # Simular uso

        # Aplicar reinstatement
        exitoso, prima = xl.aplicar_reinstatement(monto_usado)

        assert exitoso is True
        # Límite se reinstala
        assert xl.limite_disponible == Decimal("500000")
        # Prima proporcional: 5% de 300K = 15K
        assert prima == Decimal("15000")
        assert xl.reinstatements_usados == 1

    def test_reinstatements_agotados(self, config_xl_500_xs_200):
        """No debe permitir más reinstatements de los configurados"""
        xl = ExcessOfLoss(config_xl_500_xs_200)

        # Usar los 2 reinstatements disponibles
        xl.limite_disponible = Decimal("0")
        xl.aplicar_reinstatement(Decimal("500000"))
        xl.limite_disponible = Decimal("0")
        xl.aplicar_reinstatement(Decimal("500000"))

        # Tercer intento debe fallar
        xl.limite_disponible = Decimal("0")
        with pytest.raises(ValueError, match="No quedan reinstatements"):
            xl.aplicar_reinstatement(Decimal("500000"))

    def test_obtener_reinstatements_disponibles(self, config_xl_500_xs_200):
        """Debe consultar correctamente reinstatements disponibles"""
        xl = ExcessOfLoss(config_xl_500_xs_200)

        assert xl.obtener_reinstatements_disponibles() == 2

        xl.aplicar_reinstatement(Decimal("100000"))
        assert xl.obtener_reinstatements_disponibles() == 1

        xl.aplicar_reinstatement(Decimal("100000"))
        assert xl.obtener_reinstatements_disponibles() == 0


class TestExcessOfLossPrima:
    """Tests para cálculo de prima"""

    def test_calcular_prima_reaseguro(self, config_xl_500_xs_200):
        """Prima = límite * tasa_prima / 100"""
        xl = ExcessOfLoss(config_xl_500_xs_200)
        prima = xl.calcular_prima_reaseguro()

        # 5% de 500K = 25K
        assert prima == Decimal("25000")

    def test_prima_proporcional_reinstatement(self, config_xl_500_xs_200):
        """Prima de reinstatement es proporcional al monto reinstalado"""
        xl = ExcessOfLoss(config_xl_500_xs_200)

        # Reinstalar la mitad del límite
        _, prima = xl.aplicar_reinstatement(Decimal("250000"))

        # 5% de 250K = 12.5K
        assert prima == Decimal("12500")


class TestExcessOfLossModalidades:
    """Tests para diferentes modalidades de XL"""

    def test_xl_por_riesgo(self, config_xl_500_xs_200):
        """XL por riesgo aplica a cada póliza individual"""
        xl = ExcessOfLoss(config_xl_500_xs_200)
        assert xl.config.modalidad == ModalidadXL.POR_RIESGO

    def test_xl_por_evento(self, config_xl_1m_xs_500k):
        """XL por evento aplica a eventos catastróficos"""
        xl = ExcessOfLoss(config_xl_1m_xs_500k)
        assert xl.config.modalidad == ModalidadXL.POR_EVENTO


class TestExcessOfLossResultadoNeto:
    """Tests para resultado neto del contrato"""

    def test_resultado_con_recuperacion(
        self, config_xl_500_xs_200, siniestro_medio
    ):
        """Debe calcular resultado neto correctamente"""
        xl = ExcessOfLoss(config_xl_500_xs_200)

        prima_pagada = xl.calcular_prima_reaseguro()

        resultado = xl.calcular_resultado_neto(
            prima_reaseguro_cobrada=prima_pagada,
            siniestros=[siniestro_medio],
        )

        # Siniestro: $400K
        # Recuperación: $200K (exceso sobre retención de 200K)
        # Prima pagada: $25K
        # Resultado neto = 200K - 25K = 175K

        assert resultado.recuperacion_reaseguro == Decimal("200000")
        assert resultado.prima_reaseguro_pagada == Decimal("25000")
        assert resultado.resultado_neto_cedente == Decimal("175000")

    def test_resetear_limite(self, config_xl_500_xs_200):
        """Debe resetear límite y reinstatements"""
        xl = ExcessOfLoss(config_xl_500_xs_200)

        # Consumir límite
        xl.limite_disponible = Decimal("100000")
        xl.reinstatements_usados = 2

        # Resetear
        xl.resetear_limite()

        assert xl.limite_disponible == Decimal("500000")
        assert xl.reinstatements_usados == 0
