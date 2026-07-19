"""Fuentes y registros regulatorios revisados incluidos en el paquete."""

from datetime import date
from decimal import Decimal

from suite_actuarial.config.schema import (
    DataStatus,
    IMSSConfig,
    RegulatoryParameter,
    SourceReference,
    ValidationTier,
)

UMA_SOURCE = SourceReference(
    authority="INEGI",
    document_title="Unidad de Medida y Actualizacion 2026",
    url="https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2026/uma/uma2026.pdf",
    publication_date=date(2026, 1, 9),
    retrieval_date=date(2026, 7, 19),
    citation_detail="Valores de UMA diaria, mensual y anual; vigencia desde 1 de febrero.",
)

IMSS_SOURCE = SourceReference(
    authority="IMSS",
    document_title="Semanas minimas de cotizacion Ley 97 (transicion)",
    url="https://www.imss.gob.mx/tramites/imss02025a.?combine=SEMANAS+",
    retrieval_date=date(2026, 7, 19),
    citation_detail="Tabla transitoria de semanas minimas para pension Ley 97.",
)

SAT_SOURCE = SourceReference(
    authority="SAT",
    document_title="Conoce las deducciones personales",
    url="https://wwwmat.sat.gob.mx/consulta/23972/conoce-las-deducciones-personales",
    retrieval_date=date(2026, 7, 19),
    citation_detail="Referencia de limites y condiciones; la aplicacion depende del contribuyente.",
)

CNSF_SOURCE = SourceReference(
    authority="CNSF",
    document_title="CUSF, Titulo 5.1",
    url="https://lisfcusf.cnsf.gob.mx/CUSF/CUSF5_1",
    retrieval_date=date(2026, 7, 19),
    citation_detail="Marco de valuacion; los factores legacy del paquete no son una replica CUSF.",
)


def uma_parameters(
    *,
    diaria: str,
    mensual: str,
    anual: str,
    year: int,
) -> list[RegulatoryParameter]:
    """Construye los tres registros UMA con vigencia legal de febrero."""
    start = date(year, 2, 1)
    end = date(year + 1, 1, 31)
    return [
        RegulatoryParameter(
            key="uma.diaria",
            value=Decimal(diaria),
            unit="MXN/dia",
            effective_from=start,
            effective_to=end,
            source=UMA_SOURCE,
            status=DataStatus.OFFICIAL,
            validation_tier=ValidationTier.SUPPORTED,
        ),
        RegulatoryParameter(
            key="uma.mensual",
            value=Decimal(mensual),
            unit="MXN/mes",
            effective_from=start,
            effective_to=end,
            source=UMA_SOURCE,
            derivation="UMA diaria x 30.4, redondeada conforme al aviso de INEGI",
            status=DataStatus.DERIVED,
            validation_tier=ValidationTier.SUPPORTED,
        ),
        RegulatoryParameter(
            key="uma.anual",
            value=Decimal(anual),
            unit="MXN/anio",
            effective_from=start,
            effective_to=end,
            source=UMA_SOURCE,
            derivation="UMA mensual x 12 (Ley UMA, Art. 4, fracc. III), conforme al aviso de INEGI",
            status=DataStatus.DERIVED,
            validation_tier=ValidationTier.SUPPORTED,
        ),
    ]


def imss_transition(year: int) -> IMSSConfig:
    """Devuelve la tabla oficial de semanas aplicable al perfil anual."""
    values = {2024: 825, 2025: 850, 2026: 875}
    return IMSSConfig(
        semanas_minimas_ley97={year: values[year]},
        source=IMSS_SOURCE,
        status=DataStatus.OFFICIAL,
        validation_tier=ValidationTier.SUPPORTED,
    )


def legacy_scenario_parameters(year: int) -> list[RegulatoryParameter]:
    """Registra constantes legacy sin presentarlas como datos oficiales."""
    start = date(year, 2, 1)
    end = date(year + 1, 1, 31)
    return [
        RegulatoryParameter(
            key="sat.legacy_rates",
            value="profile-field",
            unit="scenario",
            effective_from=start,
            effective_to=end,
            source=SAT_SOURCE,
            status=DataStatus.ILLUSTRATIVE,
            validation_tier=ValidationTier.EXPERIMENTAL,
        ),
        RegulatoryParameter(
            key="cnsf.legacy_rcs_factors",
            value="profile-field",
            unit="scenario",
            effective_from=start,
            effective_to=end,
            source=CNSF_SOURCE,
            status=DataStatus.ILLUSTRATIVE,
            validation_tier=ValidationTier.EXPERIMENTAL,
        ),
        RegulatoryParameter(
            key="cnsf.legacy_technical_factors",
            value="profile-field",
            unit="scenario",
            effective_from=start,
            effective_to=end,
            source=CNSF_SOURCE,
            status=DataStatus.ILLUSTRATIVE,
            validation_tier=ValidationTier.EXPERIMENTAL,
        ),
    ]
