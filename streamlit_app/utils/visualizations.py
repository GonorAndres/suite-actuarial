"""
Utilidades de visualización para dashboards de Streamlit.

Funciones para crear gráficos reutilizables con Plotly.
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def crear_grafico_comparacion_productos(df: pd.DataFrame) -> go.Figure:
    """
    Crea gráfico de barras comparando productos.

    Args:
        df: DataFrame con columnas 'Producto', 'Prima Neta', 'Prima Total'

    Returns:
        Figura de Plotly
    """
    # Convertir strings formateados a números
    df_plot = df.copy()

    if isinstance(df_plot["Prima Neta"].iloc[0], str):
        df_plot["Prima Neta"] = df_plot["Prima Neta"].str.replace(
            "$", ""
        ).str.replace(",", "").astype(float)
        df_plot["Prima Total"] = df_plot["Prima Total"].str.replace(
            "$", ""
        ).str.replace(",", "").astype(float)

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            name="Prima Neta",
            x=df_plot["Producto"],
            y=df_plot["Prima Neta"],
            marker_color="#1f77b4",
            text=df_plot["Prima Neta"].apply(lambda x: f"${x:,.2f}"),
            textposition="outside",
        )
    )

    fig.add_trace(
        go.Bar(
            name="Prima Total",
            x=df_plot["Producto"],
            y=df_plot["Prima Total"],
            marker_color="#ff7f0e",
            text=df_plot["Prima Total"].apply(lambda x: f"${x:,.2f}"),
            textposition="outside",
        )
    )

    fig.update_layout(
        title="Comparación de Primas Mensuales por Producto",
        xaxis_title="Producto de Vida",
        yaxis_title="Prima Mensual (MXN)",
        barmode="group",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=500,
    )

    return fig


def crear_grafico_sensibilidad_edad(df: pd.DataFrame) -> go.Figure:
    """
    Crea gráfico de línea para análisis de sensibilidad por edad.

    Args:
        df: DataFrame con columnas 'Edad', 'Prima Neta', 'Prima Total'

    Returns:
        Figura de Plotly
    """
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["Edad"],
            y=df["Prima Neta"],
            mode="lines+markers",
            name="Prima Neta",
            line=dict(color="#1f77b4", width=3),
            marker=dict(size=6),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["Edad"],
            y=df["Prima Total"],
            mode="lines+markers",
            name="Prima Total",
            line=dict(color="#ff7f0e", width=3),
            marker=dict(size=6),
        )
    )

    fig.update_layout(
        title="Sensibilidad de Prima vs Edad del Asegurado",
        xaxis_title="Edad",
        yaxis_title="Prima Mensual (MXN)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=500,
    )

    return fig


def crear_grafico_sensibilidad_tasa(df: pd.DataFrame) -> go.Figure:
    """
    Crea gráfico de línea para análisis de sensibilidad por tasa de interés.

    Args:
        df: DataFrame con columnas 'Tasa (%)', 'Prima Neta', 'Prima Total'

    Returns:
        Figura de Plotly
    """
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["Tasa (%)"],
            y=df["Prima Neta"],
            mode="lines+markers",
            name="Prima Neta",
            line=dict(color="#2ca02c", width=3),
            marker=dict(size=6),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["Tasa (%)"],
            y=df["Prima Total"],
            mode="lines+markers",
            name="Prima Total",
            line=dict(color="#d62728", width=3),
            marker=dict(size=6),
        )
    )

    fig.update_layout(
        title="Sensibilidad de Prima vs Tasa de Interés Técnico",
        xaxis_title="Tasa de Interés (%)",
        yaxis_title="Prima Mensual (MXN)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=500,
    )

    return fig


def crear_grafico_reservas(df: pd.DataFrame, suma_asegurada: float) -> go.Figure:
    """
    Crea gráfico de área mostrando evolución de reservas matemáticas.

    Args:
        df: DataFrame con columnas 'Año', 'Reserva Matemática', '% Suma Asegurada'
        suma_asegurada: Suma asegurada para mostrar como referencia

    Returns:
        Figura de Plotly con dos ejes Y
    """
    # Crear figura con ejes secundarios
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Reserva en pesos (área)
    fig.add_trace(
        go.Scatter(
            x=df["Año"],
            y=df["Reserva Matemática"],
            mode="lines",
            name="Reserva Matemática",
            fill="tozeroy",
            line=dict(color="#1f77b4", width=2),
            hovertemplate="Año %{x}<br>Reserva: $%{y:,.2f}<extra></extra>",
        ),
        secondary_y=False,
    )

    # Línea de suma asegurada como referencia
    fig.add_trace(
        go.Scatter(
            x=df["Año"],
            y=[suma_asegurada] * len(df),
            mode="lines",
            name="Suma Asegurada",
            line=dict(color="#d62728", width=2, dash="dash"),
            hovertemplate="Suma Asegurada: $%{y:,.2f}<extra></extra>",
        ),
        secondary_y=False,
    )

    # Porcentaje (línea en eje secundario)
    fig.add_trace(
        go.Scatter(
            x=df["Año"],
            y=df["% Suma Asegurada"],
            mode="lines+markers",
            name="% Suma Asegurada",
            line=dict(color="#2ca02c", width=2),
            marker=dict(size=5),
            yaxis="y2",
            hovertemplate="Año %{x}<br>%{y:.1f}% de Suma Asegurada<extra></extra>",
        ),
        secondary_y=True,
    )

    # Actualizar ejes
    fig.update_xaxes(title_text="Año desde Inicio de Póliza")
    fig.update_yaxes(title_text="Reserva Matemática (MXN)", secondary_y=False)
    fig.update_yaxes(title_text="% de Suma Asegurada", secondary_y=True)

    fig.update_layout(
        title="Evolución de Reserva Matemática",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=500,
    )

    return fig


def crear_grafico_desglose_recargos(recargos: dict) -> go.Figure:
    """
    Crea gráfico de pie mostrando desglose de recargos.

    Args:
        recargos: Diccionario con conceptos y montos de recargos

    Returns:
        Figura de Plotly
    """
    labels = list(recargos.keys())
    values = list(recargos.values())

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                textinfo="label+percent",
                hovertemplate="<b>%{label}</b><br>$%{value:,.2f}<br>%{percent}<extra></extra>",
            )
        ]
    )

    fig.update_layout(
        title="Desglose de Recargos",
        height=400,
        showlegend=True,
        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05),
    )

    return fig


def crear_tabla_metricas_producto(
    producto: str,
    prima_neta: float,
    prima_total: float,
    suma_asegurada: float,
    plazo: int | None = None,
) -> dict:
    """
    Calcula métricas clave del producto para mostrar en cards.

    Returns:
        Diccionario con métricas formateadas
    """
    # Calcular métricas
    total_primas_anuales = prima_total * 12

    if plazo:
        total_primas_plazo = total_primas_anuales * plazo
        ratio_prima_suma = (total_primas_plazo / suma_asegurada) * 100
    else:
        # Para vida ordinario, usar horizonte de 20 años
        total_primas_plazo = total_primas_anuales * 20
        ratio_prima_suma = (total_primas_plazo / suma_asegurada) * 100

    recargos_totales = prima_total - prima_neta
    porcentaje_recargos = (recargos_totales / prima_neta) * 100 if prima_neta > 0 else 0

    return {
        "prima_mensual": f"${prima_total:,.2f}",
        "prima_anual": f"${total_primas_anuales:,.2f}",
        "total_plazo": f"${total_primas_plazo:,.2f}",
        "ratio_prima_suma": f"{ratio_prima_suma:.2f}%",
        "recargos": f"${recargos_totales:,.2f}",
        "porcentaje_recargos": f"{porcentaje_recargos:.2f}%",
    }
