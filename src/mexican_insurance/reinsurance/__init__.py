"""
Módulo de reaseguro (Fase 3).

Implementa contratos de reaseguro proporcional y no proporcional
para transferencia de riesgo.
"""

from mexican_insurance.reinsurance.base_reinsurance import ContratoReaseguro
from mexican_insurance.reinsurance.excess_of_loss import ExcessOfLoss
from mexican_insurance.reinsurance.quota_share import QuotaShare
from mexican_insurance.reinsurance.stop_loss import StopLoss

__all__ = [
    "ContratoReaseguro",
    "QuotaShare",
    "ExcessOfLoss",
    "StopLoss",
]
