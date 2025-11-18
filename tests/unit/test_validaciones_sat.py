"""
Tests para módulo de validaciones fiscales SAT.

Tests unitarios para validadores de primas deducibles, siniestros gravables
y calculadora de retenciones ISR.
"""

from decimal import Decimal

import pytest

from mexican_insurance.regulatorio.validaciones_sat import (
    CalculadoraRetencionesISR,
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

    def test_gastos_medicos_persona_fisica_deducible(self, validador_primas):
        """GMM debe ser 100% deducible para personas físicas"""
        resultado = validador_primas.validar_deducibilidad(
            tipo_seguro=TipoSeguroFiscal.GASTOS_MEDICOS,
            monto_prima=Decimal("50000"),
            es_persona_fisica=True,
        )

        assert resultado.es_deducible is True
        assert resultado.monto_deducible == Decimal("50000")
        assert resultado.porcentaje_deducible == Decimal("100")
        assert "151" in resultado.fundamento_legal

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
        assert "5 UMAs" in resultado.limite_aplicado

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

    def test_flujo_completo_renta_vitalicia(
        self, validador_siniestros, calculadora_retenciones
    ):
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
