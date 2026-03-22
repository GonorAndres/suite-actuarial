"""Cargador de configuracion regulatoria por ano."""

import importlib
from datetime import datetime

from suite_actuarial.config.schema import ConfigAnual

_CONFIGS: dict[int, ConfigAnual] = {}


def cargar_config(anio: int | None = None) -> ConfigAnual:
    """
    Carga la configuracion regulatoria para un ano dado.

    Args:
        anio: Ano fiscal. Si es None, usa el ano actual.

    Returns:
        ConfigAnual con todos los parametros regulatorios del ano.

    Raises:
        ModuleNotFoundError: Si no existe configuracion para ese ano.

    Example:
        >>> config = cargar_config(2026)
        >>> config.uma.uma_anual
        Decimal('41296.10')
    """
    if anio is None:
        anio = datetime.now().year

    if anio not in _CONFIGS:
        try:
            module = importlib.import_module(f"suite_actuarial.config.config_{anio}")
        except ModuleNotFoundError as err:
            available = sorted(_CONFIGS.keys())
            raise ModuleNotFoundError(
                f"No existe configuracion para el ano {anio}. "
                f"Disponibles: {available or 'ninguno (use cargar_config con un ano valido)'}. "
                f"Cree suite_actuarial/config/config_{anio}.py para agregarlo."
            ) from err
        _CONFIGS[anio] = module.CONFIG
    return _CONFIGS[anio]


def config_vigente() -> ConfigAnual:
    """Carga la configuracion del ano actual."""
    return cargar_config(datetime.now().year)
