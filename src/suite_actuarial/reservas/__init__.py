"""
Módulo de Reservas (Fase 4).

Implementa métodos actuariales para estimación de reservas IBNR:
- Chain Ladder: Método estándar basado en factores de desarrollo
- Bornhuetter-Ferguson: Combina experiencia observada con a priori
- Bootstrap: remuestreo de residuales; banda ilustrativa, no ODP (ver A2)
- Mack (1993): error de prediccion del Chain Ladder (sigma_k, MSEP por ano)
"""

from suite_actuarial.reservas.bootstrap import Bootstrap
from suite_actuarial.reservas.bornhuetter_ferguson import BornhuetterFerguson
from suite_actuarial.reservas.chain_ladder import ChainLadder
from suite_actuarial.reservas.cola import AjusteCola, estimar_tail_sherman
from suite_actuarial.reservas.diagnosticos import (
    BandaDispersion,
    MackUncertainty,
    ReserveValidationReport,
    banda_dispersion_link_ratios,
    calcular_mack_uncertainty,
    validar_reserva,
)
from suite_actuarial.reservas.mack import ResultadoMack, calcular_mack

__all__ = [
    "ChainLadder",
    "BornhuetterFerguson",
    "Bootstrap",
    "AjusteCola",
    "BandaDispersion",
    "ReserveValidationReport",
    "ResultadoMack",
    "banda_dispersion_link_ratios",
    "calcular_mack",
    "estimar_tail_sherman",
    "validar_reserva",
    # Deprecados: la firma anterior recibia una reserva que Mack no usa.
    "MackUncertainty",
    "calcular_mack_uncertainty",
]
