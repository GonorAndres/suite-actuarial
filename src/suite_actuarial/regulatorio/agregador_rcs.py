"""
Agregador de RCS - Combina todos los riesgos con correlaciones.

Implementa la agregación final del Requerimiento de Capital de Solvencia (RCS)
combinando riesgos de suscripción (vida y daños) e inversión, aplicando
matrices de correlación según la normativa de la CNSF.
"""

import math
from decimal import Decimal
from typing import Any

from suite_actuarial.config.loader import config_vigente
from suite_actuarial.config.schema import FactoresCNSF
from suite_actuarial.core.validators import (
    ConfiguracionRCSDanos,
    ConfiguracionRCSInversion,
    ConfiguracionRCSVida,
    ResultadoRCS,
    calcular_ratio_solvencia,
)
from suite_actuarial.regulatorio.rcs_danos import RCSDanos
from suite_actuarial.regulatorio.rcs_inversion import RCSInversion
from suite_actuarial.regulatorio.rcs_vida import RCSVida


class AgregadorRCS:
    """
    Agregador de RCS que combina todos los riesgos.

    La agregación usa una matriz de correlación para evitar doble conteo
    de riesgos que están relacionados.

    Matriz de correlación (basada en Solvencia II y adaptada a CNSF):
                    Vida    Daños   Inversión
        Vida        1.00    0.00    0.25
        Daños       0.00    1.00    0.25
        Inversión   0.25    0.25    1.00

    Justificación:
    - Vida y Daños: correlación 0 (riesgos independientes)
    - Vida e Inversión: correlación 0.25 (inversiones respaldan reservas vida)
    - Daños e Inversión: correlación 0.25 (inversiones respaldan reservas daños)

    Los valores mostrados son los del perfil regulatorio vigente y son
    ilustrativos: ningun archivo del repositorio cita una fuente CUSF/CNSF para
    ellos. Ver docs/AUDIT.md.
    """

    def __init__(
        self,
        config_vida: ConfiguracionRCSVida | None = None,
        config_danos: ConfiguracionRCSDanos | None = None,
        config_inversion: ConfiguracionRCSInversion | None = None,
        capital_minimo_pagado: Decimal = Decimal("0"),
        factores: FactoresCNSF | None = None,
    ):
        """
        Inicializa el agregador de RCS.

        La matriz de correlación proviene del perfil regulatorio anual
        (`config/config_<anio>.py`), no de constantes de esta clase.

        Args:
            config_vida: Configuración para RCS vida (opcional)
            config_danos: Configuración para RCS daños (opcional)
            config_inversion: Configuración para RCS inversión (opcional)
            capital_minimo_pagado: Capital social mínimo pagado de la aseguradora
            factores: Factores CNSF a aplicar. Si se omite, se toman del perfil
                regulatorio vigente a la fecha de hoy.
        """
        self.config_vida = config_vida
        self.config_danos = config_danos
        self.config_inversion = config_inversion
        self.capital_minimo_pagado = capital_minimo_pagado
        self.factores = factores if factores is not None else config_vigente().factores_cnsf

        # Calculadores
        self.rcs_vida: RCSVida | None = None
        self.rcs_danos: RCSDanos | None = None
        self.rcs_inversion: RCSInversion | None = None

        # Inicializar calculadores
        if config_vida:
            self.rcs_vida = RCSVida(config_vida)
        if config_danos:
            self.rcs_danos = RCSDanos(config_danos)
        if config_inversion:
            self.rcs_inversion = RCSInversion(config_inversion, factores=self.factores)

    def calcular_rcs_completo(self) -> ResultadoRCS:
        """
        Calcula el RCS completo agregando todos los riesgos con correlaciones.

        Returns:
            ResultadoRCS con todos los componentes y agregación final

        Raises:
            ValueError: Si no se configuró ningún riesgo. Sin ninguno el RCS
                agregado seria cero y el ratio de solvencia reportaria
                cumplimiento sin haber medido nada.
        """
        if self.rcs_vida is None and self.rcs_danos is None and self.rcs_inversion is None:
            raise ValueError(
                "Configura al menos un riesgo (vida, danos o inversion): sin "
                "ninguno el RCS agregado seria cero y el ratio de solvencia no "
                "significaria nada."
            )

        # Calcular RCS individuales
        rcs_vida_total = Decimal("0")
        desglose_vida: dict[str, Decimal] = {}
        if self.rcs_vida:
            rcs_vida_total, desglose_vida = self.rcs_vida.calcular_rcs_total_vida()

        rcs_danos_total = Decimal("0")
        desglose_danos: dict[str, Decimal] = {}
        if self.rcs_danos:
            rcs_danos_total, desglose_danos = self.rcs_danos.calcular_rcs_total_danos()

        rcs_inversion_total = Decimal("0")
        desglose_inversion: dict[str, Decimal] = {}
        if self.rcs_inversion:
            rcs_inversion_total, desglose_inversion = (
                self.rcs_inversion.calcular_rcs_total_inversion()
            )

        # Agregar con correlaciones
        rcs_total = self._agregar_con_correlaciones(
            rcs_vida_total, rcs_danos_total, rcs_inversion_total
        )

        # Calcular indicadores de solvencia
        excedente = self.capital_minimo_pagado - rcs_total
        ratio_solvencia = calcular_ratio_solvencia(self.capital_minimo_pagado, rcs_total)
        cumple = self.capital_minimo_pagado >= rcs_total

        # Construir desglose completo
        desglose_completo = {}
        for nombre, valor in desglose_vida.items():
            desglose_completo[nombre] = valor
        for nombre, valor in desglose_danos.items():
            desglose_completo[nombre] = valor
        for nombre, valor in desglose_inversion.items():
            desglose_completo[nombre] = valor

        # Construir resultado
        resultado = ResultadoRCS(
            # Vida
            rcs_mortalidad=desglose_vida.get("mortalidad", Decimal("0")),
            rcs_longevidad=desglose_vida.get("longevidad", Decimal("0")),
            rcs_invalidez=desglose_vida.get("invalidez", Decimal("0")),
            rcs_gastos=desglose_vida.get("gastos", Decimal("0")),
            # Daños
            rcs_prima=desglose_danos.get("prima", Decimal("0")),
            rcs_reserva=desglose_danos.get("reserva", Decimal("0")),
            # Inversión
            rcs_mercado=desglose_inversion.get("mercado", Decimal("0")),
            rcs_credito=desglose_inversion.get("credito", Decimal("0")),
            rcs_concentracion=desglose_inversion.get("concentracion", Decimal("0")),
            # Agregados
            rcs_suscripcion_vida=rcs_vida_total,
            rcs_suscripcion_danos=rcs_danos_total,
            rcs_inversion=rcs_inversion_total,
            rcs_total=rcs_total,
            # Solvencia
            capital_minimo_pagado=self.capital_minimo_pagado,
            excedente_solvencia=excedente,
            ratio_solvencia=ratio_solvencia,
            cumple_regulacion=cumple,
            desglose_por_riesgo=desglose_completo,
        )

        return resultado

    def _agregar_con_correlaciones(
        self,
        rcs_vida: Decimal,
        rcs_danos: Decimal,
        rcs_inversion: Decimal,
    ) -> Decimal:
        """
        Agrega los RCS usando matriz de correlación.

        Formula:
            RCS_total = sqrt(
                RCS_vida² +
                RCS_daños² +
                RCS_inversión² +
                2×ρ_vida_daños×RCS_vida×RCS_daños +
                2×ρ_vida_inv×RCS_vida×RCS_inversión +
                2×ρ_daños_inv×RCS_daños×RCS_inversión
            )

        Args:
            rcs_vida: RCS total de vida
            rcs_danos: RCS total de daños
            rcs_inversion: RCS total de inversión

        Returns:
            RCS total agregado
        """
        # Términos cuadráticos
        termino_vida = rcs_vida**2
        termino_danos = rcs_danos**2
        termino_inversion = rcs_inversion**2

        # Términos de correlación
        corr_vida_danos = 2 * self.factores.correlacion_vida_danos * rcs_vida * rcs_danos
        corr_vida_inv = 2 * self.factores.correlacion_vida_inversion * rcs_vida * rcs_inversion
        corr_danos_inv = 2 * self.factores.correlacion_danos_inversion * rcs_danos * rcs_inversion

        # Suma total
        suma_total = (
            termino_vida
            + termino_danos
            + termino_inversion
            + corr_vida_danos
            + corr_vida_inv
            + corr_danos_inv
        )

        # Raíz cuadrada
        rcs_total = Decimal(str(math.sqrt(float(suma_total))))

        return rcs_total.quantize(Decimal("0.01"))

    def obtener_matriz_correlacion(self) -> dict[str, Any]:
        """
        Obtiene la matriz de correlación aplicada.

        Returns:
            Diccionario con correlaciones
        """
        return {
            "vida_danos": float(self.factores.correlacion_vida_danos),
            "vida_inversion": float(self.factores.correlacion_vida_inversion),
            "danos_inversion": float(self.factores.correlacion_danos_inversion),
        }

    def obtener_composicion_rcs(self, resultado: ResultadoRCS) -> dict[str, Any]:
        """
        Obtiene la composición porcentual del RCS total.

        Args:
            resultado: Resultado del cálculo de RCS

        Returns:
            Diccionario con porcentajes de cada componente
        """
        if resultado.rcs_total == 0:
            return {}

        total = float(resultado.rcs_total)

        composicion = {
            "vida_pct": float(resultado.rcs_suscripcion_vida) / total * 100,
            "danos_pct": float(resultado.rcs_suscripcion_danos) / total * 100,
            "inversion_pct": float(resultado.rcs_inversion) / total * 100,
        }

        # Desglose detallado
        if resultado.rcs_mortalidad > 0:
            composicion["mortalidad_pct"] = float(resultado.rcs_mortalidad) / total * 100
        if resultado.rcs_longevidad > 0:
            composicion["longevidad_pct"] = float(resultado.rcs_longevidad) / total * 100
        if resultado.rcs_prima > 0:
            composicion["prima_pct"] = float(resultado.rcs_prima) / total * 100
        if resultado.rcs_mercado > 0:
            composicion["mercado_pct"] = float(resultado.rcs_mercado) / total * 100

        return composicion

    def validar_capital_suficiente(
        self, resultado: ResultadoRCS, margen_seguridad: Decimal = Decimal("0.10")
    ) -> dict[str, Any]:
        """
        Valida si el capital es suficiente con margen de seguridad.

        Args:
            resultado: Resultado del cálculo
            margen_seguridad: Margen adicional recomendado (ej: 10%)

        Returns:
            Diccionario con análisis de suficiencia
        """
        rcs_recomendado = resultado.rcs_total * (Decimal("1") + margen_seguridad)
        cumple_con_margen = self.capital_minimo_pagado >= rcs_recomendado

        return {
            "cumple_minimo": resultado.cumple_regulacion,
            "rcs_total": float(resultado.rcs_total),
            "rcs_recomendado": float(rcs_recomendado),
            "capital_disponible": float(self.capital_minimo_pagado),
            "cumple_con_margen": cumple_con_margen,
            "excedente_vs_recomendado": float(self.capital_minimo_pagado - rcs_recomendado),
            "ratio_vs_recomendado": float(
                calcular_ratio_solvencia(self.capital_minimo_pagado, rcs_recomendado)
            ),
            "margen_aplicado": float(margen_seguridad * 100),
        }

    def __repr__(self) -> str:
        """Representación string"""
        componentes = []
        if self.rcs_vida:
            componentes.append("vida")
        if self.rcs_danos:
            componentes.append("danos")
        if self.rcs_inversion:
            componentes.append("inversion")

        return f"AgregadorRCS(componentes={componentes}, capital={self.capital_minimo_pagado:,.0f})"
