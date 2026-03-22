"""
Reservas Tecnicas IBNR -- Demo interactivo de los tres metodos de reservas.

Muestra el uso de ChainLadder, BornhuetterFerguson y Bootstrap
de la libreria suite_actuarial.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))

from decimal import Decimal

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from suite_actuarial.reservas import ChainLadder, BornhuetterFerguson, Bootstrap
from suite_actuarial.core.validators import (
    ConfiguracionChainLadder,
    ConfiguracionBornhuetterFerguson,
    ConfiguracionBootstrap,
    MetodoPromedio,
)

# ---------------------------------------------------------------------------
# Configuracion de pagina
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Reservas Tecnicas", layout="wide")

st.title("Reservas Tecnicas IBNR")
st.markdown(
    "Estimacion de reservas por siniestros incurridos pero no reportados (IBNR) "
    "utilizando tres metodos actuariales estandar de la industria."
)

# ---------------------------------------------------------------------------
# Triangulo de ejemplo (acumulado, 6x6)
# ---------------------------------------------------------------------------
SAMPLE_TRIANGLE_DATA = {
    1: [3500, 5200, 5900, 6200, 6350, 6400],
    2: [3800, 5600, 6300, 6600, 6750, None],
    3: [4100, 6100, 6900, 7250, None, None],
    4: [4400, 6500, 7350, None, None, None],
    5: [4700, 7000, None, None, None, None],
    6: [5000, None, None, None, None, None],
}


def obtener_triangulo(editable: bool = True) -> pd.DataFrame:
    """Devuelve el triangulo de desarrollo como DataFrame."""
    cols = [f"Dev {j}" for j in range(1, 7)]
    df = pd.DataFrame.from_dict(SAMPLE_TRIANGLE_DATA, orient="index", columns=cols)
    df.index.name = "Anio"

    if editable:
        st.markdown("##### Triangulo de desarrollo acumulado (editable)")
        edited = st.data_editor(
            df,
            use_container_width=True,
            num_rows="fixed",
            key="triangle_editor",
        )
        return edited
    return df


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_cl, tab_bf, tab_bs = st.tabs(
    ["Chain Ladder", "Bornhuetter-Ferguson", "Bootstrap"]
)

# ===== TAB 1: Chain Ladder ================================================
with tab_cl:
    st.header("Metodo Chain Ladder")
    st.markdown(
        "El metodo Chain Ladder calcula factores de desarrollo age-to-age "
        "para proyectar el triangulo y estimar los ultimates y reservas."
    )

    col_cfg, col_tri = st.columns([1, 3])
    with col_cfg:
        metodo_prom = st.selectbox(
            "Metodo de promedio",
            options=["simple", "ponderado", "geometrico"],
            index=0,
            key="cl_metodo",
        )
        usar_tail = st.checkbox("Calcular tail factor", value=False, key="cl_tail")

    with col_tri:
        tri_cl = obtener_triangulo(editable=True)

    if st.button("Calcular Chain Ladder", key="btn_cl"):
        metodo_map = {
            "simple": MetodoPromedio.SIMPLE,
            "ponderado": MetodoPromedio.PONDERADO,
            "geometrico": MetodoPromedio.GEOMETRICO,
        }
        config = ConfiguracionChainLadder(
            metodo_promedio=metodo_map[metodo_prom],
            calcular_tail_factor=usar_tail,
        )
        cl = ChainLadder(config)
        try:
            resultado = cl.calcular(tri_cl)

            # -- Metricas principales --
            m1, m2, m3 = st.columns(3)
            m1.metric("Reserva Total IBNR", f"${float(resultado.reserva_total):,.0f}")
            m2.metric("Ultimate Total", f"${float(resultado.ultimate_total):,.0f}")
            m3.metric("Pagado Total", f"${float(resultado.pagado_total):,.0f}")

            # -- Factores de desarrollo --
            st.subheader("Factores de desarrollo")
            factores_df = pd.DataFrame(
                {
                    "Periodo": [f"{i}-{i+1}" for i in range(1, len(resultado.factores_desarrollo) + 1)],
                    "Factor": [float(f) for f in resultado.factores_desarrollo],
                }
            )
            st.dataframe(factores_df, use_container_width=True, hide_index=True)

            # -- Grafico de reservas por anio --
            st.subheader("Reservas y ultimates por anio de origen")
            anios = sorted(resultado.reservas_por_anio.keys())
            fig = go.Figure()
            fig.add_trace(go.Bar(
                name="Pagado",
                x=[str(a) for a in anios],
                y=[float(resultado.ultimates_por_anio[a] - resultado.reservas_por_anio[a]) for a in anios],
                marker_color="#1f77b4",
            ))
            fig.add_trace(go.Bar(
                name="Reserva IBNR",
                x=[str(a) for a in anios],
                y=[float(resultado.reservas_por_anio[a]) for a in anios],
                marker_color="#ff7f0e",
            ))
            fig.update_layout(
                barmode="stack",
                xaxis_title="Anio de origen",
                yaxis_title="Monto (MXN)",
                height=450,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig, use_container_width=True)

            # -- Triangulo completo --
            tri_completo = cl.obtener_triangulo_completo()
            if tri_completo is not None:
                st.subheader("Triangulo completo (proyectado)")
                st.dataframe(tri_completo.style.format("{:,.0f}"), use_container_width=True)

        except Exception as e:
            st.error(f"Error en el calculo: {e}")

    with st.expander("Codigo de ejemplo -- Chain Ladder"):
        st.code(
            """import pandas as pd
from decimal import Decimal
from suite_actuarial.reservas import ChainLadder
from suite_actuarial.core.validators import (
    ConfiguracionChainLadder, MetodoPromedio,
)

# 1. Construir triangulo acumulado (DataFrame con index=anio, cols=periodos)
data = {
    1: [3500, 5200, 5900, 6200, 6350, 6400],
    2: [3800, 5600, 6300, 6600, 6750, None],
    3: [4100, 6100, 6900, 7250, None, None],
    4: [4400, 6500, 7350, None, None, None],
    5: [4700, 7000, None, None, None, None],
    6: [5000, None, None, None, None, None],
}
cols = [f"Dev {j}" for j in range(1, 7)]
triangulo = pd.DataFrame.from_dict(data, orient="index", columns=cols)

# 2. Configurar y ejecutar
config = ConfiguracionChainLadder(
    metodo_promedio=MetodoPromedio.SIMPLE,
    calcular_tail_factor=False,
)
cl = ChainLadder(config)
resultado = cl.calcular(triangulo)

# 3. Resultados
print(f"Reserva total IBNR: ${resultado.reserva_total:,.2f}")
print(f"Ultimate total:      ${resultado.ultimate_total:,.2f}")
for anio, reserva in resultado.reservas_por_anio.items():
    print(f"  Anio {anio}: reserva = ${reserva:,.2f}")
""",
            language="python",
        )

# ===== TAB 2: Bornhuetter-Ferguson ========================================
with tab_bf:
    st.header("Metodo Bornhuetter-Ferguson")
    st.markdown(
        "Combina la experiencia observada del Chain Ladder con una expectativa "
        "a priori del loss ratio, dando mayor estabilidad en anios recientes."
    )

    col_cfg2, col_tri2 = st.columns([1, 3])
    with col_cfg2:
        loss_ratio = st.slider(
            "Loss ratio a priori (%)",
            min_value=30,
            max_value=120,
            value=65,
            step=5,
            key="bf_lr",
        )
        st.markdown("##### Primas ganadas por anio")
        primas_default = {1: 10000, 2: 10500, 3: 11000, 4: 11500, 5: 12000, 6: 12500}
        primas_df = pd.DataFrame(
            {"Anio": list(primas_default.keys()), "Prima": list(primas_default.values())}
        )
        primas_edited = st.data_editor(primas_df, use_container_width=True, num_rows="fixed", key="bf_primas")

    with col_tri2:
        tri_bf = obtener_triangulo(editable=False)

    if st.button("Calcular Bornhuetter-Ferguson", key="btn_bf"):
        try:
            primas_por_anio = {
                int(row["Anio"]): Decimal(str(row["Prima"]))
                for _, row in primas_edited.iterrows()
            }

            config_bf = ConfiguracionBornhuetterFerguson(
                loss_ratio_apriori=Decimal(str(loss_ratio / 100)),
                metodo_promedio=MetodoPromedio.SIMPLE,
            )
            bf = BornhuetterFerguson(config_bf)
            resultado_bf = bf.calcular(tri_bf, primas_por_anio)

            m1, m2, m3 = st.columns(3)
            m1.metric("Reserva Total IBNR (B-F)", f"${float(resultado_bf.reserva_total):,.0f}")
            m2.metric("Ultimate Total", f"${float(resultado_bf.ultimate_total):,.0f}")
            m3.metric("Loss Ratio implicito", resultado_bf.detalles.get("loss_ratio_implicito", "N/A"))

            # Comparacion con Chain Ladder
            st.subheader("Comparacion B-F vs Chain Ladder")
            comparacion = bf.comparar_con_chain_ladder(tri_bf, primas_por_anio)
            comparacion_fmt = comparacion.copy()
            for col in ["Ultimate_CL", "Ultimate_BF", "Reserva_CL", "Reserva_BF"]:
                comparacion_fmt[col] = comparacion_fmt[col].apply(lambda x: f"${float(x):,.0f}")
            comparacion_fmt["Diferencia_%"] = comparacion_fmt["Diferencia_%"].apply(lambda x: f"{float(x):.2f}%")
            st.dataframe(comparacion_fmt, use_container_width=True)

            # Grafico de comparacion
            anios = sorted(resultado_bf.reservas_por_anio.keys())
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(
                name="Reserva B-F",
                x=[str(a) for a in anios],
                y=[float(resultado_bf.reservas_por_anio[a]) for a in anios],
                marker_color="#2ca02c",
            ))
            config_cl2 = ConfiguracionChainLadder(metodo_promedio=MetodoPromedio.SIMPLE)
            cl2 = ChainLadder(config_cl2)
            res_cl2 = cl2.calcular(tri_bf)
            fig2.add_trace(go.Bar(
                name="Reserva Chain Ladder",
                x=[str(a) for a in anios],
                y=[float(res_cl2.reservas_por_anio[a]) for a in anios],
                marker_color="#1f77b4",
            ))
            fig2.update_layout(
                barmode="group",
                xaxis_title="Anio de origen",
                yaxis_title="Reserva IBNR (MXN)",
                height=450,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig2, use_container_width=True)

            # Porcentajes reportados
            pcts = bf.obtener_porcentajes_reportados()
            if pcts:
                st.subheader("Porcentaje reportado por anio")
                pcts_df = pd.DataFrame(
                    {"Anio": list(pcts.keys()), "% Reportado": [f"{float(v)*100:.1f}%" for v in pcts.values()]}
                )
                st.dataframe(pcts_df, use_container_width=True, hide_index=True)

        except Exception as e:
            st.error(f"Error en el calculo: {e}")

    with st.expander("Codigo de ejemplo -- Bornhuetter-Ferguson"):
        st.code(
            """from decimal import Decimal
from suite_actuarial.reservas import BornhuetterFerguson
from suite_actuarial.core.validators import (
    ConfiguracionBornhuetterFerguson, MetodoPromedio,
)

# Primas ganadas por anio de origen
primas = {
    1: Decimal("10000"), 2: Decimal("10500"),
    3: Decimal("11000"), 4: Decimal("11500"),
    5: Decimal("12000"), 6: Decimal("12500"),
}

# Configurar B-F con loss ratio a priori del 65%
config = ConfiguracionBornhuetterFerguson(
    loss_ratio_apriori=Decimal("0.65"),
    metodo_promedio=MetodoPromedio.SIMPLE,
)
bf = BornhuetterFerguson(config)
resultado = bf.calcular(triangulo, primas)

print(f"Reserva total IBNR (B-F): ${resultado.reserva_total:,.2f}")
print(f"Loss ratio implicito: {resultado.detalles['loss_ratio_implicito']}")

# Comparar con Chain Ladder
comparacion = bf.comparar_con_chain_ladder(triangulo, primas)
print(comparacion)
""",
            language="python",
        )

# ===== TAB 3: Bootstrap ===================================================
with tab_bs:
    st.header("Metodo Bootstrap")
    st.markdown(
        "Genera una distribucion completa de reservas mediante simulacion Monte Carlo, "
        "permitiendo cuantificar la incertidumbre y calcular percentiles (VaR, TVaR)."
    )

    col_cfg3, col_tri3 = st.columns([1, 3])
    with col_cfg3:
        n_sims = st.number_input(
            "Numero de simulaciones",
            min_value=100,
            max_value=5000,
            value=500,
            step=100,
            key="bs_nsims",
        )
        seed = st.number_input("Semilla aleatoria", value=42, key="bs_seed")

    with col_tri3:
        tri_bs = obtener_triangulo(editable=False)

    if st.button("Ejecutar Bootstrap", key="btn_bs"):
        with st.spinner(f"Ejecutando {n_sims} simulaciones..."):
            try:
                config_bs = ConfiguracionBootstrap(
                    num_simulaciones=int(n_sims),
                    seed=int(seed),
                    percentiles=[50, 75, 90, 95, 99],
                )
                bs = Bootstrap(config_bs)
                resultado_bs = bs.calcular(tri_bs)

                # Metricas principales
                m1, m2, m3 = st.columns(3)
                m1.metric("Reserva P50 (mediana)", f"${float(resultado_bs.reserva_total):,.0f}")
                m2.metric("Reserva P95", f"${float(resultado_bs.percentiles[95]):,.0f}")
                m3.metric("Reserva P99", f"${float(resultado_bs.percentiles[99]):,.0f}")

                # Tabla de percentiles
                st.subheader("Percentiles de la distribucion")
                perc_df = pd.DataFrame(
                    {
                        "Percentil": [f"P{p}" for p in sorted(resultado_bs.percentiles.keys())],
                        "Reserva": [f"${float(resultado_bs.percentiles[p]):,.0f}" for p in sorted(resultado_bs.percentiles.keys())],
                    }
                )
                st.dataframe(perc_df, use_container_width=True, hide_index=True)

                # Estadisticas
                st.subheader("Estadisticas de la simulacion")
                stats_cols = st.columns(4)
                stats_cols[0].metric("Media", f"${float(resultado_bs.detalles['media']):,.0f}")
                stats_cols[1].metric("Desv. Estandar", f"${float(resultado_bs.detalles['desviacion_estandar']):,.0f}")
                stats_cols[2].metric("Minimo", f"${float(resultado_bs.detalles['minimo']):,.0f}")
                stats_cols[3].metric("Maximo", f"${float(resultado_bs.detalles['maximo']):,.0f}")

                # VaR y TVaR
                var95 = bs.calcular_var(0.95)
                tvar95 = bs.calcular_tvar(0.95)
                v1, v2 = st.columns(2)
                v1.metric("VaR 95%", f"${float(var95):,.0f}")
                v2.metric("TVaR 95%", f"${float(tvar95):,.0f}")

                # Grafico de distribucion
                st.subheader("Distribucion de reservas simuladas")
                distribucion = bs.obtener_distribucion()
                if distribucion:
                    valores = [float(v) for v in distribucion]
                    fig3 = go.Figure()
                    fig3.add_trace(go.Histogram(
                        x=valores,
                        nbinsx=50,
                        marker_color="#1f77b4",
                        opacity=0.75,
                        name="Simulaciones",
                    ))
                    # Lineas de percentiles
                    for p, color, dash in [
                        (50, "#2ca02c", "solid"),
                        (95, "#ff7f0e", "dash"),
                        (99, "#d62728", "dot"),
                    ]:
                        val = float(resultado_bs.percentiles[p])
                        fig3.add_vline(
                            x=val,
                            line_dash=dash,
                            line_color=color,
                            annotation_text=f"P{p}: ${val:,.0f}",
                            annotation_position="top",
                        )
                    fig3.update_layout(
                        xaxis_title="Reserva total (MXN)",
                        yaxis_title="Frecuencia",
                        height=500,
                        showlegend=False,
                    )
                    st.plotly_chart(fig3, use_container_width=True)

            except Exception as e:
                st.error(f"Error en el calculo: {e}")

    with st.expander("Codigo de ejemplo -- Bootstrap"):
        st.code(
            """from suite_actuarial.reservas import Bootstrap
from suite_actuarial.core.validators import ConfiguracionBootstrap

# Configurar Bootstrap con 1000 simulaciones
config = ConfiguracionBootstrap(
    num_simulaciones=1000,
    seed=42,
    percentiles=[50, 75, 90, 95, 99],
)
bs = Bootstrap(config)
resultado = bs.calcular(triangulo)

# Percentiles
for p, valor in resultado.percentiles.items():
    print(f"  P{p}: ${valor:,.2f}")

# Medidas de riesgo
var_95 = bs.calcular_var(0.95)
tvar_95 = bs.calcular_tvar(0.95)
print(f"VaR 95%:  ${var_95:,.2f}")
print(f"TVaR 95%: ${tvar_95:,.2f}")

# Distribucion completa para graficar
distribucion = bs.obtener_distribucion()
print(f"Simulaciones generadas: {len(distribucion)}")
""",
            language="python",
        )

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Acerca de los metodos")
    st.markdown("""
**Chain Ladder** -- Proyeccion determinista basada en factores de desarrollo
historicos. Estandar de la industria.

**Bornhuetter-Ferguson** -- Combina la experiencia con un loss ratio a priori.
Mas estable para anios recientes.

**Bootstrap** -- Simulacion Monte Carlo que proporciona intervalos de confianza
y medidas de riesgo (VaR, TVaR).
""")
