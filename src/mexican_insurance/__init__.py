"""
mexican_insurance - Suite de análisis actuarial para seguros en México

Esta librería proporciona herramientas para:
- Cálculo de primas de seguros de vida
- Cálculo de reservas técnicas
- Optimización de reaseguro
- Cumplimiento regulatorio CNSF
"""

__version__ = "0.3.0"  # Fase 3: Reaseguro
__author__ = "Tu Nombre"

from mexican_insurance.core.base_product import ProductoSeguro, TipoProducto
from mexican_insurance.core.validators import (
    Asegurado,
    ConfiguracionProducto,
    ResultadoCalculo,
)

# Módulo de reaseguro (Fase 3)
from mexican_insurance.reinsurance import (
    ContratoReaseguro,
    ExcessOfLoss,
    QuotaShare,
    StopLoss,
)

__all__ = [
    "ProductoSeguro",
    "TipoProducto",
    "Asegurado",
    "ConfiguracionProducto",
    "ResultadoCalculo",
    # Reaseguro
    "ContratoReaseguro",
    "QuotaShare",
    "ExcessOfLoss",
    "StopLoss",
]
