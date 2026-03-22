"""
Modulo de seguros de salud (Health Insurance).

Implementa:
- Gastos Medicos Mayores (GMM): cobertura de gastos medicos mayores
- Accidentes y Enfermedades (A&E): cobertura de accidentes y perdidas organicas
"""

from suite_actuarial.salud.accidentes import AccidentesEnfermedades
from suite_actuarial.salud.gmm import GMM, NivelHospitalario, ZonaGeografica

__all__ = [
    "GMM",
    "NivelHospitalario",
    "ZonaGeografica",
    "AccidentesEnfermedades",
]
