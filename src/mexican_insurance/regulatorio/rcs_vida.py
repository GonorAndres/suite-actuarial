"""
RCS de Suscripción para Ramos de Vida.

Implementa el cálculo del Requerimiento de Capital de Solvencia (RCS)
para riesgos de suscripción en seguros de vida conforme a la normativa
de la CNSF (Comisión Nacional de Seguros y Fianzas de México).
"""

import math
from decimal import Decimal

from mexican_insurance.core.validators import ConfiguracionRCSVida


class RCSVida:
    """
    Calculadora de RCS para riesgos de suscripción en vida.

    Riesgos cubiertos:
    - Mortalidad: Muerte antes de lo esperado (impacto en seguros de vida)
    - Longevidad: Supervivencia mayor a esperada (impacto en rentas vitalicias)
    - Invalidez: Incapacidad del asegurado
    - Gastos: Gastos de administración mayores a proyectados

    Las fórmulas están basadas en las disposiciones de la CNSF y consideran
    factores de edad, duración de pólizas y tamaño de la cartera.
    """

    def __init__(self, config: ConfiguracionRCSVida):
        """
        Inicializa el calculador de RCS vida.

        Args:
            config: Configuración con parámetros de la cartera
        """
        self.config = config

    def calcular_rcs_mortalidad(self) -> Decimal:
        """
        Calcula RCS por riesgo de mortalidad.

        El riesgo de mortalidad se materializa cuando los asegurados mueren
        antes de lo esperado, resultando en pagos de suma asegurada no previstos.

        Fórmula simplificada:
            RCS_mort = 0.003 × Suma_asegurada × Factor_edad × Factor_diversificación

        Factor_edad aumenta con la edad (mayor riesgo en edades avanzadas)
        Factor_diversificación disminuye con más asegurados (ley de grandes números)

        Returns:
            RCS de mortalidad en unidades monetarias
        """
        suma_asegurada = self.config.suma_asegurada_total
        edad_promedio = self.config.edad_promedio_asegurados
        num_asegurados = self.config.numero_asegurados

        # Factor base: 0.3% de la suma asegurada
        factor_base = Decimal("0.003")

        # Factor de edad: aumenta exponencialmente con edad
        # A los 30 años: ~1.0, A los 60 años: ~2.5
        factor_edad = Decimal(str(1.0 + (edad_promedio - 30) * 0.025))
        factor_edad = max(factor_edad, Decimal("0.5"))  # Mínimo 0.5
        factor_edad = min(factor_edad, Decimal("3.0"))  # Máximo 3.0

        # Factor de diversificación: disminuye con más asegurados
        # 1000 asegurados: ~1.0, 10000 asegurados: ~0.7, 100000: ~0.5
        if num_asegurados >= 1000:
            factor_div = Decimal(
                str(1.0 / math.sqrt(num_asegurados / 1000.0))
            )
            factor_div = max(factor_div, Decimal("0.5"))  # Mínimo 0.5
        else:
            # Carteras muy pequeñas tienen factor mayor
            factor_div = Decimal("1.5")

        rcs_mortalidad = suma_asegurada * factor_base * factor_edad * factor_div

        return rcs_mortalidad.quantize(Decimal("0.01"))

    def calcular_rcs_longevidad(self) -> Decimal:
        """
        Calcula RCS por riesgo de longevidad.

        El riesgo de longevidad se materializa en rentas vitalicias cuando los
        asegurados viven más de lo esperado, requiriendo pagos adicionales.

        Fórmula simplificada:
            RCS_long = 0.002 × Reserva_matemática × Factor_edad × Factor_duración

        Factor_edad aumenta con edad (mayor impacto en edades avanzadas)
        Factor_duración aumenta con duración de pólizas (mayor exposición)

        Returns:
            RCS de longevidad en unidades monetarias
        """
        reserva = self.config.reserva_matematica
        edad_promedio = self.config.edad_promedio_asegurados
        duracion = self.config.duracion_promedio_polizas

        # Factor base: 0.2% de la reserva
        factor_base = Decimal("0.002")

        # Factor de edad: mayor impacto en edades avanzadas (rentas vitalicias)
        # A los 50 años: ~1.0, A los 70 años: ~2.0
        factor_edad = Decimal(str(1.0 + (edad_promedio - 50) * 0.02))
        factor_edad = max(factor_edad, Decimal("0.5"))
        factor_edad = min(factor_edad, Decimal("2.5"))

        # Factor de duración: mayor duración = mayor exposición
        # 10 años: ~1.0, 20 años: ~1.5, 30 años: ~2.0
        factor_duracion = Decimal(str(1.0 + (duracion - 10) * 0.05))
        factor_duracion = max(factor_duracion, Decimal("0.5"))
        factor_duracion = min(factor_duracion, Decimal("2.5"))

        rcs_longevidad = reserva * factor_base * factor_edad * factor_duracion

        return rcs_longevidad.quantize(Decimal("0.01"))

    def calcular_rcs_invalidez(self) -> Decimal:
        """
        Calcula RCS por riesgo de invalidez.

        El riesgo de invalidez se refiere a que más asegurados de lo esperado
        se invaliden, generando pagos de suma asegurada o rentas por invalidez.

        Fórmula simplificada:
            RCS_inv = 0.0015 × Suma_asegurada × Factor_edad

        Returns:
            RCS de invalidez en unidades monetarias
        """
        suma_asegurada = self.config.suma_asegurada_total
        edad_promedio = self.config.edad_promedio_asegurados

        # Factor base: 0.15% de suma asegurada (menor que mortalidad)
        factor_base = Decimal("0.0015")

        # Factor de edad: invalidez aumenta con edad pero menos que mortalidad
        # A los 40 años: ~1.0, A los 60 años: ~1.5
        factor_edad = Decimal(str(1.0 + (edad_promedio - 40) * 0.015))
        factor_edad = max(factor_edad, Decimal("0.5"))
        factor_edad = min(factor_edad, Decimal("2.0"))

        rcs_invalidez = suma_asegurada * factor_base * factor_edad

        return rcs_invalidez.quantize(Decimal("0.01"))

    def calcular_rcs_gastos(self) -> Decimal:
        """
        Calcula RCS por riesgo de gastos.

        El riesgo de gastos se materializa cuando los gastos de administración
        y operación superan lo proyectado en las primas.

        Fórmula simplificada:
            RCS_gastos = 0.001 × Suma_asegurada × Factor_cartera

        Factor_cartera: menor para carteras grandes (economías de escala)

        Returns:
            RCS de gastos en unidades monetarias
        """
        suma_asegurada = self.config.suma_asegurada_total
        num_asegurados = self.config.numero_asegurados

        # Factor base: 0.1% de suma asegurada
        factor_base = Decimal("0.001")

        # Factor de escala: economías de escala en carteras grandes
        # 1000 asegurados: ~1.2, 10000: ~1.0, 100000: ~0.8
        if num_asegurados >= 5000:
            factor_cartera = Decimal(str(1.2 / math.sqrt(num_asegurados / 5000.0)))
            factor_cartera = max(factor_cartera, Decimal("0.7"))
        else:
            # Carteras pequeñas tienen gastos unitarios altos
            factor_cartera = Decimal("1.5")

        rcs_gastos = suma_asegurada * factor_base * factor_cartera

        return rcs_gastos.quantize(Decimal("0.01"))

    def calcular_rcs_total_vida(self) -> tuple[Decimal, dict[str, Decimal]]:
        """
        Calcula RCS total de suscripción vida agregando todos los riesgos.

        Los riesgos NO se suman directamente debido a correlaciones.
        Se usa fórmula de raíz cuadrada de suma de cuadrados para riesgos
        que tienen baja correlación entre sí.

        Fórmula:
            RCS_vida = sqrt(RCS_mort² + RCS_long² + RCS_inv² + RCS_gastos²)

        Returns:
            Tupla de (RCS_total, desglose_por_riesgo)
        """
        rcs_mort = self.calcular_rcs_mortalidad()
        rcs_long = self.calcular_rcs_longevidad()
        rcs_inv = self.calcular_rcs_invalidez()
        rcs_gastos = self.calcular_rcs_gastos()

        # Agregación con raíz cuadrada (asume correlación baja entre riesgos)
        suma_cuadrados = (
            rcs_mort**2 + rcs_long**2 + rcs_inv**2 + rcs_gastos**2
        )

        rcs_total = Decimal(str(math.sqrt(float(suma_cuadrados))))

        desglose = {
            "mortalidad": rcs_mort,
            "longevidad": rcs_long,
            "invalidez": rcs_inv,
            "gastos": rcs_gastos,
        }

        return rcs_total.quantize(Decimal("0.01")), desglose

    def obtener_factores_aplicados(self) -> dict[str, Decimal]:
        """
        Obtiene los factores intermedios aplicados en los cálculos.

        Útil para auditoría y verificación de cálculos.

        Returns:
            Diccionario con factores aplicados
        """
        edad = self.config.edad_promedio_asegurados
        num_aseg = self.config.numero_asegurados
        duracion = self.config.duracion_promedio_polizas

        # Recalcular factores
        factor_edad_mort = Decimal(str(1.0 + (edad - 30) * 0.025))
        factor_edad_mort = max(factor_edad_mort, Decimal("0.5"))
        factor_edad_mort = min(factor_edad_mort, Decimal("3.0"))

        if num_aseg >= 1000:
            factor_div = Decimal(str(1.0 / math.sqrt(num_aseg / 1000.0)))
            factor_div = max(factor_div, Decimal("0.5"))
        else:
            factor_div = Decimal("1.5")

        return {
            "factor_edad_mortalidad": factor_edad_mort.quantize(
                Decimal("0.01")
            ),
            "factor_diversificacion": factor_div.quantize(Decimal("0.01")),
            "numero_asegurados": Decimal(str(num_aseg)),
            "edad_promedio": Decimal(str(edad)),
            "duracion_promedio": Decimal(str(duracion)),
        }

    def __repr__(self) -> str:
        """Representación string"""
        return (
            f"RCSVida("
            f"suma_asegurada={self.config.suma_asegurada_total:,.0f}, "
            f"reserva={self.config.reserva_matematica:,.0f}, "
            f"edad={self.config.edad_promedio_asegurados})"
        )
