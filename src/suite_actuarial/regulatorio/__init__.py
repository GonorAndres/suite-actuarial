"""
Módulo Regulatorio (Fase 5A).

Implementa herramientas para cumplimiento de normativas de la CNSF
(Comisión Nacional de Seguros y Fianzas de México).

Componentes:
- RCS Vida: Requerimiento de Capital de Solvencia para riesgos de vida
- RCS Daños: Requerimiento de Capital de Solvencia para riesgos de daños
- RCS Inversión: Requerimiento de Capital por riesgos de mercado y crédito
- Agregador RCS: Combina todos los riesgos con correlaciones
"""

from suite_actuarial.regulatorio.agregador_rcs import AgregadorRCS
from suite_actuarial.regulatorio.rcs_danos import RCSDanos
from suite_actuarial.regulatorio.rcs_inversion import RCSInversion
from suite_actuarial.regulatorio.rcs_vida import RCSVida

__all__ = [
    "RCSVida",
    "RCSDanos",
    "RCSInversion",
    "AgregadorRCS",
]
