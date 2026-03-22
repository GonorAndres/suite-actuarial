"""
Generador de reportes de inversiones para CNSF.

Convierte datos de inversiones estructurados en DataFrames listos
para exportar a Excel o CSV.
"""

from decimal import Decimal

import pandas as pd

from suite_actuarial.reportes.models import ReporteInversiones, TipoActivoInversion


class GeneradorReporteInversiones:
    """
    Genera reportes de inversiones en formato DataFrame.

    Ejemplo:
        >>> reporte = ReporteInversiones(metadata=metadata, datos_por_activo=datos)
        >>> generador = GeneradorReporteInversiones()
        >>> df = generador.generar_dataframe(reporte)
    """

    def generar_dataframe(self, reporte: ReporteInversiones) -> pd.DataFrame:
        """
        Genera DataFrame con datos de inversiones por tipo de activo.

        Args:
            reporte: Reporte de inversiones completo

        Returns:
            DataFrame con columnas: Tipo Activo, Valor Mercado, Valor Libros,
            Ganancia No Realizada, Rendimiento Trimestre %, Composición %
        """
        if not reporte.datos_por_activo:
            return pd.DataFrame()

        total_mercado = reporte.total_valor_mercado

        rows = []
        for datos in reporte.datos_por_activo:
            composicion_pct = (
                (datos.valor_mercado / total_mercado * 100) if total_mercado > 0 else 0
            )

            rows.append(
                {
                    "Tipo de Activo": self._formatear_nombre_activo(datos.tipo_activo),
                    "Valor de Mercado": float(datos.valor_mercado),
                    "Valor en Libros": float(datos.valor_libros),
                    "Ganancia No Realizada": float(datos.ganancia_no_realizada),
                    "Rendimiento Trimestre %": float(datos.rendimiento_trimestre * 100),
                    "Composición %": float(composicion_pct),
                }
            )

        df = pd.DataFrame(rows)

        # Agregar fila de totales
        totales = {
            "Tipo de Activo": "TOTAL",
            "Valor de Mercado": df["Valor de Mercado"].sum(),
            "Valor en Libros": df["Valor en Libros"].sum(),
            "Ganancia No Realizada": df["Ganancia No Realizada"].sum(),
            "Rendimiento Trimestre %": (
                (df["Valor de Mercado"].sum() / df["Valor en Libros"].sum() - 1) * 100
                if df["Valor en Libros"].sum() > 0
                else 0
            ),
            "Composición %": df["Composición %"].sum(),
        }

        df = pd.concat([df, pd.DataFrame([totales])], ignore_index=True)

        return df

    def generar_resumen(self, reporte: ReporteInversiones) -> dict[str, any]:
        """
        Genera resumen ejecutivo del reporte de inversiones.

        Args:
            reporte: Reporte de inversiones completo

        Returns:
            Diccionario con métricas clave del trimestre
        """
        if not reporte.datos_por_activo:
            return {}

        total_mercado = reporte.total_valor_mercado
        total_libros = reporte.total_valor_libros
        total_ganancia = reporte.total_ganancia_no_realizada

        # Rendimiento total de la cartera
        rendimiento_total = (
            ((total_mercado / total_libros) - 1) * 100 if total_libros > 0 else 0
        )

        # Activo con mayor valor
        activo_top = max(reporte.datos_por_activo, key=lambda x: x.valor_mercado)
        composicion_top = (
            (activo_top.valor_mercado / total_mercado * 100) if total_mercado > 0 else 0
        )

        # Activo con mejor rendimiento
        activo_mejor_rend = max(
            reporte.datos_por_activo, key=lambda x: x.rendimiento_trimestre
        )

        # Composición por tipo
        composicion = reporte.obtener_composicion_pct()

        return {
            "trimestre": f"{reporte.metadata.trimestre.value} {reporte.metadata.anio}",
            "total_valor_mercado": float(total_mercado),
            "total_valor_libros": float(total_libros),
            "ganancia_no_realizada": float(total_ganancia),
            "rendimiento_cartera_pct": float(
                Decimal(str(rendimiento_total)).quantize(Decimal("0.01"))
            ),
            "activo_principal": self._formatear_nombre_activo(activo_top.tipo_activo),
            "composicion_activo_principal_pct": float(
                Decimal(str(composicion_top)).quantize(Decimal("0.01"))
            ),
            "activo_mejor_rendimiento": self._formatear_nombre_activo(
                activo_mejor_rend.tipo_activo
            ),
            "mejor_rendimiento_pct": float(
                (activo_mejor_rend.rendimiento_trimestre * 100).quantize(
                    Decimal("0.01")
                )
            ),
            "numero_tipos_activos": len(reporte.datos_por_activo),
            "composicion_detallada": {
                self._formatear_nombre_activo(
                    TipoActivoInversion(tipo)
                ): float(pct)
                for tipo, pct in composicion.items()
            },
        }

    def _formatear_nombre_activo(self, activo: TipoActivoInversion) -> str:
        """Convierte enum de activo a nombre legible"""
        nombres = {
            TipoActivoInversion.VALORES_GUBERNAMENTALES: "Valores Gubernamentales",
            TipoActivoInversion.VALORES_PRIVADOS: "Valores Privados",
            TipoActivoInversion.ACCIONES: "Acciones",
            TipoActivoInversion.INMUEBLES: "Inmuebles",
            TipoActivoInversion.PRESTAMOS_HIPOTECARIOS: "Préstamos Hipotecarios",
            TipoActivoInversion.DEPOSITOS: "Depósitos",
            TipoActivoInversion.OTROS: "Otros",
        }
        return nombres.get(activo, activo.value)
