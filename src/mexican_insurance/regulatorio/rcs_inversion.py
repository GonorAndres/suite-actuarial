"""
RCS de Inversión (Riesgos de Mercado y Crédito).

Implementa el cálculo del Requerimiento de Capital de Solvencia (RCS)
para riesgos de inversión conforme a la normativa de la CNSF.
"""

from decimal import Decimal
from typing import Dict

from mexican_insurance.core.validators import ConfiguracionRCSInversion


class RCSInversion:
    """
    Calculadora de RCS para riesgos de inversión.

    Riesgos cubiertos:
    - Riesgo de mercado: Caída en valor de activos (acciones, bonos, inmuebles)
    - Riesgo de crédito: Incumplimiento de emisores de bonos
    - Riesgo de concentración: Exposición excesiva a un solo emisor

    El RCS de inversión es crítico ya que las aseguradoras mantienen grandes
    carteras de inversión para respaldar sus pasivos.
    """

    # Shocks de mercado según tipo de activo (basados en Solvencia II)
    SHOCK_ACCIONES = Decimal("0.35")  # 35% caída
    SHOCK_BONOS_GUBERNAMENTALES = Decimal("0.05")  # 5% caída
    SHOCK_BONOS_CORPORATIVOS = Decimal("0.15")  # 15% caída base
    SHOCK_INMUEBLES = Decimal("0.25")  # 25% caída

    # Shocks de crédito según calificación
    SHOCKS_CREDITO = {
        "AAA": Decimal("0.002"),  # 0.2%
        "AA": Decimal("0.005"),  # 0.5%
        "A": Decimal("0.010"),  # 1.0%
        "BBB": Decimal("0.020"),  # 2.0%
        "BB": Decimal("0.050"),  # 5.0%
        "B": Decimal("0.100"),  # 10.0%
        "CCC": Decimal("0.200"),  # 20.0%
        "CC": Decimal("0.350"),  # 35.0%
        "C": Decimal("0.500"),  # 50.0%
    }

    def __init__(self, config: ConfiguracionRCSInversion):
        """
        Inicializa el calculador de RCS inversión.

        Args:
            config: Configuración con cartera de inversiones
        """
        self.config = config

    def calcular_rcs_mercado_acciones(self) -> Decimal:
        """
        Calcula RCS por riesgo de mercado en acciones.

        Las acciones son el activo más volátil y requieren mayor capital.

        Formula:
            RCS_acciones = Valor_acciones × Shock_acciones

        Returns:
            RCS de mercado acciones
        """
        return (
            self.config.valor_acciones * self.SHOCK_ACCIONES
        ).quantize(Decimal("0.01"))

    def calcular_rcs_mercado_bonos_gubernamentales(self) -> Decimal:
        """
        Calcula RCS por riesgo de mercado en bonos gubernamentales.

        Los bonos gubernamentales tienen menor riesgo pero están sujetos a
        riesgo de tasa de interés.

        El shock aumenta con la duración (sensibilidad a tasas).

        Formula:
            RCS_bonos_gub = Valor × Shock_base × Ajuste_duración

        Returns:
            RCS de mercado bonos gubernamentales
        """
        valor = self.config.valor_bonos_gubernamentales
        duracion = self.config.duracion_promedio_bonos

        # Ajuste por duración: mayor duración = mayor sensibilidad a tasas
        # Duración 5 años: factor 1.0
        # Duración 10 años: factor 1.5
        # Duración 20 años: factor 2.0
        ajuste_duracion = Decimal("1.0") + (
            duracion - Decimal("5.0")
        ) * Decimal("0.1")
        ajuste_duracion = max(ajuste_duracion, Decimal("0.5"))
        ajuste_duracion = min(ajuste_duracion, Decimal("2.5"))

        shock_ajustado = self.SHOCK_BONOS_GUBERNAMENTALES * ajuste_duracion

        return (valor * shock_ajustado).quantize(Decimal("0.01"))

    def calcular_rcs_mercado_bonos_corporativos(self) -> Decimal:
        """
        Calcula RCS por riesgo de mercado en bonos corporativos.

        Los bonos corporativos tienen mayor riesgo que gubernamentales debido a:
        - Mayor riesgo de crédito
        - Menor liquidez
        - Mayor sensibilidad a condiciones económicas

        Formula:
            RCS_bonos_corp = Valor × Shock_base × Ajuste_duración × Ajuste_calificación

        Returns:
            RCS de mercado bonos corporativos
        """
        valor = self.config.valor_bonos_corporativos
        duracion = self.config.duracion_promedio_bonos
        calificacion = self.config.calificacion_promedio_bonos

        # Ajuste por duración (igual que gubernamentales)
        ajuste_duracion = Decimal("1.0") + (
            duracion - Decimal("5.0")
        ) * Decimal("0.1")
        ajuste_duracion = max(ajuste_duracion, Decimal("0.5"))
        ajuste_duracion = min(ajuste_duracion, Decimal("2.5"))

        # Ajuste por calificación: peor calificación = mayor shock
        if calificacion in ["AAA", "AA"]:
            ajuste_calif = Decimal("1.0")
        elif calificacion == "A":
            ajuste_calif = Decimal("1.2")
        elif calificacion == "BBB":
            ajuste_calif = Decimal("1.5")
        else:
            ajuste_calif = Decimal("2.0")

        shock_ajustado = (
            self.SHOCK_BONOS_CORPORATIVOS * ajuste_duracion * ajuste_calif
        )

        return (valor * shock_ajustado).quantize(Decimal("0.01"))

    def calcular_rcs_mercado_inmuebles(self) -> Decimal:
        """
        Calcula RCS por riesgo de mercado en bienes raíces.

        Los inmuebles tienen riesgo significativo por:
        - Ciclos económicos
        - Iliquidez
        - Costos de mantenimiento

        Formula:
            RCS_inmuebles = Valor_inmuebles × Shock_inmuebles

        Returns:
            RCS de mercado inmuebles
        """
        return (
            self.config.valor_inmuebles * self.SHOCK_INMUEBLES
        ).quantize(Decimal("0.01"))

    def calcular_rcs_credito(self) -> Decimal:
        """
        Calcula RCS por riesgo de crédito.

        El riesgo de crédito se refiere al incumplimiento de emisores de bonos.

        Solo aplica a bonos corporativos (se asume que gubernamentales no tienen
        riesgo de crédito significativo).

        Formula:
            RCS_credito = Valor_bonos_corp × Shock_credito_según_calificación

        Returns:
            RCS de crédito
        """
        valor = self.config.valor_bonos_corporativos
        calificacion = self.config.calificacion_promedio_bonos

        # Obtener shock de crédito según calificación
        shock_credito = self.SHOCKS_CREDITO.get(
            calificacion, Decimal("0.100")  # Default 10%
        )

        return (valor * shock_credito).quantize(Decimal("0.01"))

    def calcular_rcs_concentracion(self) -> Decimal:
        """
        Calcula RCS por riesgo de concentración.

        El riesgo de concentración se materializa cuando hay excesiva exposición
        a un solo emisor o sector.

        Formula simplificada:
            RCS_conc = 0.01 × Valor_total_inversiones

        En una implementación completa, se calcularía por emisor y se aplicaría
        solo al exceso sobre límites regulatorios.

        Returns:
            RCS de concentración
        """
        total_inversiones = (
            self.config.valor_acciones
            + self.config.valor_bonos_gubernamentales
            + self.config.valor_bonos_corporativos
            + self.config.valor_inmuebles
        )

        # Factor de concentración simple: 1% del total
        factor_concentracion = Decimal("0.01")

        return (total_inversiones * factor_concentracion).quantize(
            Decimal("0.01")
        )

    def calcular_rcs_mercado_total(self) -> Decimal:
        """
        Calcula RCS total de mercado agregando todos los activos.

        Los shocks de mercado se agregan de forma simple (suma) ya que en
        escenarios de crisis, todos los activos tienden a caer juntos.

        Returns:
            RCS total de mercado
        """
        rcs_acciones = self.calcular_rcs_mercado_acciones()
        rcs_bonos_gub = self.calcular_rcs_mercado_bonos_gubernamentales()
        rcs_bonos_corp = self.calcular_rcs_mercado_bonos_corporativos()
        rcs_inmuebles = self.calcular_rcs_mercado_inmuebles()

        # Suma simple (asume alta correlación en crisis)
        rcs_mercado = (
            rcs_acciones + rcs_bonos_gub + rcs_bonos_corp + rcs_inmuebles
        )

        return rcs_mercado.quantize(Decimal("0.01"))

    def calcular_rcs_total_inversion(
        self,
    ) -> tuple[Decimal, Dict[str, Decimal]]:
        """
        Calcula RCS total de inversión agregando mercado, crédito y concentración.

        Formula:
            RCS_inv = sqrt(RCS_mercado² + RCS_credito² + RCS_concentración²)

        Se usa raíz cuadrada ya que estos riesgos tienen correlación baja.

        Returns:
            Tupla de (RCS_total, desglose_por_riesgo)
        """
        rcs_mercado = self.calcular_rcs_mercado_total()
        rcs_credito = self.calcular_rcs_credito()
        rcs_conc = self.calcular_rcs_concentracion()

        # Agregación con raíz cuadrada (correlación baja)
        import math

        suma_cuadrados = rcs_mercado**2 + rcs_credito**2 + rcs_conc**2
        rcs_total = Decimal(str(math.sqrt(float(suma_cuadrados))))

        desglose = {
            "mercado": rcs_mercado,
            "credito": rcs_credito,
            "concentracion": rcs_conc,
            "acciones": self.calcular_rcs_mercado_acciones(),
            "bonos_gubernamentales": self.calcular_rcs_mercado_bonos_gubernamentales(),
            "bonos_corporativos": self.calcular_rcs_mercado_bonos_corporativos(),
            "inmuebles": self.calcular_rcs_mercado_inmuebles(),
        }

        return rcs_total.quantize(Decimal("0.01")), desglose

    def obtener_shocks_aplicados(self) -> Dict[str, Decimal]:
        """
        Obtiene los shocks aplicados a cada tipo de activo.

        Útil para auditoría y verificación.

        Returns:
            Diccionario con shocks aplicados
        """
        duracion = self.config.duracion_promedio_bonos
        calificacion = self.config.calificacion_promedio_bonos

        ajuste_duracion = Decimal("1.0") + (
            duracion - Decimal("5.0")
        ) * Decimal("0.1")
        ajuste_duracion = max(ajuste_duracion, Decimal("0.5"))
        ajuste_duracion = min(ajuste_duracion, Decimal("2.5"))

        shock_bonos_gub = self.SHOCK_BONOS_GUBERNAMENTALES * ajuste_duracion

        if calificacion in ["AAA", "AA"]:
            ajuste_calif = Decimal("1.0")
        elif calificacion == "A":
            ajuste_calif = Decimal("1.2")
        elif calificacion == "BBB":
            ajuste_calif = Decimal("1.5")
        else:
            ajuste_calif = Decimal("2.0")

        shock_bonos_corp = (
            self.SHOCK_BONOS_CORPORATIVOS * ajuste_duracion * ajuste_calif
        )

        return {
            "shock_acciones": self.SHOCK_ACCIONES.quantize(Decimal("0.01")),
            "shock_bonos_gubernamentales": shock_bonos_gub.quantize(
                Decimal("0.01")
            ),
            "shock_bonos_corporativos": shock_bonos_corp.quantize(
                Decimal("0.01")
            ),
            "shock_inmuebles": self.SHOCK_INMUEBLES.quantize(
                Decimal("0.01")
            ),
            "shock_credito": self.SHOCKS_CREDITO.get(
                calificacion, Decimal("0.100")
            ).quantize(Decimal("0.01")),
            "duracion_bonos": duracion.quantize(Decimal("0.01")),
            "ajuste_duracion": ajuste_duracion.quantize(Decimal("0.01")),
            "calificacion": calificacion,
        }

    def __repr__(self) -> str:
        """Representación string"""
        total_inv = (
            self.config.valor_acciones
            + self.config.valor_bonos_gubernamentales
            + self.config.valor_bonos_corporativos
            + self.config.valor_inmuebles
        )
        return (
            f"RCSInversion("
            f"total_inversiones={total_inv:,.0f}, "
            f"duracion={self.config.duracion_promedio_bonos:.1f}, "
            f"calif={self.config.calificacion_promedio_bonos})"
        )
