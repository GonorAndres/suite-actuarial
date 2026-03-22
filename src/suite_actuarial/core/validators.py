"""
Validadores con Pydantic para datos de seguros.

Este modulo re-exporta todos los modelos desde core.models para
mantener compatibilidad con importaciones existentes.
"""

# Re-export everything from the split model files
from suite_actuarial.core.models.common import (  # noqa: F401
    Fumador,
    Moneda,
    Sexo,
)
from suite_actuarial.core.models.asegurado import (  # noqa: F401
    Asegurado,
    RegistroMortalidad,
)
from suite_actuarial.core.models.producto import (  # noqa: F401
    ConfiguracionProducto,
    ResultadoCalculo,
)
from suite_actuarial.core.models.reaseguro import (  # noqa: F401
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
from suite_actuarial.core.models.reservas import (  # noqa: F401
    ConfiguracionBootstrap,
    ConfiguracionBornhuetterFerguson,
    ConfiguracionChainLadder,
    MetodoPromedio,
    MetodoReserva,
    ResultadoReserva,
    TipoTriangulo,
)
from suite_actuarial.core.models.regulatorio import (  # noqa: F401
    ConfiguracionRCSDanos,
    ConfiguracionRCSInversion,
    ConfiguracionRCSVida,
    ResultadoRCS,
    TipoRamo,
    TipoRiesgoRCS,
)

__all__ = [
    # Common
    "Sexo",
    "Fumador",
    "Moneda",
    # Asegurado
    "Asegurado",
    "RegistroMortalidad",
    # Producto
    "ConfiguracionProducto",
    "ResultadoCalculo",
    # Reaseguro
    "TipoContrato",
    "TipoSiniestro",
    "ModalidadXL",
    "Siniestro",
    "ConfiguracionReaseguro",
    "QuotaShareConfig",
    "ExcessOfLossConfig",
    "StopLossConfig",
    "ResultadoReaseguro",
    # Reservas
    "TipoTriangulo",
    "MetodoReserva",
    "MetodoPromedio",
    "ConfiguracionChainLadder",
    "ConfiguracionBornhuetterFerguson",
    "ConfiguracionBootstrap",
    "ResultadoReserva",
    # Regulatorio
    "TipoRiesgoRCS",
    "TipoRamo",
    "ConfiguracionRCSVida",
    "ConfiguracionRCSDanos",
    "ConfiguracionRCSInversion",
    "ResultadoRCS",
]
