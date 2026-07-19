"""
Configuracion regulatoria versionada por ano.

Permite cargar parametros (UMA, factores CNSF, tasas SAT) por ano fiscal.
Los modulos que necesitan parametros regulatorios aceptan un ConfigAnual opcional;
si no se proporciona, se usa la configuracion del ano vigente.
"""

from suite_actuarial.config.loader import (
    cargar_config,
    cargar_config_fecha,
    config_vigente,
    validar_configuraciones,
)
from suite_actuarial.config.schema import (
    ConfigAnual,
    DataStatus,
    FactoresCNSF,
    FactoresTecnicos,
    IMSSConfig,
    RegulatoryParameter,
    SourceReference,
    TasasSAT,
    UMAConfig,
    ValidationTier,
)

__all__ = [
    "cargar_config",
    "cargar_config_fecha",
    "config_vigente",
    "validar_configuraciones",
    "ConfigAnual",
    "UMAConfig",
    "TasasSAT",
    "FactoresCNSF",
    "FactoresTecnicos",
    "SourceReference",
    "RegulatoryParameter",
    "DataStatus",
    "ValidationTier",
    "IMSSConfig",
]
