"""
Validador de suficiencia de reservas técnicas según Circular S-11.4.

Verifica que las reservas constituidas sean suficientes para cumplir
con las obligaciones futuras de la aseguradora.
"""

from decimal import Decimal

from suite_actuarial.regulatorio.reservas_tecnicas.models import (
    ResultadoValidacionSuficiencia,
)


class ValidadorSuficiencia:
    """
    Valida que las reservas técnicas sean suficientes según S-11.4.

    La Circular S-11.4 establece que las reservas técnicas deben ser
    suficientes para cubrir las obligaciones futuras de la aseguradora
    con un nivel de confianza apropiado.

    Ejemplo:
        >>> validador = ValidadorSuficiencia()
        >>> resultado = validador.validar_reserva_individual(
        ...     reserva_constituida=Decimal("50000000"),
        ...     reserva_calculada=Decimal("45000000"),
        ...     margen_seguridad=Decimal("0.05")
        ... )
        >>> print(f"Es suficiente: {resultado.es_suficiente}")
        Es suficiente: True
    """

    # Margen de seguridad mínimo requerido por S-11.4 (5%)
    MARGEN_MINIMO_S_11_4 = Decimal("0.05")

    def validar_reserva_individual(
        self,
        reserva_constituida: Decimal,
        reserva_calculada: Decimal,
        margen_seguridad: Decimal = None,
    ) -> ResultadoValidacionSuficiencia:
        """
        Valida si una reserva individual es suficiente.

        Args:
            reserva_constituida: Reserva actualmente constituida
            reserva_calculada: Reserva calculada según métodos actuariales
            margen_seguridad: Margen de seguridad adicional (default: 5%)

        Returns:
            ResultadoValidacionSuficiencia con detalles de la validación
        """
        if margen_seguridad is None:
            margen_seguridad = self.MARGEN_MINIMO_S_11_4

        # Reserva mínima = reserva calculada × (1 + margen)
        reserva_minima = reserva_calculada * (Decimal("1") + margen_seguridad)

        # Verificar suficiencia
        es_suficiente = reserva_constituida >= reserva_minima

        # Calcular déficit o superávit
        deficit_superavit = reserva_constituida - reserva_minima

        # Porcentaje de cobertura
        porcentaje_cobertura = (
            (reserva_constituida / reserva_minima * 100)
            if reserva_minima > 0
            else Decimal("100")
        )

        return ResultadoValidacionSuficiencia(
            reserva_constituida=reserva_constituida.quantize(Decimal("0.01")),
            reserva_minima_requerida=reserva_minima.quantize(Decimal("0.01")),
            es_suficiente=es_suficiente,
            deficit_superavit=deficit_superavit.quantize(Decimal("0.01")),
            porcentaje_cobertura=porcentaje_cobertura.quantize(Decimal("0.01")),
        )

    def validar_reservas_agregadas(
        self,
        reservas_constituidas: dict[str, Decimal],
        reservas_calculadas: dict[str, Decimal],
        margen_seguridad: Decimal = None,
    ) -> dict[str, ResultadoValidacionSuficiencia]:
        """
        Valida múltiples reservas (por ramo o tipo).

        Args:
            reservas_constituidas: Dict {ramo: reserva_constituida}
            reservas_calculadas: Dict {ramo: reserva_calculada}
            margen_seguridad: Margen de seguridad adicional

        Returns:
            Dict {ramo: ResultadoValidacionSuficiencia}
        """
        resultados = {}

        # Asegurar que ambos dicts tengan las mismas claves
        ramos = set(reservas_constituidas.keys()) | set(reservas_calculadas.keys())

        for ramo in ramos:
            constituida = reservas_constituidas.get(ramo, Decimal("0"))
            calculada = reservas_calculadas.get(ramo, Decimal("0"))

            resultados[ramo] = self.validar_reserva_individual(
                reserva_constituida=constituida,
                reserva_calculada=calculada,
                margen_seguridad=margen_seguridad,
            )

        return resultados

    def generar_reporte_suficiencia(
        self,
        validaciones: dict[str, ResultadoValidacionSuficiencia],
    ) -> dict[str, any]:
        """
        Genera reporte resumen de suficiencia de reservas.

        Args:
            validaciones: Dict {ramo: ResultadoValidacionSuficiencia}

        Returns:
            Diccionario con métricas agregadas
        """
        total_constituido = sum(
            v.reserva_constituida for v in validaciones.values()
        )
        total_requerido = sum(
            v.reserva_minima_requerida for v in validaciones.values()
        )
        total_deficit_superavit = total_constituido - total_requerido

        # Identificar ramos con déficit
        ramos_deficit = [
            ramo for ramo, val in validaciones.items() if not val.es_suficiente
        ]

        # Déficit total (solo ramos con déficit)
        deficit_total = sum(
            abs(val.deficit_superavit)
            for val in validaciones.values()
            if val.deficit_superavit < 0
        )

        # Porcentaje de cobertura global
        pct_cobertura_global = (
            (total_constituido / total_requerido * 100)
            if total_requerido > 0
            else Decimal("100")
        )

        return {
            "total_reservas_constituidas": float(total_constituido),
            "total_reservas_requeridas": float(total_requerido),
            "deficit_superavit_total": float(total_deficit_superavit),
            "es_suficiente_global": len(ramos_deficit) == 0,
            "numero_ramos_con_deficit": len(ramos_deficit),
            "ramos_con_deficit": ramos_deficit,
            "deficit_total": float(deficit_total),
            "porcentaje_cobertura_global": float(
                pct_cobertura_global.quantize(Decimal("0.01"))
            ),
            "numero_ramos_total": len(validaciones),
        }
