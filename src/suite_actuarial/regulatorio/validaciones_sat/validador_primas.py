"""
Validador de deducibilidad de primas de seguros según SAT.

Determina qué primas son deducibles para ISR según la Ley del ISR
y sus límites aplicables.

Fuente del texto legal aplicado en este módulo (consultada el 2026-08-02):
Ley del Impuesto sobre la Renta, texto vigente consolidado por la Cámara de
Diputados, última reforma publicada en el DOF el 01-04-2024,
https://www.diputados.gob.mx/LeyesBiblio/pdf/LISR.pdf (Art. 151, pp. 181-184).

Lo que ese texto dice, y que este módulo aplica:

- Fracción VI: "Las primas por seguros de gastos médicos, complementarios o
  independientes de los servicios de salud proporcionados por instituciones
  públicas de seguridad social, siempre que el beneficiario sea el propio
  contribuyente, su cónyuge o la persona con quien vive en concubinato, o sus
  ascendientes o descendientes, en línea recta." Las primas de GMM son la
  fracción **VI**, no la I: la I son honorarios médicos y gastos hospitalarios.

- Fracción V: aportaciones complementarias de retiro y planes personales de
  retiro, "de hasta el 10% de los ingresos acumulables del contribuyente en el
  ejercicio, sin que dichas aportaciones excedan del equivalente a cinco
  salarios mínimos generales del área geográfica del contribuyente elevados al
  año". El porcentaje es 10%, no 15%. Los cinco salarios mínimos se leen como
  cinco UMA anuales por el Art. Tercero transitorio del decreto de
  desindexación del salario mínimo (DOF 27-01-2016).

- Último párrafo (tope global): "El monto total de las deducciones que podrán
  efectuar los contribuyentes en los términos de este artículo, no podrá
  exceder de la cantidad que resulte menor entre cinco veces el valor anual de
  la Unidad de Medida y Actualización, o del 15% del total de los ingresos del
  contribuyente, incluyendo aquéllos por los que no se pague el impuesto. Lo
  dispuesto en este párrafo no será aplicable tratándose de la fracción V de
  este artículo."

Dos límites de alcance que sobreviven a esta implementación y que viajan en el
resultado, no en un comentario:

1. El tope del último párrafo es **global**: aplica a la suma de todas las
   deducciones personales del artículo, no a una prima aislada. Este módulo ve
   una sola prima, así que la topa como si fuera la única deducción personal
   del contribuyente. Con otras deducciones personales, el monto deducible real
   es menor.
2. La rama del 15% necesita el total de ingresos del contribuyente. Sin ese
   dato el tope no queda determinado y el resultado lo declara en
   `tope_global`; nunca se devuelve 100% en silencio.
"""

from decimal import Decimal

from suite_actuarial.config.loader import config_vigente
from suite_actuarial.regulatorio.validaciones_sat.models import (
    EstadoFiscal,
    EstadoTopeGlobal,
    ResultadoDeducibilidadPrima,
    TipoSeguroFiscal,
)

# Ultimo parrafo del Art. 151 LISR: 15% del total de los ingresos.
_PORCENTAJE_TOPE_GLOBAL = Decimal("0.15")

# Art. 151, fraccion V: 10% de los ingresos acumulables.
_PORCENTAJE_FRACCION_V = Decimal("0.10")

_NOTA_PERSONA_MORAL = (
    "El tope de deducciones personales del Art. 151 LISR es de personas "
    "físicas; la deducción de una persona moral se rige por el Art. 25."
)

_NOTA_TOPE_ES_GLOBAL = (
    "El tope del último párrafo del Art. 151 LISR aplica al total de las "
    "deducciones personales del ejercicio. Aquí se aplica a esta prima como si "
    "fuera la única deducción personal del contribuyente; con otras "
    "deducciones personales el monto deducible sería menor."
)


class ValidadorPrimasDeducibles:
    """
    Valida deducibilidad de primas de seguros para ISR.

    Implementa las reglas de la Ley del ISR Art. 151 (deducciones personales de
    personas físicas) y Art. 25 (personas morales). El encabezado del módulo
    transcribe el texto aplicado y su fuente.

    Ejemplo:
        >>> from decimal import Decimal
        >>> validador = ValidadorPrimasDeducibles(
        ...     uma_anual=Decimal("42794.64"),  # UMA anual 2026 (INEGI)
        ...     limite_deducciones_umas=5,
        ... )
        >>> resultado = validador.validar_deducibilidad(
        ...     tipo_seguro=TipoSeguroFiscal.GASTOS_MEDICOS,
        ...     monto_prima=Decimal("50000"),
        ...     es_persona_fisica=True,
        ...     ingresos_totales_anuales=Decimal("300000"),
        ... )
        >>> print(f"Deducible: ${resultado.monto_deducible:,.0f}")
        Deducible: $45,000
    """

    def __init__(self, uma_anual: Decimal, limite_deducciones_umas: int | None = None):
        """
        Inicializa validador con UMA anual y el tope de deducciones en UMAs.

        El tope viene del perfil regulatorio anual
        (`config/config_<anio>.py: TasasSAT.limite_deducciones_pf_umas`), no de
        un literal. Esta clase ya recibía `uma_anual` de la configuración, pero
        multiplicaba por un `5` escrito a mano, de modo que la mitad del cálculo
        estaba versionada por año y la otra mitad no.

        Args:
            uma_anual: Valor anual de la UMA vigente (UMA mensual × 12, según
                el Art. 4, fracc. III de la Ley para Determinar el Valor de la
                UMA), que es el "valor anual de la UMA" al que remite el último
                párrafo del Art. 151 LISR.
            limite_deducciones_umas: Tope de deducciones personales en UMAs. Si
                se omite, se toma del perfil regulatorio vigente.
        """
        self.uma_anual = uma_anual
        self.limite_deducciones_umas = (
            limite_deducciones_umas
            if limite_deducciones_umas is not None
            else config_vigente().tasas_sat.limite_deducciones_pf_umas
        )

    def validar_deducibilidad(
        self,
        tipo_seguro: TipoSeguroFiscal,
        monto_prima: Decimal,
        es_persona_fisica: bool = True,
        ingreso_anual: Decimal | None = None,
        metodo_pago: str | None = None,
        relacion_beneficiario: str | None = None,
        ingresos_totales_anuales: Decimal | None = None,
    ) -> ResultadoDeducibilidadPrima:
        """
        Valida si una prima es deducible y hasta qué monto.

        Args:
            tipo_seguro: Tipo de seguro fiscal.
            monto_prima: Monto de la prima pagada.
            es_persona_fisica: Si es persona física (True) o moral (False).
            ingreso_anual: Ingresos **acumulables** del ejercicio. Es la base
                del 10% de la fracción V (planes personales de retiro).
            metodo_pago: Medio de pago; la deducción exige uno rastreable.
            relacion_beneficiario: Relación del beneficiario con el contratante.
            ingresos_totales_anuales: Total de los ingresos del contribuyente,
                **incluyendo los exentos**. Es la base del 15% del último
                párrafo del Art. 151. La ley usa dos bases distintas para el
                tope de la fracción V y para el tope global, así que se piden
                por separado en vez de suponer que coinciden.

        Returns:
            ResultadoDeducibilidadPrima con análisis de deducibilidad.
        """
        if es_persona_fisica:
            resultado = self._validar_persona_fisica(
                tipo_seguro,
                monto_prima,
                ingreso_anual=ingreso_anual,
                ingresos_totales_anuales=ingresos_totales_anuales,
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
        if resultado.tope_global == EstadoTopeGlobal.PARCIAL_SIN_INGRESOS:
            faltantes.append("ingresos_totales_anuales")
        if not es_persona_fisica and relacion_beneficiario is None:
            faltantes.append("relacion_beneficiario")
        if faltantes:
            resultado.estado = EstadoFiscal.INDETERMINATE
            resultado.factores_faltantes = faltantes
        return resultado

    @staticmethod
    def _porcentaje(monto_deducible: Decimal, monto_prima: Decimal) -> Decimal:
        """Porcentaje deducible de la prima, redondeado a dos decimales."""
        if monto_prima <= 0:
            return Decimal("0")
        return (monto_deducible / monto_prima * 100).quantize(Decimal("0.01"))

    def _validar_persona_fisica(
        self,
        tipo_seguro: TipoSeguroFiscal,
        monto_prima: Decimal,
        ingreso_anual: Decimal | None = None,
        ingresos_totales_anuales: Decimal | None = None,
    ) -> ResultadoDeducibilidadPrima:
        """
        Valida deducibilidad para personas físicas (LISR Art. 151).

        - Gastos médicos (fracc. VI): deducible, sujeto al tope global del
          último párrafo.
        - Planes personales de retiro (fracc. V): tope propio de 10% de los
          ingresos acumulables y 5 UMA anuales; excluido del tope global.
        - Seguros de vida y de daños: no son deducciones personales del
          artículo.
        """
        if tipo_seguro == TipoSeguroFiscal.GASTOS_MEDICOS:
            return self._gastos_medicos_persona_fisica(monto_prima, ingresos_totales_anuales)

        elif tipo_seguro == TipoSeguroFiscal.VIDA:
            # Seguros de vida NO son deducciones personales del Art. 151.
            return ResultadoDeducibilidadPrima(
                es_deducible=False,
                monto_prima=monto_prima,
                monto_deducible=Decimal("0"),
                porcentaje_deducible=Decimal("0"),
                fundamento_legal="LISR - Seguros de vida no deducibles para PF",
                tope_global=EstadoTopeGlobal.NO_APLICABLE,
                nota_tope_global="Sin deducción que topar: la prima no es deducible.",
            )

        elif tipo_seguro == TipoSeguroFiscal.PENSIONES:
            return self._planes_de_retiro_persona_fisica(monto_prima, ingreso_anual)

        else:
            # Otros seguros (daños, invalidez) no son deducciones personales.
            return ResultadoDeducibilidadPrima(
                es_deducible=False,
                monto_prima=monto_prima,
                monto_deducible=Decimal("0"),
                porcentaje_deducible=Decimal("0"),
                fundamento_legal=f"LISR - {tipo_seguro.value} no deducible para PF",
                tope_global=EstadoTopeGlobal.NO_APLICABLE,
                nota_tope_global="Sin deducción que topar: la prima no es deducible.",
            )

    def _gastos_medicos_persona_fisica(
        self,
        monto_prima: Decimal,
        ingresos_totales_anuales: Decimal | None,
    ) -> ResultadoDeducibilidadPrima:
        """Prima de GMM: fracción VI, sujeta al tope global del último párrafo.

        El tope es el menor entre cinco veces el valor anual de la UMA y el 15%
        del total de los ingresos. Sin el total de ingresos solo puede aplicarse
        la primera rama, y el resultado queda declarado como cota superior.
        """
        tope_uma = self.uma_anual * self.limite_deducciones_umas

        if ingresos_totales_anuales is not None:
            tope_ingresos = ingresos_totales_anuales * _PORCENTAJE_TOPE_GLOBAL
            tope = min(tope_uma, tope_ingresos)
            rama = (
                f"{self.limite_deducciones_umas} UMA anuales"
                if tope == tope_uma
                else "15% del total de ingresos"
            )
            estado_tope = EstadoTopeGlobal.APLICADO
            limite_aplicado = (
                f"Menor de {self.limite_deducciones_umas} UMA anuales "
                f"(${tope_uma:,.2f}) y 15% del total de ingresos "
                f"(${tope_ingresos:,.2f}): ${tope:,.2f}"
            )
            nota = f"Tope global aplicado por la rama de {rama}. {_NOTA_TOPE_ES_GLOBAL}"
        else:
            tope = tope_uma
            estado_tope = EstadoTopeGlobal.PARCIAL_SIN_INGRESOS
            limite_aplicado = (
                f"Solo {self.limite_deducciones_umas} UMA anuales (${tope_uma:,.2f}); "
                f"falta el total de ingresos para evaluar la rama del 15%"
            )
            nota = (
                "Tope global no determinado: sin el total de los ingresos del "
                "contribuyente no puede evaluarse la rama del 15% del último "
                "párrafo del Art. 151 LISR. Solo se aplicó la rama de "
                f"{self.limite_deducciones_umas} UMA anuales, así que el monto "
                f"deducible es una cota superior. {_NOTA_TOPE_ES_GLOBAL}"
            )

        monto_deducible = min(monto_prima, tope)
        return ResultadoDeducibilidadPrima(
            es_deducible=monto_deducible > 0,
            monto_prima=monto_prima,
            monto_deducible=monto_deducible,
            porcentaje_deducible=self._porcentaje(monto_deducible, monto_prima),
            limite_aplicado=limite_aplicado,
            fundamento_legal=(
                "LISR Art. 151, fracc. VI - Primas por seguros de gastos "
                "médicos; tope del último párrafo del mismo artículo"
            ),
            tope_global=estado_tope,
            nota_tope_global=nota,
        )

    def _planes_de_retiro_persona_fisica(
        self,
        monto_prima: Decimal,
        ingreso_anual: Decimal | None,
    ) -> ResultadoDeducibilidadPrima:
        """Aportaciones a planes personales de retiro: fracción V.

        Tope propio: 10% de los ingresos acumulables, sin exceder cinco UMA
        anuales. El último párrafo del artículo excluye expresamente a esta
        fracción del tope global, de modo que aquí no se aplica.
        """
        tope_uma = self.uma_anual * self.limite_deducciones_umas
        tope_ingreso = ingreso_anual * _PORCENTAJE_FRACCION_V if ingreso_anual is not None else None
        tope = min(tope_uma, tope_ingreso) if tope_ingreso is not None else tope_uma
        monto_deducible = min(monto_prima, tope)

        return ResultadoDeducibilidadPrima(
            es_deducible=monto_deducible > 0,
            monto_prima=monto_prima,
            monto_deducible=monto_deducible,
            porcentaje_deducible=self._porcentaje(monto_deducible, monto_prima),
            limite_aplicado=(
                f"Menor de {self.limite_deducciones_umas} UMA anuales "
                f"(${tope_uma:,.2f}) y 10% de los ingresos acumulables "
                f"(${tope_ingreso:,.2f})"
                if tope_ingreso is not None
                else f"{self.limite_deducciones_umas} UMA anuales (${tope_uma:,.2f}); "
                f"falta el ingreso acumulable para evaluar la rama del 10%"
            ),
            fundamento_legal="LISR Art. 151, fracc. V - Planes personales de retiro",
            tope_global=EstadoTopeGlobal.NO_APLICABLE,
            nota_tope_global=(
                "El último párrafo del Art. 151 LISR excluye expresamente a la "
                "fracción V del tope global de deducciones personales; esta "
                "deducción solo está sujeta a su propio tope."
            ),
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
                nota_tope_global=_NOTA_PERSONA_MORAL,
            )

        elif tipo_seguro == TipoSeguroFiscal.DANOS:
            # Seguros de daños sobre activos: deducibles
            return ResultadoDeducibilidadPrima(
                es_deducible=True,
                monto_prima=monto_prima,
                monto_deducible=monto_prima,
                porcentaje_deducible=Decimal("100"),
                fundamento_legal="LISR Art. 25, fracc. VI - Seguros sobre bienes",
                nota_tope_global=_NOTA_PERSONA_MORAL,
            )

        else:
            # Otros seguros empresariales: generalmente deducibles
            return ResultadoDeducibilidadPrima(
                es_deducible=True,
                monto_prima=monto_prima,
                monto_deducible=monto_prima,
                porcentaje_deducible=Decimal("100"),
                fundamento_legal="LISR Art. 25, fracc. VI - Gastos estrictamente indispensables",
                nota_tope_global=_NOTA_PERSONA_MORAL,
            )

    def __repr__(self) -> str:
        return f"ValidadorPrimasDeducibles(UMA_anual=${self.uma_anual:,.2f})"
