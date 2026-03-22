"""
Módulo de reportes regulatorios CNSF.

Este módulo proporciona herramientas para generar reportes trimestrales
que las aseguradoras deben presentar a la CNSF (Comisión Nacional de
Seguros y Fianzas de México).

Componentes principales:
- Modelos Pydantic para estructurar datos de reportes
- Generadores que convierten datos a DataFrames
- Exportadores a Excel y CSV

Ejemplo de uso:
    >>> from decimal import Decimal
    >>> from datetime import date
    >>> from suite_actuarial.reportes.models import (
    ...     MetadatosReporte,
    ...     DatosSuscripcionRamo,
    ...     ReporteSuscripcion,
    ...     TipoRamo,
    ...     TrimesteCNSF
    ... )
    >>> from suite_actuarial.reportes import (
    ...     GeneradorReporteSuscripcion,
    ...     ExportadorExcel
    ... )
    >>>
    >>> # Crear metadatos
    >>> metadata = MetadatosReporte(
    ...     clave_aseguradora="A0123",
    ...     nombre_aseguradora="Seguros XYZ S.A.",
    ...     trimestre=TrimesteCNSF.Q1,
    ...     anio=2024,
    ...     fecha_presentacion=date(2024, 4, 30)
    ... )
    >>>
    >>> # Crear datos de suscripción
    >>> datos_autos = DatosSuscripcionRamo(
    ...     ramo=TipoRamo.AUTOS,
    ...     primas_emitidas=Decimal("50000000"),
    ...     primas_devengadas=Decimal("48000000"),
    ...     primas_canceladas=Decimal("2000000"),
    ...     numero_polizas=15000,
    ...     suma_asegurada_total=Decimal("2000000000")
    ... )
    >>>
    >>> # Generar reporte
    >>> reporte = ReporteSuscripcion(
    ...     metadata=metadata,
    ...     datos_por_ramo=[datos_autos]
    ... )
    >>>
    >>> # Convertir a DataFrame
    >>> generador = GeneradorReporteSuscripcion()
    >>> df = generador.generar_dataframe(reporte)
    >>>
    >>> # Exportar a Excel
    >>> exportador = ExportadorExcel()
    >>> exportador.exportar_reporte_completo(
    ...     ruta_salida="reporte_Q1_2024.xlsx",
    ...     df_suscripcion=df,
    ...     metadata=metadata.__dict__
    ... )
"""

from suite_actuarial.reportes.exportadores import ExportadorCSV, ExportadorExcel
from suite_actuarial.reportes.generador_inversiones import (
    GeneradorReporteInversiones,
)
from suite_actuarial.reportes.generador_rcs import GeneradorReporteRCS
from suite_actuarial.reportes.generador_siniestros import GeneradorReporteSiniestros
from suite_actuarial.reportes.generador_suscripcion import (
    GeneradorReporteSuscripcion,
)
from suite_actuarial.reportes.models import (
    DatosInversionActivo,
    DatosReporteRCS,
    DatosSiniestrosRamo,
    DatosSuscripcionRamo,
    MetadatosReporte,
    ReporteInversiones,
    ReporteRCS,
    ReporteSiniestros,
    ReporteSuscripcion,
    TipoActivoInversion,
    TipoRamo,
    TrimesteCNSF,
)

__all__ = [
    # Modelos
    "MetadatosReporte",
    "TipoRamo",
    "TrimesteCNSF",
    "TipoActivoInversion",
    "DatosSuscripcionRamo",
    "DatosSiniestrosRamo",
    "DatosInversionActivo",
    "DatosReporteRCS",
    "ReporteSuscripcion",
    "ReporteSiniestros",
    "ReporteInversiones",
    "ReporteRCS",
    # Generadores
    "GeneradorReporteSuscripcion",
    "GeneradorReporteSiniestros",
    "GeneradorReporteInversiones",
    "GeneradorReporteRCS",
    # Exportadores
    "ExportadorExcel",
    "ExportadorCSV",
]
