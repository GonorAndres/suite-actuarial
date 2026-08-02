"""
Reserva Matemática prospectiva de primas netas para seguros de vida.

Qué problema resuelve. Una póliza de largo plazo cobra una prima nivelada: en
los primeros años la prima excede el costo del riesgo y en los últimos se queda
corta. La reserva matemática es el fondo que sostiene esa diferencia. El método
prospectivo la mide como lo que falta por pagar menos lo que falta por cobrar:

    ₜV = SA · A_{x+t : n-t}  -  P · ä_{x+t : m-t}

donde `x` es la edad de contratación, `t` la duración transcurrida, `n` el plazo
de cobertura, `m` el plazo de pago de primas, `A` el valor presente actuarial
del beneficio por fallecimiento y `ä` el de una anualidad anticipada.

Qué se asume. La mortalidad viene de una `TablaMortalidad` (por omisión la
EMSSA-09 empaquetada, declarada `illustrative` en sus metadatos) leída por sexo,
y la edad terminal ω es la última edad de la tabla para ese sexo, donde se
fuerza q_ω = 1 con la convención auditada de `vida_pricing`. El interés técnico
es plano. No hay caducidad, ni rescates, ni gastos.

Qué NO es. No es un cálculo conforme a la Circular S-11.4. Está orientado a
ella, pero la reserva institucional se calcula con la mejor estimación de la
nota técnica registrada, prima de tarifa (no neta), gastos, caducidad y margen
de riesgo. Este módulo entrega la pieza pedagógica, con su aviso
(`DISCLAIMER_RM`) dentro del propio resultado.

De dónde sale la aritmética. No se reimplementa la matemática de supervivencia:
`A` y `ä` se calculan con `actuarial.pricing.vida_pricing`, que es la maquinaria
auditada del proyecto (hallazgo A7 de `docs/AUDIT.md` para la edad terminal), la
misma que sostiene `vida/dotal.py`.

Historial. La versión anterior de este módulo declaraba conformidad con S-11.4 y
calculaba otra cosa: usaba la probabilidad de supervivencia de UN año como si
cubriera todo el plazo remanente, consultaba siempre mortalidad masculina, fijaba
ω = 85 y fin de primas a los 65 sin fuente, y caía en una ley de supervivencia
`exp(-0.00008·x²)` sin cita cuando no había tabla. Ninguna de esas piezas
sobrevive.
"""

from __future__ import annotations

import warnings
from decimal import Decimal
from typing import TYPE_CHECKING

from suite_actuarial.actuarial.pricing.vida_pricing import (
    _qx_con_edad_terminal,
    calcular_anualidad,
    calcular_seguro_vida,
)
from suite_actuarial.core.warnings import ExperimentalModelWarning
from suite_actuarial.regulatorio.reservas_tecnicas.models import (
    DISCLAIMER_RM,
    ConfiguracionRM,
    ResultadoRM,
)

if TYPE_CHECKING:
    from suite_actuarial.actuarial.mortality.tablas import TablaMortalidad

#: Redondeo de importes monetarios publicados.
CENTAVO = Decimal("0.01")


class CalculadoraRM:
    """
    Calcula la reserva matemática prospectiva de primas netas.

    Cubre dos contratos:

    - **Seguro de vida con beneficio por fallecimiento**. Temporal a `n` años
      con primas pagaderas `m` años. Un vitalicio se expresa como el temporal
      que llega a la edad terminal de la tabla, donde q_ω = 1 hace que el
      beneficio se pague con certeza.
    - **Renta vitalicia en curso de pago**. La reserva es el valor presente de
      los pagos restantes: no hay primas futuras.

    Al construirse emite `ExperimentalModelWarning` con `DISCLAIMER_RM`, y el
    mismo aviso viaja dentro de `ResultadoRM.disclaimer`.

    Args:
        config: Contrato a valuar.
        tabla_mortalidad: Tabla de mortalidad. Es obligatoria: no hay ley de
            supervivencia de respaldo, porque una reserva calculada con una
            curva sin fuente no es una reserva.

    Ejemplo:
        >>> from decimal import Decimal
        >>> from suite_actuarial.actuarial.mortality.tablas import TablaMortalidad
        >>> from suite_actuarial.core.models.common import Sexo
        >>> tabla = TablaMortalidad.cargar_emssa09()
        >>> config = ConfiguracionRM(
        ...     suma_asegurada=Decimal("1000000"),
        ...     edad_contratacion=40,
        ...     edad_asegurado=45,
        ...     sexo=Sexo.MASCULINO,
        ...     plazo_seguro_anios=20,
        ...     tasa_interes_tecnico=Decimal("0.055"),
        ... )
        >>> resultado = CalculadoraRM(config, tabla).calcular()
        >>> print(f"RM: ${resultado.reserva_matematica:,.2f}")
    """

    def __init__(
        self,
        config: ConfiguracionRM,
        tabla_mortalidad: TablaMortalidad,
    ) -> None:
        self.config = config
        self.tabla_mortalidad = tabla_mortalidad
        self.edad_terminal = self._determinar_edad_terminal()

        if config.edad_asegurado > self.edad_terminal:
            raise ValueError(
                f"La edad alcanzada ({config.edad_asegurado}) excede la edad terminal de "
                f"la tabla {tabla_mortalidad.nombre} para sexo={config.sexo.value} "
                f"({self.edad_terminal}): no hay mortalidad que aplicar."
            )

        warnings.warn(DISCLAIMER_RM, ExperimentalModelWarning, stacklevel=2)

    # ------------------------------------------------------------------
    # Supuestos derivados de la tabla
    # ------------------------------------------------------------------

    def _determinar_edad_terminal(self) -> int:
        """ω: última edad publicada por la tabla para el sexo del asegurado.

        La edad terminal no es un parámetro del modelo sino un dato de la tabla
        cargada. Fijarla a mano (la versión anterior usaba 85) hace que la
        reserva dependa de un número sin fuente. En ω se fuerza q = 1 con la
        convención auditada, de modo que ninguna cohorte residual queda viva sin
        fondear su beneficio.

        Returns:
            Edad terminal de la tabla para el sexo configurado.

        Raises:
            ValueError: Si la tabla no tiene registros para ese sexo.
        """
        datos = self.tabla_mortalidad.obtener_tabla_completa(self.config.sexo)
        if datos.empty:
            raise ValueError(
                f"La tabla {self.tabla_mortalidad.nombre} no tiene registros para "
                f"sexo={self.config.sexo.value}."
            )
        return int(datos["edad"].max())

    # ------------------------------------------------------------------
    # Componentes actuariales
    # ------------------------------------------------------------------

    def _vp_beneficio_fallecimiento(self, edad: int, plazo: int) -> Decimal:
        """SA · A_{edad:plazo}, con la convención de edad terminal.

        Args:
            edad: Edad alcanzada desde la que se valúa.
            plazo: Años de cobertura restantes.

        Returns:
            Valor presente actuarial del beneficio por fallecimiento.
        """
        if plazo <= 0 or self.config.suma_asegurada is None:
            return Decimal("0")
        return calcular_seguro_vida(
            tabla=self.tabla_mortalidad,
            edad=edad,
            sexo=self.config.sexo,
            plazo=plazo,
            tasa_interes=self.config.tasa_interes_tecnico,
            suma_asegurada=self.config.suma_asegurada,
            edad_terminal=self.edad_terminal,
        )

    def _factor_anualidad(self, edad: int, plazo: int) -> Decimal:
        """ä_{edad:plazo} anticipada, con la misma convención de edad terminal.

        Las dos piernas del contrato comparten ω a propósito: si el beneficio
        cierra en la edad terminal y la anualidad no, el principio de
        equivalencia deja de sostenerse.

        Args:
            edad: Edad alcanzada desde la que se valúa.
            plazo: Número de pagos pendientes.

        Returns:
            Valor presente de una anualidad anticipada de 1 por año.
        """
        if plazo <= 0:
            return Decimal("0")
        return calcular_anualidad(
            tabla=self.tabla_mortalidad,
            edad=edad,
            sexo=self.config.sexo,
            plazo=plazo,
            tasa_interes=self.config.tasa_interes_tecnico,
            pago_anticipado=True,
            edad_terminal=self.edad_terminal,
        )

    def _probabilidad_supervivencia(self, edad: int, anios: int) -> Decimal:
        """ₙp_x: probabilidad de sobrevivir `anios` desde `edad`.

        Producto de las probabilidades anuales de supervivencia, tomando cada
        q con la misma convención de edad terminal que usan `A` y `ä`. No es un
        supuesto nuevo: es la lectura de la tabla que ya hacen esas funciones.

        Args:
            edad: Edad inicial.
            anios: Número de años.

        Returns:
            Probabilidad de supervivencia acumulada.
        """
        prob = Decimal("1")
        for t in range(max(anios, 0)):
            qx = _qx_con_edad_terminal(
                self.tabla_mortalidad, edad + t, self.config.sexo, self.edad_terminal
            )
            prob *= Decimal("1") - qx
        return prob

    def prima_neta_anual(self) -> tuple[Decimal, bool]:
        """Prima nivelada anual del contrato y su origen.

        Si la configuración trae `prima_nivelada_anual`, esa es la prima del
        contrato y se usa tal cual: la reserva de una póliza en vigor se calcula
        con la prima que efectivamente se cobra. Si no viene, se determina por
        el principio de equivalencia **a la edad de contratación**, que es donde
        el contrato se equilibró:

            P = SA · A_{x:n} / ä_{x:m}

        Returns:
            (prima anual, True si se determinó por equivalencia)

        Raises:
            ValueError: Si el contrato no admite primas (ä = 0) y no se
                suministró una prima explícita.
        """
        if self.config.prima_nivelada_anual is not None:
            return self.config.prima_nivelada_anual, False

        plazo_seguro = self.config.plazo_seguro_anios
        plazo_pago = self.config.plazo_pago_anios
        if plazo_seguro is None or plazo_pago is None:  # pragma: no cover - validado en el modelo
            raise ValueError("El contrato no declara plazos: no se puede aplicar equivalencia.")

        edad_emision = self.config.edad_contratacion
        anualidad_emision = self._factor_anualidad(edad_emision, plazo_pago)
        if anualidad_emision == 0:
            raise ValueError(
                "El factor de anualidad a la contratación es cero: no se puede determinar "
                "la prima por equivalencia. Suministre `prima_nivelada_anual`."
            )
        beneficio_emision = self._vp_beneficio_fallecimiento(edad_emision, plazo_seguro)
        return beneficio_emision / anualidad_emision, True

    # ------------------------------------------------------------------
    # Cálculo
    # ------------------------------------------------------------------

    def calcular(self) -> ResultadoRM:
        """Calcula la reserva matemática prospectiva.

        Returns:
            `ResultadoRM` con la reserva, sus dos componentes, la prima usada y
            los supuestos que la fijan (tabla, sexo, edad terminal).
        """
        if self.config.es_renta_vitalicia:
            return self._calcular_renta_vitalicia()
        return self._calcular_seguro_vida()

    def _calcular_seguro_vida(self) -> ResultadoRM:
        """ₜV = SA · A_{x+t:n-t} - P · ä_{x+t:m-t}."""
        plazo_seguro = self.config.plazo_seguro_anios
        plazo_pago = self.config.plazo_pago_anios
        if plazo_seguro is None or plazo_pago is None:  # pragma: no cover - validado en el modelo
            raise ValueError("El contrato no declara plazos de cobertura y pago.")

        duracion = self.config.duracion_transcurrida
        edad_actual = self.config.edad_asegurado
        plazo_restante = max(plazo_seguro - duracion, 0)
        pagos_restantes = max(plazo_pago - duracion, 0)

        prima, por_equivalencia = self.prima_neta_anual()

        vp_beneficios = self._vp_beneficio_fallecimiento(edad_actual, plazo_restante)
        anualidad = self._factor_anualidad(edad_actual, pagos_restantes)
        vp_primas = prima * anualidad

        reserva = vp_beneficios - vp_primas

        return ResultadoRM(
            reserva_matematica=reserva.quantize(CENTAVO),
            reserva_a_constituir=max(reserva, Decimal("0")).quantize(CENTAVO),
            valor_presente_beneficios=vp_beneficios.quantize(CENTAVO),
            valor_presente_primas=vp_primas.quantize(CENTAVO),
            prima_neta_anual=prima.quantize(CENTAVO),
            factor_anualidad_primas=anualidad,
            edad_actuarial=edad_actual,
            duracion_transcurrida=duracion,
            sexo=self.config.sexo,
            tabla_mortalidad=self.tabla_mortalidad.nombre,
            edad_terminal_tabla=self.edad_terminal,
            probabilidad_supervivencia_plazo=self._probabilidad_supervivencia(
                edad_actual, plazo_restante
            ),
            prima_determinada_por_equivalencia=por_equivalencia,
            disclaimer=DISCLAIMER_RM,
        )

    def _calcular_renta_vitalicia(self) -> ResultadoRM:
        """Reserva de una renta vitalicia en curso: VP de los pagos restantes.

        No hay primas futuras, así que la reserva es el valor presente del
        beneficio: ₜV = 12 · renta_mensual · ä_x, con ä anual anticipada hasta
        la edad terminal.

        Simplificación declarada: la renta se paga mensualmente pero se valúa
        como anual anticipada. Eso sobreestima el valor presente (la corrección
        de Woolhouse resta ≈ 11/24 de un pago anual), de modo que el sesgo es
        conservador para la reserva. Para una valuación de rentas con
        fraccionamiento explícito use `pensiones.renta_vitalicia`, que sí aplica
        el ajuste.
        """
        monto_mensual = self.config.monto_renta_mensual
        if monto_mensual is None:  # pragma: no cover - validado en el modelo
            raise ValueError("Se requiere monto_renta_mensual para rentas vitalicias")

        edad_actual = self.config.edad_asegurado
        renta_anual = monto_mensual * 12
        pagos_restantes = self.edad_terminal - edad_actual + 1

        anualidad = self._factor_anualidad(edad_actual, pagos_restantes)
        vp_beneficios = renta_anual * anualidad

        return ResultadoRM(
            reserva_matematica=vp_beneficios.quantize(CENTAVO),
            reserva_a_constituir=vp_beneficios.quantize(CENTAVO),
            valor_presente_beneficios=vp_beneficios.quantize(CENTAVO),
            valor_presente_primas=Decimal("0.00"),
            prima_neta_anual=Decimal("0.00"),
            factor_anualidad_primas=Decimal("0"),
            edad_actuarial=edad_actual,
            duracion_transcurrida=self.config.duracion_transcurrida,
            sexo=self.config.sexo,
            tabla_mortalidad=self.tabla_mortalidad.nombre,
            edad_terminal_tabla=self.edad_terminal,
            probabilidad_supervivencia_plazo=None,
            prima_determinada_por_equivalencia=False,
            disclaimer=DISCLAIMER_RM,
        )

    def __repr__(self) -> str:
        return (
            f"CalculadoraRM("
            f"edad={self.config.edad_asegurado}, "
            f"sexo={self.config.sexo.value}, "
            f"tabla={self.tabla_mortalidad.nombre}, "
            f"omega={self.edad_terminal})"
        )
