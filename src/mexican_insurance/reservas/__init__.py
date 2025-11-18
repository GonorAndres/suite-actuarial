"""
Módulo de Reservas (Fase 4).

Implementa métodos actuariales para estimación de reservas IBNR:
- Chain Ladder: Método estándar basado en factores de desarrollo
- Bornhuetter-Ferguson: Combina experiencia observada con a priori
- Bootstrap: Simulación Monte Carlo para distribución completa
"""

from mexican_insurance.reservas.bootstrap import Bootstrap
from mexican_insurance.reservas.bornhuetter_ferguson import BornhuetterFerguson
from mexican_insurance.reservas.chain_ladder import ChainLadder

__all__ = [
    "ChainLadder",
    "BornhuetterFerguson",
    "Bootstrap",
]
