"""
Calculador de retenciones de ISR en pagos de seguros según SAT.

Calcula las retenciones que debe aplicar la aseguradora en pagos
sujetos a retención conforme a la Ley del ISR.
"""

from decimal import Decimal

from mexican_insurance.regulatorio.validaciones_sat.models import (
    ResultadoRetencion,
    TipoSeguroFiscal,
)


class CalculadoraRetencionesISR:
    """
    Calcula retenciones de ISR en pagos de seguros.

    Implementa reglas de retención según Ley del ISR y Reglamento:
    - Art. 145: Retención por rentas vitalicias
    - Art. 158: Retención por retiros de seguros con ahorro
    - Tarifas aplicables según tipo de ingreso

    Ejemplo:
        >>> from decimal import Decimal
        >>> calculadora = CalculadoraRetencionesISR()
        >>> resultado = calculadora.calcular_retencion(
        ...     tipo_seguro=TipoSeguroFiscal.PENSIONES,
        ...     monto_pago=Decimal("50000"),
        ...     monto_gravable=Decimal("25000"),
        ...     es_renta_vitalicia=True
        ... )
        >>> print(f"Retención: ${resultado.monto_retencion:,.2f}")
        Retención: $2,500.00
    """

    # Tasas de retención según tipo de pago
    TASA_RETENCION_RENTAS_VITALICIAS = Decimal("0.10")  # 10%
    TASA_RETENCION_RETIROS_AHORRO = Decimal("0.20")  # 20%
    TASA_RETENCION_OTROS_INGRESOS = Decimal("0.10")  # 10%

    def calcular_retencion(
        self,
        tipo_seguro: TipoSeguroFiscal,
        monto_pago: Decimal,
        monto_gravable: Decimal,
        es_renta_vitalicia: bool = False,
        es_retiro_ahorro: bool = False,
        requiere_retencion_forzosa: bool = False,
    ) -> ResultadoRetencion:
        """
        Calcula retención de ISR aplicable a un pago de seguro.

        Args:
            tipo_seguro: Tipo de seguro fiscal
            monto_pago: Monto total del pago
            monto_gravable: Monto gravable (después de exenciones)
            es_renta_vitalicia: Si es pago de renta vitalicia
            es_retiro_ahorro: Si es retiro de componente de ahorro
            requiere_retencion_forzosa: Si hay obligación de retener

        Returns:
            ResultadoRetencion con cálculo de retención
        """
        # Si no hay monto gravable, no hay retención
        if monto_gravable <= 0:
            return ResultadoRetencion(
                requiere_retencion=False,
                monto_pago=monto_pago,
                base_retencion=Decimal("0"),
                tasa_retencion=Decimal("0"),
                monto_retencion=Decimal("0"),
                monto_neto_pagar=monto_pago,
            )

        # Determinar si requiere retención y tasa aplicable
        requiere_retencion = False
        tasa_retencion = Decimal("0")
        fundamento_legal = ""

        # Rentas vitalicias: REQUIEREN RETENCIÓN
        if es_renta_vitalicia and tipo_seguro == TipoSeguroFiscal.PENSIONES:
            requiere_retencion = True
            tasa_retencion = self.TASA_RETENCION_RENTAS_VITALICIAS
            fundamento_legal = "LISR Art. 145 - Retención en rentas vitalicias (10%)"

        # Retiros de ahorro: REQUIEREN RETENCIÓN
        elif es_retiro_ahorro and tipo_seguro == TipoSeguroFiscal.VIDA:
            requiere_retencion = True
            tasa_retencion = self.TASA_RETENCION_RETIROS_AHORRO
            fundamento_legal = "LISR Art. 158 - Retención en retiros de seguros (20%)"

        # Indemnizaciones por muerte: NO RETENCIÓN (exentas)
        elif tipo_seguro == TipoSeguroFiscal.VIDA and not es_retiro_ahorro:
            return ResultadoRetencion(
                requiere_retencion=False,
                monto_pago=monto_pago,
                base_retencion=Decimal("0"),
                tasa_retencion=Decimal("0"),
                monto_retencion=Decimal("0"),
                monto_neto_pagar=monto_pago,
            )

        # Gastos médicos, daños, invalidez: NO RETENCIÓN (exentos)
        elif tipo_seguro in [
            TipoSeguroFiscal.GASTOS_MEDICOS,
            TipoSeguroFiscal.DANOS,
            TipoSeguroFiscal.INVALIDEZ,
        ]:
            return ResultadoRetencion(
                requiere_retencion=False,
                monto_pago=monto_pago,
                base_retencion=Decimal("0"),
                tasa_retencion=Decimal("0"),
                monto_retencion=Decimal("0"),
                monto_neto_pagar=monto_pago,
            )

        # Otros casos con retención forzosa
        elif requiere_retencion_forzosa:
            requiere_retencion = True
            tasa_retencion = self.TASA_RETENCION_OTROS_INGRESOS
            fundamento_legal = "LISR - Retención sobre ingresos gravables (10%)"

        # Calcular retención si aplica
        if requiere_retencion:
            monto_retencion = (monto_gravable * tasa_retencion).quantize(
                Decimal("0.01")
            )
            monto_neto = monto_pago - monto_retencion
        else:
            monto_retencion = Decimal("0")
            monto_neto = monto_pago

        return ResultadoRetencion(
            requiere_retencion=requiere_retencion,
            monto_pago=monto_pago,
            base_retencion=monto_gravable,
            tasa_retencion=tasa_retencion,
            monto_retencion=monto_retencion,
            monto_neto_pagar=monto_neto.quantize(Decimal("0.01")),
        )

    def calcular_retencion_masiva(
        self,
        pagos: list[dict],
    ) -> list[ResultadoRetencion]:
        """
        Calcula retenciones para múltiples pagos.

        Args:
            pagos: Lista de dicts con parámetros de cada pago

        Returns:
            Lista de ResultadoRetencion para cada pago
        """
        resultados = []

        for pago in pagos:
            resultado = self.calcular_retencion(
                tipo_seguro=pago.get("tipo_seguro"),
                monto_pago=pago.get("monto_pago"),
                monto_gravable=pago.get("monto_gravable"),
                es_renta_vitalicia=pago.get("es_renta_vitalicia", False),
                es_retiro_ahorro=pago.get("es_retiro_ahorro", False),
                requiere_retencion_forzosa=pago.get(
                    "requiere_retencion_forzosa", False
                ),
            )
            resultados.append(resultado)

        return resultados

    def generar_resumen_retenciones(
        self,
        retenciones: list[ResultadoRetencion],
    ) -> dict:
        """
        Genera resumen agregado de retenciones.

        Args:
            retenciones: Lista de ResultadoRetencion

        Returns:
            Diccionario con totales y estadísticas
        """
        total_pagos = sum(r.monto_pago for r in retenciones)
        total_gravable = sum(r.base_retencion for r in retenciones)
        total_retenido = sum(r.monto_retencion for r in retenciones)
        total_neto = sum(r.monto_neto_pagar for r in retenciones)

        pagos_con_retencion = sum(1 for r in retenciones if r.requiere_retencion)

        tasa_efectiva = (
            (total_retenido / total_gravable * 100).quantize(Decimal("0.01"))
            if total_gravable > 0
            else Decimal("0")
        )

        return {
            "numero_pagos": len(retenciones),
            "pagos_con_retencion": pagos_con_retencion,
            "pagos_sin_retencion": len(retenciones) - pagos_con_retencion,
            "total_pagos": float(total_pagos),
            "total_gravable": float(total_gravable),
            "total_retenido": float(total_retenido),
            "total_neto": float(total_neto),
            "tasa_efectiva_retencion": float(tasa_efectiva),
        }

    def __repr__(self) -> str:
        return "CalculadoraRetencionesISR()"
