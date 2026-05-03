"""
Config router -- regulatory configuration lookup endpoints.

Exposes GET endpoints for retrieving year-specific regulatory parameters
(UMA, SAT rates, CNSF factors) via the configuration loader.
"""

from decimal import Decimal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from suite_actuarial.config.loader import cargar_config

router = APIRouter(prefix="/config", tags=["config"])


# -- Response models ----------------------------------------------------------


class UMAResponse(BaseModel):
    """UMA values for a given fiscal year."""

    uma_diaria: float = Field(..., description="UMA diaria en MXN")
    uma_mensual: float = Field(..., description="UMA mensual (diaria * 30.4)")
    uma_anual: float = Field(..., description="UMA anual (diaria * 365)")


class TasasSATResponse(BaseModel):
    """SAT tax rates for a given fiscal year."""

    tasa_retencion_rentas_vitalicias: float = Field(
        ..., description="Retencion ISR sobre rentas vitalicias"
    )
    tasa_retencion_retiros_ahorro: float = Field(
        ..., description="Retencion ISR sobre retiros de ahorro"
    )
    tasa_isr_personas_morales: float = Field(
        ..., description="Tasa ISR personas morales"
    )
    tasa_iva: float = Field(..., description="Tasa IVA general")
    limite_deducciones_pf_umas: int = Field(
        ..., description="Limite de deducciones personales en UMAs (Art. 151 LISR)"
    )


class FactoresCNSFResponse(BaseModel):
    """CNSF regulatory factors for RCS calculation."""

    shock_acciones: float = Field(..., description="Shock a acciones")
    shock_bonos_gubernamentales: float = Field(
        ..., description="Shock a bonos gubernamentales"
    )
    shock_bonos_corporativos: float = Field(
        ..., description="Shock a bonos corporativos"
    )
    shock_inmuebles: float = Field(..., description="Shock a inmuebles")
    shocks_credito: dict[str, float] = Field(
        ..., description="Shock de credito por calificacion"
    )
    correlacion_vida_danos: float = Field(
        ..., description="Correlacion RCS vida vs danos"
    )
    correlacion_vida_inversion: float = Field(
        ..., description="Correlacion RCS vida vs inversion"
    )
    correlacion_danos_inversion: float = Field(
        ..., description="Correlacion RCS danos vs inversion"
    )


class FactoresTecnicosResponse(BaseModel):
    """Technical actuarial parameters."""

    tasa_interes_tecnico_vida: float = Field(
        ..., description="Tasa de interes tecnico maxima para vida"
    )
    tasa_interes_tecnico_pensiones: float = Field(
        ..., description="Tasa de interes tecnico para pensiones"
    )
    edad_omega: int = Field(..., description="Edad maxima de las tablas de mortalidad")
    margen_seguridad_s114: float = Field(
        ..., description="Margen de seguridad para reservas tecnicas (Circular S-11.4)"
    )


class ConfigAnualResponse(BaseModel):
    """Full regulatory configuration for a fiscal year."""

    anio: int
    uma: UMAResponse
    tasas_sat: TasasSATResponse
    factores_cnsf: FactoresCNSFResponse
    factores_tecnicos: FactoresTecnicosResponse


# -- Helpers ------------------------------------------------------------------


def _decimal_to_float(val):
    """Convert a value to float if it is a Decimal."""
    return float(val) if isinstance(val, Decimal) else val


def _load_config_or_404(anio: int):
    """Load config for the given year or raise HTTP 404."""
    try:
        return cargar_config(anio)
    except ModuleNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _config_to_response(config) -> ConfigAnualResponse:
    """Convert a ConfigAnual (with Decimals) to a JSON-safe response."""
    return ConfigAnualResponse(
        anio=config.anio,
        uma=UMAResponse(
            uma_diaria=float(config.uma.uma_diaria),
            uma_mensual=float(config.uma.uma_mensual),
            uma_anual=float(config.uma.uma_anual),
        ),
        tasas_sat=TasasSATResponse(
            tasa_retencion_rentas_vitalicias=float(
                config.tasas_sat.tasa_retencion_rentas_vitalicias
            ),
            tasa_retencion_retiros_ahorro=float(
                config.tasas_sat.tasa_retencion_retiros_ahorro
            ),
            tasa_isr_personas_morales=float(
                config.tasas_sat.tasa_isr_personas_morales
            ),
            tasa_iva=float(config.tasas_sat.tasa_iva),
            limite_deducciones_pf_umas=config.tasas_sat.limite_deducciones_pf_umas,
        ),
        factores_cnsf=FactoresCNSFResponse(
            shock_acciones=float(config.factores_cnsf.shock_acciones),
            shock_bonos_gubernamentales=float(
                config.factores_cnsf.shock_bonos_gubernamentales
            ),
            shock_bonos_corporativos=float(
                config.factores_cnsf.shock_bonos_corporativos
            ),
            shock_inmuebles=float(config.factores_cnsf.shock_inmuebles),
            shocks_credito={
                k: float(v)
                for k, v in config.factores_cnsf.shocks_credito.items()
            },
            correlacion_vida_danos=float(
                config.factores_cnsf.correlacion_vida_danos
            ),
            correlacion_vida_inversion=float(
                config.factores_cnsf.correlacion_vida_inversion
            ),
            correlacion_danos_inversion=float(
                config.factores_cnsf.correlacion_danos_inversion
            ),
        ),
        factores_tecnicos=FactoresTecnicosResponse(
            tasa_interes_tecnico_vida=float(
                config.factores_tecnicos.tasa_interes_tecnico_vida
            ),
            tasa_interes_tecnico_pensiones=float(
                config.factores_tecnicos.tasa_interes_tecnico_pensiones
            ),
            edad_omega=config.factores_tecnicos.edad_omega,
            margen_seguridad_s114=float(
                config.factores_tecnicos.margen_seguridad_s114
            ),
        ),
    )


# -- Endpoints ----------------------------------------------------------------


@router.get("/{anio}", response_model=ConfigAnualResponse)
def get_config(anio: int):
    """Return the full regulatory configuration for a fiscal year.

    Loads all parameters (UMA, SAT rates, CNSF factors, technical factors)
    for the requested year.
    """
    config = _load_config_or_404(anio)
    return _config_to_response(config)


@router.get("/{anio}/uma", response_model=UMAResponse)
def get_uma(anio: int):
    """Return UMA values for a fiscal year.

    Returns the daily, monthly, and annual UMA (Unidad de Medida y
    Actualizacion) amounts.
    """
    config = _load_config_or_404(anio)
    return UMAResponse(
        uma_diaria=float(config.uma.uma_diaria),
        uma_mensual=float(config.uma.uma_mensual),
        uma_anual=float(config.uma.uma_anual),
    )


@router.get("/{anio}/tasas-sat", response_model=TasasSATResponse)
def get_tasas_sat(anio: int):
    """Return SAT tax rates for a fiscal year.

    Returns ISR withholding rates, corporate tax rate, IVA rate, and
    the personal deduction limit in UMAs.
    """
    config = _load_config_or_404(anio)
    return TasasSATResponse(
        tasa_retencion_rentas_vitalicias=float(
            config.tasas_sat.tasa_retencion_rentas_vitalicias
        ),
        tasa_retencion_retiros_ahorro=float(
            config.tasas_sat.tasa_retencion_retiros_ahorro
        ),
        tasa_isr_personas_morales=float(
            config.tasas_sat.tasa_isr_personas_morales
        ),
        tasa_iva=float(config.tasas_sat.tasa_iva),
        limite_deducciones_pf_umas=config.tasas_sat.limite_deducciones_pf_umas,
    )


@router.get("/{anio}/factores-cnsf", response_model=FactoresCNSFResponse)
def get_factores_cnsf(anio: int):
    """Return CNSF regulatory factors for a fiscal year.

    Returns market shocks by asset type, credit shocks by rating, and
    the correlation matrix used for RCS (Requerimiento de Capital de
    Solvencia) calculation.
    """
    config = _load_config_or_404(anio)
    return FactoresCNSFResponse(
        shock_acciones=float(config.factores_cnsf.shock_acciones),
        shock_bonos_gubernamentales=float(
            config.factores_cnsf.shock_bonos_gubernamentales
        ),
        shock_bonos_corporativos=float(
            config.factores_cnsf.shock_bonos_corporativos
        ),
        shock_inmuebles=float(config.factores_cnsf.shock_inmuebles),
        shocks_credito={
            k: float(v)
            for k, v in config.factores_cnsf.shocks_credito.items()
        },
        correlacion_vida_danos=float(
            config.factores_cnsf.correlacion_vida_danos
        ),
        correlacion_vida_inversion=float(
            config.factores_cnsf.correlacion_vida_inversion
        ),
        correlacion_danos_inversion=float(
            config.factores_cnsf.correlacion_danos_inversion
        ),
    )
