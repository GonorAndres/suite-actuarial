"""
Generador de reportes de RCS para CNSF.

Convierte datos de RCS estructurados en DataFrames listos
para exportar a Excel o CSV.
"""

from decimal import Decimal

import pandas as pd

from mexican_insurance.reportes.models import ReporteRCS


class GeneradorReporteRCS:
    """
    Genera reportes de RCS en formato DataFrame.

    Ejemplo:
        >>> reporte = ReporteRCS(metadata=metadata, datos_rcs=datos)
        >>> generador = GeneradorReporteRCS()
        >>> df = generador.generar_dataframe(reporte)
    """

    def generar_dataframe(self, reporte: ReporteRCS) -> pd.DataFrame:
        """
        Genera DataFrame con datos de RCS por componente.

        Args:
            reporte: Reporte de RCS completo

        Returns:
            DataFrame con columnas: Componente, Monto, % del RCS Total
        """
        datos = reporte.datos_rcs
        rcs_total = datos.rcs_total

        rows = [
            {
                "Componente": "RCS Suscripción Vida",
                "Monto": float(datos.rcs_suscripcion_vida),
                "% del RCS Total": float(
                    (datos.rcs_suscripcion_vida / rcs_total * 100).quantize(
                        Decimal("0.01")
                    )
                ),
            },
            {
                "Componente": "RCS Suscripción Daños",
                "Monto": float(datos.rcs_suscripcion_danos),
                "% del RCS Total": float(
                    (datos.rcs_suscripcion_danos / rcs_total * 100).quantize(
                        Decimal("0.01")
                    )
                ),
            },
            {
                "Componente": "RCS Inversión",
                "Monto": float(datos.rcs_inversion),
                "% del RCS Total": float(
                    (datos.rcs_inversion / rcs_total * 100).quantize(Decimal("0.01"))
                ),
            },
        ]

        # Agregar RCS operacional si > 0
        if datos.rcs_operacional > 0:
            rows.append(
                {
                    "Componente": "RCS Operacional",
                    "Monto": float(datos.rcs_operacional),
                    "% del RCS Total": float(
                        (datos.rcs_operacional / rcs_total * 100).quantize(
                            Decimal("0.01")
                        )
                    ),
                }
            )

        # Fila de total RCS
        rows.append(
            {
                "Componente": "RCS TOTAL",
                "Monto": float(rcs_total),
                "% del RCS Total": 100.0,
            }
        )

        # Separador
        rows.append(
            {"Componente": "", "Monto": None, "% del RCS Total": None}
        )

        # Capital disponible
        rows.extend(
            [
                {
                    "Componente": "Capital Pagado",
                    "Monto": float(datos.capital_pagado),
                    "% del RCS Total": float(
                        (datos.capital_pagado / rcs_total * 100).quantize(
                            Decimal("0.01")
                        )
                    ),
                },
                {
                    "Componente": "Superávit",
                    "Monto": float(datos.superavit),
                    "% del RCS Total": float(
                        (datos.superavit / rcs_total * 100).quantize(Decimal("0.01"))
                    ),
                },
                {
                    "Componente": "Capital Disponible TOTAL",
                    "Monto": float(datos.capital_disponible),
                    "% del RCS Total": float(
                        (datos.capital_disponible / rcs_total * 100).quantize(
                            Decimal("0.01")
                        )
                    ),
                },
            ]
        )

        # Separador
        rows.append(
            {"Componente": "", "Monto": None, "% del RCS Total": None}
        )

        # Excedente/Déficit
        rows.append(
            {
                "Componente": "Excedente / Déficit",
                "Monto": float(datos.excedente_deficit),
                "% del RCS Total": float(
                    (datos.excedente_deficit / rcs_total * 100).quantize(
                        Decimal("0.01")
                    )
                ),
            }
        )

        return pd.DataFrame(rows)

    def generar_dataframe_ratio(self, reporte: ReporteRCS) -> pd.DataFrame:
        """
        Genera DataFrame con ratios de solvencia.

        Args:
            reporte: Reporte de RCS completo

        Returns:
            DataFrame con métricas de solvencia
        """
        datos = reporte.datos_rcs

        rows = [
            {
                "Métrica": "Ratio de Solvencia",
                "Valor": float(datos.ratio_solvencia.quantize(Decimal("0.0001"))),
                "Formato": f"{float(datos.ratio_solvencia * 100):.2f}%",
            },
            {
                "Métrica": "Cumple Regulación",
                "Valor": 1 if datos.cumple_regulacion else 0,
                "Formato": "SÍ" if datos.cumple_regulacion else "NO",
            },
            {
                "Métrica": "Excedente / Déficit",
                "Valor": float(datos.excedente_deficit),
                "Formato": f"${float(datos.excedente_deficit):,.0f}",
            },
            {
                "Métrica": "Capital Requerido (RCS)",
                "Valor": float(datos.rcs_total),
                "Formato": f"${float(datos.rcs_total):,.0f}",
            },
            {
                "Métrica": "Capital Disponible",
                "Valor": float(datos.capital_disponible),
                "Formato": f"${float(datos.capital_disponible):,.0f}",
            },
        ]

        return pd.DataFrame(rows)

    def generar_resumen(self, reporte: ReporteRCS) -> dict[str, any]:
        """
        Genera resumen ejecutivo del reporte de RCS.

        Args:
            reporte: Reporte de RCS completo

        Returns:
            Diccionario con métricas clave del trimestre
        """
        datos = reporte.datos_rcs

        # Componente dominante del RCS
        componentes = {
            "Suscripción Vida": datos.rcs_suscripcion_vida,
            "Suscripción Daños": datos.rcs_suscripcion_danos,
            "Inversión": datos.rcs_inversion,
        }
        if datos.rcs_operacional > 0:
            componentes["Operacional"] = datos.rcs_operacional

        componente_principal = max(componentes, key=componentes.get)
        valor_componente_principal = componentes[componente_principal]
        pct_componente_principal = (
            valor_componente_principal / datos.rcs_total * 100
        ).quantize(Decimal("0.01"))

        return {
            "trimestre": f"{reporte.metadata.trimestre.value} {reporte.metadata.anio}",
            "rcs_total": float(datos.rcs_total),
            "capital_disponible": float(datos.capital_disponible),
            "ratio_solvencia": float(datos.ratio_solvencia.quantize(Decimal("0.0001"))),
            "ratio_solvencia_pct": float(
                (datos.ratio_solvencia * 100).quantize(Decimal("0.01"))
            ),
            "cumple_regulacion": datos.cumple_regulacion,
            "excedente_deficit": float(datos.excedente_deficit),
            "componente_principal": componente_principal,
            "valor_componente_principal": float(valor_componente_principal),
            "pct_componente_principal": float(pct_componente_principal),
            "desglose_rcs": {
                "suscripcion_vida": float(datos.rcs_suscripcion_vida),
                "suscripcion_danos": float(datos.rcs_suscripcion_danos),
                "inversion": float(datos.rcs_inversion),
                "operacional": float(datos.rcs_operacional),
            },
            "desglose_capital": {
                "capital_pagado": float(datos.capital_pagado),
                "superavit": float(datos.superavit),
            },
        }
