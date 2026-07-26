"""Esquemas para configuracion regulatoria y su trazabilidad.

Los perfiles anuales se mantienen por compatibilidad con v2.0, pero cada
perfil puede incluir ahora parametros con vigencia, fuente y nivel de soporte.
Esto evita presentar supuestos ilustrativos como si fueran valores oficiales.
"""

from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class DataStatus(StrEnum):
    """Estado de los datos usados por una configuracion."""

    OFFICIAL = "official"
    DERIVED = "derived"
    USER_SUPPLIED = "user_supplied"
    ILLUSTRATIVE = "illustrative"


class ValidationTier(StrEnum):
    """Nivel de respaldo que puede comunicarse a usuarios y APIs."""

    SUPPORTED = "supported"
    EXPERIMENTAL = "experimental"
    DEPRECATED = "deprecated"


class SourceReference(BaseModel):
    """Referencia primaria o documental de un parametro."""

    authority: str = Field(..., min_length=1, description="Autoridad emisora")
    document_title: str = Field(..., min_length=1, description="Titulo del documento")
    url: str = Field(..., min_length=1, description="URL estable de la fuente")
    publication_date: date | None = None
    retrieval_date: date = Field(default_factory=date.today)
    citation_detail: str | None = None


class RegulatoryParameter(BaseModel):
    """Valor regulatorio declarativo y efectivo-dated."""

    key: str = Field(..., min_length=1)
    value: Decimal | str
    unit: str = Field(..., min_length=1)
    effective_from: date
    effective_to: date | None = None
    source: SourceReference
    derivation: str | None = None
    status: DataStatus = DataStatus.OFFICIAL
    validation_tier: ValidationTier = ValidationTier.SUPPORTED

    @model_validator(mode="after")
    def validate_parameter(self) -> "RegulatoryParameter":
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("effective_to no puede ser anterior a effective_from")
        if self.status == DataStatus.DERIVED and not self.derivation:
            raise ValueError("Los parametros derivados deben documentar su derivacion")
        if self.status == DataStatus.OFFICIAL and not self.source.url.startswith(
            ("http://", "https://")
        ):
            raise ValueError("Los parametros oficiales requieren una URL de fuente")
        expected_units = {
            "uma.diaria": "MXN/dia",
            "uma.mensual": "MXN/mes",
            "uma.anual": "MXN/anio",
        }
        expected = expected_units.get(self.key)
        if expected and self.unit != expected:
            raise ValueError(f"Unidad inconsistente para {self.key}: se esperaba {expected}")
        return self


class IMSSConfig(BaseModel):
    """Parametros de transicion de semanas Ley 97 publicados por IMSS."""

    semanas_minimas_ley97: dict[int, int] = Field(default_factory=dict)
    source: SourceReference | None = None
    status: DataStatus = DataStatus.OFFICIAL
    validation_tier: ValidationTier = ValidationTier.SUPPORTED

    @model_validator(mode="after")
    def validate_source(self) -> "IMSSConfig":
        if self.status == DataStatus.OFFICIAL and self.source is None:
            raise ValueError("Los parametros IMSS oficiales requieren fuente")
        return self


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
    tasa_retencion_otros_ingresos: Decimal = Field(
        ..., ge=0, le=1, description="Retencion ISR sobre otros ingresos gravables"
    )
    tasa_isr_personas_morales: Decimal = Field(
        ..., ge=0, le=1, description="Tasa ISR personas morales"
    )
    tasa_iva: Decimal = Field(..., ge=0, le=1, description="Tasa IVA general")
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
    shock_inmuebles: Decimal = Field(..., ge=0, le=1, description="Shock a inmuebles")

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
        ...,
        ge=0,
        le=Decimal("0.10"),
        description="Tasa de interes tecnico maxima para vida (CNSF: 5.5%)",
    )
    tasa_interes_tecnico_pensiones: Decimal = Field(
        ..., ge=0, le=Decimal("0.10"), description="Tasa de interes tecnico para pensiones"
    )
    edad_omega: int = Field(
        ..., ge=90, le=130, description="Edad maxima de las tablas de mortalidad"
    )
    margen_seguridad_s114: Decimal = Field(
        ...,
        ge=0,
        le=Decimal("0.20"),
        description="Margen de seguridad para reservas tecnicas (Circular S-11.4)",
    )


class ConfigAnual(BaseModel):
    """Configuracion regulatoria completa para un ano fiscal."""

    anio: int = Field(..., ge=2020, le=2100, description="Ano fiscal")
    uma: UMAConfig
    tasas_sat: TasasSAT
    factores_cnsf: FactoresCNSF
    factores_tecnicos: FactoresTecnicos
    effective_from: date | None = Field(
        default=None, description="Inicio de vigencia del perfil (inclusive)"
    )
    effective_to: date | None = Field(
        default=None, description="Fin de vigencia del perfil (inclusive)"
    )
    parametros: list[RegulatoryParameter] = Field(default_factory=list)
    imss: IMSSConfig = Field(default_factory=IMSSConfig)
    validation_tier: ValidationTier = ValidationTier.EXPERIMENTAL

    @model_validator(mode="after")
    def validate_dates_and_keys(self) -> "ConfigAnual":
        if self.effective_from and self.effective_to and self.effective_to < self.effective_from:
            raise ValueError("La vigencia del perfil es invalida")
        keys = [p.key for p in self.parametros]
        if len(keys) != len(set(keys)):
            raise ValueError("No puede haber claves regulatorias duplicadas")
        return self

    def parametros_vigentes(self, fecha: date) -> list[RegulatoryParameter]:
        """Devuelve parametros del perfil aplicables en ``fecha``."""
        return [
            p
            for p in self.parametros
            if p.effective_from <= fecha and (p.effective_to is None or fecha <= p.effective_to)
        ]

    def provenance(self) -> dict[str, Any]:
        """Serializa un resumen de fuentes para reportes y APIs."""
        return {
            p.key: {
                "value": str(p.value),
                "unit": p.unit,
                "status": p.status.value,
                "validation_tier": p.validation_tier.value,
                "source": p.source.model_dump(mode="json"),
            }
            for p in self.parametros
        }
