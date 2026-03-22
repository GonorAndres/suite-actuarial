"""
Validador de gravabilidad de siniestros de seguros según SAT.

Determina qué pagos por siniestros están gravados o exentos para ISR
según la Ley del ISR.
"""

from decimal import Decimal

from suite_actuarial.regulatorio.validaciones_sat.models import (
    ResultadoGravabilidadSiniestro,
    TipoSeguroFiscal,
)


class ValidadorSiniestrosGravables:
    """
    Valida gravabilidad de pagos por siniestros para ISR.

    Implementa reglas de Ley del ISR sobre exenciones de ingresos
    por seguros (Art. 93, 109 y otros).

    Ejemplo:
        >>> from decimal import Decimal
        >>> validador = ValidadorSiniestrosGravables()
        >>> resultado = validador.validar_gravabilidad(
        ...     tipo_seguro=TipoSeguroFiscal.VIDA,
        ...     monto_pago=Decimal("500000"),
        ...     es_indemnizacion_muerte=True
        ... )
        >>> print(f"Gravable: {resultado.es_gravable}")
        Gravable: False
    """

    def validar_gravabilidad(
        self,
        tipo_seguro: TipoSeguroFiscal,
        monto_pago: Decimal,
        es_persona_fisica: bool = True,
        es_indemnizacion_muerte: bool = False,
        es_renta_vitalicia: bool = False,
        es_retiro_ahorro: bool = False,
        monto_primas_pagadas: Decimal = None,
    ) -> ResultadoGravabilidadSiniestro:
        """
        Valida si un pago por siniestro está gravado para ISR.

        Args:
            tipo_seguro: Tipo de seguro fiscal
            monto_pago: Monto del pago del siniestro
            es_persona_fisica: Si el beneficiario es persona física
            es_indemnizacion_muerte: Si es indemnización por fallecimiento
            es_renta_vitalicia: Si es pago de renta vitalicia
            es_retiro_ahorro: Si es retiro del componente de ahorro
            monto_primas_pagadas: Primas pagadas (para calcular ganancia)

        Returns:
            ResultadoGravabilidadSiniestro con análisis de gravabilidad
        """
        if es_persona_fisica:
            return self._validar_persona_fisica(
                tipo_seguro=tipo_seguro,
                monto_pago=monto_pago,
                es_indemnizacion_muerte=es_indemnizacion_muerte,
                es_renta_vitalicia=es_renta_vitalicia,
                es_retiro_ahorro=es_retiro_ahorro,
                monto_primas_pagadas=monto_primas_pagadas,
            )
        else:
            return self._validar_persona_moral(
                tipo_seguro=tipo_seguro,
                monto_pago=monto_pago,
                es_indemnizacion_muerte=es_indemnizacion_muerte,
            )

    def _validar_persona_fisica(
        self,
        tipo_seguro: TipoSeguroFiscal,
        monto_pago: Decimal,
        es_indemnizacion_muerte: bool = False,
        es_renta_vitalicia: bool = False,
        es_retiro_ahorro: bool = False,
        monto_primas_pagadas: Decimal = None,
    ) -> ResultadoGravabilidadSiniestro:
        """
        Valida gravabilidad para personas físicas.

        Reglas Ley ISR:
        - Art. 93, fracc. XIII: Indemnizaciones por muerte exentas
        - Art. 93, fracc. IV: Gastos médicos exentos
        - Art. 93, fracc. XV: Seguros de daños exentos (reposición)
        - Art. 142: Rentas vitalicias parcialmente gravables
        - Retiros de ahorro: gravables solo la ganancia
        """
        # Indemnizaciones por muerte: EXENTAS
        if es_indemnizacion_muerte and tipo_seguro == TipoSeguroFiscal.VIDA:
            return ResultadoGravabilidadSiniestro(
                esta_gravado=False,
                monto_siniestro=monto_pago,
                monto_gravado=Decimal("0"),
                monto_exento=monto_pago,
                tasa_isr_aplicable=Decimal("0"),
                fundamento_legal="LISR Art. 93, fracc. XIII - Indemnizaciones por muerte exentas",
            )

        # Gastos médicos: EXENTOS (reembolso, no ingreso)
        if tipo_seguro == TipoSeguroFiscal.GASTOS_MEDICOS:
            return ResultadoGravabilidadSiniestro(
                esta_gravado=False,
                monto_siniestro=monto_pago,
                monto_gravado=Decimal("0"),
                monto_exento=monto_pago,
                tasa_isr_aplicable=Decimal("0"),
                fundamento_legal="LISR Art. 93, fracc. IV - Gastos médicos exentos",
            )

        # Seguros de daños: EXENTOS (reposición patrimonial)
        if tipo_seguro == TipoSeguroFiscal.DANOS:
            return ResultadoGravabilidadSiniestro(
                esta_gravado=False,
                monto_siniestro=monto_pago,
                monto_gravado=Decimal("0"),
                monto_exento=monto_pago,
                tasa_isr_aplicable=Decimal("0"),
                fundamento_legal="LISR Art. 93, fracc. XV - Daños patrimoniales exentos",
            )

        # Invalidez: EXENTA
        if tipo_seguro == TipoSeguroFiscal.INVALIDEZ:
            return ResultadoGravabilidadSiniestro(
                esta_gravado=False,
                monto_siniestro=monto_pago,
                monto_gravado=Decimal("0"),
                monto_exento=monto_pago,
                tasa_isr_aplicable=Decimal("0"),
                fundamento_legal="LISR Art. 93, fracc. XIV - Invalidez exenta",
            )

        # Rentas vitalicias: PARCIALMENTE GRAVABLES
        if es_renta_vitalicia and tipo_seguro == TipoSeguroFiscal.PENSIONES:
            # Simplificación: 50% gravable, 50% exento (recuperación de capital)
            # En realidad depende de tabla actuarial Art. 142 LISR
            monto_gravable = monto_pago * Decimal("0.5")
            monto_exento = monto_pago * Decimal("0.5")

            return ResultadoGravabilidadSiniestro(
                esta_gravado=True,
                monto_siniestro=monto_pago,
                monto_gravado=monto_gravable,
                monto_exento=monto_exento,
                tasa_isr_aplicable=Decimal("0.5"),  # 50% gravable
                fundamento_legal="LISR Art. 142 - Rentas vitalicias parcialmente gravables",
            )

        # Retiro de ahorro: GRAVABLE solo la ganancia
        if es_retiro_ahorro and tipo_seguro == TipoSeguroFiscal.VIDA:
            if monto_primas_pagadas is not None:
                # Ganancia = Pago - Primas pagadas
                ganancia = max(monto_pago - monto_primas_pagadas, Decimal("0"))
                monto_exento = monto_primas_pagadas

                return ResultadoGravabilidadSiniestro(
                    esta_gravado=ganancia > 0,
                    monto_siniestro=monto_pago,
                    monto_gravado=ganancia,
                    monto_exento=monto_exento,
                    tasa_isr_aplicable=(
                        (ganancia / monto_pago).quantize(Decimal("0.0001"))
                        if monto_pago > 0
                        else Decimal("0")
                    ),
                    fundamento_legal="LISR Art. 158 - Retiros de seguros con ahorro",
                )
            else:
                # Sin información de primas, asumir 100% gravable
                return ResultadoGravabilidadSiniestro(
                    esta_gravado=True,
                    monto_siniestro=monto_pago,
                    monto_gravado=monto_pago,
                    monto_exento=Decimal("0"),
                    tasa_isr_aplicable=Decimal("1"),  # 100% gravable
                    fundamento_legal="LISR Art. 158 - Retiros de seguros con ahorro (sin info primas)",
                )

        # Seguros de vida (no muerte, no retiro): generalmente EXENTOS
        if tipo_seguro == TipoSeguroFiscal.VIDA:
            return ResultadoGravabilidadSiniestro(
                esta_gravado=False,
                monto_siniestro=monto_pago,
                monto_gravado=Decimal("0"),
                monto_exento=monto_pago,
                tasa_isr_aplicable=Decimal("0"),
                fundamento_legal="LISR Art. 93 - Indemnizaciones de seguros exentas",
            )

        # Pensiones (no renta): generalmente EXENTAS hasta límite
        if tipo_seguro == TipoSeguroFiscal.PENSIONES:
            return ResultadoGravabilidadSiniestro(
                esta_gravado=False,
                monto_siniestro=monto_pago,
                monto_gravado=Decimal("0"),
                monto_exento=monto_pago,
                tasa_isr_aplicable=Decimal("0"),
                fundamento_legal="LISR Art. 93, fracc. IV - Pensiones exentas (hasta límite)",
            )

        # Default: NO GRAVABLE (principio de que indemnizaciones no son ingreso)
        return ResultadoGravabilidadSiniestro(
            esta_gravado=False,
            monto_siniestro=monto_pago,
            monto_gravado=Decimal("0"),
            monto_exento=monto_pago,
            tasa_isr_aplicable=Decimal("0"),
            fundamento_legal="LISR - Indemnizaciones generalmente no gravables",
        )

    def _validar_persona_moral(
        self,
        tipo_seguro: TipoSeguroFiscal,
        monto_pago: Decimal,
        es_indemnizacion_muerte: bool = False,
    ) -> ResultadoGravabilidadSiniestro:
        """
        Valida gravabilidad para personas morales.

        Reglas Ley ISR:
        - Seguros de daños: NO gravables (reposición patrimonial)
        - Seguros de vida empleados (beneficiario empresa): GRAVABLES
        - Otros seguros empresariales: generalmente gravables
        """
        # Seguros de daños: NO GRAVABLES (reponen patrimonio)
        if tipo_seguro == TipoSeguroFiscal.DANOS:
            return ResultadoGravabilidadSiniestro(
                esta_gravado=False,
                monto_siniestro=monto_pago,
                monto_gravado=Decimal("0"),
                monto_exento=monto_pago,
                tasa_isr_aplicable=Decimal("0"),
                fundamento_legal="LISR - Reposición patrimonial no gravable",
            )

        # Seguros de vida (empresa beneficiaria): GRAVABLES
        if tipo_seguro == TipoSeguroFiscal.VIDA:
            return ResultadoGravabilidadSiniestro(
                esta_gravado=True,
                monto_siniestro=monto_pago,
                monto_gravado=monto_pago,
                monto_exento=Decimal("0"),
                tasa_isr_aplicable=Decimal("1"),  # 100%
                fundamento_legal="LISR Art. 18 - Ingresos acumulables de PM",
            )

        # Otros seguros: generalmente GRAVABLES como ingreso
        return ResultadoGravabilidadSiniestro(
            esta_gravado=True,
            monto_siniestro=monto_pago,
            monto_gravado=monto_pago,
            monto_exento=Decimal("0"),
            tasa_isr_aplicable=Decimal("1"),
            fundamento_legal="LISR Art. 18 - Ingresos acumulables de PM",
        )

    def __repr__(self) -> str:
        return "ValidadorSiniestrosGravables()"
