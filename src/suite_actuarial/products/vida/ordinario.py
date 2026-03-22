"""
Seguro de Vida Ordinario (Vida Entera / Whole Life)

Este producto proporciona cobertura durante toda la vida del asegurado.
A diferencia del temporal, el pago del beneficio está GARANTIZADO - solo
es cuestión de cuándo, no de si.

Características:
- Cobertura vitalicia (hasta edad omega, típicamente 99-100 años)
- Pago de suma asegurada al fallecimiento (garantizado)
- Prima nivelada durante el periodo de pago
- Reserva matemática crece hasta alcanzar la suma asegurada
- Usado para planeación patrimonial y sucesoria
"""

from decimal import Decimal

from suite_actuarial.actuarial.mortality.tablas import TablaMortalidad
from suite_actuarial.actuarial.pricing.vida_pricing import (
    calcular_anualidad,
    calcular_seguro_vida,
)
from suite_actuarial.core.base_product import ProductoSeguro, TipoProducto
from suite_actuarial.core.validators import (
    Asegurado,
    ConfiguracionProducto,
    ResultadoCalculo,
)


class VidaOrdinario(ProductoSeguro):
    """
    Seguro de Vida Ordinario (Whole Life).

    Proporciona cobertura de fallecimiento durante toda la vida del asegurado.
    El beneficio está garantizado, solo es cuestión de cuándo se pagará.

    Attributes:
        config: Configuración del producto (plazo_years se usa para periodo de pago)
        tabla_mortalidad: Tabla de mortalidad a usar
        edad_omega: Edad final de la tabla (típicamente 100)
        plazo_pago: Años durante los cuales se paga prima

    Examples:
        >>> from suite_actuarial.actuarial.mortality.tablas import TablaMortalidad
        >>> from suite_actuarial.core.validators import *
        >>> from decimal import Decimal
        >>>
        >>> # Cargar tabla
        >>> tabla = TablaMortalidad.cargar_emssa09()
        >>>
        >>> # Configurar producto - plazo_years = años de pago de prima
        >>> config = ConfiguracionProducto(
        ...     nombre_producto="Vida Ordinario - Pago Limitado 20 años",
        ...     plazo_years=20,  # Paga prima solo 20 años
        ...     tasa_interes_tecnico=Decimal("0.055")
        ... )
        >>>
        >>> # Crear producto
        >>> producto = VidaOrdinario(config, tabla)
        >>>
        >>> # Asegurado
        >>> asegurado = Asegurado(
        ...     edad=35,
        ...     sexo=Sexo.HOMBRE,
        ...     suma_asegurada=Decimal("1000000")
        ... )
        >>>
        >>> # Calcular prima
        >>> resultado = producto.calcular_prima(asegurado)
        >>> print(f"Prima anual (20 años): ${resultado.prima_total:,.2f}")
    """

    def __init__(
        self,
        config: ConfiguracionProducto,
        tabla_mortalidad: TablaMortalidad,
        edad_omega: int = 100,
        plazo_pago_vitalicio: bool = False,
    ):
        """
        Inicializa un seguro de vida ordinario.

        Args:
            config: Configuración del producto
            tabla_mortalidad: Tabla de mortalidad
            edad_omega: Edad final de la tabla (default 100)
            plazo_pago_vitalicio: Si True, paga prima toda la vida;
                                 si False, usa config.plazo_years como periodo de pago

        Note:
            - Si plazo_pago_vitalicio=True: Paga prima hasta fallecimiento
            - Si plazo_pago_vitalicio=False: Paga prima durante config.plazo_years años
              (llamado "pago limitado"), pero cobertura es vitalicia
        """
        super().__init__(config, TipoProducto.VIDA_ORDINARIO)
        self.tabla_mortalidad = tabla_mortalidad
        self.edad_omega = edad_omega
        self.plazo_pago_vitalicio = plazo_pago_vitalicio

        # Si es pago vitalicio, no hay plazo limitado
        if plazo_pago_vitalicio:
            self.plazo_pago = None  # Paga hasta el final
        else:
            self.plazo_pago = config.plazo_years

    def calcular_prima(
        self,
        asegurado: Asegurado,
        frecuencia_pago: str = "anual",
        **kwargs: dict,
    ) -> ResultadoCalculo:
        """
        Calcula la prima para un seguro de vida ordinario.

        El cálculo difiere del temporal en que:
        - La cobertura se extiende hasta edad omega (no un plazo fijo)
        - El beneficio está garantizado (se pagará eventualmente)
        - La prima puede ser vitalicia o de pago limitado

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
            >>> print(f"Prima: ${resultado.prima_total:,.2f}")
        """
        # Validar asegurabilidad
        es_asegurable, razon = self.validar_asegurabilidad(asegurado)
        if not es_asegurable:
            raise ValueError(f"Asegurado no es asegurable: {razon}")

        # Calcular plazo de cobertura (hasta edad omega)
        plazo_cobertura = self.edad_omega - asegurado.edad

        if plazo_cobertura <= 0:
            raise ValueError(
                f"Edad del asegurado ({asegurado.edad}) >= edad omega ({self.edad_omega})"
            )

        # Valor presente del beneficio (toda la vida)
        axn = calcular_seguro_vida(
            tabla=self.tabla_mortalidad,
            edad=asegurado.edad,
            sexo=asegurado.sexo,
            plazo=plazo_cobertura,
            tasa_interes=self.config.tasa_interes_tecnico,
            suma_asegurada=asegurado.suma_asegurada,
        )

        # Valor presente de los pagos de prima
        if self.plazo_pago_vitalicio:
            # Anualidad vitalicia
            plazo_anualidad = plazo_cobertura
        else:
            # Anualidad de pago limitado
            plazo_anualidad = min(self.plazo_pago, plazo_cobertura)

        axm = calcular_anualidad(
            tabla=self.tabla_mortalidad,
            edad=asegurado.edad,
            sexo=asegurado.sexo,
            plazo=plazo_anualidad,
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

        # Metadata
        tipo_pago = "vitalicio" if self.plazo_pago_vitalicio else f"{self.plazo_pago} años"

        return ResultadoCalculo(
            prima_neta=prima_neta_ajustada,
            prima_total=prima_total,
            moneda=self.config.moneda,
            desglose_recargos=desglose,
            metadata={
                "producto": self.config.nombre_producto,
                "tipo": "vida_ordinario",
                "plazo_cobertura": plazo_cobertura,
                "plazo_pago": tipo_pago,
                "frecuencia_pago": frecuencia_pago,
                "tabla_mortalidad": self.tabla_mortalidad.nombre,
                "tasa_interes": str(self.config.tasa_interes_tecnico),
                "edad": asegurado.edad,
                "sexo": asegurado.sexo.value,
                "edad_omega": self.edad_omega,
            },
        )

    def calcular_reserva(
        self,
        asegurado: Asegurado,
        anio: int,
        **kwargs: dict,
    ) -> Decimal:
        """
        Calcula la reserva matemática en un año dado.

        Para vida ordinario, la reserva crece continuamente hasta alcanzar
        la suma asegurada en la edad omega.

        Fórmula: V_t = A_(x+t) - P * ä_(x+t)

        donde los componentes se calculan desde edad x+t hasta omega.

        Args:
            asegurado: Datos del asegurado
            anio: Año de la póliza (0 = inicio)
            **kwargs: Parámetros adicionales

        Returns:
            Monto de la reserva matemática

        Raises:
            ValueError: Si el año está fuera de rango

        Examples:
            >>> reserva_10 = producto.calcular_reserva(asegurado, anio=10)
            >>> print(f"Reserva año 10: ${reserva_10:,.2f}")
        """
        plazo_total = self.edad_omega - asegurado.edad

        if anio < 0 or anio > plazo_total:
            raise ValueError(
                f"Año {anio} fuera de rango [0, {plazo_total}]"
            )

        # Al inicio, reserva = 0
        if anio == 0:
            return Decimal("0")

        # Al final (edad omega), reserva = suma asegurada
        if anio == plazo_total:
            return asegurado.suma_asegurada

        # Edad actual
        edad_actual = asegurado.edad + anio
        plazo_restante = self.edad_omega - edad_actual

        # Valor presente del beneficio futuro
        axn_futuro = calcular_seguro_vida(
            tabla=self.tabla_mortalidad,
            edad=edad_actual,
            sexo=asegurado.sexo,
            plazo=plazo_restante,
            tasa_interes=self.config.tasa_interes_tecnico,
            suma_asegurada=asegurado.suma_asegurada,
        )

        # Determinar si todavía hay pagos de prima
        if self.plazo_pago_vitalicio:
            # Paga hasta el final
            plazo_pago_restante = plazo_restante
        else:
            # Pago limitado
            plazo_pago_restante = max(0, self.plazo_pago - anio)

        # Si ya no hay pagos, reserva = beneficio futuro
        if plazo_pago_restante == 0:
            return axn_futuro

        # Valor presente de primas futuras
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

        # Reserva = Beneficio futuro - Primas futuras
        reserva = axn_futuro - (prima_neta * axm_futuro)

        return reserva

    def validar_asegurabilidad(
        self,
        asegurado: Asegurado,
    ) -> tuple[bool, str | None]:
        """
        Valida asegurabilidad específica para vida ordinario.

        Args:
            asegurado: Datos del asegurado

        Returns:
            (es_asegurable, razon_rechazo)
        """
        # Validación base
        es_asegurable, razon = super().validar_asegurabilidad(asegurado)
        if not es_asegurable:
            return False, razon

        # Edad máxima de emisión
        if asegurado.edad > 75:
            return (
                False,
                "Edad máxima de emisión para vida ordinario es 75 años",
            )

        # Edad debe permitir al menos 5 años de cobertura
        if asegurado.edad >= (self.edad_omega - 5):
            return (
                False,
                f"Edad muy cercana a edad omega ({self.edad_omega})",
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
        tipo_pago = "vitalicio" if self.plazo_pago_vitalicio else f"{self.plazo_pago} años"
        return (
            f"VidaOrdinario("
            f"pago={tipo_pago}, "
            f"omega={self.edad_omega}, "
            f"tabla={self.tabla_mortalidad.nombre})"
        )
