"""
Tests completos para RCS (Daños, Inversión y Agregador).

Valida todos los componentes del sistema RCS.
"""

from decimal import Decimal

import pytest

from suite_actuarial.core.validators import (
    ConfiguracionRCSDanos,
    ConfiguracionRCSInversion,
    ConfiguracionRCSVida,
)
from suite_actuarial.regulatorio import (
    AgregadorRCS,
    RCSDanos,
    RCSInversion,
)

# ======================================
# Tests RCS Daños
# ======================================


@pytest.fixture
def config_danos_basico():
    """Configuración básica de RCS daños"""
    return ConfiguracionRCSDanos(
        primas_retenidas_12m=Decimal("250000000"),
        reserva_siniestros=Decimal("180000000"),
        coeficiente_variacion=Decimal("0.15"),
        numero_ramos=5,
    )


class TestRCSDanos:
    """Tests para RCS Daños"""

    def test_crear_rcs_danos(self, config_danos_basico):
        """Debe crear RCS Daños válido"""
        rcs = RCSDanos(config_danos_basico)
        assert rcs.config.primas_retenidas_12m == Decimal("250000000")

    def test_calcular_rcs_prima(self, config_danos_basico):
        """Debe calcular RCS prima positivo"""
        rcs = RCSDanos(config_danos_basico)
        rcs_prima = rcs.calcular_rcs_prima()
        assert rcs_prima > Decimal("0")

    def test_calcular_rcs_reserva(self, config_danos_basico):
        """Debe calcular RCS reserva positivo"""
        rcs = RCSDanos(config_danos_basico)
        rcs_reserva = rcs.calcular_rcs_reserva()
        assert rcs_reserva > Decimal("0")

    def test_rcs_total_danos(self, config_danos_basico):
        """Debe calcular RCS total daños con correlación"""
        rcs = RCSDanos(config_danos_basico)
        rcs_total, desglose = rcs.calcular_rcs_total_danos()

        assert rcs_total > Decimal("0")
        assert "prima" in desglose
        assert "reserva" in desglose

        # Total debe ser menor que suma (por correlación)
        suma_simple = desglose["prima"] + desglose["reserva"]
        assert rcs_total < suma_simple

    def test_diversificacion_por_ramos(self):
        """Más ramos deben reducir RCS relativo"""
        config_1_ramo = ConfiguracionRCSDanos(
            primas_retenidas_12m=Decimal("100000000"),
            reserva_siniestros=Decimal("80000000"),
            coeficiente_variacion=Decimal("0.15"),
            numero_ramos=1,
        )

        config_5_ramos = ConfiguracionRCSDanos(
            primas_retenidas_12m=Decimal("100000000"),
            reserva_siniestros=Decimal("80000000"),
            coeficiente_variacion=Decimal("0.15"),
            numero_ramos=5,
        )

        prima_1_ramo = RCSDanos(config_1_ramo).calcular_rcs_prima()
        prima_5_ramos = RCSDanos(config_5_ramos).calcular_rcs_prima()

        # Diversificación: más ramos = menor RCS
        assert prima_5_ramos < prima_1_ramo

    def test_cv_invalido(self):
        """Coeficiente de variación debe estar en rango válido"""
        with pytest.raises((ValueError, Exception)):
            ConfiguracionRCSDanos(
                primas_retenidas_12m=Decimal("100000000"),
                reserva_siniestros=Decimal("80000000"),
                coeficiente_variacion=Decimal("0.01"),  # Muy bajo (< 0.05)
            )


# ======================================
# Tests RCS Inversión
# ======================================


@pytest.fixture
def config_inversion_basico():
    """Configuración básica de RCS inversión"""
    return ConfiguracionRCSInversion(
        valor_acciones=Decimal("50000000"),
        valor_bonos_gubernamentales=Decimal("300000000"),
        valor_bonos_corporativos=Decimal("150000000"),
        valor_inmuebles=Decimal("100000000"),
        duracion_promedio_bonos=Decimal("7.5"),
        calificacion_promedio_bonos="AA",
    )


class TestRCSInversion:
    """Tests para RCS Inversión"""

    def test_crear_rcs_inversion(self, config_inversion_basico):
        """Debe crear RCS Inversión válido"""
        rcs = RCSInversion(config_inversion_basico)
        assert rcs.config.valor_acciones == Decimal("50000000")

    def test_rcs_mercado_acciones(self, config_inversion_basico):
        """Debe calcular RCS mercado acciones con shock 35%"""
        rcs = RCSInversion(config_inversion_basico)
        rcs_acciones = rcs.calcular_rcs_mercado_acciones()

        # Debe ser aproximadamente 35% del valor
        esperado = config_inversion_basico.valor_acciones * Decimal("0.35")
        assert abs(rcs_acciones - esperado) < Decimal("1")

    def test_rcs_bonos_gubernamentales(self, config_inversion_basico):
        """Debe calcular RCS bonos gubernamentales con shock ajustado"""
        rcs = RCSInversion(config_inversion_basico)
        rcs_bonos = rcs.calcular_rcs_mercado_bonos_gubernamentales()
        assert rcs_bonos > Decimal("0")

    def test_rcs_bonos_corporativos(self, config_inversion_basico):
        """Debe calcular RCS bonos corporativos"""
        rcs = RCSInversion(config_inversion_basico)
        rcs_corp = rcs.calcular_rcs_mercado_bonos_corporativos()
        assert rcs_corp > Decimal("0")

    def test_rcs_inmuebles(self, config_inversion_basico):
        """Debe calcular RCS inmuebles con shock 25%"""
        rcs = RCSInversion(config_inversion_basico)
        rcs_inmuebles = rcs.calcular_rcs_mercado_inmuebles()

        esperado = config_inversion_basico.valor_inmuebles * Decimal("0.25")
        assert abs(rcs_inmuebles - esperado) < Decimal("1")

    def test_rcs_credito(self, config_inversion_basico):
        """Debe calcular RCS crédito según calificación"""
        rcs = RCSInversion(config_inversion_basico)
        rcs_credito = rcs.calcular_rcs_credito()
        assert rcs_credito > Decimal("0")

    def test_rcs_concentracion(self, config_inversion_basico):
        """Debe calcular RCS concentración"""
        rcs = RCSInversion(config_inversion_basico)
        rcs_conc = rcs.calcular_rcs_concentracion()
        assert rcs_conc > Decimal("0")

    def test_rcs_total_inversion(self, config_inversion_basico):
        """Debe calcular RCS total inversión"""
        rcs = RCSInversion(config_inversion_basico)
        rcs_total, desglose = rcs.calcular_rcs_total_inversion()

        assert rcs_total > Decimal("0")
        assert "mercado" in desglose
        assert "credito" in desglose
        assert "concentracion" in desglose

    def test_calificacion_invalida(self):
        """Calificación inválida debe fallar"""
        with pytest.raises(ValueError, match="no válida"):
            ConfiguracionRCSInversion(
                valor_acciones=Decimal("50000000"),
                calificacion_promedio_bonos="ZZZ",  # Inválido
            )

    def test_rcs_mercado_correlacion_menor_que_suma(self, config_inversion_basico):
        """RCS mercado con correlacion 0.75 debe ser menor que suma simple"""
        rcs = RCSInversion(config_inversion_basico)

        # Compute individual components
        rcs_acc = rcs.calcular_rcs_mercado_acciones()
        rcs_bg = rcs.calcular_rcs_mercado_bonos_gubernamentales()
        rcs_bc = rcs.calcular_rcs_mercado_bonos_corporativos()
        rcs_inm = rcs.calcular_rcs_mercado_inmuebles()

        suma_simple = rcs_acc + rcs_bg + rcs_bc + rcs_inm
        rcs_mercado = rcs.calcular_rcs_mercado_total()

        # Correlation 0.75 < 1.0 must yield a lower aggregate
        assert rcs_mercado < suma_simple
        # But it should still be meaningfully large
        assert rcs_mercado > Decimal("0")

    def test_sin_inversiones(self):
        """Debe requerir al menos una inversión"""
        with pytest.raises(ValueError, match="al menos un tipo"):
            ConfiguracionRCSInversion()


# ======================================
# Tests Agregador RCS
# ======================================


@pytest.fixture
def config_completo():
    """Configuración completa para todos los riesgos"""
    config_vida = ConfiguracionRCSVida(
        suma_asegurada_total=Decimal("500000000"),
        reserva_matematica=Decimal("350000000"),
        edad_promedio_asegurados=45,
        duracion_promedio_polizas=15,
        numero_asegurados=10000,
    )

    config_danos = ConfiguracionRCSDanos(
        primas_retenidas_12m=Decimal("250000000"),
        reserva_siniestros=Decimal("180000000"),
        coeficiente_variacion=Decimal("0.15"),
        numero_ramos=5,
    )

    config_inversion = ConfiguracionRCSInversion(
        valor_acciones=Decimal("50000000"),
        valor_bonos_gubernamentales=Decimal("300000000"),
        valor_bonos_corporativos=Decimal("150000000"),
        valor_inmuebles=Decimal("100000000"),
        duracion_promedio_bonos=Decimal("7.5"),
        calificacion_promedio_bonos="AA",
    )

    return config_vida, config_danos, config_inversion


class TestAgregadorRCS:
    """Tests para Agregador RCS"""

    def test_crear_agregador_completo(self, config_completo):
        """Debe crear agregador con todos los componentes"""
        config_vida, config_danos, config_inv = config_completo

        agregador = AgregadorRCS(
            config_vida=config_vida,
            config_danos=config_danos,
            config_inversion=config_inv,
            capital_minimo_pagado=Decimal("100000000"),
        )

        assert agregador.rcs_vida is not None
        assert agregador.rcs_danos is not None
        assert agregador.rcs_inversion is not None

    def test_calcular_rcs_completo(self, config_completo):
        """Debe calcular RCS completo con todos los componentes"""
        config_vida, config_danos, config_inv = config_completo

        agregador = AgregadorRCS(
            config_vida=config_vida,
            config_danos=config_danos,
            config_inversion=config_inv,
            capital_minimo_pagado=Decimal("100000000"),
        )

        resultado = agregador.calcular_rcs_completo()

        # Validar que todos los componentes están presentes
        assert resultado.rcs_suscripcion_vida > Decimal("0")
        assert resultado.rcs_suscripcion_danos > Decimal("0")
        assert resultado.rcs_inversion > Decimal("0")
        assert resultado.rcs_total > Decimal("0")

        # Validar campos de solvencia
        assert resultado.capital_minimo_pagado == Decimal("100000000")
        assert resultado.ratio_solvencia > Decimal("0")
        assert isinstance(resultado.cumple_regulacion, bool)

    def test_agregacion_con_correlaciones(self, config_completo):
        """RCS total debe ser menor que suma por correlación"""
        config_vida, config_danos, config_inv = config_completo

        agregador = AgregadorRCS(
            config_vida=config_vida,
            config_danos=config_danos,
            config_inversion=config_inv,
            capital_minimo_pagado=Decimal("100000000"),
        )

        resultado = agregador.calcular_rcs_completo()

        # Suma simple de componentes
        suma_simple = (
            resultado.rcs_suscripcion_vida
            + resultado.rcs_suscripcion_danos
            + resultado.rcs_inversion
        )

        # RCS total debe ser menor (correlaciones < 1)
        assert resultado.rcs_total < suma_simple

    def test_cumplimiento_regulacion_suficiente(self):
        """Debe cumplir si capital >= RCS"""
        config_vida = ConfiguracionRCSVida(
            suma_asegurada_total=Decimal("100000000"),
            reserva_matematica=Decimal("70000000"),
            edad_promedio_asegurados=40,
            duracion_promedio_polizas=15,
        )

        agregador = AgregadorRCS(
            config_vida=config_vida,
            capital_minimo_pagado=Decimal(
                "100000000"
            ),  # Capital alto suficiente
        )

        resultado = agregador.calcular_rcs_completo()

        # Debe cumplir con capital suficiente
        assert resultado.cumple_regulacion is True
        assert resultado.excedente_solvencia > Decimal("0")
        assert resultado.ratio_solvencia < Decimal("1.0")

    def test_incumplimiento_regulacion(self):
        """Debe NO cumplir si capital < RCS"""
        config_vida = ConfiguracionRCSVida(
            suma_asegurada_total=Decimal("500000000"),
            reserva_matematica=Decimal("350000000"),
            edad_promedio_asegurados=45,
            duracion_promedio_polizas=15,
        )

        agregador = AgregadorRCS(
            config_vida=config_vida,
            capital_minimo_pagado=Decimal("1000000"),  # Capital muy bajo
        )

        resultado = agregador.calcular_rcs_completo()

        # NO debe cumplir
        assert resultado.cumple_regulacion is False
        assert resultado.excedente_solvencia < Decimal("0")
        assert resultado.ratio_solvencia > Decimal("1.0")

    def test_matriz_correlacion(self, config_completo):
        """Debe obtener matriz de correlación"""
        config_vida, config_danos, config_inv = config_completo

        agregador = AgregadorRCS(
            config_vida=config_vida,
            config_danos=config_danos,
            config_inversion=config_inv,
            capital_minimo_pagado=Decimal("100000000"),
        )

        matriz = agregador.obtener_matriz_correlacion()

        assert "vida_danos" in matriz
        assert "vida_inversion" in matriz
        assert "danos_inversion" in matriz

        # Vida y daños no están correlacionados
        assert matriz["vida_danos"] == 0.0

    def test_composicion_rcs(self, config_completo):
        """Debe obtener composición porcentual del RCS"""
        config_vida, config_danos, config_inv = config_completo

        agregador = AgregadorRCS(
            config_vida=config_vida,
            config_danos=config_danos,
            config_inversion=config_inv,
            capital_minimo_pagado=Decimal("100000000"),
        )

        resultado = agregador.calcular_rcs_completo()
        composicion = agregador.obtener_composicion_rcs(resultado)

        assert "vida_pct" in composicion
        assert "danos_pct" in composicion
        assert "inversion_pct" in composicion

        # Los porcentajes deben sumar aproximadamente 100%
        # (no exacto por correlaciones - puede ser mayor o menor)
        total_pct = (
            composicion["vida_pct"]
            + composicion["danos_pct"]
            + composicion["inversion_pct"]
        )
        assert 80 < total_pct < 130  # Rango razonable con correlaciones

    def test_validar_capital_con_margen(self, config_completo):
        """Debe validar capital con margen de seguridad"""
        config_vida, config_danos, config_inv = config_completo

        agregador = AgregadorRCS(
            config_vida=config_vida,
            config_danos=config_danos,
            config_inversion=config_inv,
            capital_minimo_pagado=Decimal("100000000"),
        )

        resultado = agregador.calcular_rcs_completo()
        validacion = agregador.validar_capital_suficiente(
            resultado, margen_seguridad=Decimal("0.10")  # 10% margen
        )

        assert "cumple_minimo" in validacion
        assert "rcs_recomendado" in validacion
        assert "cumple_con_margen" in validacion

    def test_solo_vida(self):
        """Debe funcionar solo con vida"""
        config_vida = ConfiguracionRCSVida(
            suma_asegurada_total=Decimal("100000000"),
            reserva_matematica=Decimal("70000000"),
            edad_promedio_asegurados=40,
            duracion_promedio_polizas=15,
        )

        agregador = AgregadorRCS(
            config_vida=config_vida,
            capital_minimo_pagado=Decimal("50000000"),
        )

        resultado = agregador.calcular_rcs_completo()

        # Solo vida debe tener valores
        assert resultado.rcs_suscripcion_vida > Decimal("0")
        assert resultado.rcs_suscripcion_danos == Decimal("0")
        assert resultado.rcs_inversion == Decimal("0")

    def test_solo_danos(self):
        """Debe funcionar solo con daños"""
        config_danos = ConfiguracionRCSDanos(
            primas_retenidas_12m=Decimal("100000000"),
            reserva_siniestros=Decimal("80000000"),
            coeficiente_variacion=Decimal("0.15"),
        )

        agregador = AgregadorRCS(
            config_danos=config_danos,
            capital_minimo_pagado=Decimal("50000000"),
        )

        resultado = agregador.calcular_rcs_completo()

        # Solo daños debe tener valores
        assert resultado.rcs_suscripcion_vida == Decimal("0")
        assert resultado.rcs_suscripcion_danos > Decimal("0")
        assert resultado.rcs_inversion == Decimal("0")
