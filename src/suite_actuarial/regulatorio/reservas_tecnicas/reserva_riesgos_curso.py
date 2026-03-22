"""
Calculadora de Reserva de Riesgos en Curso (RRC) según Circular S-11.4.

La RRC es la reserva que deben constituir las aseguradoras para seguros
de corto plazo (típicamente daños) para cubrir la porción no devengada
de las primas.
"""

from decimal import Decimal

from suite_actuarial.regulatorio.reservas_tecnicas.models import (
    ConfiguracionRRC,
    MetodoCalculoRRC,
    ResultadoRRC,
)


class CalculadoraRRC:
    """
    Calcula Reserva de Riesgos en Curso para seguros de corto plazo.

    La RRC representa la obligación futura de la aseguradora por la parte
    no devengada de las primas emitidas.

    Ejemplo:
        >>> from decimal import Decimal
        >>> from datetime import date
        >>> config = ConfiguracionRRC(
        ...     prima_emitida=Decimal("100000000"),
        ...     prima_devengada=Decimal("60000000"),
        ...     fecha_calculo=date(2024, 6, 30),
        ...     dias_promedio_vigencia=365,
        ...     dias_promedio_transcurridos=219  # ~60% del año
        ... )
        >>> calc = CalculadoraRRC(config)
        >>> resultado = calc.calcular()
        >>> print(f"RRC: ${resultado.reserva_calculada:,.0f}")
        RRC: $40,000,000
    """

    def __init__(self, config: ConfiguracionRRC):
        self.config = config

    def calcular(self) -> ResultadoRRC:
        """
        Calcula la RRC según el método configurado.

        Returns:
            ResultadoRRC con la reserva calculada y detalles

        Raises:
            ValueError: Si el método especificado no está soportado
        """
        if self.config.metodo == MetodoCalculoRRC.AVOS_365:
            return self._calcular_365avos()
        elif self.config.metodo == MetodoCalculoRRC.PRIMA_NO_DEVENGADA:
            return self._calcular_prima_no_devengada()
        else:
            raise ValueError(f"Método {self.config.metodo} no soportado")

    def _calcular_365avos(self) -> ResultadoRRC:
        """
        Calcula RRC usando método de 365avos.

        Este método distribuye la prima proporcionalmente durante la vigencia:
        RRC = Prima_emitida × (Días_por_transcurrir / Días_vigencia_total)

        Si se proporcionan días específicos, usa esos valores.
        Si no, calcula basándose en prima devengada.
        """
        prima_emitida = self.config.prima_emitida
        dias_vigencia = self.config.dias_promedio_vigencia or 365

        if self.config.dias_promedio_transcurridos is not None:
            # Cálculo directo con días
            dias_transcurridos = self.config.dias_promedio_transcurridos
            dias_por_transcurrir = max(dias_vigencia - dias_transcurridos, 0)

            fraccion_no_devengada = Decimal(dias_por_transcurrir) / Decimal(
                dias_vigencia
            )
            reserva = prima_emitida * fraccion_no_devengada

            prima_no_devengada = reserva
            porcentaje = fraccion_no_devengada

        else:
            # Cálculo basado en prima devengada
            prima_devengada = self.config.prima_devengada
            prima_no_devengada = prima_emitida - prima_devengada

            porcentaje = (
                prima_no_devengada / prima_emitida if prima_emitida > 0 else Decimal("0")
            )
            reserva = prima_no_devengada

            # Estimar días transcurridos
            dias_transcurridos = int(
                dias_vigencia * float(prima_devengada / prima_emitida)
                if prima_emitida > 0
                else 0
            )
            dias_por_transcurrir = dias_vigencia - dias_transcurridos

        return ResultadoRRC(
            reserva_calculada=reserva.quantize(Decimal("0.01")),
            prima_no_devengada=prima_no_devengada.quantize(Decimal("0.01")),
            porcentaje_reserva=porcentaje.quantize(Decimal("0.0001")),
            metodo_utilizado=MetodoCalculoRRC.AVOS_365,
            dias_vigencia_promedio=dias_vigencia,
            dias_transcurridos_promedio=dias_transcurridos,
        )

    def _calcular_prima_no_devengada(self) -> ResultadoRRC:
        """
        Calcula RRC como prima no devengada directamente.

        Este método simple usa:
        RRC = Prima_emitida - Prima_devengada
        """
        prima_emitida = self.config.prima_emitida
        prima_devengada = self.config.prima_devengada
        prima_no_devengada = prima_emitida - prima_devengada

        porcentaje = (
            prima_no_devengada / prima_emitida if prima_emitida > 0 else Decimal("0")
        )

        return ResultadoRRC(
            reserva_calculada=prima_no_devengada.quantize(Decimal("0.01")),
            prima_no_devengada=prima_no_devengada.quantize(Decimal("0.01")),
            porcentaje_reserva=porcentaje.quantize(Decimal("0.0001")),
            metodo_utilizado=MetodoCalculoRRC.PRIMA_NO_DEVENGADA,
        )

    def __repr__(self) -> str:
        return (
            f"CalculadoraRRC("
            f"prima_emitida={self.config.prima_emitida:,.0f}, "
            f"metodo={self.config.metodo.value})"
        )
