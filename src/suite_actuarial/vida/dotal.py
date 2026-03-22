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

from suite_actuarial.actuarial.mortality.tablas import TablaMortalidad
from suite_actuarial.actuarial.pricing.vida_pricing import calcular_anualidad
from suite_actuarial.core.base_product import ProductoSeguro, TipoProducto
from suite_actuarial.core.validators import (
    Asegurado,
    ConfiguracionProducto,
    ResultadoCalculo,
)


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
        ...     sexo=Sexo.HOMBRE,
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
        self.plazo_pago = plazo_pago or config.plazo_years

        if self.plazo_pago > config.plazo_years:
            raise ValueError(
                f"Plazo de pago ({self.plazo_pago}) no puede ser mayor "
                f"al plazo del seguro ({config.plazo_years})"
            )

    def calcular_prima(
        self,
        asegurado: Asegurado,
        frecuencia_pago: str = "anual",
        **kwargs: dict,
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
        )

    def _calcular_seguro_dotal(
        self,
        edad: int,
        sexo,
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

        # Total = Muerte + Supervivencia
        vp_total = (vp_muerte + vp_supervivencia) * suma_asegurada

        return vp_total

    def calcular_reserva(
        self,
        asegurado: Asegurado,
        anio: int,
        **kwargs: dict,
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
            raise ValueError(
                f"Año {anio} fuera de rango [0, {self.config.plazo_years}]"
            )

        # Al inicio, reserva = 0
        if anio == 0:
            return Decimal("0")

        # Al vencimiento, reserva = suma asegurada (pago garantizado)
        if anio == self.config.plazo_years:
            return asegurado.suma_asegurada

        # Años intermedios
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
        """Obtiene factor de conversión para frecuencias de pago"""
        factores = {
            "anual": Decimal("1.00"),
            "semestral": Decimal("0.51"),
            "trimestral": Decimal("0.26"),
            "mensual": Decimal("0.087"),
        }

        if frecuencia not in factores:
            raise ValueError(
                f"Frecuencia '{frecuencia}' no soportada. "
                f"Usa una de: {list(factores.keys())}"
            )

        return factores[frecuencia]

    def __repr__(self) -> str:
        """Representación en string"""
        return (
            f"VidaDotal("
            f"plazo={self.config.plazo_years} años, "
            f"pago={self.plazo_pago} años, "
            f"tabla={self.tabla_mortalidad.nombre})"
        )
