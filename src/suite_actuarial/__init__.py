"""
suite_actuarial - Libreria actuarial fundamental para el mercado mexicano.

Cuatro dominios: Vida, Danos, Salud, Pensiones.
Modulos transversales: Reservas, Reaseguro, Regulatorio, Config.

Uso rapido:
    from suite_actuarial import VidaTemporal, SeguroAuto, GMM, RentaVitalicia
    from suite_actuarial import cargar_config
"""

__version__ = "2.0.0"
__author__ = "Andres Gonzalez Ortega"

# --- Core ---
from suite_actuarial.actuarial.interest.tasas import CurvaRendimiento
from suite_actuarial.actuarial.mortality.tablas import TablaMortalidad
from suite_actuarial.config import cargar_config, config_vigente
from suite_actuarial.core.base_product import ProductoSeguro, TipoProducto
from suite_actuarial.core.validators import (
    Asegurado,
    ConfiguracionProducto,
    ResultadoCalculo,
)

# --- Danos ---
from suite_actuarial.danos import (
    CalculadoraBonusMalus,
    Cobertura,
    FactorCredibilidad,
    ModeloColectivo,
    SeguroAuto,
    SeguroIncendio,
    SeguroRC,
)

# --- Pensiones ---
from suite_actuarial.pensiones import (
    CalculadoraIMSS,
    PensionLey73,
    PensionLey97,
    RentaVitalicia,
    TablaConmutacion,
)

# --- Reaseguro ---
from suite_actuarial.reaseguro import (
    ContratoReaseguro,
    ExcessOfLoss,
    QuotaShare,
    StopLoss,
)

# --- Salud ---
from suite_actuarial.salud import (
    GMM,
    AccidentesEnfermedades,
    NivelHospitalario,
    ZonaGeografica,
)

# --- Vida ---
from suite_actuarial.vida import VidaDotal, VidaOrdinario, VidaTemporal

__all__ = [
    # Core
    "ProductoSeguro",
    "TipoProducto",
    "Asegurado",
    "ConfiguracionProducto",
    "ResultadoCalculo",
    "TablaMortalidad",
    "CurvaRendimiento",
    "cargar_config",
    "config_vigente",
    # Vida
    "VidaTemporal",
    "VidaOrdinario",
    "VidaDotal",
    # Danos
    "ModeloColectivo",
    "SeguroAuto",
    "Cobertura",
    "SeguroIncendio",
    "SeguroRC",
    "FactorCredibilidad",
    "CalculadoraBonusMalus",
    # Salud
    "GMM",
    "NivelHospitalario",
    "ZonaGeografica",
    "AccidentesEnfermedades",
    # Pensiones
    "TablaConmutacion",
    "RentaVitalicia",
    "PensionLey73",
    "PensionLey97",
    "CalculadoraIMSS",
    # Reaseguro
    "ContratoReaseguro",
    "QuotaShare",
    "ExcessOfLoss",
    "StopLoss",
]
