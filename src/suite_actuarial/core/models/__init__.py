"""
Modelos Pydantic para datos de seguros.

Organizado por dominio: common, asegurado, producto, reaseguro, reservas, regulatorio.
"""

from suite_actuarial.core.models.asegurado import Asegurado, RegistroMortalidad
from suite_actuarial.core.models.common import (
    CalculationMetadata,
    Fumador,
    Moneda,
    Sexo,
    normalizar_sexo,
)
from suite_actuarial.core.models.producto import ConfiguracionProducto, ResultadoCalculo
from suite_actuarial.core.models.reaseguro import (
    ConfiguracionReaseguro,
    ExcessOfLossConfig,
    ModalidadXL,
    QuotaShareConfig,
    ResultadoReaseguro,
    Siniestro,
    StopLossConfig,
    TipoContrato,
    TipoSiniestro,
)
from suite_actuarial.core.models.regulatorio import (
    ConfiguracionRCSDanos,
    ConfiguracionRCSInversion,
    ConfiguracionRCSVida,
    ResultadoRCS,
    TipoRamo,
    TipoRiesgoRCS,
    calcular_ratio_solvencia,
)
from suite_actuarial.core.models.reservas import (
    ConfiguracionBootstrap,
    ConfiguracionBornhuetterFerguson,
    ConfiguracionChainLadder,
    MetodoPromedio,
    MetodoReserva,
    ResultadoReserva,
    TipoTriangulo,
)

__all__ = [
    "Sexo",
    "normalizar_sexo",
    "Fumador",
    "Moneda",
    "CalculationMetadata",
    "Asegurado",
    "RegistroMortalidad",
    "ConfiguracionProducto",
    "ResultadoCalculo",
    "TipoContrato",
    "TipoSiniestro",
    "ModalidadXL",
    "Siniestro",
    "ConfiguracionReaseguro",
    "QuotaShareConfig",
    "ExcessOfLossConfig",
    "StopLossConfig",
    "ResultadoReaseguro",
    "TipoTriangulo",
    "MetodoReserva",
    "MetodoPromedio",
    "ConfiguracionChainLadder",
    "ConfiguracionBornhuetterFerguson",
    "ConfiguracionBootstrap",
    "ResultadoReserva",
    "TipoRiesgoRCS",
    "TipoRamo",
    "ConfiguracionRCSVida",
    "ConfiguracionRCSDanos",
    "ConfiguracionRCSInversion",
    "ResultadoRCS",
    "calcular_ratio_solvencia",
]
