"""
Seguro Dotal (Endowment / Seguro Mixto)

El seguro dotal combina protección por fallecimiento con un componente de ahorro.
Paga la suma asegurada en dos escenarios:
1. Si el asegurado MUERE durante el plazo → Paga a beneficiarios
2. Si el asegurado SOBREVIVE al plazo → Paga al asegurado (dotal puro)

Características:
- Doble beneficio: muerte O supervivencia
- Prima más alta que temporal (pago garantizado)
- Usado para ahorro con protección (educación, retiro, compra inmueble)
- Reserva crece hasta la suma asegurada al vencimiento
- Popular en México para planeación financiera
"""

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from suite_actuarial.actuarial.mortality.tablas import TablaMortalidad
from suite_actuarial.actuarial.pricing.vida_pricing import calcular_anualidad
from suite_actuarial.core.base_product import ProductoSeguro, TipoProducto
from suite_actuarial.core.models.common import CalculationMetadata
from suite_actuarial.core.validators import (
    Asegurado,
    ConfiguracionProducto,
    ResultadoCalculo,
    Sexo,
)
from suite_actuarial.pensiones.conmutacion import TablaConmutacion

#: Tolerancia relativa de las verificaciones. Absorbe la diferencia de
#: redondeo entre el motor de bucles y las funciones de conmutación, que
#: acumulan `lx` desde una raíz entera; no absorbe un error de método.
TOLERANCIA_RELATIVA = Decimal("0.0001")


def _diferencia_relativa(
    valor: Decimal,
    referencia: Decimal,
    *,
    escala: Decimal | None = None,
) -> Decimal:
    """Diferencia relativa entre dos importes, escalada para comparar.

    El resultado se compara siempre contra `TOLERANCIA_RELATIVA`, que es una
    tolerancia **relativa**. Por eso no se admite un denominador cero: devolver
    la diferencia absoluta en ese caso la haría pasar por relativa y la
    verificación quedaría comparando pesos contra 1e-4. Cuando la referencia es
    cero (p. ej. la reserva en t=0), pase una `escala` explícita.

    Args:
        valor: Importe calculado
        referencia: Importe del oráculo independiente
        escala: Denominador alterno; obligatorio cuando la referencia es cero
            (p. ej. la suma asegurada, para comparar contra la reserva en t=0)

    Returns:
        |valor - referencia| / denominador

    Raises:
        ValueError: si el denominador es cero, para no devolver en silencio una
            diferencia absoluta donde se espera una relativa
    """
    denominador = escala if escala is not None else abs(referencia)
    if denominador == 0:
        raise ValueError(
            "No se puede calcular una diferencia relativa contra cero: pase una "
            "`escala` explicita (por ejemplo la suma asegurada)."
        )
    return abs(valor - referencia) / denominador


class PuntoReservaDotal(BaseModel):
    """Punto anual de la reserva prospectiva de un seguro dotal."""

    anio: int = Field(..., ge=0)
    edad_alcanzada: int = Field(..., ge=0)
    reserva: Decimal


class VerificacionesDotal(BaseModel):
    """Identidades que hacen auditable un experimento de seguro dotal.

    Cada verificación contrasta el motor de valuación contra una ruta de
    cálculo **independiente**: las funciones de conmutación (Dx/Nx/Mx), que
    llegan al mismo valor por una construcción distinta, o la recursión de
    Fackler, que es retrospectiva mientras la reserva se calcula de forma
    prospectiva. Ninguna compara un valor consigo mismo.
    """

    descomposicion_beneficios: bool
    principio_equivalencia: bool
    reserva_inicial_cero: bool
    reserva_final_igual_beneficio: bool
    recursion_fackler: bool
    diferencia_equivalencia: Decimal = Field(..., ge=0)
    diferencia_descomposicion: Decimal = Field(
        ...,
        ge=0,
        description="Diferencia relativa contra SA*(A_{x:n} temporal + nEx) por conmutación",
    )
    diferencia_recursion: Decimal = Field(
        ...,
        ge=0,
        description="Máxima diferencia relativa en la recursión de Fackler",
    )


class ResultadoAnalisisDotal(BaseModel):
    """Resultado reproducible para construir y examinar un seguro dotal."""

    resultado_prima: ResultadoCalculo
    plazo_pago: int = Field(..., ge=1)
    vp_beneficio_muerte: Decimal = Field(..., ge=0)
    vp_beneficio_supervivencia: Decimal = Field(..., ge=0)
    vp_beneficios_total: Decimal = Field(..., ge=0)
    factor_anualidad_primas: Decimal = Field(..., gt=0)
    prima_neta_anual_equivalente: Decimal = Field(..., gt=0)
    reservas: list[PuntoReservaDotal]
    verificaciones: VerificacionesDotal


class VidaDotal(ProductoSeguro):
    """
    Seguro Dotal (Endowment / Seguro Mixto).

    Combina un seguro temporal con un componente de supervivencia (ahorro).
    Garantiza el pago de la suma asegurada ya sea por muerte o por supervivencia.

    Attributes:
        config: Configuración del producto
        tabla_mortalidad: Tabla de mortalidad a usar
        plazo_pago: Años durante los cuales se paga prima

    Examples:
        >>> from suite_actuarial.actuarial.mortality.tablas import TablaMortalidad
        >>> from suite_actuarial.core.validators import *
        >>> from decimal import Decimal
        >>>
        >>> # Dotal a 20 años para educación universitaria
        >>> tabla = TablaMortalidad.cargar_emssa09()
        >>> config = ConfiguracionProducto(
        ...     nombre_producto="Dotal Educativo 20 años",
        ...     plazo_years=20,
        ...     tasa_interes_tecnico=Decimal("0.055")
        ... )
        >>>
        >>> producto = VidaDotal(config, tabla)
        >>>
        >>> # Asegurado: padre de 30 años, ahorra para hijo
        >>> asegurado = Asegurado(
        ...     edad=30,
        ...     sexo=Sexo.MASCULINO,
        ...     suma_asegurada=Decimal("500000")  # 500K para universidad
        ... )
        >>>
        >>> resultado = producto.calcular_prima(asegurado)
        >>> print(f"Prima anual 20 años: ${resultado.prima_total:,.2f}")
        >>> print(f"Garantiza $500,000 en 20 años (vivo o fallecido)")
    """

    def __init__(
        self,
        config: ConfiguracionProducto,
        tabla_mortalidad: TablaMortalidad,
        plazo_pago: int | None = None,
    ):
        """
        Inicializa un seguro dotal.

        Args:
            config: Configuración del producto
            tabla_mortalidad: Tabla de mortalidad
            plazo_pago: Plazo de pago de primas (default = plazo del seguro)

        Note:
            Típicamente plazo_pago = plazo del seguro, pero puede ser menor
            (ej: pago 10 años, cobertura 20 años)
        """
        super().__init__(config, TipoProducto.VIDA_DOTAL)
        self.tabla_mortalidad = tabla_mortalidad
        self.plazo_pago = config.plazo_years if plazo_pago is None else plazo_pago

        if self.plazo_pago < 1:
            raise ValueError("El plazo de pago debe ser al menos 1 anio")

        if self.plazo_pago > config.plazo_years:
            raise ValueError(
                f"Plazo de pago ({self.plazo_pago}) no puede ser mayor "
                f"al plazo del seguro ({config.plazo_years})"
            )

    def calcular_prima(
        self,
        asegurado: Asegurado,
        frecuencia_pago: str = "anual",
        **kwargs: Any,
    ) -> ResultadoCalculo:
        """
        Calcula la prima para un seguro dotal.

        El dotal se descompone en:
        1. Componente de muerte: Temporal a n años
        2. Componente de supervivencia: Dotal puro (paga si sobrevive)

        Prima Dotal = Prima Temporal + Prima Dotal Puro

        Técnicamente: A^1_x:n (muerte) + A^1_x:n (supervivencia) = A_x:n

        Args:
            asegurado: Datos del asegurado
            frecuencia_pago: "anual", "mensual", "semestral", "trimestral"
            **kwargs: Parámetros adicionales

        Returns:
            ResultadoCalculo con prima neta, prima total y desglose

        Raises:
            ValueError: Si el asegurado no es asegurable

        Examples:
            >>> resultado = producto.calcular_prima(asegurado)
            >>> print(f"Prima anual: ${resultado.prima_total:,.2f}")
            >>> print(f"Paga $500,000 en 20 años (garantizado)")
        """
        # Validar asegurabilidad
        es_asegurable, razon = self.validar_asegurabilidad(asegurado)
        if not es_asegurable:
            raise ValueError(f"Asegurado no es asegurable: {razon}")

        # Calcular valor presente del seguro dotal
        # Fórmula: A_x:n = Componente Muerte + Componente Supervivencia
        axn = self._calcular_seguro_dotal(
            edad=asegurado.edad,
            sexo=asegurado.sexo,
            plazo=self.config.plazo_years,
            suma_asegurada=asegurado.suma_asegurada,
        )

        # Valor presente de los pagos de prima
        axm = calcular_anualidad(
            tabla=self.tabla_mortalidad,
            edad=asegurado.edad,
            sexo=asegurado.sexo,
            plazo=self.plazo_pago,
            tasa_interes=self.config.tasa_interes_tecnico,
            pago_anticipado=True,
        )

        # Prima neta = Beneficio / Pagos
        prima_neta = axn / axm

        # Ajustar por frecuencia
        factor_frecuencia = self._obtener_factor_frecuencia(frecuencia_pago)
        prima_neta_ajustada = prima_neta * factor_frecuencia

        # Aplicar recargos
        prima_total, desglose = self.aplicar_recargos(prima_neta_ajustada)

        return ResultadoCalculo(
            prima_neta=prima_neta_ajustada,
            prima_total=prima_total,
            moneda=self.config.moneda,
            desglose_recargos=desglose,
            metadata={
                "producto": self.config.nombre_producto,
                "tipo": "vida_dotal",
                "plazo_seguro": self.config.plazo_years,
                "plazo_pago": self.plazo_pago,
                "frecuencia_pago": frecuencia_pago,
                "tabla_mortalidad": self.tabla_mortalidad.nombre,
                "tasa_interes": str(self.config.tasa_interes_tecnico),
                "edad": asegurado.edad,
                "sexo": asegurado.sexo.value,
                "componentes": "muerte + supervivencia",
            },
            calculation_metadata=CalculationMetadata(
                validation_tier="experimental"
                if self.tabla_mortalidad.metadata.get("data_status") == "illustrative"
                else "supported",
                sources=[
                    self.tabla_mortalidad.metadata.get("source", self.tabla_mortalidad.nombre)
                ],
                assumptions_snapshot={"tabla_mortalidad": self.tabla_mortalidad.nombre},
            ),
        )

    def _calcular_seguro_dotal(
        self,
        edad: int,
        sexo: Sexo,
        plazo: int,
        suma_asegurada: Decimal,
    ) -> Decimal:
        """
        Calcula el valor presente del seguro dotal.

        Dotal = Muerte durante plazo + Supervivencia al final

        Componente Muerte: Σ(v^(t+1) * t_p_x * q_(x+t)) para t=0...n-1
        Componente Supervivencia: v^n * n_p_x

        Args:
            edad: Edad del asegurado
            sexo: Sexo del asegurado
            plazo: Plazo del seguro
            suma_asegurada: Suma asegurada

        Returns:
            Valor presente actuarial del dotal
        """
        vp_muerte, vp_supervivencia = self._calcular_componentes_beneficio(
            edad=edad,
            sexo=sexo,
            plazo=plazo,
            suma_asegurada=suma_asegurada,
        )
        return vp_muerte + vp_supervivencia

    def _calcular_componentes_beneficio(
        self,
        edad: int,
        sexo: Sexo,
        plazo: int,
        suma_asegurada: Decimal,
    ) -> tuple[Decimal, Decimal]:
        """Calcula por separado los VP de muerte y supervivencia."""
        v = Decimal("1") / (Decimal("1") + self.config.tasa_interes_tecnico)

        # Componente 1: Muerte durante el plazo (igual que temporal)
        vp_muerte = Decimal("0")
        prob_supervivencia = Decimal("1")

        for t in range(plazo):
            edad_actual = edad + t
            qx = self.tabla_mortalidad.obtener_qx(edad_actual, sexo, interpolar=True)

            # Muerte en año t+1
            factor_descuento = v ** (t + 1)
            componente = factor_descuento * prob_supervivencia * qx
            vp_muerte += componente

            # Actualizar supervivencia
            prob_supervivencia *= Decimal("1") - qx

        # Componente 2: Supervivencia al final del plazo
        # v^n * n_p_x (prob de sobrevivir n años)
        factor_descuento_final = v**plazo
        vp_supervivencia = factor_descuento_final * prob_supervivencia

        return vp_muerte * suma_asegurada, vp_supervivencia * suma_asegurada

    def analizar_producto(
        self,
        asegurado: Asegurado,
        frecuencia_pago: str = "anual",
    ) -> ResultadoAnalisisDotal:
        """Construye un análisis completo y verificable del producto.

        Args:
            asegurado: Perfil y suma asegurada del contrato.
            frecuencia_pago: Frecuencia usada para presentar la prima.

        Returns:
            Descomposición de beneficios, prima, reservas e identidades.
        """
        resultado_prima = self.calcular_prima(
            asegurado,
            frecuencia_pago=frecuencia_pago,
        )
        vp_muerte, vp_supervivencia = self._calcular_componentes_beneficio(
            edad=asegurado.edad,
            sexo=asegurado.sexo,
            plazo=self.config.plazo_years,
            suma_asegurada=asegurado.suma_asegurada,
        )
        vp_total = vp_muerte + vp_supervivencia
        factor_anualidad = calcular_anualidad(
            tabla=self.tabla_mortalidad,
            edad=asegurado.edad,
            sexo=asegurado.sexo,
            plazo=self.plazo_pago,
            tasa_interes=self.config.tasa_interes_tecnico,
            pago_anticipado=True,
        )
        prima_neta_anual = vp_total / factor_anualidad

        # Oráculo 1 — conmutación. Ruta de cálculo independiente del motor de
        # bucles de `vida_pricing`: A_{x:n̄}^1 = (M_x - M_{x+n})/D_x para la
        # parte de muerte y nEx = D_{x+n}/D_x para el dotal puro.
        tc = TablaConmutacion(
            tabla_mortalidad=self.tabla_mortalidad,
            sexo=asegurado.sexo,
            tasa_interes=self.config.tasa_interes_tecnico,
        )
        vp_total_conmutacion = asegurado.suma_asegurada * (
            tc.Ax(asegurado.edad, self.config.plazo_years)
            + tc.nEx(asegurado.edad, self.config.plazo_years)
        )
        diferencia_descomposicion = _diferencia_relativa(vp_total, vp_total_conmutacion)

        # Oráculo 2 — principio de equivalencia sobre la salida real del motor
        # de pricing. La prima que se contrasta es la que devuelve
        # `calcular_prima`, no `vp_total / factor_anualidad`, que sería el mismo
        # número dividido y vuelto a multiplicar.
        prima_neta_motor = resultado_prima.prima_neta / self._obtener_factor_frecuencia(
            frecuencia_pago
        )
        diferencia_equivalencia = abs(prima_neta_motor * factor_anualidad - vp_total)

        reservas = [
            PuntoReservaDotal(
                anio=anio,
                edad_alcanzada=asegurado.edad + anio,
                reserva=self.calcular_reserva(asegurado, anio),
            )
            for anio in range(self.config.plazo_years + 1)
        ]

        # Oráculo 3 — recursión de Fackler (Bowers et al., cap. 7). Relación
        # retrospectiva entre reservas consecutivas:
        #     tV + P = v * [q_{x+t} * SA + p_{x+t} * (t+1)V]
        # Las reservas se calculan de forma prospectiva, así que la recursión es
        # una ruta distinta y puede fallar.
        diferencia_recursion = self._verificar_recursion_fackler(
            asegurado=asegurado,
            reservas=[punto.reserva for punto in reservas],
            prima_neta_anual=prima_neta_motor,
        )

        return ResultadoAnalisisDotal(
            resultado_prima=resultado_prima,
            plazo_pago=self.plazo_pago,
            vp_beneficio_muerte=vp_muerte,
            vp_beneficio_supervivencia=vp_supervivencia,
            vp_beneficios_total=vp_total,
            factor_anualidad_primas=factor_anualidad,
            prima_neta_anual_equivalente=prima_neta_anual,
            reservas=reservas,
            verificaciones=VerificacionesDotal(
                descomposicion_beneficios=diferencia_descomposicion <= TOLERANCIA_RELATIVA,
                principio_equivalencia=diferencia_equivalencia <= Decimal("0.01"),
                # La reserva prospectiva llega a estos valores por sí sola: los
                # atajos que los devolvían como constantes fueron eliminados.
                reserva_inicial_cero=(
                    _diferencia_relativa(
                        reservas[0].reserva, Decimal("0"), escala=asegurado.suma_asegurada
                    )
                    <= TOLERANCIA_RELATIVA
                ),
                reserva_final_igual_beneficio=(
                    _diferencia_relativa(reservas[-1].reserva, asegurado.suma_asegurada)
                    <= TOLERANCIA_RELATIVA
                ),
                recursion_fackler=diferencia_recursion <= TOLERANCIA_RELATIVA,
                diferencia_equivalencia=diferencia_equivalencia,
                diferencia_descomposicion=diferencia_descomposicion,
                diferencia_recursion=diferencia_recursion,
            ),
        )

    def _verificar_recursion_fackler(
        self,
        asegurado: Asegurado,
        reservas: list[Decimal],
        prima_neta_anual: Decimal,
    ) -> Decimal:
        """Máxima diferencia relativa en la recursión de Fackler.

        Identidad (Bowers et al., *Actuarial Mathematics*, cap. 7):

            (ₜV + P) * (1 + i) = q_{x+t} * SA + p_{x+t} * ₜ₊₁V

        Es una relación **retrospectiva** entre reservas consecutivas: la
        reserva del año t más la prima, capitalizada un año, debe alcanzar
        exactamente para pagar a los que mueren y constituir la reserva del año
        siguiente para los que sobreviven. Las reservas de este producto se
        calculan de forma **prospectiva** (`A - P·ä`), así que la recursión es
        una ruta de cálculo distinta y puede detectar un error.

        La prima solo se suma mientras haya pagos pendientes (t < plazo_pago).

        Args:
            asegurado: Perfil y suma asegurada del contrato
            reservas: Reservas anuales, de t=0 a t=n
            prima_neta_anual: Prima neta anual del motor de pricing

        Returns:
            Máxima diferencia relativa observada sobre todos los años
        """
        i = self.config.tasa_interes_tecnico
        suma_asegurada = asegurado.suma_asegurada
        maxima = Decimal("0")

        for t in range(len(reservas) - 1):
            edad_t = asegurado.edad + t
            qx = self.tabla_mortalidad.obtener_qx(edad_t, asegurado.sexo)
            px = Decimal("1") - qx

            prima = prima_neta_anual if t < self.plazo_pago else Decimal("0")
            izquierda = (reservas[t] + prima) * (Decimal("1") + i)
            derecha = qx * suma_asegurada + px * reservas[t + 1]

            maxima = max(
                maxima,
                _diferencia_relativa(izquierda, derecha, escala=suma_asegurada),
            )

        return maxima

    def calcular_reserva(
        self,
        asegurado: Asegurado,
        anio: int,
        **kwargs: Any,
    ) -> Decimal:
        """
        Calcula la reserva matemática en un año dado.

        Para un dotal, la reserva crece continuamente y alcanza exactamente
        la suma asegurada al vencimiento (porque se paga con certeza).

        Fórmula: V_t = A_(x+t):(n-t) - P * ä_(x+t):(m-t)

        Args:
            asegurado: Datos del asegurado
            anio: Año de la póliza (0 = inicio)
            **kwargs: Parámetros adicionales

        Returns:
            Monto de la reserva matemática

        Raises:
            ValueError: Si el año está fuera del plazo

        Examples:
            >>> # Reserva crece hasta suma asegurada
            >>> for anio in [0, 5, 10, 15, 20]:
            ...     r = producto.calcular_reserva(asegurado, anio)
            ...     print(f"Año {anio}: ${r:,.2f}")
        """
        if anio < 0 or anio > self.config.plazo_years:
            raise ValueError(f"Año {anio} fuera de rango [0, {self.config.plazo_years}]")

        # No hay atajos en t=0 ni en t=n. Antes se devolvían 0 y la suma
        # asegurada como constantes, lo que hacía que dos de las cuatro
        # `verificaciones` fueran ciertas por construcción (hallazgo A9). La
        # fórmula prospectiva produce ambos valores por sí sola: en t=0 por el
        # principio de equivalencia, y en t=n porque el dotal a plazo 0 vale la
        # suma asegurada y ya no quedan primas.
        edad_actual = asegurado.edad + anio
        plazo_restante = self.config.plazo_years - anio

        # Valor del seguro dotal restante
        axn_futuro = self._calcular_seguro_dotal(
            edad=edad_actual,
            sexo=asegurado.sexo,
            plazo=plazo_restante,
            suma_asegurada=asegurado.suma_asegurada,
        )

        # Plazo de pago restante
        plazo_pago_restante = max(0, self.plazo_pago - anio)

        # Si ya no hay pagos, reserva = beneficio futuro
        if plazo_pago_restante == 0:
            return axn_futuro

        # Valor de primas futuras
        axm_futuro = calcular_anualidad(
            tabla=self.tabla_mortalidad,
            edad=edad_actual,
            sexo=asegurado.sexo,
            plazo=plazo_pago_restante,
            tasa_interes=self.config.tasa_interes_tecnico,
            pago_anticipado=True,
        )

        # Prima neta original
        resultado = self.calcular_prima(asegurado, frecuencia_pago="anual")
        prima_neta = resultado.prima_neta

        # Reserva
        reserva = axn_futuro - (prima_neta * axm_futuro)

        return reserva

    def validar_asegurabilidad(
        self,
        asegurado: Asegurado,
    ) -> tuple[bool, str | None]:
        """
        Valida asegurabilidad específica para dotal.

        Args:
            asegurado: Datos del asegurado

        Returns:
            (es_asegurable, razon_rechazo)
        """
        # Validación base
        es_asegurable, razon = super().validar_asegurabilidad(asegurado)
        if not es_asegurable:
            return False, razon

        # Edad + plazo no debe exceder edad razonable
        edad_vencimiento = asegurado.edad + self.config.plazo_years

        if edad_vencimiento > 90:
            return (
                False,
                f"Edad al vencimiento ({edad_vencimiento}) excede límite (90)",
            )

        # Para dotales cortos (< 5 años), puede haber restricciones
        if self.config.plazo_years < 5:
            return (
                False,
                "Plazo mínimo para dotales es 5 años (evitar anti-selección)",
            )

        return True, None

    def _obtener_factor_frecuencia(self, frecuencia: str) -> Decimal:
        """Obtiene factor de conversión para frecuencias de pago.

        Delegates to the shared implementation in vida_pricing, passing
        this product's technical interest rate.
        """
        from suite_actuarial.actuarial.pricing.vida_pricing import _obtener_factor_frecuencia

        return _obtener_factor_frecuencia(frecuencia, self.config.tasa_interes_tecnico)

    def __repr__(self) -> str:
        """Representación en string"""
        return (
            f"VidaDotal("
            f"plazo={self.config.plazo_years} años, "
            f"pago={self.plazo_pago} años, "
            f"tabla={self.tabla_mortalidad.nombre})"
        )
