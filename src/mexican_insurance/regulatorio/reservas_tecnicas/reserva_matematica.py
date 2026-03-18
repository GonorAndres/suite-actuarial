"""
Calculadora de Reserva Matemática (RM) según Circular S-11.4.

La RM es la reserva para seguros de largo plazo (vida) calculada como
el valor presente de obligaciones futuras menos primas futuras.
"""

import math
from decimal import Decimal

from mexican_insurance.regulatorio.reservas_tecnicas.models import (
    ConfiguracionRM,
    ResultadoRM,
)


class CalculadoraRM:
    """
    Calcula Reserva Matemática para seguros de vida y largo plazo.

    La RM representa el valor presente de las obligaciones futuras netas:
    RM = VP(Beneficios Futuros) - VP(Primas Futuras)

    Ejemplo:
        >>> from decimal import Decimal
        >>> config = ConfiguracionRM(
        ...     suma_asegurada=Decimal("1000000"),
        ...     edad_asegurado=45,
        ...     edad_contratacion=40,
        ...     tasa_interes_tecnico=Decimal("0.055"),
        ...     prima_nivelada_anual=Decimal("25000")
        ... )
        >>> calc = CalculadoraRM(config)
        >>> resultado = calc.calcular()
        >>> print(f"RM: ${resultado.reserva_matematica:,.0f}")
    """

    def __init__(self, config: ConfiguracionRM):
        self.config = config

    def calcular(self) -> ResultadoRM:
        """
        Calcula la Reserva Matemática usando método prospectivo.

        El método prospectivo calcula:
        RM = VP(Beneficios) - VP(Primas)

        Donde VP = Valor Presente considerando:
        - Tasa de interés técnico
        - Probabilidades de supervivencia
        - Duración del seguro

        Returns:
            ResultadoRM con reserva calculada y componentes
        """
        if self.config.es_renta_vitalicia:
            return self._calcular_renta_vitalicia()
        else:
            return self._calcular_seguro_vida()

    def _calcular_seguro_vida(self) -> ResultadoRM:
        """
        Calcula RM para seguro de vida tradicional.

        Usa fórmulas actuariales simplificadas basadas en:
        - Factor de descuento por interés
        - Probabilidad de supervivencia (tabla mortalidad simplificada)
        - Duración del seguro
        """
        suma_asegurada = self.config.suma_asegurada
        edad_actual = self.config.edad_asegurado
        edad_contratacion = self.config.edad_contratacion
        tasa = self.config.tasa_interes_tecnico
        prima_anual = self.config.prima_nivelada_anual

        # Años transcurridos desde contratación
        edad_actual - edad_contratacion

        # Probabilidad de supervivencia simplificada (tabla mortalidad básica)
        prob_supervivencia = self._calcular_probabilidad_supervivencia(edad_actual)

        # Esperanza de vida remanente (simplificado)
        años_esperados_vida = max(85 - edad_actual, 1)

        # Factor de descuento acumulado
        # VP = suma / (1 + i)^n × probabilidad_muerte
        factor_descuento_beneficio = Decimal(
            str(1 / ((1 + float(tasa)) ** años_esperados_vida))
        )
        prob_muerte = Decimal("1") - prob_supervivencia

        # VP de beneficios = SA × factor_descuento × prob_muerte
        vp_beneficios = suma_asegurada * factor_descuento_beneficio * prob_muerte

        # VP de primas futuras (anualidad)
        # Asumiendo que se pagan hasta edad 65 o 85, lo que ocurra primero
        edad_fin_primas = min(65, 85)
        años_primas_restantes = max(edad_fin_primas - edad_actual, 0)

        if años_primas_restantes > 0:
            # Anualidad: a = (1 - v^n) / d, donde v = 1/(1+i), d = tasa efectiva
            v = Decimal(str(1 / (1 + float(tasa))))
            vn = v ** años_primas_restantes
            anualidad = (Decimal("1") - vn) / (Decimal("1") - v)

            vp_primas = prima_anual * anualidad * prob_supervivencia
        else:
            vp_primas = Decimal("0")

        # Reserva matemática = VP beneficios - VP primas
        reserva = vp_beneficios - vp_primas

        # La reserva no puede ser negativa (significa que primas cubren sobradamente)
        reserva = max(reserva, Decimal("0"))

        return ResultadoRM(
            reserva_matematica=reserva.quantize(Decimal("0.01")),
            valor_presente_beneficios=vp_beneficios.quantize(Decimal("0.01")),
            valor_presente_primas=vp_primas.quantize(Decimal("0.01")),
            edad_actuarial=edad_actual,
            probabilidad_supervivencia=prob_supervivencia.quantize(Decimal("0.0001")),
        )

    def _calcular_renta_vitalicia(self) -> ResultadoRM:
        """
        Calcula RM para renta vitalicia.

        Una renta vitalicia paga un monto periódico mientras el rentista viva.
        RM = Renta_mensual × 12 × Factor_anualidad_vitalicia
        """
        if not self.config.monto_renta_mensual:
            raise ValueError(
                "Se requiere monto_renta_mensual para rentas vitalicias"
            )

        renta_mensual = self.config.monto_renta_mensual
        renta_anual = renta_mensual * 12
        edad_actual = self.config.edad_asegurado
        tasa = self.config.tasa_interes_tecnico

        # Esperanza de vida remanente
        años_esperados = max(85 - edad_actual, 1)

        # Probabilidad de supervivencia
        prob_supervivencia = self._calcular_probabilidad_supervivencia(edad_actual)

        # Factor de anualidad vitalicia (simplificado)
        v = Decimal(str(1 / (1 + float(tasa))))
        vn = v ** años_esperados
        anualidad_vitalicia = (Decimal("1") - vn) / (Decimal("1") - v)

        # RM = Renta anual × anualidad × prob supervivencia
        reserva = renta_anual * anualidad_vitalicia * prob_supervivencia

        return ResultadoRM(
            reserva_matematica=reserva.quantize(Decimal("0.01")),
            valor_presente_beneficios=reserva.quantize(Decimal("0.01")),
            valor_presente_primas=Decimal("0"),  # No hay primas futuras en rentas
            edad_actuarial=edad_actual,
            probabilidad_supervivencia=prob_supervivencia.quantize(Decimal("0.0001")),
        )

    def _calcular_probabilidad_supervivencia(self, edad: int) -> Decimal:
        """
        Calcula probabilidad de supervivencia usando tabla mortalidad simplificada.

        Basado en tabla EMSSA-09 (Experiencia Mexicana de Seguros de Sobrevivencia)
        simplificada.

        Args:
            edad: Edad del asegurado

        Returns:
            Probabilidad de supervivencia (0 a 1)
        """
        # Función de supervivencia simplificada: s(x) = exp(-k × x^2)
        # Ajustada para mortalidad mexicana

        if edad < 0:
            return Decimal("1")
        if edad >= 120:
            return Decimal("0")

        # Parámetro de mortalidad (ajustado para México)
        k = 0.00008

        # Probabilidad de supervivencia
        prob = math.exp(-k * (edad ** 2))

        return Decimal(str(prob))

    def __repr__(self) -> str:
        return (
            f"CalculadoraRM("
            f"suma={self.config.suma_asegurada:,.0f}, "
            f"edad={self.config.edad_asegurado})"
        )
