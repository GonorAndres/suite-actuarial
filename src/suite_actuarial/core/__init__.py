"""Módulo core con clases base y validadores"""

from suite_actuarial.core.base_product import ProductoSeguro, TipoProducto
from suite_actuarial.core.validators import (
    Asegurado,
    ConfiguracionProducto,
    ResultadoCalculo,
)

__all__ = [
    "ProductoSeguro",
    "TipoProducto",
    "Asegurado",
    "ConfiguracionProducto",
    "ResultadoCalculo",
]
