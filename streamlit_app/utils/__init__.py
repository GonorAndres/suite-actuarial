"""
Utilidades para dashboards de Streamlit.
"""

from .calculations import (
    analisis_sensibilidad_edad,
    analisis_sensibilidad_tasa,
    calcular_prima_dotal,
    calcular_prima_ordinario,
    calcular_prima_temporal,
    crear_asegurado,
    generar_tabla_comparacion,
    proyeccion_reservas,
)
from .visualizations import (
    crear_grafico_comparacion_productos,
    crear_grafico_desglose_recargos,
    crear_grafico_reservas,
    crear_grafico_sensibilidad_edad,
    crear_grafico_sensibilidad_tasa,
    crear_tabla_metricas_producto,
)

__all__ = [
    # Calculations
    "analisis_sensibilidad_edad",
    "analisis_sensibilidad_tasa",
    "calcular_prima_dotal",
    "calcular_prima_ordinario",
    "calcular_prima_temporal",
    "crear_asegurado",
    "generar_tabla_comparacion",
    "proyeccion_reservas",
    # Visualizations
    "crear_grafico_comparacion_productos",
    "crear_grafico_desglose_recargos",
    "crear_grafico_reservas",
    "crear_grafico_sensibilidad_edad",
    "crear_grafico_sensibilidad_tasa",
    "crear_tabla_metricas_producto",
]
