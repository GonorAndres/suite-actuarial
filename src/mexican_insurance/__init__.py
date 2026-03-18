"""
mexican_insurance - Suite de analisis actuarial para el mercado asegurador mexicano

Libreria completa que cubre el ciclo operativo de una aseguradora:

- Fase 1: Fundamentos (tablas de mortalidad EMSSA-09, validadores Pydantic)
- Fase 2: Productos de vida (temporal, ordinario, dotal)
- Fase 3: Reaseguro (Quota Share, Excess of Loss, Stop Loss)
- Fase 4: Reservas avanzadas (Chain Ladder, Bornhuetter-Ferguson, Bootstrap)
- Fase 5: Cumplimiento regulatorio (RCS, CNSF, S-11.4, SAT)
- Fase 6: Dashboards interactivos (Streamlit)
"""

__version__ = "1.0.0"
__author__ = "Andres Gonzalez Ortega"

from mexican_insurance.core.base_product import ProductoSeguro, TipoProducto
from mexican_insurance.core.validators import (
    Asegurado,
    ConfiguracionProducto,
    ResultadoCalculo,
)
from mexican_insurance.reinsurance import (
    ContratoReaseguro,
    ExcessOfLoss,
    QuotaShare,
    StopLoss,
)

__all__ = [
    # Core
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
    # Tambien disponibles: products.vida, reservas, regulatorio, reportes
]
