"""
Calculadora de Reserva Matematica (RM) segun Circular S-11.4.

La RM es la reserva para seguros de largo plazo (vida) calculada como
el valor presente de obligaciones futuras menos primas futuras.
"""

from __future__ import annotations

import math
from decimal import Decimal
from typing import TYPE_CHECKING

from suite_actuarial.regulatorio.reservas_tecnicas.models import (
    ConfiguracionRM,
    ResultadoRM,
)

if TYPE_CHECKING:
    from suite_actuarial.actuarial.mortality.tablas import TablaMortalidad


class CalculadoraRM:
    """
    Calcula Reserva Matematica para seguros de vida y largo plazo.

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

    def __init__(
        self,
        config: ConfiguracionRM,
        tabla_mortalidad: TablaMortalidad | None = None,
    ):
        self.config = config
        self.tabla_mortalidad = tabla_mortalidad

    def calcular(self) -> ResultadoRM:
        """
        Calcula la Reserva Matematica usando metodo prospectivo.

        El metodo prospectivo calcula:
        RM = VP(Beneficios) - VP(Primas)

        Donde VP = Valor Presente considerando:
        - Tasa de interes tecnico
        - Probabilidades de supervivencia
        - Duracion del seguro

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

        Usa formulas actuariales basadas en:
        - Factor de descuento por interes
        - Probabilidad de supervivencia (tabla mortalidad EMSSA-09 o aprox.)
        - Duracion remanente del seguro
        """
        suma_asegurada = self.config.suma_asegurada
        edad_actual = self.config.edad_asegurado
        edad_contratacion = self.config.edad_contratacion
        tasa = self.config.tasa_interes_tecnico
        prima_anual = self.config.prima_nivelada_anual

        # Anios transcurridos desde contratacion
        anos_transcurridos = edad_actual - edad_contratacion

        # Probabilidad de supervivencia
        prob_supervivencia = self._calcular_probabilidad_supervivencia(edad_actual)

        # Termino remanente del seguro (considerando duracion del contrato)
        # Se asume cobertura hasta edad 85 como omega de la poliza
        edad_omega_poliza = 85
        anos_remanentes_cobertura = max(edad_omega_poliza - edad_actual, 1)

        # VP de beneficios futuros para el termino remanente
        # Se calcula como la suma del VP de beneficio por muerte en cada anio
        # VP_beneficios = SA * sum_{t=1}^{n} v^t * (1 - px_t)
        # Usando aproximacion simplificada:
        v = Decimal(str(1 / (1 + float(tasa))))

        # Factor de descuento acumulado para beneficios
        vn = v ** anos_remanentes_cobertura
        prob_muerte = Decimal("1") - prob_supervivencia

        # VP de beneficios = SA * factor_descuento * prob_muerte
        vp_beneficios = suma_asegurada * vn * prob_muerte

        # VP de primas futuras (anualidad para el termino remanente)
        # Primas se pagan hasta edad 65 o fin de cobertura, lo que ocurra primero
        edad_fin_primas = min(65, edad_omega_poliza)
        anos_primas_restantes = max(edad_fin_primas - edad_actual, 0)

        if anos_primas_restantes > 0:
            # Anualidad: a = (1 - v^n) / (1 - v)
            vn_primas = v ** anos_primas_restantes
            anualidad = (Decimal("1") - vn_primas) / (Decimal("1") - v)

            vp_primas = prima_anual * anualidad * prob_supervivencia
        else:
            vp_primas = Decimal("0")

        # Reserva matematica = VP beneficios - VP primas
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

        Una renta vitalicia paga un monto periodico mientras el rentista viva.
        RM = Renta_mensual * 12 * Factor_anualidad_vitalicia
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
        anos_esperados = max(85 - edad_actual, 1)

        # Probabilidad de supervivencia
        prob_supervivencia = self._calcular_probabilidad_supervivencia(edad_actual)

        # Factor de anualidad vitalicia (simplificado)
        v = Decimal(str(1 / (1 + float(tasa))))
        vn = v ** anos_esperados
        anualidad_vitalicia = (Decimal("1") - vn) / (Decimal("1") - v)

        # RM = Renta anual * anualidad * prob supervivencia
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
        Calcula probabilidad de supervivencia.

        Si se proporciono una TablaMortalidad (e.g. EMSSA-09), se usa
        ``tabla.obtener_qx(edad, sexo)`` para obtener la tasa real de
        mortalidad.  En caso contrario se recurre a la aproximacion
        cuadratica original para mantener compatibilidad hacia atras.

        Args:
            edad: Edad del asegurado

        Returns:
            Probabilidad de supervivencia (0 a 1)
        """
        if edad < 0:
            return Decimal("1")
        if edad >= 120:
            return Decimal("0")

        # --- Ruta 1: tabla de mortalidad real (EMSSA-09 u otra) ---
        if self.tabla_mortalidad is not None:
            try:
                qx = self.tabla_mortalidad.obtener_qx(edad, "H")
                return Decimal("1") - qx
            except (ValueError, KeyError):
                # Edad fuera de rango en la tabla: caer al fallback
                pass

        # --- Ruta 2: aproximacion cuadratica (fallback) ---
        # Funcion de supervivencia simplificada: s(x) = exp(-k * x^2)
        # Ajustada para mortalidad mexicana
        k = 0.00008
        prob = math.exp(-k * (edad ** 2))

        return Decimal(str(prob))

    def __repr__(self) -> str:
        return (
            f"CalculadoraRM("
            f"suma={self.config.suma_asegurada:,.0f}, "
            f"edad={self.config.edad_asegurado})"
        )
