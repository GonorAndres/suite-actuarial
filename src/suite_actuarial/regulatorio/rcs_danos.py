"""
RCS de Suscripción para Ramos de Daños.

Implementa el cálculo del Requerimiento de Capital de Solvencia (RCS)
para riesgos de suscripción en seguros de daños (no vida) conforme a
la normativa de la CNSF.
"""

import math
from decimal import Decimal

from suite_actuarial.core.validators import ConfiguracionRCSDanos

DISCLAIMER = (
    "AVISO: Los factores de RCS en este modulo son aproximaciones pedagogicas "
    "simplificadas, no el modelo estocastico completo de la CNSF. Los resultados "
    "son indicativos y pueden subestimar el requerimiento de capital real."
)


class RCSDanos:
    """
    Calculadora de RCS para riesgos de suscripción en daños.

    Riesgos cubiertos:
    - Riesgo de prima: Primas insuficientes vs siniestralidad observada
    - Riesgo de reserva: Reservas de siniestros insuficientes

    En daños, la volatilidad es generalmente mayor que en vida debido a:
    - Eventos catastróficos (huracanes, terremotos)
    - Siniestros de alta severidad
    - Menor predictibilidad
    """

    def __init__(self, config: ConfiguracionRCSDanos):
        """
        Inicializa el calculador de RCS daños.

        Args:
            config: Configuración con parámetros de la cartera de daños
        """
        self.config = config

    def calcular_rcs_prima(self) -> Decimal:
        """
        Calcula RCS por riesgo de prima.

        El riesgo de prima se refiere a que las primas cobradas sean insuficientes
        para cubrir los siniestros que ocurran, debido a:
        - Tarificación inadecuada
        - Cambios en frecuencia/severidad de siniestros
        - Eventos catastróficos

        Fórmula simplificada:
            RCS_prima = α × Primas_retenidas × σ × Factor_ramos

        Donde:
            α = 3 (factor de confianza 99.5%)
            σ = coeficiente de variación de la siniestralidad
            Factor_ramos = ajuste por diversificación de ramos

        Returns:
            RCS de prima en unidades monetarias
        """
        primas = self.config.primas_retenidas_12m
        sigma = self.config.coeficiente_variacion
        num_ramos = self.config.numero_ramos

        # Factor de confianza para percentil 99.5% (típico en Solvencia II)
        alpha = Decimal("3.0")

        # Factor de diversificación por número de ramos
        # 1 ramo: 1.0, 5 ramos: ~0.85, 10+ ramos: ~0.75
        if num_ramos == 1:
            factor_ramos = Decimal("1.0")
        elif num_ramos <= 5:
            factor_ramos = Decimal(str(1.0 - (num_ramos - 1) * 0.03))
        else:
            factor_ramos = Decimal("0.75")

        rcs_prima = primas * alpha * sigma * factor_ramos

        return rcs_prima.quantize(Decimal("0.01"))

    def calcular_rcs_reserva(self) -> Decimal:
        """
        Calcula RCS por riesgo de reserva.

        El riesgo de reserva se refiere a que las reservas de siniestros
        pendientes sean insuficientes para pagar todos los siniestros,
        ya sea por:
        - Desarrollo adverso de siniestros
        - Inflación en costos de reparación/indemnización
        - Siniestros IBNR (ocurridos pero no reportados) subestimados

        Fórmula simplificada:
            RCS_reserva = β × Reserva_siniestros × √(σ)

        Donde:
            β = 2 (factor de ajuste)
            σ = coeficiente de variación

        El uso de √σ refleja que el riesgo de reserva es menor que el de prima
        ya que la reserva tiene menos incertidumbre (siniestros ya ocurrieron).

        Returns:
            RCS de reserva en unidades monetarias
        """
        reserva = self.config.reserva_siniestros
        sigma = self.config.coeficiente_variacion

        # Factor de ajuste para reservas (menor que primas)
        beta = Decimal("2.0")

        # Raíz cuadrada del coeficiente de variación
        # (reserva tiene menor volatilidad que prima)
        sigma_reserva = Decimal(str(math.sqrt(float(sigma))))

        rcs_reserva = reserva * beta * sigma_reserva

        return rcs_reserva.quantize(Decimal("0.01"))

    def calcular_rcs_total_danos(self) -> tuple[Decimal, dict[str, Decimal]]:
        """
        Calcula RCS total de suscripción daños agregando riesgo de prima y reserva.

        Los riesgos de prima y reserva están correlacionados (ambos dependen
        de la siniestralidad), pero no perfectamente correlacionados.

        Fórmula con correlación:
            RCS_daños = sqrt(RCS_prima² + RCS_reserva² + 2×ρ×RCS_prima×RCS_reserva)

        Donde ρ (rho) es el coeficiente de correlación, típicamente 0.5

        Returns:
            Tupla de (RCS_total, desglose_por_riesgo)
        """
        rcs_prima = self.calcular_rcs_prima()
        rcs_reserva = self.calcular_rcs_reserva()

        # Coeficiente de correlación entre prima y reserva
        # Típicamente 0.5 (correlación positiva moderada)
        rho = Decimal("0.5")

        # Agregación con correlación
        termino_cuadratico = rcs_prima**2 + rcs_reserva**2
        termino_correlacion = 2 * rho * rcs_prima * rcs_reserva

        suma_total = termino_cuadratico + termino_correlacion

        rcs_total = Decimal(str(math.sqrt(float(suma_total))))

        desglose = {
            "prima": rcs_prima,
            "reserva": rcs_reserva,
        }

        return rcs_total.quantize(Decimal("0.01")), desglose

    def obtener_parametros_calculo(self) -> dict[str, Decimal]:
        """
        Obtiene parámetros utilizados en el cálculo.

        Útil para auditoría y verificación.

        Returns:
            Diccionario con parámetros del cálculo
        """
        num_ramos = self.config.numero_ramos

        if num_ramos == 1:
            factor_ramos = Decimal("1.0")
        elif num_ramos <= 5:
            factor_ramos = Decimal(str(1.0 - (num_ramos - 1) * 0.03))
        else:
            factor_ramos = Decimal("0.75")

        sigma_reserva = Decimal(
            str(math.sqrt(float(self.config.coeficiente_variacion)))
        )

        return {
            "primas_retenidas_12m": self.config.primas_retenidas_12m.quantize(
                Decimal("0.01")
            ),
            "reserva_siniestros": self.config.reserva_siniestros.quantize(
                Decimal("0.01")
            ),
            "coeficiente_variacion": self.config.coeficiente_variacion.quantize(
                Decimal("0.01")
            ),
            "numero_ramos": Decimal(str(num_ramos)),
            "factor_diversificacion_ramos": factor_ramos.quantize(
                Decimal("0.01")
            ),
            "sigma_reserva": sigma_reserva.quantize(Decimal("0.01")),
            "correlacion_prima_reserva": Decimal("0.5"),
        }

    def __repr__(self) -> str:
        """Representación string"""
        return (
            f"RCSDanos("
            f"primas={self.config.primas_retenidas_12m:,.0f}, "
            f"reserva={self.config.reserva_siniestros:,.0f}, "
            f"cv={self.config.coeficiente_variacion:.2f})"
        )
