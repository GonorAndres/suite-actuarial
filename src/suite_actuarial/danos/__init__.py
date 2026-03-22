"""
Modulo de seguros de danos (P&C / Property & Casualty).

Implementa:
- Modelo colectivo de riesgo (frecuencia-severidad)
- Motor de tarificacion y credibilidad
- Producto de seguro de auto con tablas AMIS
- Seguro de incendio
- Seguro de responsabilidad civil
"""

from suite_actuarial.danos.auto import Cobertura, SeguroAuto
from suite_actuarial.danos.frecuencia_severidad import ModeloColectivo
from suite_actuarial.danos.incendio import SeguroIncendio
from suite_actuarial.danos.rc import SeguroRC
from suite_actuarial.danos.tarifas import (
    CalculadoraBonusMalus,
    FactorCredibilidad,
    TablaTarifas,
)

__all__ = [
    # Modelo colectivo
    "ModeloColectivo",
    # Tarificacion
    "FactorCredibilidad",
    "CalculadoraBonusMalus",
    "TablaTarifas",
    # Productos
    "SeguroAuto",
    "Cobertura",
    "SeguroIncendio",
    "SeguroRC",
]
