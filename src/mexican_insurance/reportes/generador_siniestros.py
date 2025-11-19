"""
Generador de reportes de siniestros para CNSF.

Convierte datos de siniestros estructurados en DataFrames listos
para exportar a Excel o CSV.
"""

from decimal import Decimal
from typing import Dict

import pandas as pd

from mexican_insurance.reportes.models import ReporteSiniestros, TipoRamo


class GeneradorReporteSiniestros:
    """
    Genera reportes de siniestros en formato DataFrame.

    Ejemplo:
        >>> reporte = ReporteSiniestros(metadata=metadata, datos_por_ramo=datos)
        >>> generador = GeneradorReporteSiniestros()
        >>> df = generador.generar_dataframe(reporte)
    """

    def generar_dataframe(self, reporte: ReporteSiniestros) -> pd.DataFrame:
        """
        Genera DataFrame con datos de siniestros por ramo.

        Args:
            reporte: Reporte de siniestros completo

        Returns:
            DataFrame con columnas: Ramo, Siniestros Ocurridos, Siniestros Pagados,
            Reserva Siniestros, Número Siniestros, Pendientes, Siniestralidad %,
            Costo Promedio
        """
        if not reporte.datos_por_ramo:
            return pd.DataFrame()

        rows = []
        for datos in reporte.datos_por_ramo:
            # Costo promedio por siniestro
            costo_promedio = (
                datos.siniestros_pagados / datos.numero_siniestros
                if datos.numero_siniestros > 0
                else 0
            )

            rows.append(
                {
                    "Ramo": self._formatear_nombre_ramo(datos.ramo),
                    "Siniestros Ocurridos": float(datos.siniestros_ocurridos),
                    "Siniestros Pagados": float(datos.siniestros_pagados),
                    "Reserva Siniestros": float(datos.reserva_siniestros),
                    "Número Siniestros": datos.numero_siniestros,
                    "Pendientes": datos.numero_siniestros_pendientes,
                    "Costo Promedio": float(costo_promedio),
                }
            )

        df = pd.DataFrame(rows)

        # Agregar fila de totales
        totales = {
            "Ramo": "TOTAL",
            "Siniestros Ocurridos": df["Siniestros Ocurridos"].sum(),
            "Siniestros Pagados": df["Siniestros Pagados"].sum(),
            "Reserva Siniestros": df["Reserva Siniestros"].sum(),
            "Número Siniestros": df["Número Siniestros"].sum(),
            "Pendientes": df["Pendientes"].sum(),
            "Costo Promedio": (
                df["Siniestros Pagados"].sum() / df["Número Siniestros"].sum()
                if df["Número Siniestros"].sum() > 0
                else 0
            ),
        }

        df = pd.concat([df, pd.DataFrame([totales])], ignore_index=True)

        return df

    def generar_resumen(self, reporte: ReporteSiniestros) -> Dict[str, any]:
        """
        Genera resumen ejecutivo del reporte de siniestros.

        Args:
            reporte: Reporte de siniestros completo

        Returns:
            Diccionario con métricas clave del trimestre
        """
        if not reporte.datos_por_ramo:
            return {}

        total_ocurridos = reporte.total_siniestros_ocurridos
        total_pagados = reporte.total_siniestros_pagados
        total_reservas = reporte.total_reservas
        total_casos = sum(d.numero_siniestros for d in reporte.datos_por_ramo)
        total_pendientes = sum(
            d.numero_siniestros_pendientes for d in reporte.datos_por_ramo
        )

        # Porcentaje de casos pendientes
        pct_pendientes = (
            Decimal(total_pendientes) / Decimal(total_casos) * 100
            if total_casos > 0
            else Decimal("0")
        )

        # Ramo con más siniestros
        ramo_top = max(reporte.datos_por_ramo, key=lambda x: x.siniestros_ocurridos)

        # Ramo con mayor costo promedio
        ramos_con_casos = [d for d in reporte.datos_por_ramo if d.numero_siniestros > 0]
        if ramos_con_casos:
            ramo_mayor_costo = max(
                ramos_con_casos,
                key=lambda x: x.siniestros_pagados / x.numero_siniestros,
            )
            mayor_costo_promedio = (
                ramo_mayor_costo.siniestros_pagados / ramo_mayor_costo.numero_siniestros
            )
        else:
            ramo_mayor_costo = None
            mayor_costo_promedio = Decimal("0")

        return {
            "trimestre": f"{reporte.metadata.trimestre.value} {reporte.metadata.anio}",
            "total_siniestros_ocurridos": float(total_ocurridos),
            "total_siniestros_pagados": float(total_pagados),
            "total_reserva_siniestros": float(total_reservas),
            "numero_casos": total_casos,
            "numero_pendientes": total_pendientes,
            "pct_casos_pendientes": float(pct_pendientes.quantize(Decimal("0.01"))),
            "costo_promedio_general": float(
                total_pagados / total_casos if total_casos > 0 else 0
            ),
            "ramo_mas_siniestros": self._formatear_nombre_ramo(ramo_top.ramo),
            "ramo_mayor_costo_promedio": (
                self._formatear_nombre_ramo(ramo_mayor_costo.ramo)
                if ramo_mayor_costo
                else "N/A"
            ),
            "mayor_costo_promedio": float(mayor_costo_promedio),
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
