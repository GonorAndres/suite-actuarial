"""Procedencia de los parametros regulatorios y estados indeterminados.

Estas pruebas fijan una propiedad estructural, no un valor actuarial: los
factores que entran a un calculo deben venir del perfil regulatorio versionado
(`config/config_<anio>.py`) y no de constantes duplicadas dentro de los modulos
de calculo. Antes de la auditoria del 2026-07-26 `RCSInversion` y `AgregadorRCS`
llevaban su propia copia de los mismos numeros, de modo que editar la
configuracion no cambiaba el resultado.

Los valores esperados aqui se derivan de la configuracion inyectada en cada
prueba, no de repetir la formula bajo prueba.
"""

from decimal import Decimal

import pytest

from suite_actuarial.config.loader import config_vigente
from suite_actuarial.config.schema import FactoresCNSF
from suite_actuarial.core.validators import (
    ConfiguracionRCSInversion,
    ConfiguracionRCSVida,
)
from suite_actuarial.regulatorio.agregador_rcs import AgregadorRCS
from suite_actuarial.regulatorio.rcs_inversion import RCSInversion
from suite_actuarial.regulatorio.validaciones_sat.models import (
    EstadoFiscal,
    TipoSeguroFiscal,
)
from suite_actuarial.regulatorio.validaciones_sat.validador_retenciones import (
    CalculadoraRetencionesISR,
)


def _factores(**overrides: object) -> FactoresCNSF:
    """Factores CNSF de referencia con los campos que la prueba quiera mover."""
    base = {
        "shock_acciones": Decimal("0.35"),
        "shock_bonos_gubernamentales": Decimal("0.05"),
        "shock_bonos_corporativos": Decimal("0.15"),
        "shock_inmuebles": Decimal("0.25"),
        "shocks_credito": {"AA": Decimal("0.005")},
        "correlacion_vida_danos": Decimal("0.00"),
        "correlacion_vida_inversion": Decimal("0.25"),
        "correlacion_danos_inversion": Decimal("0.25"),
    }
    base.update(overrides)
    return FactoresCNSF(**base)  # type: ignore[arg-type]


class TestFactoresVienenDeLaConfiguracion:
    """El calculo debe obedecer a la configuracion inyectada."""

    def test_shock_de_acciones_obedece_a_la_configuracion(self):
        """Un shock de 0.99 sobre 1,000,000 debe dar 990,000, no 350,000.

        El valor esperado sale de la configuracion inyectada (0.99 x 1e6).
        Con las constantes de clase anteriores este calculo devolvia 350,000.
        """
        config = ConfiguracionRCSInversion(
            valor_acciones=Decimal("1000000"),
            valor_bonos_gubernamentales=Decimal("0"),
            valor_bonos_corporativos=Decimal("0"),
            valor_inmuebles=Decimal("0"),
            duracion_promedio_bonos=Decimal("5.0"),
            calificacion_promedio_bonos="AA",
        )
        rcs = RCSInversion(config, factores=_factores(shock_acciones=Decimal("0.99")))

        assert rcs.calcular_rcs_mercado_acciones() == Decimal("990000.00")

    def test_shock_de_inmuebles_obedece_a_la_configuracion(self):
        """Shock de 0.40 sobre 500,000 de inmuebles -> 200,000."""
        config = ConfiguracionRCSInversion(
            valor_acciones=Decimal("0"),
            valor_bonos_gubernamentales=Decimal("0"),
            valor_bonos_corporativos=Decimal("0"),
            valor_inmuebles=Decimal("500000"),
            duracion_promedio_bonos=Decimal("5.0"),
            calificacion_promedio_bonos="AA",
        )
        rcs = RCSInversion(config, factores=_factores(shock_inmuebles=Decimal("0.40")))

        assert rcs.calcular_rcs_mercado_inmuebles() == Decimal("200000.00")

    def test_por_defecto_toma_el_perfil_vigente(self):
        """Sin `factores` explicitos se usa el perfil regulatorio vigente."""
        config = ConfiguracionRCSInversion(
            valor_acciones=Decimal("1000000"),
            valor_bonos_gubernamentales=Decimal("0"),
            valor_bonos_corporativos=Decimal("0"),
            valor_inmuebles=Decimal("0"),
            duracion_promedio_bonos=Decimal("5.0"),
            calificacion_promedio_bonos="AA",
        )
        rcs = RCSInversion(config)

        assert rcs.factores == config_vigente().factores_cnsf

    def test_correlaciones_obedecen_a_la_configuracion(self):
        """Con correlacion 1.0 en todos los pares, la agregacion es la suma simple.

        sqrt(a^2 + b^2 + c^2 + 2ab + 2ac + 2bc) = a + b + c cuando rho = 1.
        Es una identidad algebraica, no una repeticion del codigo bajo prueba.
        """
        agregador = AgregadorRCS(
            factores=_factores(
                correlacion_vida_danos=Decimal("1"),
                correlacion_vida_inversion=Decimal("1"),
                correlacion_danos_inversion=Decimal("1"),
            )
        )
        total = agregador._agregar_con_correlaciones(Decimal("100"), Decimal("200"), Decimal("150"))

        assert abs(float(total) - 450.0) < 0.01


class TestRCSSinRiesgosConfigurados:
    """Un RCS sin riesgos no es un RCS que se cumple: es un RCS sin medir."""

    def test_agregado_sin_ningun_riesgo_falla(self):
        agregador = AgregadorRCS(capital_minimo_pagado=Decimal("100000000"))

        with pytest.raises(ValueError, match="al menos un riesgo"):
            agregador.calcular_rcs_completo()

    def test_con_un_solo_riesgo_calcula(self):
        agregador = AgregadorRCS(
            config_vida=ConfiguracionRCSVida(
                suma_asegurada_total=Decimal("50000000"),
                reserva_matematica=Decimal("15000000"),
                edad_promedio_asegurados=40,
                duracion_promedio_polizas=10,
                numero_asegurados=1000,
            ),
            capital_minimo_pagado=Decimal("100000000"),
        )

        assert agregador.calcular_rcs_completo().rcs_total > 0


class TestRetencionesCombinacionIncoherente:
    """Un pago es renta vitalicia o retiro de ahorro, no ambos."""

    def test_ambas_banderas_es_error(self):
        calculadora = CalculadoraRetencionesISR()

        with pytest.raises(ValueError, match="no puede ser renta vitalicia"):
            calculadora.calcular_retencion(
                tipo_seguro=TipoSeguroFiscal.VIDA,
                monto_pago=Decimal("500000"),
                monto_gravable=Decimal("350000"),
                es_renta_vitalicia=True,
                es_retiro_ahorro=True,
            )

    def test_el_resultado_declara_la_regla_que_aplico(self):
        """El lector debe poder ver que rama produjo el numero."""
        calculadora = CalculadoraRetencionesISR()
        resultado = calculadora.calcular_retencion(
            tipo_seguro=TipoSeguroFiscal.VIDA,
            monto_pago=Decimal("500000"),
            monto_gravable=Decimal("350000"),
            es_retiro_ahorro=True,
        )

        assert resultado.regla_aplicada
        assert "retiro de ahorro" in resultado.regla_aplicada


class TestDeducibilidadIndeterminada:
    """La capa de dominio ya distingue 'no deducible' de 'no se sabe'."""

    def test_falta_metodo_de_pago_deja_el_estado_indeterminado(self):
        from suite_actuarial.regulatorio.validaciones_sat.validador_primas import (
            ValidadorPrimasDeducibles,
        )

        validador = ValidadorPrimasDeducibles(uma_anual=Decimal("42794.64"))
        resultado = validador.validar_deducibilidad(
            tipo_seguro=TipoSeguroFiscal.GASTOS_MEDICOS,
            monto_prima=Decimal("50000"),
            es_persona_fisica=True,
        )

        assert resultado.estado == EstadoFiscal.INDETERMINATE
        assert "metodo_pago" in resultado.factores_faltantes
