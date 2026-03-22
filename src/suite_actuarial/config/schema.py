"""Esquemas Pydantic para configuracion regulatoria anual."""

from decimal import Decimal

from pydantic import BaseModel, Field


class UMAConfig(BaseModel):
    """Unidad de Medida y Actualizacion."""

    uma_diaria: Decimal = Field(..., gt=0, description="UMA diaria en MXN")
    uma_mensual: Decimal = Field(..., gt=0, description="UMA mensual (diaria * 30.4)")
    uma_anual: Decimal = Field(..., gt=0, description="UMA anual (diaria * 365)")


class TasasSAT(BaseModel):
    """Tasas fiscales del SAT / LISR."""

    tasa_retencion_rentas_vitalicias: Decimal = Field(
        ..., ge=0, le=1, description="Retencion ISR sobre rentas vitalicias"
    )
    tasa_retencion_retiros_ahorro: Decimal = Field(
        ..., ge=0, le=1, description="Retencion ISR sobre retiros de ahorro"
    )
    tasa_isr_personas_morales: Decimal = Field(
        ..., ge=0, le=1, description="Tasa ISR personas morales"
    )
    tasa_iva: Decimal = Field(
        ..., ge=0, le=1, description="Tasa IVA general"
    )
    limite_deducciones_pf_umas: int = Field(
        ..., ge=1, description="Limite de deducciones personales en UMAs (Art. 151 LISR)"
    )


class FactoresCNSF(BaseModel):
    """Factores regulatorios de la CNSF para calculo de RCS."""

    # Shocks de mercado por tipo de activo
    shock_acciones: Decimal = Field(
        ..., ge=0, le=1, description="Shock a acciones (ej: 0.35 = 35%)"
    )
    shock_bonos_gubernamentales: Decimal = Field(
        ..., ge=0, le=1, description="Shock a bonos gubernamentales"
    )
    shock_bonos_corporativos: Decimal = Field(
        ..., ge=0, le=1, description="Shock a bonos corporativos"
    )
    shock_inmuebles: Decimal = Field(
        ..., ge=0, le=1, description="Shock a inmuebles"
    )

    # Shocks de credito por calificacion
    shocks_credito: dict[str, Decimal] = Field(
        ..., description="Shock de credito por calificacion (AAA, AA, A, BBB, ...)"
    )

    # Matriz de correlacion (valores entre -1 y 1)
    correlacion_vida_danos: Decimal = Field(
        ..., ge=-1, le=1, description="Correlacion RCS vida vs danos"
    )
    correlacion_vida_inversion: Decimal = Field(
        ..., ge=-1, le=1, description="Correlacion RCS vida vs inversion"
    )
    correlacion_danos_inversion: Decimal = Field(
        ..., ge=-1, le=1, description="Correlacion RCS danos vs inversion"
    )


class FactoresTecnicos(BaseModel):
    """Parametros tecnicos actuariales."""

    tasa_interes_tecnico_vida: Decimal = Field(
        ..., ge=0, le=Decimal("0.10"),
        description="Tasa de interes tecnico maxima para vida (CNSF: 5.5%)"
    )
    tasa_interes_tecnico_pensiones: Decimal = Field(
        ..., ge=0, le=Decimal("0.10"),
        description="Tasa de interes tecnico para pensiones"
    )
    edad_omega: int = Field(
        ..., ge=90, le=130, description="Edad maxima de las tablas de mortalidad"
    )
    margen_seguridad_s114: Decimal = Field(
        ..., ge=0, le=Decimal("0.20"),
        description="Margen de seguridad para reservas tecnicas (Circular S-11.4)"
    )


class ConfigAnual(BaseModel):
    """Configuracion regulatoria completa para un ano fiscal."""

    anio: int = Field(..., ge=2020, le=2100, description="Ano fiscal")
    uma: UMAConfig
    tasas_sat: TasasSAT
    factores_cnsf: FactoresCNSF
    factores_tecnicos: FactoresTecnicos
