"""
Configuracion regulatoria versionada por ano.

Permite cargar parametros (UMA, factores CNSF, tasas SAT) por ano fiscal.
Los modulos que necesitan parametros regulatorios aceptan un ConfigAnual opcional;
si no se proporciona, se usa la configuracion del ano vigente.
"""

from suite_actuarial.config.loader import cargar_config, config_vigente
from suite_actuarial.config.schema import (
    ConfigAnual,
    FactoresCNSF,
    FactoresTecnicos,
    TasasSAT,
    UMAConfig,
)

__all__ = [
    "cargar_config",
    "config_vigente",
    "ConfigAnual",
    "UMAConfig",
    "TasasSAT",
    "FactoresCNSF",
    "FactoresTecnicos",
]
