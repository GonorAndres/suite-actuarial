"""
Tests para módulo de validaciones fiscales SAT.

Tests unitarios para validadores de primas deducibles, siniestros gravables
y calculadora de retenciones ISR.
"""

from decimal import Decimal

import pytest

from suite_actuarial.config.loader import config_vigente
from suite_actuarial.config.schema import TasasSAT
from suite_actuarial.regulatorio.validaciones_sat import (
    CalculadoraRetencionesISR,
    EstadoFiscal,
    EstadoTopeGlobal,
    TipoSeguroFiscal,
    ValidadorPrimasDeducibles,
    ValidadorSiniestrosGravables,
)

# ======================================
# Fixtures
# ======================================


@pytest.fixture
def uma_anual_2024():
    """UMA anual aproximada para 2024"""
    return Decimal("37500")  # ~103 pesos/día × 365 días


@pytest.fixture
def validador_primas(uma_anual_2024):
    """Validador de primas deducibles"""
    return ValidadorPrimasDeducibles(uma_anual=uma_anual_2024)


@pytest.fixture
def validador_siniestros():
    """Validador de siniestros gravables"""
    return ValidadorSiniestrosGravables()


@pytest.fixture
def calculadora_retenciones():
    """Calculadora de retenciones ISR"""
    return CalculadoraRetencionesISR()


# ======================================
# Tests de ValidadorPrimasDeducibles
# ======================================


class TestValidadorPrimasDeducibles:
    """Tests para ValidadorPrimasDeducibles"""

    def test_gastos_medicos_persona_fisica_es_deducible_pero_topada(self, validador_primas):
        """GMM es deducible, pero nunca "sin límite".

        Esta prueba fijaba antes el defecto: exigía 100% deducible. El último
        párrafo del Art. 151 LISR topa el total de deducciones personales, y la
        prima de GMM (fracc. VI) queda dentro de ese tope. Con la UMA de la
        fixture (37,500) el tope de 5 UMA es 187,500, muy por encima de una
        prima de 50,000, así que el monto no se recorta; lo que sí cambia es
        que el resultado ya declara qué pasó con el tope.
        """
        resultado = validador_primas.validar_deducibilidad(
            tipo_seguro=TipoSeguroFiscal.GASTOS_MEDICOS,
            monto_prima=Decimal("50000"),
            es_persona_fisica=True,
        )

        assert resultado.es_deducible is True
        assert resultado.monto_deducible == Decimal("50000")
        assert resultado.porcentaje_deducible == Decimal("100")
        assert "151" in resultado.fundamento_legal
        # La fracción es la VI (primas de GMM), no la I (honorarios médicos).
        assert "fracc. VI" in resultado.fundamento_legal
        # Sin el ingreso total, la rama del 15% no pudo evaluarse y se dice.
        assert resultado.tope_global == EstadoTopeGlobal.PARCIAL_SIN_INGRESOS

    def test_vida_persona_fisica_no_deducible(self, validador_primas):
        """Seguros de vida NO deducibles para personas físicas"""
        resultado = validador_primas.validar_deducibilidad(
            tipo_seguro=TipoSeguroFiscal.VIDA,
            monto_prima=Decimal("20000"),
            es_persona_fisica=True,
        )

        assert resultado.es_deducible is False
        assert resultado.monto_deducible == Decimal("0")
        assert resultado.porcentaje_deducible == Decimal("0")

    def test_pensiones_persona_fisica_limite_5_umas(self, validador_primas, uma_anual_2024):
        """Pensiones deducibles hasta 5 UMAs para personas físicas"""
        # Prima mayor a 5 UMAs
        prima_alta = Decimal("200000")
        resultado = validador_primas.validar_deducibilidad(
            tipo_seguro=TipoSeguroFiscal.PENSIONES,
            monto_prima=prima_alta,
            es_persona_fisica=True,
        )

        limite_esperado = uma_anual_2024 * 5  # 187,500

        assert resultado.es_deducible is True
        assert resultado.monto_deducible == limite_esperado
        assert resultado.monto_deducible < prima_alta
        assert "5 UMA anuales" in resultado.limite_aplicado

    def test_pensiones_persona_fisica_bajo_limite(self, validador_primas):
        """Pensiones bajo el límite deben ser 100% deducibles"""
        prima_baja = Decimal("100000")
        resultado = validador_primas.validar_deducibilidad(
            tipo_seguro=TipoSeguroFiscal.PENSIONES,
            monto_prima=prima_baja,
            es_persona_fisica=True,
        )

        assert resultado.es_deducible is True
        assert resultado.monto_deducible == prima_baja
        assert resultado.porcentaje_deducible == Decimal("100")

    def test_danos_persona_fisica_no_deducible(self, validador_primas):
        """Seguros de daños NO deducibles para personas físicas"""
        resultado = validador_primas.validar_deducibilidad(
            tipo_seguro=TipoSeguroFiscal.DANOS,
            monto_prima=Decimal("15000"),
            es_persona_fisica=True,
        )

        assert resultado.es_deducible is False
        assert resultado.monto_deducible == Decimal("0")

    def test_gastos_medicos_persona_moral_deducible(self, validador_primas):
        """GMM de empleados 100% deducible para personas morales"""
        resultado = validador_primas.validar_deducibilidad(
            tipo_seguro=TipoSeguroFiscal.GASTOS_MEDICOS,
            monto_prima=Decimal("500000"),
            es_persona_fisica=False,
        )

        assert resultado.es_deducible is True
        assert resultado.monto_deducible == Decimal("500000")
        assert resultado.porcentaje_deducible == Decimal("100")
        assert "Art. 25" in resultado.fundamento_legal

    def test_vida_persona_moral_deducible(self, validador_primas):
        """Seguros de vida de empleados deducibles para PM"""
        resultado = validador_primas.validar_deducibilidad(
            tipo_seguro=TipoSeguroFiscal.VIDA,
            monto_prima=Decimal("200000"),
            es_persona_fisica=False,
        )

        assert resultado.es_deducible is True
        assert resultado.monto_deducible == Decimal("200000")
        assert "Art. 25" in resultado.fundamento_legal

    def test_danos_persona_moral_deducible(self, validador_primas):
        """Seguros de daños sobre activos deducibles para PM"""
        resultado = validador_primas.validar_deducibilidad(
            tipo_seguro=TipoSeguroFiscal.DANOS,
            monto_prima=Decimal("100000"),
            es_persona_fisica=False,
        )

        assert resultado.es_deducible is True
        assert resultado.monto_deducible == Decimal("100000")
        assert "bienes" in resultado.fundamento_legal.lower()

    def test_invalidez_persona_moral_deducible(self, validador_primas):
        """Seguros de invalidez de empleados deducibles para PM"""
        resultado = validador_primas.validar_deducibilidad(
            tipo_seguro=TipoSeguroFiscal.INVALIDEZ,
            monto_prima=Decimal("50000"),
            es_persona_fisica=False,
        )

        assert resultado.es_deducible is True
        assert resultado.monto_deducible == Decimal("50000")


class TestTopeGlobalArt151:
    """Tope global de deducciones personales, último párrafo del Art. 151 LISR.

    Texto aplicado (Ley del ISR, texto vigente consolidado por la Cámara de
    Diputados, última reforma DOF 01-04-2024, consultado el 2026-08-02 en
    https://www.diputados.gob.mx/LeyesBiblio/pdf/LISR.pdf):

        "El monto total de las deducciones que podrán efectuar los
        contribuyentes en los términos de este artículo, no podrá exceder de la
        cantidad que resulte menor entre cinco veces el valor anual de la
        Unidad de Medida y Actualización, o del 15% del total de los ingresos
        del contribuyente, incluyendo aquéllos por los que no se pague el
        impuesto. Lo dispuesto en este párrafo no será aplicable tratándose de
        la fracción V de este artículo."

    Las cifras esperadas de cada caso se calculan a mano a partir de ese texto
    y de la UMA anual del perfil 2026 (42,794.64 MXN, INEGI, vigente del
    2026-02-01 al 2027-01-31), no ejecutando la fórmula bajo prueba.

        5 UMA anuales = 5 x 42,794.64 = 213,973.20 MXN
    """

    UMA_ANUAL_2026 = Decimal("42794.64")
    CINCO_UMA = Decimal("213973.20")

    @pytest.fixture
    def validador(self):
        return ValidadorPrimasDeducibles(
            uma_anual=self.UMA_ANUAL_2026,
            limite_deducciones_umas=5,
        )

    def test_manda_la_rama_del_15_por_ciento(self, validador):
        """Ingreso bajo: el 15% topa por debajo de las 5 UMA.

        Aritmética a mano:
            15% x 300,000 = 45,000
            5 UMA         = 213,973.20
            tope = min(45,000 ; 213,973.20) = 45,000
            deducible = min(prima 50,000 ; 45,000) = 45,000
            porcentaje = 45,000 / 50,000 = 90.00%
        """
        r = validador.validar_deducibilidad(
            tipo_seguro=TipoSeguroFiscal.GASTOS_MEDICOS,
            monto_prima=Decimal("50000"),
            es_persona_fisica=True,
            ingresos_totales_anuales=Decimal("300000"),
            metodo_pago="transferencia",
        )

        assert r.monto_deducible == Decimal("45000")
        assert r.porcentaje_deducible == Decimal("90.00")
        assert r.tope_global == EstadoTopeGlobal.APLICADO
        assert r.estado == EstadoFiscal.ELIGIBLE
        # El defecto cerrado: antes esto devolvia 50,000 al 100%.
        assert r.monto_deducible < r.monto_prima

    def test_manda_la_rama_de_las_cinco_umas(self, validador):
        """Ingreso alto: las 5 UMA topan por debajo del 15%.

        Aritmética a mano:
            15% x 3,000,000 = 450,000
            5 UMA           = 213,973.20
            tope = min(450,000 ; 213,973.20) = 213,973.20
            deducible = min(prima 400,000 ; 213,973.20) = 213,973.20
            porcentaje = 213,973.20 / 400,000 = 0.5349330 -> 53.49%
        """
        r = validador.validar_deducibilidad(
            tipo_seguro=TipoSeguroFiscal.GASTOS_MEDICOS,
            monto_prima=Decimal("400000"),
            es_persona_fisica=True,
            ingresos_totales_anuales=Decimal("3000000"),
            metodo_pago="transferencia",
        )

        assert r.monto_deducible == self.CINCO_UMA
        assert r.porcentaje_deducible == Decimal("53.49")
        assert r.tope_global == EstadoTopeGlobal.APLICADO

    def test_tope_no_restrictivo_deja_la_prima_completa(self, validador):
        """Prima por debajo de ambas ramas: se deduce completa.

        Aritmética a mano:
            15% x 300,000 = 45,000
            5 UMA         = 213,973.20
            tope = 45,000; deducible = min(prima 20,000 ; 45,000) = 20,000
        """
        r = validador.validar_deducibilidad(
            tipo_seguro=TipoSeguroFiscal.GASTOS_MEDICOS,
            monto_prima=Decimal("20000"),
            es_persona_fisica=True,
            ingresos_totales_anuales=Decimal("300000"),
            metodo_pago="transferencia",
        )

        assert r.monto_deducible == Decimal("20000")
        assert r.porcentaje_deducible == Decimal("100.00")
        assert r.tope_global == EstadoTopeGlobal.APLICADO

    def test_sin_ingresos_el_tope_queda_declarado_como_no_determinado(self, validador):
        """Sin el ingreso total, la rama del 15% no puede evaluarse.

        No se devuelve 100% en silencio: se aplica la única rama conocida
        (5 UMA = 213,973.20), el resultado se marca indeterminado y nombra el
        dato que falta. Aritmética a mano:
            deducible = min(prima 400,000 ; 213,973.20) = 213,973.20 (cota superior)
        """
        r = validador.validar_deducibilidad(
            tipo_seguro=TipoSeguroFiscal.GASTOS_MEDICOS,
            monto_prima=Decimal("400000"),
            es_persona_fisica=True,
            metodo_pago="transferencia",
        )

        assert r.monto_deducible == self.CINCO_UMA
        assert r.tope_global == EstadoTopeGlobal.PARCIAL_SIN_INGRESOS
        assert r.estado == EstadoFiscal.INDETERMINATE
        assert "ingresos_totales_anuales" in r.factores_faltantes
        assert "15%" in r.nota_tope_global

    def test_sin_ingresos_una_prima_pequena_no_se_declara_cierta(self, validador):
        """Aunque el monto no se recorte, el estado no finge certeza.

        prima 50,000 < 5 UMA (213,973.20), así que la rama conocida no muerde;
        pero la rama del 15% podría hacerlo (bastan ingresos por debajo de
        333,333.33) y no se evaluó. El monto es el mismo que el defecto viejo
        producía; lo que no es igual es que ahora se declara indeterminado.
        """
        r = validador.validar_deducibilidad(
            tipo_seguro=TipoSeguroFiscal.GASTOS_MEDICOS,
            monto_prima=Decimal("50000"),
            es_persona_fisica=True,
            metodo_pago="transferencia",
        )

        assert r.monto_deducible == Decimal("50000")
        assert r.tope_global == EstadoTopeGlobal.PARCIAL_SIN_INGRESOS
        assert r.estado == EstadoFiscal.INDETERMINATE

    def test_la_nota_dice_que_el_tope_es_global(self, validador):
        """El tope aplica al total de deducciones personales, no a una prima."""
        r = validador.validar_deducibilidad(
            tipo_seguro=TipoSeguroFiscal.GASTOS_MEDICOS,
            monto_prima=Decimal("50000"),
            es_persona_fisica=True,
            ingresos_totales_anuales=Decimal("300000"),
            metodo_pago="transferencia",
        )

        assert "total de las" in r.nota_tope_global
        assert "única deducción personal" in r.nota_tope_global

    def test_la_fraccion_de_gmm_es_la_vi(self, validador):
        """Las primas de GMM son la fracc. VI; la I son honorarios médicos."""
        r = validador.validar_deducibilidad(
            tipo_seguro=TipoSeguroFiscal.GASTOS_MEDICOS,
            monto_prima=Decimal("50000"),
            es_persona_fisica=True,
            metodo_pago="transferencia",
        )

        assert "fracc. VI" in r.fundamento_legal
        assert "fracc. I -" not in r.fundamento_legal


class TestFraccionVPlanesDeRetiro:
    """Fracción V: tope propio del 10%, y exclusión del tope global.

    Texto aplicado (misma fuente y fecha de consulta que `TestTopeGlobalArt151`):

        "El monto de la deducción a que se refiere esta fracción será de hasta
        el 10% de los ingresos acumulables del contribuyente en el ejercicio,
        sin que dichas aportaciones excedan del equivalente a cinco salarios
        mínimos generales del área geográfica del contribuyente elevados al
        año."

    Los cinco salarios mínimos se leen como cinco UMA anuales por el Art.
    Tercero transitorio del decreto de desindexación (DOF 27-01-2016), que es
    lo que el perfil anual versiona como `limite_deducciones_pf_umas`.
    """

    UMA_ANUAL_2026 = Decimal("42794.64")

    @pytest.fixture
    def validador(self):
        return ValidadorPrimasDeducibles(
            uma_anual=self.UMA_ANUAL_2026,
            limite_deducciones_umas=5,
        )

    def test_el_porcentaje_de_la_fraccion_v_es_diez_no_quince(self, validador):
        """El código calculaba 15%; el estatuto dice 10%.

        Aritmética a mano:
            10% x 1,000,000 = 100,000
            5 UMA           = 213,973.20
            tope = min(100,000 ; 213,973.20) = 100,000
            deducible = min(prima 150,000 ; 100,000) = 100,000

        Con el 15% anterior el tope habría sido 150,000 y la prima entera
        habría resultado deducible: el caso discrimina las dos versiones.
        """
        r = validador.validar_deducibilidad(
            tipo_seguro=TipoSeguroFiscal.PENSIONES,
            monto_prima=Decimal("150000"),
            es_persona_fisica=True,
            ingreso_anual=Decimal("1000000"),
            metodo_pago="transferencia",
        )

        assert r.monto_deducible == Decimal("100000")
        assert "10%" in r.limite_aplicado

    def test_la_fraccion_v_queda_fuera_del_tope_global(self, validador):
        """El último párrafo excluye expresamente a la fracción V."""
        r = validador.validar_deducibilidad(
            tipo_seguro=TipoSeguroFiscal.PENSIONES,
            monto_prima=Decimal("150000"),
            es_persona_fisica=True,
            ingreso_anual=Decimal("1000000"),
            metodo_pago="transferencia",
        )

        assert r.tope_global == EstadoTopeGlobal.NO_APLICABLE
        assert "fracción V" in r.nota_tope_global

    def test_manda_el_tope_de_cinco_umas_con_ingreso_alto(self, validador):
        """Ingreso alto: el 10% supera las 5 UMA y manda el tope en UMA.

        Aritmética a mano:
            10% x 5,000,000 = 500,000
            5 UMA           = 213,973.20
            tope = 213,973.20; deducible = min(prima 300,000 ; 213,973.20)
        """
        r = validador.validar_deducibilidad(
            tipo_seguro=TipoSeguroFiscal.PENSIONES,
            monto_prima=Decimal("300000"),
            es_persona_fisica=True,
            ingreso_anual=Decimal("5000000"),
            metodo_pago="transferencia",
        )

        assert r.monto_deducible == Decimal("213973.20")


# ======================================
# Tests de ValidadorSiniestrosGravables
# ======================================


class TestValidadorSiniestrosGravables:
    """Tests para ValidadorSiniestrosGravables"""

    def test_indemnizacion_muerte_exenta(self, validador_siniestros):
        """Indemnizaciones por muerte deben estar exentas"""
        resultado = validador_siniestros.validar_gravabilidad(
            tipo_seguro=TipoSeguroFiscal.VIDA,
            monto_pago=Decimal("1000000"),
            es_persona_fisica=True,
            es_indemnizacion_muerte=True,
        )

        assert resultado.esta_gravado is False
        assert resultado.monto_gravado == Decimal("0")
        assert resultado.monto_exento == Decimal("1000000")
        assert "Art. 93" in resultado.fundamento_legal

    def test_gastos_medicos_exentos(self, validador_siniestros):
        """Reembolsos de gastos médicos están exentos"""
        resultado = validador_siniestros.validar_gravabilidad(
            tipo_seguro=TipoSeguroFiscal.GASTOS_MEDICOS,
            monto_pago=Decimal("200000"),
            es_persona_fisica=True,
        )

        assert resultado.esta_gravado is False
        assert resultado.monto_exento == Decimal("200000")
        assert "Art. 93" in resultado.fundamento_legal

    def test_seguros_danos_exentos(self, validador_siniestros):
        """Indemnizaciones por daños están exentas (reposición)"""
        resultado = validador_siniestros.validar_gravabilidad(
            tipo_seguro=TipoSeguroFiscal.DANOS,
            monto_pago=Decimal("500000"),
            es_persona_fisica=True,
        )

        assert resultado.esta_gravado is False
        assert resultado.monto_exento == Decimal("500000")

    def test_invalidez_exenta(self, validador_siniestros):
        """Pagos por invalidez están exentos"""
        resultado = validador_siniestros.validar_gravabilidad(
            tipo_seguro=TipoSeguroFiscal.INVALIDEZ,
            monto_pago=Decimal("800000"),
            es_persona_fisica=True,
        )

        assert resultado.esta_gravado is False
        assert resultado.monto_exento == Decimal("800000")

    def test_renta_vitalicia_parcialmente_gravable(self, validador_siniestros):
        """Rentas vitalicias son parcialmente gravables"""
        resultado = validador_siniestros.validar_gravabilidad(
            tipo_seguro=TipoSeguroFiscal.PENSIONES,
            monto_pago=Decimal("10000"),
            es_persona_fisica=True,
            es_renta_vitalicia=True,
        )

        # Simplificación: 50% gravable, 50% exento
        assert resultado.esta_gravado is True
        assert resultado.monto_gravado == Decimal("5000")
        assert resultado.monto_exento == Decimal("5000")
        assert resultado.tasa_isr_aplicable == Decimal("0.5")  # 50%
        assert "Art. 142" in resultado.fundamento_legal

    def test_retiro_ahorro_con_ganancia(self, validador_siniestros):
        """Retiro de ahorro gravable solo la ganancia"""
        resultado = validador_siniestros.validar_gravabilidad(
            tipo_seguro=TipoSeguroFiscal.VIDA,
            monto_pago=Decimal("300000"),
            es_persona_fisica=True,
            es_retiro_ahorro=True,
            monto_primas_pagadas=Decimal("200000"),
        )

        # Ganancia = 300,000 - 200,000 = 100,000
        assert resultado.esta_gravado is True
        assert resultado.monto_gravado == Decimal("100000")
        assert resultado.monto_exento == Decimal("200000")
        assert "Art. 158" in resultado.fundamento_legal

    def test_retiro_ahorro_sin_ganancia(self, validador_siniestros):
        """Retiro de ahorro sin ganancia no debe ser gravable"""
        resultado = validador_siniestros.validar_gravabilidad(
            tipo_seguro=TipoSeguroFiscal.VIDA,
            monto_pago=Decimal("150000"),
            es_persona_fisica=True,
            es_retiro_ahorro=True,
            monto_primas_pagadas=Decimal("200000"),
        )

        # No hay ganancia (pago < primas)
        assert resultado.esta_gravado is False
        assert resultado.monto_gravado == Decimal("0")

    def test_retiro_ahorro_sin_info_primas(self, validador_siniestros):
        """Retiro de ahorro sin info de primas debe ser 100% gravable"""
        resultado = validador_siniestros.validar_gravabilidad(
            tipo_seguro=TipoSeguroFiscal.VIDA,
            monto_pago=Decimal("300000"),
            es_persona_fisica=True,
            es_retiro_ahorro=True,
            monto_primas_pagadas=None,
        )

        assert resultado.esta_gravado is True
        assert resultado.monto_gravado == Decimal("300000")
        assert resultado.tasa_isr_aplicable == Decimal("1")  # 100%

    def test_persona_moral_danos_no_gravable(self, validador_siniestros):
        """Seguros de daños no gravables para PM (reposición)"""
        resultado = validador_siniestros.validar_gravabilidad(
            tipo_seguro=TipoSeguroFiscal.DANOS,
            monto_pago=Decimal("1000000"),
            es_persona_fisica=False,
        )

        assert resultado.esta_gravado is False
        assert resultado.monto_exento == Decimal("1000000")

    def test_persona_moral_vida_gravable(self, validador_siniestros):
        """Seguros de vida gravables para PM (beneficiario empresa)"""
        resultado = validador_siniestros.validar_gravabilidad(
            tipo_seguro=TipoSeguroFiscal.VIDA,
            monto_pago=Decimal("500000"),
            es_persona_fisica=False,
            es_indemnizacion_muerte=True,
        )

        assert resultado.esta_gravado is True
        assert resultado.monto_gravado == Decimal("500000")
        assert "Art. 18" in resultado.fundamento_legal

    def test_persona_moral_pensiones_gravable(self, validador_siniestros):
        """PM fallback for non-danos, non-vida: gravable como ingreso acumulable"""
        resultado = validador_siniestros.validar_gravabilidad(
            tipo_seguro=TipoSeguroFiscal.PENSIONES,
            monto_pago=Decimal("100000"),
            es_persona_fisica=False,
        )

        assert resultado.esta_gravado is True
        assert resultado.monto_gravado == Decimal("100000")
        assert resultado.monto_exento == Decimal("0")
        assert "Art. 18" in resultado.fundamento_legal

    def test_persona_moral_invalidez_gravable(self, validador_siniestros):
        """PM fallback for invalidez: gravable como ingreso"""
        resultado = validador_siniestros.validar_gravabilidad(
            tipo_seguro=TipoSeguroFiscal.INVALIDEZ,
            monto_pago=Decimal("200000"),
            es_persona_fisica=False,
        )

        assert resultado.esta_gravado is True
        assert resultado.monto_gravado == Decimal("200000")


# ======================================
# Tests de CalculadoraRetencionesISR
# ======================================


class TestCalculadoraRetencionesISR:
    """Tests para CalculadoraRetencionesISR"""

    def test_retencion_renta_vitalicia(self, calculadora_retenciones):
        """Rentas vitalicias deben tener retención del 10%"""
        resultado = calculadora_retenciones.calcular_retencion(
            tipo_seguro=TipoSeguroFiscal.PENSIONES,
            monto_pago=Decimal("10000"),
            monto_gravable=Decimal("5000"),
            es_renta_vitalicia=True,
        )

        # Retención = 5,000 × 10% = 500
        assert resultado.requiere_retencion is True
        assert resultado.tasa_retencion == Decimal("0.10")
        assert resultado.monto_retencion == Decimal("500.00")
        assert resultado.monto_neto_pagar == Decimal("9500.00")

    def test_retencion_retiro_ahorro(self, calculadora_retenciones):
        """Retiros de ahorro deben tener retención del 20%"""
        resultado = calculadora_retenciones.calcular_retencion(
            tipo_seguro=TipoSeguroFiscal.VIDA,
            monto_pago=Decimal("300000"),
            monto_gravable=Decimal("100000"),
            es_retiro_ahorro=True,
        )

        # Retención = 100,000 × 20% = 20,000
        assert resultado.requiere_retencion is True
        assert resultado.tasa_retencion == Decimal("0.20")
        assert resultado.monto_retencion == Decimal("20000.00")
        assert resultado.monto_neto_pagar == Decimal("280000.00")

    def test_sin_retencion_indemnizacion_muerte(self, calculadora_retenciones):
        """Indemnizaciones por muerte no tienen retención"""
        resultado = calculadora_retenciones.calcular_retencion(
            tipo_seguro=TipoSeguroFiscal.VIDA,
            monto_pago=Decimal("1000000"),
            monto_gravable=Decimal("0"),
        )

        assert resultado.requiere_retencion is False
        assert resultado.monto_retencion == Decimal("0")
        assert resultado.monto_neto_pagar == Decimal("1000000")

    def test_sin_retencion_gastos_medicos(self, calculadora_retenciones):
        """Gastos médicos no tienen retención (exentos)"""
        resultado = calculadora_retenciones.calcular_retencion(
            tipo_seguro=TipoSeguroFiscal.GASTOS_MEDICOS,
            monto_pago=Decimal("200000"),
            monto_gravable=Decimal("0"),
        )

        assert resultado.requiere_retencion is False
        assert resultado.monto_neto_pagar == Decimal("200000")

    def test_sin_retencion_danos(self, calculadora_retenciones):
        """Seguros de daños no tienen retención"""
        resultado = calculadora_retenciones.calcular_retencion(
            tipo_seguro=TipoSeguroFiscal.DANOS,
            monto_pago=Decimal("500000"),
            monto_gravable=Decimal("0"),
        )

        assert resultado.requiere_retencion is False
        assert resultado.monto_neto_pagar == Decimal("500000")

    def test_sin_retencion_invalidez(self, calculadora_retenciones):
        """Invalidez no tiene retención (exenta)"""
        resultado = calculadora_retenciones.calcular_retencion(
            tipo_seguro=TipoSeguroFiscal.INVALIDEZ,
            monto_pago=Decimal("800000"),
            monto_gravable=Decimal("0"),
        )

        assert resultado.requiere_retencion is False
        assert resultado.monto_neto_pagar == Decimal("800000")

    def test_calculo_masivo_retenciones(self, calculadora_retenciones):
        """Debe calcular retenciones para múltiples pagos"""
        pagos = [
            {
                "tipo_seguro": TipoSeguroFiscal.PENSIONES,
                "monto_pago": Decimal("10000"),
                "monto_gravable": Decimal("5000"),
                "es_renta_vitalicia": True,
            },
            {
                "tipo_seguro": TipoSeguroFiscal.VIDA,
                "monto_pago": Decimal("300000"),
                "monto_gravable": Decimal("100000"),
                "es_retiro_ahorro": True,
            },
            {
                "tipo_seguro": TipoSeguroFiscal.GASTOS_MEDICOS,
                "monto_pago": Decimal("50000"),
                "monto_gravable": Decimal("0"),
            },
        ]

        resultados = calculadora_retenciones.calcular_retencion_masiva(pagos)

        assert len(resultados) == 3
        assert resultados[0].requiere_retencion is True  # Renta
        assert resultados[1].requiere_retencion is True  # Retiro ahorro
        assert resultados[2].requiere_retencion is False  # GMM

    def test_resumen_retenciones(self, calculadora_retenciones):
        """Debe generar resumen agregado de retenciones"""
        pagos = [
            {
                "tipo_seguro": TipoSeguroFiscal.PENSIONES,
                "monto_pago": Decimal("10000"),
                "monto_gravable": Decimal("5000"),
                "es_renta_vitalicia": True,
            },
            {
                "tipo_seguro": TipoSeguroFiscal.VIDA,
                "monto_pago": Decimal("300000"),
                "monto_gravable": Decimal("100000"),
                "es_retiro_ahorro": True,
            },
        ]

        resultados = calculadora_retenciones.calcular_retencion_masiva(pagos)
        resumen = calculadora_retenciones.generar_resumen_retenciones(resultados)

        assert resumen["numero_pagos"] == 2
        assert resumen["pagos_con_retencion"] == 2
        assert resumen["total_pagos"] == 310000.0
        assert resumen["total_gravable"] == 105000.0
        # Retención renta = 500, retiro = 20,000 → total = 20,500
        assert resumen["total_retenido"] == 20500.0
        assert resumen["total_neto"] == 289500.0

    def test_sin_monto_gravable_no_retencion(self, calculadora_retenciones):
        """Sin monto gravable no debe haber retención"""
        resultado = calculadora_retenciones.calcular_retencion(
            tipo_seguro=TipoSeguroFiscal.VIDA,
            monto_pago=Decimal("100000"),
            monto_gravable=Decimal("0"),
        )

        assert resultado.requiere_retencion is False
        assert resultado.monto_retencion == Decimal("0")


# ======================================
# Tests de Integración
# ======================================


class TestIntegracionValidaciones:
    """Tests de integración entre validadores"""

    def test_flujo_completo_gastos_medicos(
        self, validador_primas, validador_siniestros, calculadora_retenciones
    ):
        """Flujo completo: prima deducible + siniestro exento + sin retención"""
        # 1. Validar prima deducible
        prima_resultado = validador_primas.validar_deducibilidad(
            tipo_seguro=TipoSeguroFiscal.GASTOS_MEDICOS,
            monto_prima=Decimal("50000"),
            es_persona_fisica=True,
        )

        assert prima_resultado.es_deducible is True

        # 2. Validar siniestro exento
        siniestro_resultado = validador_siniestros.validar_gravabilidad(
            tipo_seguro=TipoSeguroFiscal.GASTOS_MEDICOS,
            monto_pago=Decimal("80000"),
            es_persona_fisica=True,
        )

        assert siniestro_resultado.esta_gravado is False

        # 3. Sin retención
        retencion_resultado = calculadora_retenciones.calcular_retencion(
            tipo_seguro=TipoSeguroFiscal.GASTOS_MEDICOS,
            monto_pago=Decimal("80000"),
            monto_gravable=siniestro_resultado.monto_gravado,
        )

        assert retencion_resultado.requiere_retencion is False

    def test_flujo_completo_renta_vitalicia(self, validador_siniestros, calculadora_retenciones):
        """Flujo completo: renta parcialmente gravable + retención 10%"""
        # 1. Validar gravabilidad (50% gravable)
        siniestro_resultado = validador_siniestros.validar_gravabilidad(
            tipo_seguro=TipoSeguroFiscal.PENSIONES,
            monto_pago=Decimal("20000"),
            es_persona_fisica=True,
            es_renta_vitalicia=True,
        )

        assert siniestro_resultado.esta_gravado is True
        assert siniestro_resultado.monto_gravado == Decimal("10000")

        # 2. Calcular retención sobre parte gravable
        retencion_resultado = calculadora_retenciones.calcular_retencion(
            tipo_seguro=TipoSeguroFiscal.PENSIONES,
            monto_pago=Decimal("20000"),
            monto_gravable=siniestro_resultado.monto_gravado,
            es_renta_vitalicia=True,
        )

        # Retención = 10,000 × 10% = 1,000
        assert retencion_resultado.requiere_retencion is True
        assert retencion_resultado.monto_retencion == Decimal("1000.00")
        assert retencion_resultado.monto_neto_pagar == Decimal("19000.00")


class TestTasasVienenDelPerfilAnual:
    """Las cifras SAT deben salir del perfil del año, no de literales en la clase.

    `TasasSAT` estaba versionada por año, pero nadie la leía para calcular:
    `CalculadoraRetencionesISR` llevaba sus tasas como constantes de clase y ni
    siquiera aceptaba configuración, y `ValidadorPrimasDeducibles` multiplicaba
    la UMA por un `5` escrito a mano. Como 2024, 2025 y 2026 traen los mismos
    valores, la divergencia no se veía; habría aparecido sin aviso en cuanto un
    año trajera otra cifra.

    Estas pruebas usan un perfil sintético con cifras distintas: si el cálculo
    volviera a leer literales, darían el valor viejo y fallarían.
    """

    @staticmethod
    def _tasas_divergentes() -> TasasSAT:
        """Un año hipotético donde las tres tasas y el tope cambian."""
        return TasasSAT(
            tasa_retencion_rentas_vitalicias=Decimal("0.12"),  # vs 0.10
            tasa_retencion_retiros_ahorro=Decimal("0.25"),  # vs 0.20
            tasa_retencion_otros_ingresos=Decimal("0.15"),  # vs 0.10
            tasa_isr_personas_morales=Decimal("0.30"),
            tasa_iva=Decimal("0.16"),
            limite_deducciones_pf_umas=7,  # vs 5
        )

    def test_renta_vitalicia_usa_la_tasa_del_perfil(self):
        calc = CalculadoraRetencionesISR(tasas=self._tasas_divergentes())
        r = calc.calcular_retencion(
            tipo_seguro=TipoSeguroFiscal.PENSIONES,
            monto_pago=Decimal("50000"),
            monto_gravable=Decimal("25000"),
            es_renta_vitalicia=True,
        )
        # 25,000 x 12% = 3,000 (con la tasa vieja de 10% habrian sido 2,500).
        assert r.tasa_retencion == Decimal("0.12")
        assert r.monto_retencion == Decimal("3000.00")

    def test_retiro_de_ahorro_usa_la_tasa_del_perfil(self):
        calc = CalculadoraRetencionesISR(tasas=self._tasas_divergentes())
        r = calc.calcular_retencion(
            tipo_seguro=TipoSeguroFiscal.VIDA,
            monto_pago=Decimal("100000"),
            monto_gravable=Decimal("40000"),
            es_retiro_ahorro=True,
        )
        # 40,000 x 25% = 10,000 (con 20% habrian sido 8,000).
        assert r.tasa_retencion == Decimal("0.25")
        assert r.monto_retencion == Decimal("10000.00")

    def test_otros_ingresos_usa_la_tasa_del_perfil(self):
        """Esta tasa ni siquiera existía en el esquema: se agregó al migrarla."""
        calc = CalculadoraRetencionesISR(tasas=self._tasas_divergentes())
        r = calc.calcular_retencion(
            tipo_seguro=TipoSeguroFiscal.PENSIONES,
            monto_pago=Decimal("10000"),
            monto_gravable=Decimal("10000"),
            es_renta_vitalicia=False,
            requiere_retencion_forzosa=True,
        )
        assert r.tasa_retencion == Decimal("0.15")
        assert r.monto_retencion == Decimal("1500.00")

    def test_el_tope_de_deducciones_usa_el_perfil(self):
        """El tope en UMAs se leía como un 5 literal junto a una UMA configurada."""
        uma_anual = Decimal("40000")
        validador = ValidadorPrimasDeducibles(uma_anual=uma_anual, limite_deducciones_umas=7)
        r = validador.validar_deducibilidad(
            tipo_seguro=TipoSeguroFiscal.PENSIONES,
            monto_prima=Decimal("1000000"),  # por encima de cualquier tope
            es_persona_fisica=True,
        )
        # 7 UMAs x 40,000 = 280,000 (con el 5 literal habrian sido 200,000).
        assert r.monto_deducible == Decimal("280000")
        assert "7 UMA anuales" in r.limite_aplicado

    def test_por_omision_toma_el_perfil_vigente(self):
        """Sin argumento debe leer la configuración, no una constante."""
        vigente = config_vigente().tasas_sat
        calc = CalculadoraRetencionesISR()
        assert calc.tasas.tasa_retencion_rentas_vitalicias == (
            vigente.tasa_retencion_rentas_vitalicias
        )
        assert calc.tasas.tasa_retencion_otros_ingresos == vigente.tasa_retencion_otros_ingresos
