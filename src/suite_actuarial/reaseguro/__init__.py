"""
Modulo de reaseguro (Fase 3).

Implementa contratos de reaseguro proporcional y no proporcional
para transferencia de riesgo.
"""

from suite_actuarial.reaseguro.base_reinsurance import ContratoReaseguro
from suite_actuarial.reaseguro.excess_of_loss import ExcessOfLoss
from suite_actuarial.reaseguro.quota_share import QuotaShare
from suite_actuarial.reaseguro.stop_loss import StopLoss

__all__ = [
    "ContratoReaseguro",
    "QuotaShare",
    "ExcessOfLoss",
    "StopLoss",
]
