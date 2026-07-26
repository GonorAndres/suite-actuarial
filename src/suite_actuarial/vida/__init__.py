"""Productos de seguros de vida."""

from suite_actuarial.vida.dotal import (
    PuntoReservaDotal,
    ResultadoAnalisisDotal,
    VerificacionesDotal,
    VidaDotal,
)
from suite_actuarial.vida.ordinario import VidaOrdinario
from suite_actuarial.vida.temporal import VidaTemporal

__all__ = ["VidaTemporal", "VidaOrdinario", "VidaDotal"]
