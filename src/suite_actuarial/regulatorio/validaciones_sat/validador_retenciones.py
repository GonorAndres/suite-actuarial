"""
Calculador de retenciones de ISR en pagos de seguros según SAT.

Calcula las retenciones que debe aplicar la aseguradora en pagos
sujetos a retención conforme a la Ley del ISR.
"""

from decimal import Decimal
from typing import Any

from suite_actuarial.config.loader import config_vigente
from suite_actuarial.config.schema import TasasSAT
from suite_actuarial.regulatorio.validaciones_sat.models import (
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

    ADVERTENCIA (auditoría 2026-07-26): ni las tasas de retención de esta clase
    ni las citas de artículos anteriores están verificadas contra el texto vigente
    de la LISR. Son cifras ilustrativas heredadas del desarrollo inicial. No las
    uses como referencia fiscal. Ver docs/AUDIT.md.

    Limitación conocida de `requiere_retencion_forzosa`: la rama que lo consume
    está al final de la cadena `elif`, después de las salidas anticipadas de
    vida-sin-retiro y de gastos médicos/daños/invalidez. En la práctica solo es
    alcanzable para PENSIONES sin renta vitalicia; para el resto de los tipos el
    parámetro no tiene efecto observable.

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

    def __init__(self, tasas: TasasSAT | None = None):
        """
        Inicializa la calculadora con las tasas de retención a aplicar.

        Las tasas vienen del perfil regulatorio anual
        (`config/config_<anio>.py`), no de constantes de esta clase. Antes eran
        constantes de clase y la clase no recibía configuración alguna, así que
        `TasasSAT` quedaba versionada por año pero nadie la leía para calcular:
        cambiar el perfil de un año no cambiaba ninguna retención. Los valores
        coincidían entre 2024 y 2026, de modo que la divergencia no se veía
        todavía; habría aparecido, sin aviso, en cuanto un año trajera otra tasa.

        Args:
            tasas: Tasas SAT a aplicar. Si se omite, se toman del perfil
                regulatorio vigente a la fecha de hoy.
        """
        self.tasas = tasas if tasas is not None else config_vigente().tasas_sat

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

        Raises:
            ValueError: Si el pago se declara simultáneamente renta vitalicia y
                retiro de ahorro.
        """
        # Un pago es una renta vitalicia o un retiro del componente de ahorro,
        # no ambos. Aceptar la combinación obligaría a inventar una precedencia
        # que este modulo no tiene fundamentada.
        if es_renta_vitalicia and es_retiro_ahorro:
            raise ValueError(
                "Un pago no puede ser renta vitalicia y retiro de ahorro a la vez; elige uno."
            )

        # Si no hay monto gravable, no hay retención
        if monto_gravable <= 0:
            return ResultadoRetencion(
                requiere_retencion=False,
                monto_pago=monto_pago,
                base_retencion=Decimal("0"),
                tasa_retencion=Decimal("0"),
                monto_retencion=Decimal("0"),
                monto_neto_pagar=monto_pago,
                regla_aplicada="Sin monto gravable: no hay base sobre la cual retener.",
            )

        # Determinar si requiere retención y tasa aplicable
        requiere_retencion = False
        tasa_retencion = Decimal("0")
        regla = ""

        # Rentas vitalicias: REQUIEREN RETENCIÓN
        if es_renta_vitalicia and tipo_seguro == TipoSeguroFiscal.PENSIONES:
            requiere_retencion = True
            tasa_retencion = self.tasas.tasa_retencion_rentas_vitalicias
            regla = "Pensiones + renta vitalicia: se aplica la tasa de rentas vitalicias."

        # Retiros de ahorro: REQUIEREN RETENCIÓN
        elif es_retiro_ahorro and tipo_seguro == TipoSeguroFiscal.VIDA:
            requiere_retencion = True
            tasa_retencion = self.tasas.tasa_retencion_retiros_ahorro
            regla = "Vida + retiro de ahorro: se aplica la tasa de retiros de ahorro."

        # Indemnizaciones por muerte: NO RETENCIÓN (exentas)
        elif tipo_seguro == TipoSeguroFiscal.VIDA and not es_retiro_ahorro:
            return ResultadoRetencion(
                requiere_retencion=False,
                monto_pago=monto_pago,
                base_retencion=Decimal("0"),
                tasa_retencion=Decimal("0"),
                monto_retencion=Decimal("0"),
                monto_neto_pagar=monto_pago,
                regla_aplicada=(
                    "Vida sin retiro de ahorro: el modulo trata la indemnizacion "
                    "por muerte como exenta."
                ),
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
                regla_aplicada=(f"{tipo_seguro.value}: el modulo trata este pago como exento."),
            )

        # Otros casos con retención forzosa.
        # Alcanzable solo para PENSIONES sin renta vitalicia: las ramas anteriores
        # ya retornaron para vida, gastos medicos, danos e invalidez.
        elif requiere_retencion_forzosa:
            requiere_retencion = True
            tasa_retencion = self.tasas.tasa_retencion_otros_ingresos
            regla = "Retencion forzosa declarada: se aplica la tasa de otros ingresos."

        if not requiere_retencion and not regla:
            regla = (
                "Ninguna regla de retencion del modulo aplico a esta combinacion "
                "de tipo de seguro y banderas."
            )

        # Calcular retención si aplica
        if requiere_retencion:
            monto_retencion = (monto_gravable * tasa_retencion).quantize(Decimal("0.01"))
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
            regla_aplicada=regla,
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
                tipo_seguro=pago["tipo_seguro"],
                monto_pago=pago["monto_pago"],
                monto_gravable=pago["monto_gravable"],
                es_renta_vitalicia=pago.get("es_renta_vitalicia", False),
                es_retiro_ahorro=pago.get("es_retiro_ahorro", False),
                requiere_retencion_forzosa=pago.get("requiere_retencion_forzosa", False),
            )
            resultados.append(resultado)

        return resultados

    def generar_resumen_retenciones(
        self,
        retenciones: list[ResultadoRetencion],
    ) -> dict[str, Any]:
        """
        Genera resumen agregado de retenciones.

        Args:
            retenciones: Lista de ResultadoRetencion

        Returns:
            Diccionario con totales y estadísticas
        """
        total_pagos = sum((r.monto_pago for r in retenciones), Decimal("0"))
        total_gravable = sum((r.base_retencion for r in retenciones), Decimal("0"))
        total_retenido = sum((r.monto_retencion for r in retenciones), Decimal("0"))
        total_neto = sum((r.monto_neto_pagar for r in retenciones), Decimal("0"))

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
