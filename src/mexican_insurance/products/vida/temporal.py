"""
Seguro de Vida Temporal

Este es uno de los productos más básicos y populares:
- Cobertura por un plazo fijo (ej: 10, 20, 30 años)
- Si el asegurado muere en el plazo, se paga la suma asegurada
- Si sobrevive al plazo, no hay pago (seguro puro de riesgo)
- Prima nivelada durante todo el plazo de pago
"""

from decimal import Decimal
from typing import Dict, Optional

from mexican_insurance.actuarial.mortality.tablas import TablaMortalidad
from mexican_insurance.actuarial.pricing.vida_pricing import (
    calcular_anualidad,
    calcular_prima_neta_temporal,
    calcular_seguro_vida,
)
from mexican_insurance.core.base_product import ProductoSeguro, TipoProducto
from mexican_insurance.core.validators import (
    Asegurado,
    ConfiguracionProducto,
    ResultadoCalculo,
)


class VidaTemporal(ProductoSeguro):
    """
    Seguro de Vida Temporal.

    Proporciona cobertura de fallecimiento durante un plazo específico.
    Es el producto más simple y común en el mercado mexicano.

    Attributes:
        config: Configuración del producto
        tabla_mortalidad: Tabla de mortalidad a usar para cálculos

    Examples:
        >>> from mexican_insurance.actuarial.mortality.tablas import TablaMortalidad
        >>> from mexican_insurance.core.validators import *
        >>> from decimal import Decimal
        >>>
        >>> # Configurar producto
        >>> config = ConfiguracionProducto(
        ...     nombre_producto="Vida Temporal 20 años",
        ...     plazo_years=20,
        ...     tasa_interes_tecnico=Decimal("0.055")
        ... )
        >>>
        >>> # Cargar tabla de mortalidad
        >>> tabla = TablaMortalidad.cargar_emssa09()
        >>>
        >>> # Crear producto
        >>> producto = VidaTemporal(config, tabla)
        >>>
        >>> # Calcular prima para un asegurado
        >>> asegurado = Asegurado(
        ...     edad=35,
        ...     sexo=Sexo.HOMBRE,
        ...     suma_asegurada=Decimal("1000000")
        ... )
        >>>
        >>> resultado = producto.calcular_prima(asegurado)
        >>> print(f"Prima anual: ${resultado.prima_total:,.2f}")
    """

    def __init__(
        self,
        config: ConfiguracionProducto,
        tabla_mortalidad: TablaMortalidad,
        plazo_pago: Optional[int] = None,
        edad_max_aceptacion: int = 70,
    ):
        """
        Inicializa un seguro de vida temporal.

        Args:
            config: Configuración del producto
            tabla_mortalidad: Tabla de mortalidad a usar
            plazo_pago: Plazo de pago de primas (si es diferente al plazo del seguro)
                       Por default es igual al plazo del seguro.
            edad_max_aceptacion: Edad máxima de aceptación (default: 70 años)
        """
        super().__init__(config, TipoProducto.VIDA_TEMPORAL, edad_max_aceptacion)
        self.tabla_mortalidad = tabla_mortalidad

        # Por default, el plazo de pago es igual al plazo del seguro
        self.plazo_pago = plazo_pago or config.plazo_years

        # Validar que plazo de pago no sea mayor al plazo del seguro
        if self.plazo_pago > config.plazo_years:
            raise ValueError(
                f"El plazo de pago ({self.plazo_pago}) no puede ser mayor "
                f"al plazo del seguro ({config.plazo_years})"
            )

    def calcular_prima(
        self,
        asegurado: Asegurado,
        frecuencia_pago: str = "anual",
        **kwargs: Dict,
    ) -> ResultadoCalculo:
        """
        Calcula la prima para un asegurado dado.

        Args:
            asegurado: Datos del asegurado
            frecuencia_pago: "anual", "mensual", "semestral", "trimestral"
            **kwargs: Parámetros adicionales (no usados actualmente)

        Returns:
            ResultadoCalculo con prima neta, prima total y desglose

        Raises:
            ValueError: Si el asegurado no es asegurable

        Examples:
            >>> resultado = producto.calcular_prima(asegurado, frecuencia_pago="mensual")
            >>> print(f"Prima mensual: ${resultado.prima_total:,.2f}")
        """
        # Validar asegurabilidad
        es_asegurable, razon = self.validar_asegurabilidad(asegurado)
        if not es_asegurable:
            raise ValueError(f"Asegurado no es asegurable: {razon}")

        # Calcular prima neta
        prima_neta = calcular_prima_neta_temporal(
            tabla=self.tabla_mortalidad,
            edad=asegurado.edad,
            sexo=asegurado.sexo,
            plazo_seguro=self.config.plazo_years,
            plazo_pago=self.plazo_pago,
            tasa_interes=self.config.tasa_interes_tecnico,
            suma_asegurada=asegurado.suma_asegurada,
            frecuencia_pago=frecuencia_pago,
        )

        # Aplicar recargos
        prima_total, desglose = self.aplicar_recargos(prima_neta)

        # Crear resultado
        return ResultadoCalculo(
            prima_neta=prima_neta,
            prima_total=prima_total,
            moneda=self.config.moneda,
            desglose_recargos=desglose,
            metadata={
                "producto": self.config.nombre_producto,
                "plazo_seguro": self.config.plazo_years,
                "plazo_pago": self.plazo_pago,
                "frecuencia_pago": frecuencia_pago,
                "tabla_mortalidad": self.tabla_mortalidad.nombre,
                "tasa_interes": str(self.config.tasa_interes_tecnico),
                "edad": asegurado.edad,
                "sexo": asegurado.sexo.value,
            },
        )

    def calcular_reserva(
        self,
        asegurado: Asegurado,
        anio: int,
        **kwargs: Dict,
    ) -> Decimal:
        """
        Calcula la reserva matemática en un año dado.

        La reserva matemática es:
        V_t = A[x+t:n-t] - P * ä[x+t:m-t]

        Donde:
        - A[x+t:n-t] = valor del seguro restante
        - P = prima nivelada
        - ä[x+t:m-t] = valor de las primas futuras

        Args:
            asegurado: Datos del asegurado
            anio: Año de la póliza (0 = inicio, 1 = fin del primer año, etc.)
            **kwargs: Parámetros adicionales

        Returns:
            Monto de la reserva matemática

        Raises:
            ValueError: Si el año está fuera del plazo

        Examples:
            >>> reserva_5 = producto.calcular_reserva(asegurado, anio=5)
            >>> print(f"Reserva al año 5: ${reserva_5:,.2f}")
        """
        if anio < 0 or anio > self.config.plazo_years:
            raise ValueError(
                f"Año {anio} fuera de rango [0, {self.config.plazo_years}]"
            )

        # Al inicio y al final, la reserva es 0
        if anio == 0 or anio == self.config.plazo_years:
            return Decimal("0")

        # Edad actual del asegurado en este año
        edad_actual = asegurado.edad + anio

        # Plazo restante del seguro
        plazo_restante_seguro = self.config.plazo_years - anio

        # Plazo restante de pago
        plazo_restante_pago = max(0, self.plazo_pago - anio)

        # Valor presente del beneficio futuro
        axn_futuro = calcular_seguro_vida(
            tabla=self.tabla_mortalidad,
            edad=edad_actual,
            sexo=asegurado.sexo,
            plazo=plazo_restante_seguro,
            tasa_interes=self.config.tasa_interes_tecnico,
            suma_asegurada=asegurado.suma_asegurada,
        )

        # Si ya no hay más pagos de prima, la reserva es solo el beneficio
        if plazo_restante_pago == 0:
            return axn_futuro

        # Valor presente de las primas futuras
        axm_futuro = calcular_anualidad(
            tabla=self.tabla_mortalidad,
            edad=edad_actual,
            sexo=asegurado.sexo,
            plazo=plazo_restante_pago,
            tasa_interes=self.config.tasa_interes_tecnico,
            pago_anticipado=True,
        )

        # Calcular la prima neta original (sin frecuencia)
        resultado = self.calcular_prima(asegurado, frecuencia_pago="anual")
        prima_neta = resultado.prima_neta

        # Reserva = Beneficio futuro - Primas futuras
        reserva = axn_futuro - (prima_neta * axm_futuro)

        return reserva

    def validar_asegurabilidad(
        self,
        asegurado: Asegurado,
    ) -> tuple[bool, Optional[str]]:
        """
        Valida asegurabilidad específica para vida temporal.

        Añade validaciones adicionales a las de la clase base.

        Args:
            asegurado: Datos del asegurado

        Returns:
            (es_asegurable, razon_rechazo)
        """
        # Validación base
        es_asegurable, razon = super().validar_asegurabilidad(asegurado)
        if not es_asegurable:
            return False, razon

        # Validación específica: edad + plazo no debe exceder edad máxima
        edad_final = asegurado.edad + self.config.plazo_years
        if edad_final > 100:
            return (
                False,
                f"La edad al vencimiento ({edad_final}) excede el límite (100)",
            )

        # Validación: edad mínima para seguros largos
        if self.config.plazo_years >= 30 and asegurado.edad < 25:
            return (
                False,
                "Edad mínima de 25 años para seguros de 30+ años",
            )

        # Validación: personas de 70+ años requieren mínimo 20 años de plazo
        if asegurado.edad >= 70 and self.config.plazo_years < 20:
            return (
                False,
                f"Asegurados de 70+ años requieren plazo mínimo de 20 años (plazo actual: {self.config.plazo_years})",
            )

        return True, None

    def __repr__(self) -> str:
        """Representación en string"""
        return (
            f"VidaTemporal("
            f"plazo={self.config.plazo_years} años, "
            f"tabla={self.tabla_mortalidad.nombre})"
        )
