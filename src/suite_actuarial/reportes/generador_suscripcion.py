"""
Generador de reportes de suscripción para CNSF.

Convierte datos de suscripción estructurados en DataFrames listos
para exportar a Excel o CSV.
"""

from decimal import Decimal

import pandas as pd

from suite_actuarial.reportes.models import ReporteSuscripcion, TipoRamo


class GeneradorReporteSuscripcion:
    """
    Genera reportes de suscripción en formato DataFrame.

    Ejemplo:
        >>> from suite_actuarial.reportes.models import (
        ...     MetadatosReporte,
        ...     DatosSuscripcionRamo,
        ...     TrimesteCNSF
        ... )
        >>> from datetime import date
        >>> from decimal import Decimal
        >>>
        >>> metadata = MetadatosReporte(
        ...     clave_aseguradora="A0123",
        ...     nombre_aseguradora="Seguros XYZ",
        ...     trimestre=TrimesteCNSF.Q1,
        ...     anio=2024,
        ...     fecha_presentacion=date(2024, 4, 30)
        ... )
        >>>
        >>> datos = [
        ...     DatosSuscripcionRamo(
        ...         ramo=TipoRamo.AUTOS,
        ...         primas_emitidas=Decimal("50000000"),
        ...         primas_devengadas=Decimal("48000000"),
        ...         primas_canceladas=Decimal("2000000"),
        ...         numero_polizas=15000,
        ...         suma_asegurada_total=Decimal("2000000000")
        ...     )
        ... ]
        >>>
        >>> reporte = ReporteSuscripcion(metadata=metadata, datos_por_ramo=datos)
        >>> generador = GeneradorReporteSuscripcion()
        >>> df = generador.generar_dataframe(reporte)
    """

    def generar_dataframe(self, reporte: ReporteSuscripcion) -> pd.DataFrame:
        """
        Genera DataFrame con datos de suscripción por ramo.

        Args:
            reporte: Reporte de suscripción completo

        Returns:
            DataFrame con columnas: Ramo, Primas Emitidas, Primas Devengadas,
            Primas Canceladas, Número de Pólizas, Suma Asegurada Total,
            Primas Netas, Prima Promedio
        """
        if not reporte.datos_por_ramo:
            return pd.DataFrame()

        rows = []
        for datos in reporte.datos_por_ramo:
            primas_netas = datos.primas_emitidas - datos.primas_canceladas
            prima_promedio = (
                primas_netas / datos.numero_polizas if datos.numero_polizas > 0 else 0
            )

            rows.append(
                {
                    "Ramo": self._formatear_nombre_ramo(datos.ramo),
                    "Primas Emitidas": float(datos.primas_emitidas),
                    "Primas Devengadas": float(datos.primas_devengadas),
                    "Primas Canceladas": float(datos.primas_canceladas),
                    "Primas Netas": float(primas_netas),
                    "Número de Pólizas": datos.numero_polizas,
                    "Suma Asegurada Total": float(datos.suma_asegurada_total),
                    "Prima Promedio": float(prima_promedio),
                }
            )

        df = pd.DataFrame(rows)

        # Agregar fila de totales
        totales = {
            "Ramo": "TOTAL",
            "Primas Emitidas": df["Primas Emitidas"].sum(),
            "Primas Devengadas": df["Primas Devengadas"].sum(),
            "Primas Canceladas": df["Primas Canceladas"].sum(),
            "Primas Netas": df["Primas Netas"].sum(),
            "Número de Pólizas": df["Número de Pólizas"].sum(),
            "Suma Asegurada Total": df["Suma Asegurada Total"].sum(),
            "Prima Promedio": (
                df["Primas Netas"].sum() / df["Número de Pólizas"].sum()
                if df["Número de Pólizas"].sum() > 0
                else 0
            ),
        }

        df = pd.concat([df, pd.DataFrame([totales])], ignore_index=True)

        return df

    def generar_resumen(self, reporte: ReporteSuscripcion) -> dict[str, any]:
        """
        Genera resumen ejecutivo del reporte de suscripción.

        Args:
            reporte: Reporte de suscripción completo

        Returns:
            Diccionario con métricas clave del trimestre
        """
        if not reporte.datos_por_ramo:
            return {}

        total_primas_emitidas = reporte.total_primas_emitidas
        total_primas_devengadas = reporte.total_primas_devengadas
        total_primas_canceladas = sum(
            d.primas_canceladas for d in reporte.datos_por_ramo
        )
        total_polizas = sum(d.numero_polizas for d in reporte.datos_por_ramo)

        # Tasa de cancelación
        tasa_cancelacion = (
            (total_primas_canceladas / total_primas_emitidas * 100)
            if total_primas_emitidas > 0
            else Decimal("0")
        )

        # Ramo con más primas
        ramo_top = max(reporte.datos_por_ramo, key=lambda x: x.primas_devengadas)

        # Concentración del ramo top
        concentracion_top = (
            (ramo_top.primas_devengadas / total_primas_devengadas * 100)
            if total_primas_devengadas > 0
            else Decimal("0")
        )

        return {
            "trimestre": f"{reporte.metadata.trimestre.value} {reporte.metadata.anio}",
            "total_primas_emitidas": float(total_primas_emitidas),
            "total_primas_devengadas": float(total_primas_devengadas),
            "total_primas_canceladas": float(total_primas_canceladas),
            "tasa_cancelacion_pct": float(tasa_cancelacion.quantize(Decimal("0.01"))),
            "total_polizas": total_polizas,
            "total_suma_asegurada": float(reporte.total_suma_asegurada),
            "ramo_principal": self._formatear_nombre_ramo(ramo_top.ramo),
            "concentracion_ramo_principal_pct": float(
                concentracion_top.quantize(Decimal("0.01"))
            ),
            "numero_ramos_activos": len(reporte.datos_por_ramo),
        }

    def _formatear_nombre_ramo(self, ramo: TipoRamo) -> str:
        """Convierte enum de ramo a nombre legible"""
        nombres = {
            TipoRamo.VIDA_INDIVIDUAL: "Vida Individual",
            TipoRamo.VIDA_GRUPO: "Vida Grupo",
            TipoRamo.PENSIONES: "Pensiones",
            TipoRamo.AUTOS: "Autos",
            TipoRamo.INCENDIO: "Incendio",
            TipoRamo.GASTOS_MEDICOS: "Gastos Médicos",
            TipoRamo.RESPONSABILIDAD_CIVIL: "Responsabilidad Civil",
            TipoRamo.DIVERSOS: "Diversos",
            TipoRamo.MARITIMO: "Marítimo",
            TipoRamo.TERREMOTO: "Terremoto",
        }
        return nombres.get(ramo, ramo.value)
