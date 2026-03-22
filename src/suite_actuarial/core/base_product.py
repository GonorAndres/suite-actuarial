"""
Clase base para productos de seguros

Esta es la clase padre de la que heredan todos los productos específicos
(vida, salud, daños, etc.). Define la interfaz común.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from enum import StrEnum

from suite_actuarial.core.validators import (
    Asegurado,
    ConfiguracionProducto,
    ResultadoCalculo,
)


class TipoProducto(StrEnum):
    """Tipos de productos de seguros según clasificación CNSF"""

    # Seguros de vida
    VIDA_TEMPORAL = "vida_temporal"
    VIDA_ORDINARIO = "vida_ordinario"
    VIDA_DOTAL = "vida_dotal"
    VIDA_UNIVERSAL = "vida_universal"

    # Seguros de salud
    GASTOS_MEDICOS = "gastos_medicos_mayores"
    ACCIDENTES_ENFERMEDADES = "accidentes_y_enfermedades"

    # Seguros de daños
    AUTOS = "automoviles"
    INCENDIO = "incendio"
    DIVERSOS = "diversos"


class ProductoSeguro(ABC):
    """
    Clase base abstracta para todos los productos de seguros.

    Esta clase define la interfaz que deben implementar todos los productos.
    No se puede instanciar directamente, solo sirve como plantilla.

    Atributos:
        config: Configuración del producto
        tipo: Tipo de producto según clasificación CNSF
    """

    def __init__(
        self,
        config: ConfiguracionProducto,
        tipo: TipoProducto,
    ):
        """
        Inicializa un producto de seguros.

        Args:
            config: Configuración del producto
            tipo: Tipo de producto
        """
        self.config = config
        self.tipo = tipo

    @abstractmethod
    def calcular_prima(
        self,
        asegurado: Asegurado,
        **kwargs: dict,
    ) -> ResultadoCalculo:
        """
        Calcula la prima para un asegurado dado.

        Este método debe ser implementado por cada producto específico
        según sus reglas de tarificación.

        Args:
            asegurado: Datos del asegurado
            **kwargs: Parámetros adicionales específicos del producto

        Returns:
            ResultadoCalculo con prima neta, prima total y desglose

        Raises:
            ValueError: Si los datos del asegurado no son válidos para este producto
        """
        pass

    @abstractmethod
    def calcular_reserva(
        self,
        asegurado: Asegurado,
        anio: int,
        **kwargs: dict,
    ) -> Decimal:
        """
        Calcula la reserva matemática en un año dado.

        Args:
            asegurado: Datos del asegurado
            anio: Año de la póliza para el cual calcular reserva
            **kwargs: Parámetros adicionales

        Returns:
            Monto de la reserva matemática

        Raises:
            ValueError: Si el año está fuera del plazo de la póliza
        """
        pass

    def validar_asegurabilidad(
        self,
        asegurado: Asegurado,
    ) -> tuple[bool, str | None]:
        """
        Valida si un asegurado es elegible para este producto.

        Esta es una validación básica. Cada producto puede extenderla
        con reglas de suscripción específicas.

        Args:
            asegurado: Datos del asegurado

        Returns:
            (es_asegurable, razon_rechazo)
            - es_asegurable: True si es asegurable, False si no
            - razon_rechazo: None si es asegurable, string con razón si no

        Examples:
            >>> producto.validar_asegurabilidad(asegurado)
            (True, None)
            >>> producto.validar_asegurabilidad(asegurado_rechazado)
            (False, "Edad fuera de rango aceptable")
        """
        # Validación básica de edad
        if asegurado.edad < 18:
            return False, "El asegurado debe ser mayor de edad (18+)"

        if asegurado.edad > 70:
            return False, "Edad máxima de aceptación excedida (70 años)"

        # Validación de suma asegurada
        if asegurado.suma_asegurada > Decimal("50000000"):  # 50M MXN
            return (
                False,
                "Suma asegurada excede límites de suscripción automática",
            )

        return True, None

    def aplicar_recargos(
        self,
        prima_neta: Decimal,
    ) -> tuple[Decimal, dict[str, Decimal]]:
        """
        Aplica los recargos configurados a la prima neta.

        Args:
            prima_neta: Prima neta antes de recargos

        Returns:
            (prima_total, desglose_recargos)
            - prima_total: Prima neta + todos los recargos
            - desglose_recargos: Dict con el monto de cada recargo

        Examples:
            >>> producto.aplicar_recargos(Decimal("1000"))
            (Decimal("1180"), {"gastos_admin": ..., "gastos_adq": ..., "utilidad": ...})
        """
        # Calcular cada recargo
        recargo_admin = prima_neta * self.config.recargo_gastos_admin
        recargo_adq = prima_neta * self.config.recargo_gastos_adq
        recargo_util = prima_neta * self.config.recargo_utilidad

        # Desglose para transparencia
        desglose = {
            "gastos_admin": recargo_admin,
            "gastos_adq": recargo_adq,
            "utilidad": recargo_util,
        }

        # Prima total
        prima_total = prima_neta + sum(desglose.values())

        return prima_total, desglose

    def __repr__(self) -> str:
        """Representación en string del producto"""
        return (
            f"{self.__class__.__name__}("
            f"tipo={self.tipo.value}, "
            f"nombre={self.config.nombre_producto})"
        )
