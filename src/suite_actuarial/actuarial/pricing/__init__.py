"""Módulo de pricing (tarificación) de seguros"""

from suite_actuarial.actuarial.pricing.vida_pricing import (
    calcular_anualidad,
    calcular_prima_neta_temporal,
    calcular_seguro_vida,
)

__all__ = [
    "calcular_prima_neta_temporal",
    "calcular_seguro_vida",
    "calcular_anualidad",
]
