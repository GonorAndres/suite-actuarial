"""Productos de seguros de vida."""
from suite_actuarial.vida.dotal import VidaDotal
from suite_actuarial.vida.ordinario import VidaOrdinario
from suite_actuarial.vida.temporal import VidaTemporal

__all__ = ["VidaTemporal", "VidaOrdinario", "VidaDotal"]
