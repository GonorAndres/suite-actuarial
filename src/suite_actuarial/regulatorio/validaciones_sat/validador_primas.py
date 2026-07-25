"""
Validador de deducibilidad de primas de seguros según SAT.

Determina qué primas son deducibles para ISR según la Ley del ISR
y sus límites aplicables.
"""

from decimal import Decimal

from suite_actuarial.regulatorio.validaciones_sat.models import (
    EstadoFiscal,
    ResultadoDeducibilidadPrima,
    TipoSeguroFiscal,
)


class ValidadorPrimasDeducibles:
    """
    Valida deducibilidad de primas de seguros para ISR.

    Implementa reglas de Ley del ISR Art. 151, fracción V para personas físicas
    y Art. 25 para personas morales.

    Ejemplo:
        >>> from decimal import Decimal
        >>> validador = ValidadorPrimasDeducibles(
        ...     uma_anual=Decimal("37500")  # UMA 2024 aproximada
        ... )
        >>> resultado = validador.validar_deducibilidad(
        ...     tipo_seguro=TipoSeguroFiscal.GASTOS_MEDICOS,
        ...     monto_prima=Decimal("50000"),
        ...     es_persona_fisica=True
        ... )
        >>> print(f"Deducible: ${resultado.monto_deducible:,.0f}")
    """

    def __init__(self, uma_anual: Decimal):
        """
        Inicializa validador con UMA anual.

        Args:
            uma_anual: Valor de UMA anual vigente (UMA diaria × 365)
        """
        self.uma_anual = uma_anual

    def validar_deducibilidad(
        self,
        tipo_seguro: TipoSeguroFiscal,
        monto_prima: Decimal,
        es_persona_fisica: bool = True,
        ingreso_anual: Decimal | None = None,
        metodo_pago: str | None = None,
        relacion_beneficiario: str | None = None,
    ) -> ResultadoDeducibilidadPrima:
        """
        Valida si una prima es deducible y hasta qué monto.

        Args:
            tipo_seguro: Tipo de seguro fiscal
            monto_prima: Monto de la prima pagada
            es_persona_fisica: Si es persona física (True) o moral (False)

        Returns:
            ResultadoDeducibilidadPrima con análisis de deducibilidad
        """
        if es_persona_fisica:
            resultado = self._validar_persona_fisica(
                tipo_seguro, monto_prima, ingreso_anual=ingreso_anual
            )
        else:
            resultado = self._validar_persona_moral(tipo_seguro, monto_prima)
        faltantes: list[str] = []
        if metodo_pago is None:
            faltantes.append("metodo_pago")
        if (
            es_persona_fisica
            and tipo_seguro == TipoSeguroFiscal.PENSIONES
            and ingreso_anual is None
        ):
            faltantes.append("ingreso_anual")
        if not es_persona_fisica and relacion_beneficiario is None:
            faltantes.append("relacion_beneficiario")
        if faltantes:
            resultado.estado = EstadoFiscal.INDETERMINATE
            resultado.factores_faltantes = faltantes
        return resultado

    def _validar_persona_fisica(
        self,
        tipo_seguro: TipoSeguroFiscal,
        monto_prima: Decimal,
        ingreso_anual: Decimal | None = None,
    ) -> ResultadoDeducibilidadPrima:
        """
        Valida deducibilidad para personas físicas.

        Reglas Ley ISR Art. 151:
        - Gastos médicos: 100% deducible sin límite
        - Seguros de vida: no deducibles para personas físicas
        - Otros: generalmente no deducibles
        """
        if tipo_seguro == TipoSeguroFiscal.GASTOS_MEDICOS:
            # GMM es 100% deducible sin límite (Art. 151, fracc. I)
            return ResultadoDeducibilidadPrima(
                es_deducible=True,
                monto_prima=monto_prima,
                monto_deducible=monto_prima,
                porcentaje_deducible=Decimal("100"),
                fundamento_legal="LISR Art. 151, fracc. I - Gastos médicos",
            )

        elif tipo_seguro == TipoSeguroFiscal.VIDA:
            # Seguros de vida NO son deducibles para personas físicas
            return ResultadoDeducibilidadPrima(
                es_deducible=False,
                monto_prima=monto_prima,
                monto_deducible=Decimal("0"),
                porcentaje_deducible=Decimal("0"),
                fundamento_legal="LISR - Seguros de vida no deducibles para PF",
            )

        elif tipo_seguro == TipoSeguroFiscal.PENSIONES:
            # Aportaciones a planes de pensiones: deducible hasta 10% ingresos o 5 UMAs
            limite_uma = self.uma_anual * 5
            limite_ingreso = ingreso_anual * Decimal("0.15") if ingreso_anual is not None else None
            limite_aplicable = (
                min(limite_uma, limite_ingreso) if limite_ingreso is not None else limite_uma
            )
            monto_deducible = min(monto_prima, limite_aplicable)

            return ResultadoDeducibilidadPrima(
                es_deducible=True,
                monto_prima=monto_prima,
                monto_deducible=monto_deducible,
                porcentaje_deducible=(monto_deducible / monto_prima * 100).quantize(Decimal("0.01"))
                if monto_prima > 0
                else Decimal("0"),
                limite_aplicado=(
                    f"Menor de 5 UMAs (${limite_uma:,.2f}) y 15% del ingreso"
                    if limite_ingreso is not None
                    else f"5 UMAs anuales (${limite_uma:,.2f})"
                ),
                fundamento_legal="LISR Art. 151, fracc. V - Planes personales de retiro",
            )

        else:
            # Otros seguros (daños, etc.) generalmente no deducibles para PF
            return ResultadoDeducibilidadPrima(
                es_deducible=False,
                monto_prima=monto_prima,
                monto_deducible=Decimal("0"),
                porcentaje_deducible=Decimal("0"),
                fundamento_legal=f"LISR - {tipo_seguro.value} no deducible para PF",
            )

    def _validar_persona_moral(
        self, tipo_seguro: TipoSeguroFiscal, monto_prima: Decimal
    ) -> ResultadoDeducibilidadPrima:
        """
        Valida deducibilidad para personas morales.

        Reglas Ley ISR Art. 25:
        - Seguros relacionados con actividad empresarial: deducibles
        - GMM de empleados: deducible
        - Vida de empleados (beneficiario empresa): deducible
        """
        if tipo_seguro in [
            TipoSeguroFiscal.GASTOS_MEDICOS,
            TipoSeguroFiscal.VIDA,
            TipoSeguroFiscal.INVALIDEZ,
        ]:
            # Seguros de personal: 100% deducibles
            return ResultadoDeducibilidadPrima(
                es_deducible=True,
                monto_prima=monto_prima,
                monto_deducible=monto_prima,
                porcentaje_deducible=Decimal("100"),
                fundamento_legal="LISR Art. 25, fracc. VI - Seguros de personal",
            )

        elif tipo_seguro == TipoSeguroFiscal.DANOS:
            # Seguros de daños sobre activos: deducibles
            return ResultadoDeducibilidadPrima(
                es_deducible=True,
                monto_prima=monto_prima,
                monto_deducible=monto_prima,
                porcentaje_deducible=Decimal("100"),
                fundamento_legal="LISR Art. 25, fracc. VI - Seguros sobre bienes",
            )

        else:
            # Otros seguros empresariales: generalmente deducibles
            return ResultadoDeducibilidadPrima(
                es_deducible=True,
                monto_prima=monto_prima,
                monto_deducible=monto_prima,
                porcentaje_deducible=Decimal("100"),
                fundamento_legal="LISR Art. 25, fracc. VI - Gastos estrictamente indispensables",
            )

    def __repr__(self) -> str:
        return f"ValidadorPrimasDeducibles(UMA_anual=${self.uma_anual:,.2f})"
