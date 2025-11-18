"""Módulo core con clases base y validadores"""

from mexican_insurance.core.base_product import ProductoSeguro, TipoProducto
from mexican_insurance.core.validators import (
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
