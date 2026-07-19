"""
Módulo de Reservas (Fase 4).

Implementa métodos actuariales para estimación de reservas IBNR:
- Chain Ladder: Método estándar basado en factores de desarrollo
- Bornhuetter-Ferguson: Combina experiencia observada con a priori
- Bootstrap: Simulación Monte Carlo para distribución completa
"""

from suite_actuarial.reservas.bootstrap import Bootstrap
from suite_actuarial.reservas.bornhuetter_ferguson import BornhuetterFerguson
from suite_actuarial.reservas.chain_ladder import ChainLadder
from suite_actuarial.reservas.diagnosticos import (
    MackUncertainty,
    ReserveValidationReport,
    calcular_mack_uncertainty,
    validar_reserva,
)

__all__ = [
    "ChainLadder",
    "BornhuetterFerguson",
    "Bootstrap",
    "MackUncertainty",
    "ReserveValidationReport",
    "calcular_mack_uncertainty",
    "validar_reserva",
]
