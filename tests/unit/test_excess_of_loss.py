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
        """Debe crear un contrato XL válido.

        El agregado del periodo es `limite * (1 + reinstalaciones)`: con dos
        reinstalaciones la capacidad total es 1.5M, no 500K (A4).
        """
        xl = ExcessOfLoss(config_xl_500_xs_200)
        assert xl.config.retencion == Decimal("200000")
        assert xl.config.limite == Decimal("500000")
        assert xl.limite_agregado == Decimal("1500000")
        assert xl.limite_disponible == Decimal("1500000")

    @pytest.mark.parametrize(
        ("limite", "retencion"),
        [
            (Decimal("5000000"), Decimal("5000000")),  # 5M xs 5M
            (Decimal("5000000"), Decimal("10000000")),  # 5M xs 10M
        ],
    )
    def test_capas_xl_validas_no_requieren_limite_mayor_retencion(self, limite, retencion):
        """El ancho de capa y la prioridad son importes independientes."""
        config = ExcessOfLossConfig(
            tipo_contrato=TipoContrato.EXCESS_OF_LOSS,
            vigencia_inicio=date(2024, 1, 1),
            vigencia_fin=date(2024, 12, 31),
            retencion=retencion,
            limite=limite,
            tasa_prima=Decimal("5"),
        )

        assert config.limite == limite
        assert config.retencion == retencion

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

    def test_siniestro_bajo_retencion(self, config_xl_500_xs_200, siniestro_pequeño):
        """Siniestro $150K < retención $200K → recuperación $0"""
        xl = ExcessOfLoss(config_xl_500_xs_200)
        recuperacion = xl.calcular_recuperacion(siniestro_pequeño)

        assert recuperacion == Decimal("0")
        assert xl.limite_disponible == Decimal("1500000")  # No se consume

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

    def test_siniestro_dentro_limite(self, config_xl_500_xs_200, siniestro_medio):
        """Siniestro $400K → exceso $200K → recuperación $200K"""
        xl = ExcessOfLoss(config_xl_500_xs_200)
        recuperacion = xl.calcular_recuperacion(siniestro_medio)

        # Exceso = 400K - 200K = 200K
        assert recuperacion == Decimal("200000")
        # El agregado se erosiona: 1.5M - 200K
        assert xl.limite_disponible == Decimal("1300000")

    def test_siniestro_excede_limite(self, config_xl_500_xs_200, siniestro_grande):
        """Siniestro $800K → exceso $600K → recuperación limitada a $500K"""
        xl = ExcessOfLoss(config_xl_500_xs_200)
        recuperacion = xl.calcular_recuperacion(siniestro_grande)

        # Exceso = 800K - 200K = 600K, capado por ocurrencia en 500K
        assert recuperacion == Decimal("500000")
        # Queda agregado para dos ocurrencias más (dos reinstalaciones)
        assert xl.limite_disponible == Decimal("1000000")

    def test_multiples_siniestros_agotan_el_agregado(self, config_xl_500_xs_200):
        """El agregado cubre tres ocurrencias completas y se agota (A4).

        Con 500K de límite y dos reinstalaciones, el agregado es 1.5M: tres
        siniestros que rebasen la capa recuperan 500K cada uno y el cuarto no
        recupera nada. La versión anterior erosionaba un único límite de 500K
        compartido, así que el segundo siniestro ya no recuperaba nada.
        """
        xl = ExcessOfLoss(config_xl_500_xs_200)
        recuperaciones = []

        for n in range(4):
            siniestro = Siniestro(
                id_siniestro=f"SIN-{n}",
                fecha_ocurrencia=date(2024, 6, 1),
                monto_bruto=Decimal("900000"),  # exceso 700K, capado en 500K
                tipo=TipoSiniestro.INDIVIDUAL,
            )
            recuperaciones.append(xl.calcular_recuperacion(siniestro))

        assert recuperaciones == [
            Decimal("500000"),
            Decimal("500000"),
            Decimal("500000"),
            Decimal("0"),
        ]
        assert xl.limite_disponible == Decimal("0")
        assert xl.reinstatements_usados == 2

    def test_el_agregado_se_agota_con_recuperaciones_parciales(self, config_xl_500_xs_200):
        """Siniestros que no llenan la capa también erosionan el agregado."""
        xl = ExcessOfLoss(config_xl_500_xs_200)

        total = Decimal("0")
        for n in range(9):
            siniestro = Siniestro(
                id_siniestro=f"SIN-{n}",
                fecha_ocurrencia=date(2024, 6, 1),
                monto_bruto=Decimal("400000"),  # exceso 200K
                tipo=TipoSiniestro.INDIVIDUAL,
            )
            total += xl.calcular_recuperacion(siniestro)

        # 7 siniestros de 200K = 1.4M, el octavo aporta solo los 100K restantes
        assert total == Decimal("1500000")
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
    """Reinstalaciones — cierre del hallazgo A4 de `docs/AUDIT.md`.

    Las reinstalaciones se aplican solas conforme el agregado se erosiona: no
    hay que "activarlas" a mano. La API anterior (`aplicar_reinstatement`) daba
    a entender lo contrario y, en la práctica, ninguna recuperación las usaba.
    """

    @pytest.fixture
    def xl_5m_xs_5m_una_reinstalacion(self):
        """La capa canónica del hallazgo A4: 5M xs 5M con una reinstalación."""
        return ExcessOfLoss(
            ExcessOfLossConfig(
                tipo_contrato=TipoContrato.EXCESS_OF_LOSS,
                vigencia_inicio=date(2024, 1, 1),
                vigencia_fin=date(2024, 12, 31),
                retencion=Decimal("5000000"),
                limite=Decimal("5000000"),
                numero_reinstatements=1,
                tasa_prima=Decimal("10"),
            )
        )

    @staticmethod
    def _perdida(identificador: str, monto: str) -> Siniestro:
        return Siniestro(
            id_siniestro=identificador,
            fecha_ocurrencia=date(2024, 6, 1),
            monto_bruto=Decimal(monto),
            tipo=TipoSiniestro.INDIVIDUAL,
        )

    def test_dos_perdidas_ceden_dos_limites(self, xl_5m_xs_5m_una_reinstalacion):
        """El escenario exacto del hallazgo: debe ceder 10M, no 5M.

        Dos pérdidas de 12M sobre 5M xs 5M: cada una excede la capa en 7M y se
        capa por ocurrencia en 5M. Con una reinstalación el agregado es 10M, así
        que ambas se recuperan completas. El cálculo a mano es 5M + 5M = 10M.
        """
        xl = xl_5m_xs_5m_una_reinstalacion
        perdidas = [self._perdida("S1", "12000000"), self._perdida("S2", "12000000")]

        total, detalle = xl.calcular_recuperacion_multiple(perdidas)

        assert total == Decimal("10000000")
        assert [recup for _, _, recup in detalle] == [
            Decimal("5000000"),
            Decimal("5000000"),
        ]
        assert xl.limite_disponible == Decimal("0")

    def test_sin_reinstalaciones_solo_se_cede_un_limite(self):
        """Con cero reinstalaciones el agregado es una sola capa.

        Es el contraste que separa la mecánica correcta de la defectuosa: el
        mismo par de pérdidas cede 5M aquí y 10M con una reinstalación.
        """
        xl = ExcessOfLoss(
            ExcessOfLossConfig(
                tipo_contrato=TipoContrato.EXCESS_OF_LOSS,
                vigencia_inicio=date(2024, 1, 1),
                vigencia_fin=date(2024, 12, 31),
                retencion=Decimal("5000000"),
                limite=Decimal("5000000"),
                numero_reinstatements=0,
                tasa_prima=Decimal("10"),
            )
        )
        perdidas = [self._perdida("S1", "12000000"), self._perdida("S2", "12000000")]

        total, _ = xl.calcular_recuperacion_multiple(perdidas)

        assert total == Decimal("5000000")
        assert xl.limite_agregado == Decimal("5000000")

    def test_la_tercera_perdida_no_recupera(self, xl_5m_xs_5m_una_reinstalacion):
        """Agotado el agregado, el contrato deja de responder."""
        xl = xl_5m_xs_5m_una_reinstalacion
        xl.calcular_recuperacion_multiple(
            [self._perdida("S1", "12000000"), self._perdida("S2", "12000000")]
        )

        assert xl.calcular_recuperacion(self._perdida("S3", "12000000")) == Decimal("0")

    def test_las_reinstalaciones_se_consumen_por_limite_completo(self, config_xl_500_xs_200):
        """Una reinstalación por cada límite completo erosionado."""
        xl = ExcessOfLoss(config_xl_500_xs_200)

        assert xl.obtener_reinstatements_disponibles() == 2

        # Media capa: todavía no se consume ninguna reinstalación
        xl.calcular_recuperacion(self._perdida("SIN-1", "450000"))
        assert xl.reinstatements_usados == 0
        assert xl.obtener_reinstatements_disponibles() == 2

        # Completar el primer límite consume la primera reinstalación
        xl.calcular_recuperacion(self._perdida("SIN-2", "500000"))
        assert xl.reinstatements_usados == 1
        assert xl.obtener_reinstatements_disponibles() == 1

    def test_el_tope_por_ocurrencia_es_independiente_del_agregado(
        self, xl_5m_xs_5m_una_reinstalacion
    ):
        """Una sola pérdida enorme no puede consumir todo el agregado.

        El límite por ocurrencia y el agregado son restricciones distintas: una
        pérdida de 100M recupera 5M (la capa), no 10M (el agregado).
        """
        xl = xl_5m_xs_5m_una_reinstalacion

        recuperacion = xl.calcular_recuperacion(self._perdida("S1", "100000000"))

        assert recuperacion == Decimal("5000000")
        assert xl.limite_disponible == Decimal("5000000")


class TestExcessOfLossPrima:
    """Tests para cálculo de prima"""

    def test_calcular_prima_reaseguro(self, config_xl_500_xs_200):
        """Prima = límite * tasa_prima / 100"""
        xl = ExcessOfLoss(config_xl_500_xs_200)
        prima = xl.calcular_prima_reaseguro()

        # 5% de 500K = 25K
        assert prima == Decimal("25000")

    def test_prima_de_reinstalacion_es_pro_rata_a_la_cantidad(self, config_xl_500_xs_200):
        """Prima de reinstalación = (repuesto / límite) * prima base.

        Sin erosión no hay prima. Media capa erosionada cuesta media prima base
        (25K / 2 = 12.5K), y una capa completa cuesta una prima base entera.
        """
        xl = ExcessOfLoss(config_xl_500_xs_200)
        assert xl.calcular_prima_reinstalacion() == Decimal("0")

        # Erosionar media capa: exceso de 250K sobre la retención
        xl.calcular_recuperacion(
            Siniestro(
                id_siniestro="SIN-1",
                fecha_ocurrencia=date(2024, 6, 1),
                monto_bruto=Decimal("450000"),
                tipo=TipoSiniestro.INDIVIDUAL,
            )
        )
        assert xl.calcular_prima_reinstalacion() == Decimal("12500")

        # Completar la capa: prima base entera
        xl.calcular_recuperacion(
            Siniestro(
                id_siniestro="SIN-2",
                fecha_ocurrencia=date(2024, 6, 1),
                monto_bruto=Decimal("450000"),
                tipo=TipoSiniestro.INDIVIDUAL,
            )
        )
        assert xl.calcular_prima_reinstalacion() == Decimal("25000")

    def test_la_prima_de_reinstalacion_se_topa_en_la_capacidad_reinstalable(
        self, config_xl_500_xs_200
    ):
        """Agotado el agregado, solo se cobran las reinstalaciones existentes.

        Con dos reinstalaciones se reponen a lo sumo dos límites, así que la
        prima de reinstalación no puede exceder dos primas base.
        """
        xl = ExcessOfLoss(config_xl_500_xs_200)
        for n in range(4):
            xl.calcular_recuperacion(
                Siniestro(
                    id_siniestro=f"SIN-{n}",
                    fecha_ocurrencia=date(2024, 6, 1),
                    monto_bruto=Decimal("900000"),
                    tipo=TipoSiniestro.INDIVIDUAL,
                )
            )

        assert xl.calcular_prima_reinstalacion() == Decimal("50000")


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

    def test_resultado_con_recuperacion(self, config_xl_500_xs_200, siniestro_medio):
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

        # Consumir agregado con dos siniestros que rebasan la capa
        for n in range(2):
            xl.calcular_recuperacion(
                Siniestro(
                    id_siniestro=f"SIN-{n}",
                    fecha_ocurrencia=date(2024, 6, 1),
                    monto_bruto=Decimal("900000"),
                    tipo=TipoSiniestro.INDIVIDUAL,
                )
            )
        assert xl.reinstatements_usados == 2

        # Resetear
        xl.resetear_limite()

        assert xl.limite_disponible == Decimal("1500000")
        assert xl.reinstatements_usados == 0
