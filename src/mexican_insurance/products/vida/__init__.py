"""Productos de seguros de vida"""

from mexican_insurance.products.vida.dotal import VidaDotal
from mexican_insurance.products.vida.ordinario import VidaOrdinario
from mexican_insurance.products.vida.temporal import VidaTemporal

__all__ = ["VidaTemporal", "VidaOrdinario", "VidaDotal"]
