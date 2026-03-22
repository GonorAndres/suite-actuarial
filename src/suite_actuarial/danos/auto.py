"""
Producto de seguro de automovil con tarificacion AMIS.

Integra las tablas de referencia AMIS, el sistema Bonus-Malus
y el motor de factores para generar cotizaciones completas.
"""

from decimal import Decimal, ROUND_HALF_UP
from enum import StrEnum

from suite_actuarial.danos.tablas_amis import (
    FACTOR_DEDUCIBLE,
    FACTOR_EDAD_CONDUCTOR,
    TASAS_BASE,
    ZONAS_RIESGO,
    obtener_depreciacion,
    obtener_grupo,
    obtener_zona,
    rango_edad_conductor,
)
from suite_actuarial.danos.tarifas import CalculadoraBonusMalus


class Cobertura(StrEnum):
    """Coberturas disponibles para seguros de auto."""

    DANOS_MATERIALES = "danos_materiales"
    ROBO_TOTAL = "robo_total"
    RC_BIENES = "rc_bienes"
    RC_PERSONAS = "rc_personas"
    GASTOS_MEDICOS = "gastos_medicos"
    ASISTENCIA_VIAL = "asistencia_vial"


# Coberturas basicas obligatorias (paquete minimo legal mexicano)
COBERTURAS_BASICAS = [
    Cobertura.RC_BIENES,
    Cobertura.RC_PERSONAS,
]

# Paquete amplio tipico
COBERTURAS_AMPLIA = list(Cobertura)


class SeguroAuto:
    """
    Producto de seguro de automovil con tarificacion AMIS.

    Calcula primas por cobertura usando:
    - Tasas base por grupo de vehiculo
    - Factores de zona, edad, deducible
    - Depreciacion por antiguedad
    - Ajuste Bonus-Malus
    """

    def __init__(
        self,
        valor_vehiculo: Decimal,
        tipo_vehiculo: str,
        antiguedad_anos: int,
        zona: str,
        edad_conductor: int,
        deducible_pct: Decimal = Decimal("0.05"),
        config: dict | None = None,
    ) -> None:
        """
        Args:
            valor_vehiculo: valor comercial del vehiculo en pesos MXN.
            tipo_vehiculo: clave del tipo de vehiculo (ver GRUPOS_VEHICULO).
            antiguedad_anos: anos de antiguedad del vehiculo.
            zona: clave de la zona de riesgo (ver ZONAS_RIESGO).
            edad_conductor: edad del conductor principal en anos.
            deducible_pct: porcentaje de deducible (default 5%).
            config: configuracion adicional opcional.
        """
        if valor_vehiculo <= 0:
            raise ValueError("El valor del vehiculo debe ser positivo.")
        if antiguedad_anos < 0:
            raise ValueError("La antiguedad no puede ser negativa.")
        if edad_conductor < 18:
            raise ValueError("El conductor debe tener al menos 18 anos.")
        if deducible_pct not in FACTOR_DEDUCIBLE:
            raise ValueError(
                f"Deducible no valido: {deducible_pct}. "
                f"Opciones: {list(FACTOR_DEDUCIBLE)}"
            )

        self.valor_vehiculo = valor_vehiculo
        self.tipo_vehiculo = tipo_vehiculo
        self.antiguedad_anos = antiguedad_anos
        self.zona = zona
        self.edad_conductor = edad_conductor
        self.deducible_pct = deducible_pct
        self.config = config or {}

        # Precalcular factores
        self.grupo = obtener_grupo(tipo_vehiculo)
        self.factor_zona = obtener_zona(zona)
        self.factor_depreciacion = obtener_depreciacion(antiguedad_anos)
        self.rango_edad = rango_edad_conductor(edad_conductor)
        self.factor_edad = FACTOR_EDAD_CONDUCTOR[self.rango_edad]
        self.factor_deducible = FACTOR_DEDUCIBLE[deducible_pct]

        # Valor asegurado ajustado por depreciacion
        self.valor_asegurado = (valor_vehiculo * self.factor_depreciacion).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    def _prima_cobertura(self, cobertura: Cobertura) -> Decimal:
        """Calcula la prima para una cobertura individual."""
        cob_key = cobertura.value
        if cob_key not in TASAS_BASE:
            raise ValueError(f"Cobertura sin tasa base: {cob_key}")

        tasa = TASAS_BASE[cob_key].get(self.grupo)
        if tasa is None:
            raise ValueError(
                f"Grupo {self.grupo} no tiene tasa para {cob_key}"
            )

        # Prima = (valor_asegurado / 1000) * tasa * factores
        prima = (self.valor_asegurado / Decimal("1000")) * tasa

        # Aplicar factores
        prima = prima * self.factor_zona
        prima = prima * self.factor_edad

        # Deducible solo aplica a coberturas propias (danos materiales, robo)
        if cobertura in (Cobertura.DANOS_MATERIALES, Cobertura.ROBO_TOTAL):
            prima = prima * self.factor_deducible

        return prima.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calcular_tarifa(self) -> dict[Cobertura, Decimal]:
        """
        Calcula la prima por cobertura usando tablas AMIS.

        Returns:
            Dict {cobertura: prima_anual}.
        """
        return {cob: self._prima_cobertura(cob) for cob in Cobertura}

    def aplicar_bonus_malus(self, historial_siniestros: list[int]) -> Decimal:
        """
        Aplica el ajuste Bonus-Malus al total de primas.

        Args:
            historial_siniestros: lista de conteos de siniestros anuales.

        Returns:
            Prima total ajustada por BMS.
        """
        bms = CalculadoraBonusMalus(nivel_actual=0)
        for s in historial_siniestros:
            bms.transicion(s)

        prima_total = self.calcular_prima_total()
        ajustada = (prima_total * bms.factor_actual()).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        return ajustada

    def calcular_prima_total(
        self, coberturas: list[Cobertura] | None = None
    ) -> Decimal:
        """
        Prima total para las coberturas seleccionadas.

        Args:
            coberturas: lista de coberturas. None = todas.

        Returns:
            Suma de primas de las coberturas seleccionadas.
        """
        if coberturas is None:
            coberturas = list(Cobertura)

        tarifas = self.calcular_tarifa()
        total = sum(tarifas[c] for c in coberturas)
        return Decimal(str(total)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def generar_cotizacion(
        self,
        coberturas: list[Cobertura] | None = None,
        historial_siniestros: list[int] | None = None,
    ) -> dict:
        """
        Cotizacion completa con desglose por cobertura.

        Args:
            coberturas: coberturas a cotizar (None = todas).
            historial_siniestros: historial para BMS (None = sin ajuste).

        Returns:
            Dict con desglose completo de la cotizacion.
        """
        if coberturas is None:
            coberturas = list(Cobertura)

        tarifas = self.calcular_tarifa()
        desglose = {c.value: tarifas[c] for c in coberturas}
        subtotal = sum(tarifas[c] for c in coberturas)
        subtotal = Decimal(str(subtotal)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # Bonus-Malus
        factor_bms = Decimal("1.00")
        nivel_bms = 0
        if historial_siniestros:
            bms = CalculadoraBonusMalus(nivel_actual=0)
            for s in historial_siniestros:
                bms.transicion(s)
            factor_bms = bms.factor_actual()
            nivel_bms = bms.nivel_actual

        prima_ajustada = (subtotal * factor_bms).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # Deducible en pesos
        deducible_pesos = (self.valor_asegurado * self.deducible_pct).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        return {
            "vehiculo": {
                "tipo": self.tipo_vehiculo,
                "grupo": self.grupo,
                "valor_original": self.valor_vehiculo,
                "antiguedad": self.antiguedad_anos,
                "valor_asegurado": self.valor_asegurado,
            },
            "conductor": {
                "edad": self.edad_conductor,
                "rango_edad": self.rango_edad,
                "factor_edad": self.factor_edad,
            },
            "zona": {
                "nombre": self.zona,
                "factor": self.factor_zona,
            },
            "deducible": {
                "porcentaje": self.deducible_pct,
                "pesos": deducible_pesos,
                "factor": self.factor_deducible,
            },
            "coberturas": desglose,
            "subtotal": subtotal,
            "bonus_malus": {
                "nivel": nivel_bms,
                "factor": factor_bms,
            },
            "prima_total": prima_ajustada,
        }
