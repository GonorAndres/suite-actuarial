"""
Demo: Modulo de Danos -- suite_actuarial

Seguro de auto (AMIS), modelo colectivo frecuencia-severidad,
y sistema Bonus-Malus.
"""

import sys
from decimal import Decimal
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR / "src"))

from suite_actuarial.danos import SeguroAuto, ModeloColectivo, CalculadoraBonusMalus, Cobertura
from suite_actuarial.danos.tablas_amis import GRUPOS_VEHICULO, ZONAS_RIESGO

st.set_page_config(page_title="Danos -- suite_actuarial", layout="wide")

st.title("Seguros de Danos")
st.markdown(
    "Motor de tarificacion para seguros de propiedad y responsabilidad civil "
    "(`suite_actuarial.danos`): auto AMIS, modelo colectivo y Bonus-Malus."
)

# -----------------------------------------------------------------------
# Helpers for dropdowns
# -----------------------------------------------------------------------
TIPOS_VEHICULO = list(GRUPOS_VEHICULO.keys())
NOMBRES_VEHICULO = {k: k.replace("_", " ").title() for k in TIPOS_VEHICULO}

ZONAS = list(ZONAS_RIESGO.keys())
NOMBRES_ZONA = {k: k.replace("_", " ").title() for k in ZONAS}

OPCIONES_DEDUCIBLE = {
    "3%": Decimal("0.03"),
    "5%": Decimal("0.05"),
    "10%": Decimal("0.10"),
    "15%": Decimal("0.15"),
    "20%": Decimal("0.20"),
}

# -----------------------------------------------------------------------
# Tabs
# -----------------------------------------------------------------------
tab_auto, tab_colectivo, tab_bms = st.tabs(
    ["Cotizacion Auto", "Modelo Colectivo", "Bonus-Malus"]
)

# ===== TAB 1: Cotizacion Auto =====
with tab_auto:
    st.subheader("Cotizacion de seguro de auto")

    c1, c2 = st.columns(2)
    with c1:
        tipo_vehiculo_label = st.selectbox(
            "Tipo de vehiculo",
            options=TIPOS_VEHICULO,
            format_func=lambda x: f"{NOMBRES_VEHICULO[x]} (grupo {GRUPOS_VEHICULO[x]})",
            index=1,
        )
        valor_vehiculo = st.number_input(
            "Valor del vehiculo (MXN)",
            min_value=50_000,
            max_value=5_000_000,
            value=400_000,
            step=50_000,
            format="%d",
        )
        antiguedad = st.slider("Antiguedad (anos)", 0, 10, 2)

    with c2:
        zona_label = st.selectbox(
            "Zona de riesgo",
            options=ZONAS,
            format_func=lambda x: f"{NOMBRES_ZONA[x]} (factor {ZONAS_RIESGO[x]})",
            index=7,  # guadalajara
        )
        edad_conductor = st.slider("Edad del conductor", 18, 80, 35)
        deducible_label = st.selectbox(
            "Deducible",
            options=list(OPCIONES_DEDUCIBLE.keys()),
            index=1,  # 5%
        )

    deducible_pct = OPCIONES_DEDUCIBLE[deducible_label]

    auto = SeguroAuto(
        valor_vehiculo=Decimal(str(valor_vehiculo)),
        tipo_vehiculo=tipo_vehiculo_label,
        antiguedad_anos=antiguedad,
        zona=zona_label,
        edad_conductor=edad_conductor,
        deducible_pct=deducible_pct,
    )
    cotizacion = auto.generar_cotizacion()

    # Resumen general
    r1, r2, r3 = st.columns(3)
    r1.metric("Valor asegurado", f"${float(cotizacion['vehiculo']['valor_asegurado']):,.0f}")
    r2.metric("Prima total anual", f"${float(cotizacion['prima_total']):,.2f}")
    r3.metric(
        "Deducible en pesos",
        f"${float(cotizacion['deducible']['pesos']):,.0f}",
    )

    # Tabla de coberturas
    filas_cob = []
    for cob_key, prima in cotizacion["coberturas"].items():
        filas_cob.append({
            "Cobertura": cob_key.replace("_", " ").title(),
            "Prima anual (MXN)": float(prima),
        })

    df_cob = pd.DataFrame(filas_cob)
    st.dataframe(
        df_cob.style.format({"Prima anual (MXN)": "${:,.2f}"}),
        use_container_width=True,
        hide_index=True,
    )

    # Chart
    fig_cob = px.pie(
        df_cob,
        values="Prima anual (MXN)",
        names="Cobertura",
        title="Distribucion de prima por cobertura",
    )
    st.plotly_chart(fig_cob, use_container_width=True)

    with st.expander("Ver codigo Python"):
        st.code(
            f'''from decimal import Decimal
from suite_actuarial.danos import SeguroAuto

auto = SeguroAuto(
    valor_vehiculo=Decimal("{valor_vehiculo}"),
    tipo_vehiculo="{tipo_vehiculo_label}",
    antiguedad_anos={antiguedad},
    zona="{zona_label}",
    edad_conductor={edad_conductor},
    deducible_pct=Decimal("{deducible_pct}"),
)

cotizacion = auto.generar_cotizacion()

print(f"Valor asegurado: ${{cotizacion['vehiculo']['valor_asegurado']:,.2f}}")
print(f"Prima total anual: ${{cotizacion['prima_total']:,.2f}}")
print()
for cob, prima in cotizacion["coberturas"].items():
    print(f"  {{cob:.<25s}} ${{prima:>10,.2f}}")
''',
            language="python",
        )


# ===== TAB 2: Modelo Colectivo =====
with tab_colectivo:
    st.subheader("Modelo colectivo de riesgo (frecuencia-severidad)")
    st.markdown(
        "S = X1 + X2 + ... + XN, donde N ~ frecuencia y Xi ~ severidad. "
        "Simulacion Monte Carlo de perdidas agregadas."
    )

    mc1, mc2 = st.columns(2)

    with mc1:
        st.markdown("**Distribucion de frecuencia**")
        dist_freq = st.selectbox(
            "Distribucion",
            ["poisson", "negbinom", "binomial"],
            key="freq_dist",
        )
        if dist_freq == "poisson":
            lam = st.number_input("lambda", min_value=0.1, max_value=100.0, value=5.0, step=0.5)
            params_freq = {"lambda_": lam}
        elif dist_freq == "negbinom":
            n_nb = st.number_input("n (exitos)", min_value=1.0, max_value=50.0, value=5.0, step=1.0)
            p_nb = st.number_input("p (prob. exito)", min_value=0.01, max_value=0.99, value=0.30, step=0.05)
            params_freq = {"n": n_nb, "p": p_nb}
        else:
            n_b = st.number_input("n (ensayos)", min_value=1, max_value=100, value=20, step=1)
            p_b = st.number_input("p (probabilidad)", min_value=0.01, max_value=0.99, value=0.10, step=0.05)
            params_freq = {"n": n_b, "p": p_b}

    with mc2:
        st.markdown("**Distribucion de severidad**")
        dist_sev = st.selectbox(
            "Distribucion",
            ["lognormal", "gamma", "pareto", "weibull", "exponencial"],
            key="sev_dist",
        )
        if dist_sev == "lognormal":
            mu_ln = st.number_input("mu (log-media)", min_value=0.0, max_value=15.0, value=10.0, step=0.5)
            sigma_ln = st.number_input("sigma (log-desv)", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
            params_sev = {"mu": mu_ln, "sigma": sigma_ln}
        elif dist_sev == "gamma":
            alpha_g = st.number_input("alpha (forma)", min_value=0.1, max_value=20.0, value=2.0, step=0.5)
            beta_g = st.number_input("beta (tasa)", min_value=0.0001, max_value=1.0, value=0.0001, step=0.0001, format="%.4f")
            params_sev = {"alpha": alpha_g, "beta": beta_g}
        elif dist_sev == "pareto":
            alpha_p = st.number_input("alpha (forma)", min_value=1.1, max_value=10.0, value=3.0, step=0.5)
            scale_p = st.number_input("scale (escala)", min_value=100.0, max_value=1_000_000.0, value=50000.0, step=10000.0)
            params_sev = {"alpha": alpha_p, "scale": scale_p}
        elif dist_sev == "weibull":
            c_w = st.number_input("c (forma)", min_value=0.1, max_value=10.0, value=1.5, step=0.1)
            scale_w = st.number_input("scale (escala)", min_value=100.0, max_value=1_000_000.0, value=50000.0, step=10000.0)
            params_sev = {"c": c_w, "scale": scale_w}
        else:  # exponencial
            lam_e = st.number_input("lambda (tasa)", min_value=0.000001, max_value=0.01, value=0.0001, step=0.00001, format="%.6f")
            params_sev = {"lambda_": lam_e}

    n_sim = st.slider("Numero de simulaciones", 1_000, 100_000, 10_000, step=1_000)

    @st.cache_data(show_spinner="Simulando perdidas...")
    def _simular(df, pf, ds, ps, ns, seed):
        modelo = ModeloColectivo(df, pf, ds, ps)
        stats = modelo.estadisticas(n_simulaciones=ns, seed=seed)
        perdidas = modelo.simular_perdidas(n_simulaciones=ns, seed=seed)
        return stats, perdidas

    stats_mc, perdidas = _simular(dist_freq, params_freq, dist_sev, params_sev, n_sim, 42)

    # Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Prima pura E[S]", f"${float(stats_mc['prima_pura']):,.2f}")
    m2.metric("Desv. estandar", f"${float(stats_mc['desviacion_estandar']):,.2f}")
    m3.metric("VaR 95%", f"${float(stats_mc['var_95']):,.2f}")
    m4.metric("TVaR 95%", f"${float(stats_mc['tvar_95']):,.2f}")

    # Histogram
    fig_hist = px.histogram(
        x=perdidas,
        nbins=80,
        title="Distribucion de perdidas agregadas (simulacion Monte Carlo)",
        labels={"x": "Perdida agregada (MXN)", "count": "Frecuencia"},
    )
    fig_hist.add_vline(
        x=float(stats_mc["prima_pura"]),
        line_dash="dash",
        line_color="green",
        annotation_text="E[S]",
    )
    fig_hist.add_vline(
        x=float(stats_mc["var_95"]),
        line_dash="dash",
        line_color="orange",
        annotation_text="VaR 95%",
    )
    fig_hist.add_vline(
        x=float(stats_mc["tvar_95"]),
        line_dash="dash",
        line_color="red",
        annotation_text="TVaR 95%",
    )
    fig_hist.update_layout(showlegend=False)
    st.plotly_chart(fig_hist, use_container_width=True)

    with st.expander("Estadisticas completas"):
        stats_display = {k: str(v) for k, v in stats_mc.items()}
        st.json(stats_display)

    with st.expander("Ver codigo Python"):
        freq_params_str = str(params_freq)
        sev_params_str = str(params_sev)
        st.code(
            f'''from suite_actuarial.danos import ModeloColectivo

modelo = ModeloColectivo(
    dist_frecuencia="{dist_freq}",
    params_frecuencia={freq_params_str},
    dist_severidad="{dist_sev}",
    params_severidad={sev_params_str},
)

# Momentos analiticos
print(f"Prima pura E[S]: ${{modelo.prima_pura():,.2f}}")
print(f"Desv. estandar:  ${{modelo.desviacion_estandar():,.2f}}")

# Medidas de riesgo via simulacion
print(f"VaR 95%:  ${{modelo.var(nivel=0.95, n_simulaciones={n_sim}, seed=42):,.2f}}")
print(f"TVaR 95%: ${{modelo.tvar(nivel=0.95, n_simulaciones={n_sim}, seed=42):,.2f}}")

# Resumen completo
estadisticas = modelo.estadisticas(n_simulaciones={n_sim}, seed=42)
for k, v in estadisticas.items():
    print(f"  {{k}}: {{v}}")

# Simulacion (array numpy)
perdidas = modelo.simular_perdidas(n_simulaciones={n_sim}, seed=42)
''',
            language="python",
        )


# ===== TAB 3: Bonus-Malus =====
with tab_bms:
    st.subheader("Sistema Bonus-Malus")
    st.markdown(
        "Escala mexicana de descuentos/recargos por historial de siniestros. "
        "Sin siniestros: -5% por ano (max -30%). Con siniestro: +15% a +50%."
    )

    st.markdown("**Ingresa el historial de siniestros por ano:**")
    n_anos_bms = st.slider("Anos de historial", 1, 15, 5, key="bms_anos")

    cols_bms = st.columns(min(n_anos_bms, 5))
    historial = []
    for i in range(n_anos_bms):
        col_idx = i % min(n_anos_bms, 5)
        with cols_bms[col_idx]:
            s = st.number_input(
                f"Ano {i + 1}",
                min_value=0,
                max_value=5,
                value=0,
                step=1,
                key=f"bms_{i}",
            )
            historial.append(s)

    bms = CalculadoraBonusMalus(nivel_actual=0)
    trayectoria = bms.historial_completo(historial)

    df_bms = pd.DataFrame(trayectoria)
    df_bms["factor"] = df_bms["factor"].apply(float)
    df_bms["descuento_recargo"] = df_bms["factor"].apply(
        lambda f: f"{(f - 1) * 100:+.0f}%"
    )

    st.dataframe(
        df_bms[["ano", "siniestros", "nivel_previo", "nivel_nuevo", "factor", "descuento_recargo"]].rename(
            columns={
                "ano": "Ano",
                "siniestros": "Siniestros",
                "nivel_previo": "Nivel previo",
                "nivel_nuevo": "Nivel nuevo",
                "factor": "Factor prima",
                "descuento_recargo": "Ajuste",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    # Chart
    fig_bms = go.Figure()
    fig_bms.add_trace(
        go.Scatter(
            x=df_bms["ano"],
            y=df_bms["factor"],
            mode="lines+markers",
            name="Factor BMS",
            line=dict(color="#E91E63", width=2),
        )
    )
    fig_bms.add_hline(y=1.0, line_dash="dash", line_color="gray", annotation_text="Base (1.00)")
    fig_bms.update_layout(
        title="Trayectoria del factor Bonus-Malus",
        xaxis_title="Ano",
        yaxis_title="Factor de prima",
        yaxis=dict(range=[0.6, 1.6]),
    )
    st.plotly_chart(fig_bms, use_container_width=True)

    with st.expander("Ver codigo Python"):
        st.code(
            f'''from suite_actuarial.danos import CalculadoraBonusMalus

bms = CalculadoraBonusMalus(nivel_actual=0)

historial = {historial}
trayectoria = bms.historial_completo(historial)

for paso in trayectoria:
    print(
        f"Ano {{paso['ano']}}: {{paso['siniestros']}} siniestros | "
        f"nivel {{paso['nivel_previo']}} -> {{paso['nivel_nuevo']}} | "
        f"factor {{paso['factor']}}"
    )

print(f"\\nFactor final: {{bms.factor_actual()}}")
print(f"Nivel final:  {{bms.nivel_actual}}")
''',
            language="python",
        )
