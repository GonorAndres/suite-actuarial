"""
Dashboard de Reservas Técnicas - Mexican Insurance Analytics Suite

Análisis de reservas para siniestros con métodos actuariales avanzados.
"""

import sys
from decimal import Decimal
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# Agregar src al path para imports
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

from mexican_insurance.reservas.bornhuetter_ferguson import (
    BornhuetterFerguson,
)
from mexican_insurance.reservas.bootstrap import Bootstrap
from mexican_insurance.reservas.chain_ladder import ChainLadder
from mexican_insurance.core.validators import (
    ConfiguracionChainLadder,
    ConfiguracionBornhuetterFerguson,
    ConfiguracionBootstrap,
)

# Configuración de la página
st.set_page_config(
    page_title="Reservas Técnicas - Mexican Insurance",
    page_icon="R",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Título
st.title("Dashboard de Reservas Técnicas")
st.markdown("""
Análisis de reservas para siniestros incurridos pero no reportados (IBNR) y
reservas de desarrollo usando métodos actuariales avanzados.
""")

# ============================================================================
# FUNCIONES HELPER
# ============================================================================


def generar_triangulo_ejemplo(escenario: str) -> pd.DataFrame:
    """Genera triángulo de desarrollo de ejemplo según escenario."""

    if escenario == "Estable":
        # Triángulo con desarrollo estable y predecible
        data = {
            0: [1000, 1100, 1200, 1300, 1400],
            1: [1300, 1430, 1560, 1690, np.nan],
            2: [1450, 1595, 1740, np.nan, np.nan],
            3: [1520, 1672, np.nan, np.nan, np.nan],
            4: [1550, np.nan, np.nan, np.nan, np.nan],
        }
    elif escenario == "Catastrófico":
        # Triángulo con spike en año reciente (catástrofe)
        data = {
            0: [1000, 1100, 1200, 1300, 2500],  # Año catastrófico
            1: [1250, 1375, 1500, 1625, np.nan],
            2: [1400, 1540, 1680, np.nan, np.nan],
            3: [1480, 1628, np.nan, np.nan, np.nan],
            4: [1520, np.nan, np.nan, np.nan, np.nan],
        }
    elif escenario == "Inflacionario":
        # Triángulo con inflación acelerada
        data = {
            0: [1000, 1200, 1500, 1900, 2400],  # Crecimiento acelerado
            1: [1300, 1560, 1950, 2470, np.nan],
            2: [1450, 1740, 2175, np.nan, np.nan],
            3: [1520, 1824, np.nan, np.nan, np.nan],
            4: [1550, np.nan, np.nan, np.nan, np.nan],
        }
    else:  # "Personalizado"
        # Permitir al usuario ingresar datos
        data = {
            0: [1000, 1100, 1200, 1300, 1400],
            1: [1300, 1430, 1560, 1690, np.nan],
            2: [1450, 1595, 1740, np.nan, np.nan],
            3: [1520, 1672, np.nan, np.nan, np.nan],
            4: [1550, np.nan, np.nan, np.nan, np.nan],
        }

    df = pd.DataFrame(data)
    df.index = [2020, 2021, 2022, 2023, 2024]  # Años de origen
    df.columns.name = "Desarrollo"

    return df


def crear_heatmap_triangulo(df: pd.DataFrame, title: str) -> go.Figure:
    """Crea heatmap del triángulo de desarrollo."""

    # Preparar datos para heatmap
    z = df.values
    x = [f"Año {i}" for i in range(len(df.columns))]
    y = df.index.tolist()

    # Crear máscara para NaN
    mask = np.isnan(z)

    # Crear texto con formato
    text = []
    for i in range(len(y)):
        row_text = []
        for j in range(len(x)):
            if mask[i][j]:
                row_text.append("")
            else:
                row_text.append(f"${z[i][j]:,.0f}")
        text.append(row_text)

    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=x,
            y=y,
            text=text,
            texttemplate="%{text}",
            textfont={"size": 10},
            colorscale="Blues",
            showscale=True,
            hoverongaps=False,
        )
    )

    fig.update_layout(
        title=title,
        xaxis_title="Años de Desarrollo",
        yaxis_title="Año de Origen",
        height=400,
    )

    return fig


# ============================================================================
# SIDEBAR: Parámetros
# ============================================================================

with st.sidebar:
    st.header("Configuración del Análisis")

    # Escenario de triángulo
    st.subheader("Datos de Entrada")

    escenario = st.selectbox(
        "Escenario de Triángulo",
        options=["Estable", "Catastrófico", "Inflacionario", "Personalizado"],
        help="Selecciona un escenario pre-configurado o personaliza los datos",
    )

    st.markdown("---")

    # Parámetros para métodos
    st.subheader("Parámetros Técnicos")

    # Para Bornhuetter-Ferguson
    expected_loss_ratio = st.slider(
        "Loss Ratio Esperado (%)",
        min_value=40,
        max_value=95,
        value=65,
        step=5,
        help="Para método Bornhuetter-Ferguson",
    ) / 100

    # Para Bootstrap
    n_simulaciones = st.select_slider(
        "Simulaciones Bootstrap",
        options=[100, 500, 1000, 2000, 5000],
        value=1000,
        help="Número de simulaciones para Bootstrap",
    )

    nivel_confianza = st.slider(
        "Nivel de Confianza (%)",
        min_value=90,
        max_value=99,
        value=95,
        step=1,
        help="Para intervalos de confianza Bootstrap",
    )

    st.markdown("---")

    st.info("""
    **Métodos Disponibles:**

    - **Chain Ladder**: Clásico, basado en factores de desarrollo
    - **Bornhuetter-Ferguson**: Combina datos históricos + expectativa
    - **Bootstrap**: Estima incertidumbre mediante simulación
    """)

# ============================================================================
# Generar triángulo
# ============================================================================

df_triangulo = generar_triangulo_ejemplo(escenario)

# ============================================================================
# VISTA PRINCIPAL: TABS
# ============================================================================

tab1, tab2, tab3, tab4 = st.tabs([
    "Triángulo de Datos",
    "Chain Ladder",
    "Bornhuetter-Ferguson",
    "Bootstrap",
])

# ============================================================================
# TAB 1: TRIÁNGULO DE DATOS
# ============================================================================

with tab1:
    st.header("Triángulo de Desarrollo")

    st.markdown("""
    El **triángulo de desarrollo** muestra los pagos acumulados de siniestros
    por año de origen y años de desarrollo.
    """)

    # Mostrar heatmap
    fig_heatmap = crear_heatmap_triangulo(
        df_triangulo,
        f"Triángulo de Desarrollo - Escenario: {escenario}",
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)

    st.markdown("---")

    # Editor de triángulo (si es personalizado)
    if escenario == "Personalizado":
        st.subheader("Editar Triángulo (Personalizado)")

        st.warning("""
        [!] **Nota:** Modifica los valores del triángulo. Deja celdas vacías para
        valores no disponibles (aún no transcurridos).
        """)

        df_editable = st.data_editor(
            df_triangulo,
            use_container_width=True,
            num_rows="fixed",
        )

        if st.button("Aplicar Cambios"):
            df_triangulo = df_editable
            st.success("[OK] Triángulo actualizado")
            st.rerun()

    # Tabla con formato
    st.subheader("Datos del Triángulo")

    df_display = df_triangulo.copy()
    for col in df_display.columns:
        df_display[col] = df_display[col].apply(
            lambda x: f"${x:,.0f}" if pd.notna(x) else "-"
        )

    st.dataframe(df_display, use_container_width=True)

    # Estadísticas del triángulo
    st.markdown("---")
    st.subheader("Estadísticas")

    col1, col2, col3, col4 = st.columns(4)

    # Calcular estadísticas
    ultimo_anio = df_triangulo.iloc[-1, 0]
    total_acumulado = df_triangulo.iloc[0, -1]  # Año más maduro
    incremento_anual = (df_triangulo.iloc[-1, 0] / df_triangulo.iloc[-2, 0] - 1) * 100

    with col1:
        st.metric(
            "Último Año Reportado",
            f"${ultimo_anio:,.0f}",
            help="Siniestralidad del año más reciente",
        )

    with col2:
        st.metric(
            "Total Acumulado (Maduro)",
            f"${total_acumulado:,.0f}",
            help="Desarrollo completo del año más antiguo",
        )

    with col3:
        st.metric(
            "Incremento Anual",
            f"{incremento_anual:+.1f}%",
            delta=f"vs año anterior",
            help="Cambio en siniestralidad año a año",
        )

    with col4:
        st.metric(
            "Años de Origen",
            len(df_triangulo),
            help="Número de años en el triángulo",
        )

# ============================================================================
# TAB 2: CHAIN LADDER
# ============================================================================

with tab2:
    st.header("Método Chain Ladder")

    st.markdown("""
    El **Chain Ladder** es el método más tradicional. Calcula factores de desarrollo
    promedio y los aplica para proyectar el triángulo completo.
    """)

    # Calcular Chain Ladder
    with st.spinner("Calculando Chain Ladder..."):
        config_cl = ConfiguracionChainLadder()
        cl = ChainLadder(config_cl)
        resultado_cl = cl.calcular(df_triangulo)

        # Extract results from ResultadoReserva
        factores = [float(f) for f in resultado_cl.factores_desarrollo]
        triangulo_completo = cl.obtener_triangulo_completo()
        reservas_por_anio_cl = resultado_cl.reservas_por_anio
        ultimates_por_anio_cl = resultado_cl.ultimates_por_anio

    # Métricas principales
    st.subheader("Reservas Calculadas")

    cl_col1, cl_col2, cl_col3 = st.columns(3)

    total_reserva_cl = float(resultado_cl.reserva_total)
    total_pagado = float(resultado_cl.pagado_total)
    ratio_reserva = (total_reserva_cl / total_pagado) * 100 if total_pagado > 0 else 0

    with cl_col1:
        st.metric(
            "Reserva IBNR Total",
            f"${total_reserva_cl:,.0f}",
            help="Total de reservas por Chain Ladder",
        )

    with cl_col2:
        st.metric(
            "Total Pagado a la Fecha",
            f"${total_pagado:,.0f}",
            help="Suma de todos los pagos acumulados",
        )

    with cl_col3:
        st.metric(
            "Ratio Reserva/Pagado",
            f"{ratio_reserva:.1f}%",
            help="Reservas como % de lo ya pagado",
        )

    st.markdown("---")

    # Factores de desarrollo
    st.subheader("Factores de Desarrollo")

    col_left, col_right = st.columns([2, 1])

    with col_left:
        # Gráfico de factores
        fig_factores = go.Figure()

        fig_factores.add_trace(
            go.Bar(
                x=[f"{i}-{i+1}" for i in range(len(factores))],
                y=factores,
                marker_color="#1f77b4",
                text=[f"{f:.4f}" for f in factores],
                textposition="outside",
            )
        )

        fig_factores.update_layout(
            title="Factores de Desarrollo (LDFs)",
            xaxis_title="Período de Desarrollo",
            yaxis_title="Factor",
            height=400,
        )

        st.plotly_chart(fig_factores, use_container_width=True)

    with col_right:
        # Tabla de factores
        df_factores = pd.DataFrame({
            "Período": [f"{i} → {i+1}" for i in range(len(factores))],
            "Factor": factores,
            "Incremento %": [(f - 1) * 100 for f in factores],
        })

        df_factores["Factor"] = df_factores["Factor"].apply(lambda x: f"{x:.4f}")
        df_factores["Incremento %"] = df_factores["Incremento %"].apply(
            lambda x: f"{x:.2f}%"
        )

        st.dataframe(df_factores, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Triángulo completo proyectado
    st.subheader("Triángulo Proyectado Completo")

    # Crear heatmap del triángulo completo
    fig_completo = crear_heatmap_triangulo(
        triangulo_completo,
        "Triángulo Proyectado (Chain Ladder)",
    )
    st.plotly_chart(fig_completo, use_container_width=True)

    # Tabla de reservas por año
    with st.expander("Ver reservas por año de origen"):
        anos_cl = sorted(reservas_por_anio_cl.keys())
        reservas_cl_values = [float(reservas_por_anio_cl[a]) for a in anos_cl]
        pct_total = [
            float(reservas_por_anio_cl[a]) / total_reserva_cl * 100
            if total_reserva_cl > 0 else 0
            for a in anos_cl
        ]

        df_reservas_cl = pd.DataFrame({
            "Año de Origen": anos_cl,
            "Reserva IBNR": reservas_cl_values,
            "% del Total": pct_total,
        })

        df_reservas_cl["Reserva IBNR"] = df_reservas_cl["Reserva IBNR"].apply(
            lambda x: f"${x:,.0f}"
        )
        df_reservas_cl["% del Total"] = df_reservas_cl["% del Total"].apply(
            lambda x: f"{x:.2f}%"
        )

        st.dataframe(df_reservas_cl, use_container_width=True, hide_index=True)

# ============================================================================
# TAB 3: BORNHUETTER-FERGUSON
# ============================================================================

with tab3:
    st.header("Método Bornhuetter-Ferguson")

    st.markdown("""
    **Bornhuetter-Ferguson** combina datos históricos con una estimación a priori
    del loss ratio esperado. Es más estable que Chain Ladder ante datos volátiles.
    """)

    # Calcular primas para B-F (simplificado: asumir que prima = siniestro inicial * 1.5)
    primas_series = df_triangulo.iloc[:, 0] * 1.5
    # Build primas_por_anio dict mapping year index -> Decimal premium
    primas_por_anio = {
        int(anio): Decimal(str(prima))
        for anio, prima in primas_series.items()
    }

    # Calcular B-F
    with st.spinner("Calculando Bornhuetter-Ferguson..."):
        config_bf = ConfiguracionBornhuetterFerguson(
            loss_ratio_apriori=Decimal(str(expected_loss_ratio)),
        )
        bf = BornhuetterFerguson(config_bf)
        resultado_bf = bf.calcular(df_triangulo, primas_por_anio)

        reservas_por_anio_bf = resultado_bf.reservas_por_anio

    # Métricas principales
    st.subheader("Reservas Calculadas (B-F)")

    bf_col1, bf_col2, bf_col3, bf_col4 = st.columns(4)

    total_reserva_bf = float(resultado_bf.reserva_total)
    siniestros_esperados = sum(float(p) for p in primas_por_anio.values()) * expected_loss_ratio

    with bf_col1:
        st.metric(
            "Reserva IBNR Total (B-F)",
            f"${total_reserva_bf:,.0f}",
            help="Total de reservas por Bornhuetter-Ferguson",
        )

    with bf_col2:
        st.metric(
            "Loss Ratio Esperado",
            f"{expected_loss_ratio*100:.0f}%",
            help="Loss ratio a priori usado en el cálculo",
        )

    with bf_col3:
        st.metric(
            "Siniestros Esperados",
            f"${siniestros_esperados:,.0f}",
            help="Primas × Loss Ratio Esperado",
        )

    with bf_col4:
        diferencia_cl = total_reserva_bf - total_reserva_cl
        pct_diferencia = (diferencia_cl / total_reserva_cl) * 100 if total_reserva_cl > 0 else 0
        st.metric(
            "Diferencia vs Chain Ladder",
            f"${diferencia_cl:,.0f}",
            delta=f"{pct_diferencia:+.1f}%",
            help="Diferencia entre B-F y Chain Ladder",
        )

    st.markdown("---")

    # Comparación B-F vs Chain Ladder
    st.subheader("Comparación: B-F vs Chain Ladder")

    # Preparar datos para comparación
    anos = sorted(reservas_por_anio_bf.keys())
    reservas_bf_list = [float(reservas_por_anio_bf[a]) for a in anos]
    reservas_cl_list = [float(reservas_por_anio_cl.get(a, Decimal("0"))) for a in anos]

    fig_comparacion = go.Figure()

    fig_comparacion.add_trace(
        go.Bar(
            name="Chain Ladder",
            x=anos,
            y=reservas_cl_list,
            marker_color="#1f77b4",
        )
    )

    fig_comparacion.add_trace(
        go.Bar(
            name="Bornhuetter-Ferguson",
            x=anos,
            y=reservas_bf_list,
            marker_color="#ff7f0e",
        )
    )

    fig_comparacion.update_layout(
        title="Comparación de Reservas por Método",
        xaxis_title="Año de Origen",
        yaxis_title="Reserva IBNR (MXN)",
        barmode="group",
        height=450,
    )

    st.plotly_chart(fig_comparacion, use_container_width=True)

    # Tabla comparativa
    with st.expander("Ver tabla comparativa detallada"):
        df_comp = pd.DataFrame({
            "Año": anos,
            "Chain Ladder": reservas_cl_list,
            "Bornhuetter-Ferguson": reservas_bf_list,
            "Diferencia": [b - c for b, c in zip(reservas_bf_list, reservas_cl_list)],
            "% Diferencia": [
                ((b - c) / c * 100) if c > 0 else 0
                for b, c in zip(reservas_bf_list, reservas_cl_list)
            ],
        })

        df_comp["Chain Ladder"] = df_comp["Chain Ladder"].apply(lambda x: f"${x:,.0f}")
        df_comp["Bornhuetter-Ferguson"] = df_comp["Bornhuetter-Ferguson"].apply(
            lambda x: f"${x:,.0f}"
        )
        df_comp["Diferencia"] = df_comp["Diferencia"].apply(lambda x: f"${x:,.0f}")
        df_comp["% Diferencia"] = df_comp["% Diferencia"].apply(lambda x: f"{x:.2f}%")

        st.dataframe(df_comp, use_container_width=True, hide_index=True)

    # Interpretación
    st.info(f"""
    **Interpretación:**

    B-F es menos sensible a valores atípicos que Chain Ladder. Utiliza un loss ratio
    esperado ({expected_loss_ratio*100:.0f}%) para estabilizar las proyecciones,
    especialmente útil cuando los datos históricos son volátiles o limitados.

    **Diferencia total:** ${diferencia_cl:,.0f} ({pct_diferencia:+.1f}%)
    """)

# ============================================================================
# TAB 4: BOOTSTRAP
# ============================================================================

with tab4:
    st.header("Método Bootstrap")

    st.markdown("""
    **Bootstrap** estima la **incertidumbre** en las reservas mediante simulación.
    Genera múltiples escenarios resampleando residuales.
    """)

    # Calcular Bootstrap
    if st.button("Ejecutar Bootstrap", type="primary"):
        with st.spinner(f"Ejecutando {n_simulaciones:,} simulaciones..."):
            config_bs = ConfiguracionBootstrap(
                num_simulaciones=n_simulaciones,
                seed=42,
                percentiles=[50, 75, 90, 95, 99],
            )
            bs = Bootstrap(config_bs)
            resultado_bs = bs.calcular(df_triangulo)

            # Get the full simulation distribution for histogram
            distribucion = bs.obtener_distribucion()
            reservas_bootstrap = [float(r) for r in distribucion] if distribucion else []

            # Risk metrics
            var_value = float(bs.calcular_var(nivel_confianza / 100))
            tvar_value = float(bs.calcular_tvar(nivel_confianza / 100))

            # Build statistics from resultado and detalles
            media_bs = float(resultado_bs.detalles["media"])
            desv_std_bs = float(resultado_bs.detalles["desviacion_estandar"])

            # Percentiles from resultado
            percentiles_dict = resultado_bs.percentiles  # dict[int, Decimal]
            percentil_inf_key = 100 - nivel_confianza
            percentil_sup_key = nivel_confianza
            percentil_inf = float(percentiles_dict.get(percentil_inf_key, Decimal("0")))
            percentil_sup = float(percentiles_dict.get(percentil_sup_key, Decimal("0")))

            estadisticas = {
                "media": media_bs,
                "desviacion_estandar": desv_std_bs,
                "percentil_inferior": percentil_inf,
                "percentil_superior": percentil_sup,
                "var": var_value,
                "tvar": tvar_value,
            }

        # Guardar en session state
        st.session_state["bootstrap_ejecutado"] = True
        st.session_state["reservas_bootstrap"] = reservas_bootstrap
        st.session_state["estadisticas_bootstrap"] = estadisticas
        st.session_state["n_sims"] = n_simulaciones
        st.session_state["nivel_conf"] = nivel_confianza

    # Mostrar resultados si ya se ejecutó
    if st.session_state.get("bootstrap_ejecutado", False):
        estadisticas = st.session_state["estadisticas_bootstrap"]
        reservas_bootstrap = st.session_state["reservas_bootstrap"]
        n_sims_ejecutadas = st.session_state["n_sims"]
        nivel_conf = st.session_state["nivel_conf"]

        st.success(
            f"[OK] Bootstrap ejecutado con {n_sims_ejecutadas:,} simulaciones "
            f"(nivel de confianza {nivel_conf}%)"
        )

        # Métricas principales
        st.subheader("Resultados Bootstrap")

        bs_col1, bs_col2, bs_col3, bs_col4 = st.columns(4)

        media_bs = float(estadisticas["media"])
        percentil_inf = float(estadisticas["percentil_inferior"])
        percentil_sup = float(estadisticas["percentil_superior"])
        desv_std = float(estadisticas["desviacion_estandar"])

        with bs_col1:
            st.metric(
                "Media Bootstrap",
                f"${media_bs:,.0f}",
                help="Reserva promedio de todas las simulaciones",
            )

        with bs_col2:
            st.metric(
                "Desviación Estándar",
                f"${desv_std:,.0f}",
                help="Volatilidad de las reservas estimadas",
            )

        with bs_col3:
            st.metric(
                f"Percentil {100 - nivel_conf}%",
                f"${percentil_inf:,.0f}",
                help=f"Límite inferior intervalo {nivel_conf}%",
            )

        with bs_col4:
            st.metric(
                f"Percentil {nivel_conf}%",
                f"${percentil_sup:,.0f}",
                help=f"Límite superior intervalo {nivel_conf}%",
            )

        st.markdown("---")

        # Histograma de distribución
        st.subheader("Distribución de Reservas (Bootstrap)")

        fig_hist = go.Figure()

        fig_hist.add_trace(
            go.Histogram(
                x=reservas_bootstrap,
                nbinsx=50,
                marker_color="#1f77b4",
                opacity=0.7,
                name="Simulaciones",
            )
        )

        # Líneas de percentiles
        fig_hist.add_vline(
            x=media_bs,
            line_dash="dash",
            line_color="green",
            annotation_text=f"Media: ${media_bs:,.0f}",
            annotation_position="top",
        )

        fig_hist.add_vline(
            x=percentil_inf,
            line_dash="dot",
            line_color="red",
            annotation_text=f"P{100-nivel_conf}: ${percentil_inf:,.0f}",
            annotation_position="bottom left",
        )

        fig_hist.add_vline(
            x=percentil_sup,
            line_dash="dot",
            line_color="red",
            annotation_text=f"P{nivel_conf}: ${percentil_sup:,.0f}",
            annotation_position="bottom right",
        )

        fig_hist.update_layout(
            title=f"Distribución de Reservas IBNR ({n_sims_ejecutadas:,} simulaciones)",
            xaxis_title="Reserva Total (MXN)",
            yaxis_title="Frecuencia",
            height=450,
            showlegend=False,
        )

        st.plotly_chart(fig_hist, use_container_width=True)

        # Comparación con otros métodos
        st.markdown("---")
        st.subheader("Comparación con Otros Métodos")

        # Comparar media Bootstrap vs Chain Ladder y B-F
        metodos = ["Chain Ladder", "Bornhuetter-Ferguson", "Bootstrap (Media)"]
        reservas_metodos = [total_reserva_cl, total_reserva_bf, media_bs]

        fig_comp_metodos = go.Figure()

        fig_comp_metodos.add_trace(
            go.Bar(
                x=metodos,
                y=reservas_metodos,
                marker_color=["#1f77b4", "#ff7f0e", "#2ca02c"],
                text=[f"${r:,.0f}" for r in reservas_metodos],
                textposition="outside",
            )
        )

        # Agregar barras de error para Bootstrap
        fig_comp_metodos.add_trace(
            go.Scatter(
                x=["Bootstrap (Media)"],
                y=[media_bs],
                error_y=dict(
                    type="data",
                    symmetric=False,
                    array=[percentil_sup - media_bs],
                    arrayminus=[media_bs - percentil_inf],
                    color="red",
                    thickness=2,
                    width=10,
                ),
                mode="markers",
                marker=dict(size=10, color="#2ca02c"),
                name=f"IC {nivel_conf}%",
                showlegend=True,
            )
        )

        fig_comp_metodos.update_layout(
            title="Comparación de Métodos de Reservas",
            xaxis_title="Método",
            yaxis_title="Reserva IBNR Total (MXN)",
            height=450,
        )

        st.plotly_chart(fig_comp_metodos, use_container_width=True)

        # Interpretación
        st.info(f"""
        **Intervalo de Confianza {nivel_conf}%:** [${percentil_inf:,.0f}, ${percentil_sup:,.0f}]

        **Amplitud del intervalo:** ${percentil_sup - percentil_inf:,.0f}

        **Coeficiente de Variación:** {(desv_std / media_bs * 100):.1f}%

        El método Bootstrap permite cuantificar la incertidumbre en las reservas.
        Un intervalo amplio indica mayor volatilidad en los datos.
        """)

    else:
        st.warning("Haz clic en el botón para ejecutar el análisis Bootstrap")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9em;">
    Métodos actuariales avanzados para estimación de reservas |
    Mexican Insurance Analytics Suite
</div>
""", unsafe_allow_html=True)
