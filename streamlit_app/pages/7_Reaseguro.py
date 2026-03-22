"""
Reaseguro -- Demo interactivo de contratos de reaseguro.

Muestra el uso de QuotaShare, ExcessOfLoss y StopLoss
de la librería suite_actuarial.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR / "src"))

from datetime import date
from decimal import Decimal

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from suite_actuarial.reaseguro import QuotaShare, ExcessOfLoss, StopLoss
from suite_actuarial.core.validators import (
    QuotaShareConfig,
    ExcessOfLossConfig,
    StopLossConfig,
    Siniestro,
    TipoContrato,
)

# ---------------------------------------------------------------------------
# Configuracion de pagina
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Reaseguro", layout="wide")

st.title("Contratos de Reaseguro")
st.markdown(
    "Simulador interactivo de los tres tipos de contrato de reaseguro: "
    "proporcional (Quota Share) y no proporcional (Excess of Loss, Stop Loss)."
)

# ---------------------------------------------------------------------------
# Siniestros de ejemplo
# ---------------------------------------------------------------------------
SAMPLE_CLAIMS = [
    Siniestro(id_siniestro=f"SIN-{i+1:03d}", fecha_ocurrencia=date(2025, 6, 15), monto_bruto=Decimal(str(m)))
    for i, m in enumerate([
        50000, 120000, 80000, 350000, 25000,
        500000, 15000, 200000, 750000, 45000,
        180000, 90000, 420000, 60000, 300000,
    ])
]

SAMPLE_PRIMA_BRUTA = Decimal("2500000")


def crear_tabla_siniestros(siniestros: list[Siniestro]) -> pd.DataFrame:
    """Crea DataFrame de siniestros para visualizacion."""
    return pd.DataFrame({
        "ID": [s.id_siniestro for s in siniestros],
        "Monto": [f"${float(s.monto_bruto):,.0f}" for s in siniestros],
        "Monto_num": [float(s.monto_bruto) for s in siniestros],
    })


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_qs, tab_xl, tab_sl, tab_comp = st.tabs(
    ["Quota Share", "Excess of Loss", "Stop Loss", "Comparación"]
)

# ===== TAB 1: Quota Share ==================================================
with tab_qs:
    st.header("Quota Share (Cuota Parte)")
    st.markdown(
        "El reasegurador acepta un porcentaje fijo de cada riesgo y paga "
        "una comisión a la cedente por los gastos de adquisición."
    )

    col_cfg, col_res = st.columns([1, 2])

    with col_cfg:
        st.subheader("Parámetros del contrato")
        qs_cesion = st.slider("Porcentaje de cesión (%)", 5, 90, 30, step=5, key="qs_cesion")
        qs_comision = st.slider("Comisión de reaseguro (%)", 0, 45, 25, step=1, key="qs_comision")
        qs_override = st.slider("Comisión override (%)", 0, 10, 0, step=1, key="qs_override")

        st.markdown("---")
        st.subheader("Cartera")
        qs_prima = st.number_input(
            "Prima bruta ($)", min_value=100000, value=2500000, step=100000, key="qs_prima"
        )

        st.markdown("##### Siniestros de ejemplo")
        df_sin = crear_tabla_siniestros(SAMPLE_CLAIMS)
        st.dataframe(df_sin[["ID", "Monto"]], use_container_width=True, hide_index=True, height=200)

    with col_res:
        if st.button("Aplicar Quota Share", key="btn_qs"):
            try:
                config_qs = QuotaShareConfig(
                    tipo_contrato=TipoContrato.QUOTA_SHARE,
                    vigencia_inicio=date(2025, 1, 1),
                    vigencia_fin=date(2025, 12, 31),
                    porcentaje_cesion=Decimal(str(qs_cesion)),
                    comision_reaseguro=Decimal(str(qs_comision)),
                    comision_override=Decimal(str(qs_override)),
                )
                qs = QuotaShare(config_qs)
                resultado = qs.calcular_resultado_neto(
                    prima_bruta=Decimal(str(qs_prima)),
                    siniestros=SAMPLE_CLAIMS,
                )

                # Metricas
                m1, m2 = st.columns(2)
                m1.metric("Prima retenida", f"${float(resultado.monto_retenido):,.0f}")
                m2.metric("Prima cedida", f"${float(resultado.monto_cedido):,.0f}")

                m3, m4 = st.columns(2)
                m3.metric("Comisión recibida", f"${float(resultado.comision_recibida):,.0f}")
                m4.metric("Recuperación siniestros", f"${float(resultado.recuperacion_reaseguro):,.0f}")

                st.metric("Resultado neto cedente", f"${float(resultado.resultado_neto_cedente):,.0f}")

                # Graficos
                col_g1, col_g2 = st.columns(2)

                with col_g1:
                    fig_prima = go.Figure(data=[go.Pie(
                        labels=["Retenida", "Cedida"],
                        values=[float(resultado.monto_retenido), float(resultado.monto_cedido)],
                        hole=0.4,
                        marker_colors=["#1f77b4", "#ff7f0e"],
                        textinfo="label+percent",
                    )])
                    fig_prima.update_layout(title="Distribución de primas", height=350, showlegend=False)
                    st.plotly_chart(fig_prima, use_container_width=True)

                with col_g2:
                    # Siniestros retenidos vs cedidos
                    sin_total = sum(float(s.monto_bruto) for s in SAMPLE_CLAIMS)
                    sin_cedido = float(resultado.recuperacion_reaseguro)
                    sin_retenido = sin_total - sin_cedido

                    fig_sin = go.Figure()
                    for s in SAMPLE_CLAIMS:
                        m = float(s.monto_bruto)
                        ced = m * qs_cesion / 100
                        ret = m - ced
                        fig_sin.add_trace(go.Bar(
                            name=s.id_siniestro,
                            x=[s.id_siniestro],
                            y=[ret],
                            marker_color="#1f77b4",
                            showlegend=False,
                        ))
                        fig_sin.add_trace(go.Bar(
                            name=s.id_siniestro + " ced",
                            x=[s.id_siniestro],
                            y=[ced],
                            marker_color="#ff7f0e",
                            showlegend=False,
                        ))
                    # Simpler visualization
                    fig_sin2 = go.Figure(data=[go.Pie(
                        labels=["Siniestros retenidos", "Siniestros cedidos"],
                        values=[sin_retenido, sin_cedido],
                        hole=0.4,
                        marker_colors=["#1f77b4", "#ff7f0e"],
                        textinfo="label+percent",
                    )])
                    fig_sin2.update_layout(title="Distribución de siniestros", height=350, showlegend=False)
                    st.plotly_chart(fig_sin2, use_container_width=True)

            except Exception as e:
                st.error(f"Error: {e}")

    with st.expander("Código de ejemplo -- Quota Share"):
        st.code(
            """from datetime import date
from decimal import Decimal
from suite_actuarial.reaseguro import QuotaShare
from suite_actuarial.core.validators import (
    QuotaShareConfig, TipoContrato, Siniestro,
)

config = QuotaShareConfig(
    tipo_contrato=TipoContrato.QUOTA_SHARE,
    vigencia_inicio=date(2025, 1, 1),
    vigencia_fin=date(2025, 12, 31),
    porcentaje_cesion=Decimal("30"),
    comision_reaseguro=Decimal("25"),
    comision_override=Decimal("0"),
)
qs = QuotaShare(config)

# Crear siniestros
siniestros = [
    Siniestro(id_siniestro="SIN-001", fecha_ocurrencia=date(2025, 6, 15),
              monto_bruto=Decimal("350000")),
    Siniestro(id_siniestro="SIN-002", fecha_ocurrencia=date(2025, 8, 20),
              monto_bruto=Decimal("500000")),
]

resultado = qs.calcular_resultado_neto(
    prima_bruta=Decimal("2500000"),
    siniestros=siniestros,
)
print(f"Prima retenida:  ${resultado.monto_retenido:,.2f}")
print(f"Prima cedida:    ${resultado.monto_cedido:,.2f}")
print(f"Comision:        ${resultado.comision_recibida:,.2f}")
print(f"Recuperacion:    ${resultado.recuperacion_reaseguro:,.2f}")
""",
            language="python",
        )

# ===== TAB 2: Excess of Loss ==============================================
with tab_xl:
    st.header("Excess of Loss (Exceso de Pérdida)")
    st.markdown(
        "El reasegurador paga cuando un siniestro individual excede la retención "
        "de la cedente, hasta un límite máximo. Protege contra siniestros grandes."
    )

    col_cfg2, col_res2 = st.columns([1, 2])

    with col_cfg2:
        st.subheader("Parámetros del contrato")
        xl_retencion = st.number_input(
            "Retención ($)", min_value=10000, value=200000, step=25000, key="xl_ret"
        )
        xl_limite = st.number_input(
            "Límite ($)", min_value=50000, value=500000, step=50000, key="xl_lim"
        )
        xl_tasa = st.slider("Tasa de prima (%)", 1.0, 20.0, 5.0, step=0.5, key="xl_tasa")

        st.markdown("##### Siniestros de ejemplo")
        df_sin2 = crear_tabla_siniestros(SAMPLE_CLAIMS)
        st.dataframe(df_sin2[["ID", "Monto"]], use_container_width=True, hide_index=True, height=200)

    with col_res2:
        if st.button("Aplicar Excess of Loss", key="btn_xl"):
            try:
                if xl_limite <= xl_retencion:
                    st.error("El límite debe ser mayor que la retención.")
                else:
                    config_xl = ExcessOfLossConfig(
                        tipo_contrato=TipoContrato.EXCESS_OF_LOSS,
                        vigencia_inicio=date(2025, 1, 1),
                        vigencia_fin=date(2025, 12, 31),
                        retencion=Decimal(str(xl_retencion)),
                        limite=Decimal(str(xl_limite)),
                        tasa_prima=Decimal(str(xl_tasa)),
                    )
                    xl = ExcessOfLoss(config_xl)

                    prima_xl = xl.calcular_prima_reaseguro()
                    resultado_xl = xl.calcular_resultado_neto(
                        prima_reaseguro_cobrada=prima_xl,
                        siniestros=SAMPLE_CLAIMS,
                    )

                    # Metricas
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Prima de reaseguro", f"${float(prima_xl):,.0f}")
                    m2.metric("Recuperación total", f"${float(resultado_xl.recuperacion_reaseguro):,.0f}")
                    m3.metric("Resultado neto", f"${float(resultado_xl.resultado_neto_cedente):,.0f}")

                    # Detalle por siniestro
                    st.subheader("Detalle por siniestro")
                    detalle_data = []
                    for s in SAMPLE_CLAIMS:
                        monto = float(s.monto_bruto)
                        if monto <= xl_retencion:
                            retenido = monto
                            recuperado = 0
                        else:
                            exceso = monto - xl_retencion
                            recuperado = min(exceso, xl_limite)
                            retenido = monto - recuperado
                        detalle_data.append({
                            "ID": s.id_siniestro,
                            "Monto bruto": f"${monto:,.0f}",
                            "Retenido": f"${retenido:,.0f}",
                            "Recuperado": f"${recuperado:,.0f}",
                            "Retenido_num": retenido,
                            "Recuperado_num": recuperado,
                        })
                    df_det = pd.DataFrame(detalle_data)
                    st.dataframe(
                        df_det[["ID", "Monto bruto", "Retenido", "Recuperado"]],
                        use_container_width=True,
                        hide_index=True,
                    )

                    # Grafico de barras apiladas
                    fig_xl = go.Figure()
                    fig_xl.add_trace(go.Bar(
                        name="Retenido",
                        x=df_det["ID"],
                        y=df_det["Retenido_num"],
                        marker_color="#1f77b4",
                    ))
                    fig_xl.add_trace(go.Bar(
                        name="Recuperado",
                        x=df_det["ID"],
                        y=df_det["Recuperado_num"],
                        marker_color="#2ca02c",
                    ))
                    fig_xl.add_hline(
                        y=xl_retencion,
                        line_dash="dash",
                        line_color="red",
                        annotation_text=f"Retención: ${xl_retencion:,.0f}",
                    )
                    fig_xl.update_layout(
                        barmode="stack",
                        xaxis_title="Siniestro",
                        yaxis_title="Monto (MXN)",
                        height=450,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    )
                    st.plotly_chart(fig_xl, use_container_width=True)

            except Exception as e:
                st.error(f"Error: {e}")

    with st.expander("Código de ejemplo -- Excess of Loss"):
        st.code(
            """from datetime import date
from decimal import Decimal
from suite_actuarial.reaseguro import ExcessOfLoss
from suite_actuarial.core.validators import (
    ExcessOfLossConfig, TipoContrato, Siniestro,
)

# Contrato XL 500,000 xs 200,000
config = ExcessOfLossConfig(
    tipo_contrato=TipoContrato.EXCESS_OF_LOSS,
    vigencia_inicio=date(2025, 1, 1),
    vigencia_fin=date(2025, 12, 31),
    retencion=Decimal("200000"),
    limite=Decimal("500000"),
    tasa_prima=Decimal("5.0"),
)
xl = ExcessOfLoss(config)

siniestros = [
    Siniestro(id_siniestro="SIN-001", fecha_ocurrencia=date(2025, 3, 10),
              monto_bruto=Decimal("150000")),  # No excede retencion
    Siniestro(id_siniestro="SIN-002", fecha_ocurrencia=date(2025, 7, 22),
              monto_bruto=Decimal("400000")),  # Excede, recupera 200K
    Siniestro(id_siniestro="SIN-003", fecha_ocurrencia=date(2025, 11, 5),
              monto_bruto=Decimal("800000")),  # Excede, recupera 500K (limite)
]

prima_xl = xl.calcular_prima_reaseguro()
resultado = xl.calcular_resultado_neto(prima_xl, siniestros)

print(f"Prima XL:      ${prima_xl:,.2f}")
print(f"Recuperacion:  ${resultado.recuperacion_reaseguro:,.2f}")
print(f"Retenido:      ${resultado.monto_retenido:,.2f}")
""",
            language="python",
        )

# ===== TAB 3: Stop Loss ===================================================
with tab_sl:
    st.header("Stop Loss (Limitación de Pérdidas)")
    st.markdown(
        "Protege cuando la siniestralidad agregada de la cartera "
        "excede un porcentaje objetivo (attachment point) de las primas."
    )

    col_cfg3, col_res3 = st.columns([1, 2])

    with col_cfg3:
        st.subheader("Parámetros del contrato")
        sl_attachment = st.slider("Attachment point (%)", 50, 150, 80, step=5, key="sl_att")
        sl_limite = st.slider("Límite de cobertura (%)", 5, 50, 20, step=5, key="sl_lim")
        sl_primas = st.number_input(
            "Primas sujetas ($)", min_value=100000, value=2500000, step=100000, key="sl_primas"
        )

        st.markdown("##### Siniestros de ejemplo")
        total_siniestros = sum(float(s.monto_bruto) for s in SAMPLE_CLAIMS)
        siniestralidad = (total_siniestros / float(sl_primas)) * 100
        st.markdown(f"Total siniestros: ${total_siniestros:,.0f}")
        st.markdown(f"Siniestralidad: {siniestralidad:.1f}%")

    with col_res3:
        if st.button("Aplicar Stop Loss", key="btn_sl"):
            try:
                config_sl = StopLossConfig(
                    tipo_contrato=TipoContrato.STOP_LOSS,
                    vigencia_inicio=date(2025, 1, 1),
                    vigencia_fin=date(2025, 12, 31),
                    attachment_point=Decimal(str(sl_attachment)),
                    limite_cobertura=Decimal(str(sl_limite)),
                    primas_sujetas=Decimal(str(sl_primas)),
                )
                sl = StopLoss(config_sl)
                resultado_sl = sl.calcular_resultado_neto(
                    primas_totales=Decimal(str(sl_primas)),
                    siniestros=SAMPLE_CLAIMS,
                )

                # Metricas
                m1, m2 = st.columns(2)
                m1.metric("Siniestralidad bruta", resultado_sl.detalles.get("siniestralidad_bruta", "N/A"))
                m2.metric("Siniestralidad neta", resultado_sl.detalles.get("siniestralidad_neta", "N/A"))

                m3, m4, m5 = st.columns(3)
                m3.metric("Recuperación", f"${float(resultado_sl.recuperacion_reaseguro):,.0f}")
                m4.metric("Prima reaseguro", f"${float(resultado_sl.prima_reaseguro_pagada):,.0f}")
                m5.metric("Contrato activado", "SI" if resultado_sl.detalles.get("contrato_activado") else "NO")

                # Grafico de siniestralidad
                st.subheader("Visualización del contrato")
                attachment_monto = sl_primas * sl_attachment / 100
                techo_monto = sl_primas * (sl_attachment + sl_limite) / 100

                fig_sl = go.Figure()

                # Barra de siniestralidad
                fig_sl.add_trace(go.Bar(
                    x=["Cartera"],
                    y=[min(total_siniestros, attachment_monto)],
                    name="Retenido (bajo attachment)",
                    marker_color="#1f77b4",
                ))
                if total_siniestros > attachment_monto:
                    recuperable = min(total_siniestros - attachment_monto, techo_monto - attachment_monto)
                    fig_sl.add_trace(go.Bar(
                        x=["Cartera"],
                        y=[recuperable],
                        name="Cubierto por Stop Loss",
                        marker_color="#2ca02c",
                    ))
                    exceso_sobre_techo = max(0, total_siniestros - techo_monto)
                    if exceso_sobre_techo > 0:
                        fig_sl.add_trace(go.Bar(
                            x=["Cartera"],
                            y=[exceso_sobre_techo],
                            name="Sobre el límite (retenido)",
                            marker_color="#d62728",
                        ))

                fig_sl.add_hline(
                    y=attachment_monto,
                    line_dash="dash",
                    line_color="orange",
                    annotation_text=f"Attachment: {sl_attachment}% = ${attachment_monto:,.0f}",
                )
                fig_sl.add_hline(
                    y=techo_monto,
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"Techo: {sl_attachment + sl_limite}% = ${techo_monto:,.0f}",
                )
                fig_sl.update_layout(
                    barmode="stack",
                    yaxis_title="Monto (MXN)",
                    height=450,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                )
                st.plotly_chart(fig_sl, use_container_width=True)

            except Exception as e:
                st.error(f"Error: {e}")

    with st.expander("Código de ejemplo -- Stop Loss"):
        st.code(
            """from datetime import date
from decimal import Decimal
from suite_actuarial.reaseguro import StopLoss
from suite_actuarial.core.validators import (
    StopLossConfig, TipoContrato, Siniestro,
)

# Contrato Stop Loss: attachment 80%, limite 20%, sobre 10M de primas
config = StopLossConfig(
    tipo_contrato=TipoContrato.STOP_LOSS,
    vigencia_inicio=date(2025, 1, 1),
    vigencia_fin=date(2025, 12, 31),
    attachment_point=Decimal("80"),
    limite_cobertura=Decimal("20"),
    primas_sujetas=Decimal("10000000"),
)
sl = StopLoss(config)

siniestros = [
    Siniestro(id_siniestro=f"SIN-{i}", fecha_ocurrencia=date(2025, 6, 1),
              monto_bruto=Decimal(str(m)))
    for i, m in enumerate([500000, 1200000, 3000000, 2500000, 1800000])
]

resultado = sl.calcular_resultado_neto(
    primas_totales=Decimal("10000000"),
    siniestros=siniestros,
)
print(f"Siniestralidad bruta: {resultado.detalles['siniestralidad_bruta']}")
print(f"Recuperacion:         ${resultado.recuperacion_reaseguro:,.2f}")
print(f"Contrato activado:    {resultado.detalles['contrato_activado']}")
""",
            language="python",
        )

# ===== TAB 4: Comparacion =================================================
with tab_comp:
    st.header("Comparación de estrategias de reaseguro")
    st.markdown(
        "Comparación lado a lado de las tres estrategias aplicadas "
        "a los mismos siniestros de ejemplo."
    )

    st.subheader("Parámetros para la comparación")
    c1, c2, c3 = st.columns(3)
    with c1:
        comp_cesion = st.slider("QS: Cesión (%)", 5, 90, 30, step=5, key="comp_qs")
        comp_comision = st.slider("QS: Comisión (%)", 0, 45, 25, step=1, key="comp_qs_com")
    with c2:
        comp_ret = st.number_input("XL: Retención ($)", min_value=10000, value=200000, step=25000, key="comp_ret")
        comp_lim = st.number_input("XL: Límite ($)", min_value=50000, value=500000, step=50000, key="comp_lim")
        comp_tasa = st.slider("XL: Tasa prima (%)", 1.0, 20.0, 5.0, step=0.5, key="comp_tasa")
    with c3:
        comp_att = st.slider("SL: Attachment (%)", 50, 150, 80, step=5, key="comp_att")
        comp_sl_lim = st.slider("SL: Límite (%)", 5, 50, 20, step=5, key="comp_sl_lim")
        comp_sl_prima = st.number_input("SL: Primas sujetas ($)", min_value=100000, value=2500000, step=100000, key="comp_sl_p")

    if st.button("Comparar las 3 estrategias", key="btn_comp"):
        try:
            results = {}

            # 1. Quota Share
            cfg_qs = QuotaShareConfig(
                tipo_contrato=TipoContrato.QUOTA_SHARE,
                vigencia_inicio=date(2025, 1, 1),
                vigencia_fin=date(2025, 12, 31),
                porcentaje_cesion=Decimal(str(comp_cesion)),
                comision_reaseguro=Decimal(str(comp_comision)),
            )
            qs_obj = QuotaShare(cfg_qs)
            res_qs = qs_obj.calcular_resultado_neto(Decimal(str(comp_sl_prima)), SAMPLE_CLAIMS)
            results["Quota Share"] = res_qs

            # 2. Excess of Loss
            if comp_lim > comp_ret:
                cfg_xl = ExcessOfLossConfig(
                    tipo_contrato=TipoContrato.EXCESS_OF_LOSS,
                    vigencia_inicio=date(2025, 1, 1),
                    vigencia_fin=date(2025, 12, 31),
                    retencion=Decimal(str(comp_ret)),
                    limite=Decimal(str(comp_lim)),
                    tasa_prima=Decimal(str(comp_tasa)),
                )
                xl_obj = ExcessOfLoss(cfg_xl)
                prima_xl_calc = xl_obj.calcular_prima_reaseguro()
                res_xl = xl_obj.calcular_resultado_neto(prima_xl_calc, SAMPLE_CLAIMS)
                results["Excess of Loss"] = res_xl

            # 3. Stop Loss
            cfg_sl = StopLossConfig(
                tipo_contrato=TipoContrato.STOP_LOSS,
                vigencia_inicio=date(2025, 1, 1),
                vigencia_fin=date(2025, 12, 31),
                attachment_point=Decimal(str(comp_att)),
                limite_cobertura=Decimal(str(comp_sl_lim)),
                primas_sujetas=Decimal(str(comp_sl_prima)),
            )
            sl_obj = StopLoss(cfg_sl)
            res_sl = sl_obj.calcular_resultado_neto(Decimal(str(comp_sl_prima)), SAMPLE_CLAIMS)
            results["Stop Loss"] = res_sl

            # Tabla comparativa
            st.subheader("Tabla comparativa")
            total_sin = sum(float(s.monto_bruto) for s in SAMPLE_CLAIMS)

            comp_data = []
            for nombre, res in results.items():
                comp_data.append({
                    "Estrategia": nombre,
                    "Recuperación": f"${float(res.recuperacion_reaseguro):,.0f}",
                    "Siniestros retenidos": f"${total_sin - float(res.recuperacion_reaseguro):,.0f}",
                    "Prima/Costo reaseguro": f"${float(res.prima_reaseguro_pagada):,.0f}",
                    "Resultado neto": f"${float(res.resultado_neto_cedente):,.0f}",
                    "Recuperacion_num": float(res.recuperacion_reaseguro),
                    "Retenido_num": total_sin - float(res.recuperacion_reaseguro),
                    "Costo_num": float(res.prima_reaseguro_pagada),
                    "Neto_num": float(res.resultado_neto_cedente),
                })

            df_comp = pd.DataFrame(comp_data)
            st.dataframe(
                df_comp[["Estrategia", "Recuperación", "Siniestros retenidos", "Prima/Costo reaseguro", "Resultado neto"]],
                use_container_width=True,
                hide_index=True,
            )

            # Graficos comparativos
            col_g1, col_g2 = st.columns(2)

            with col_g1:
                fig_comp1 = go.Figure()
                fig_comp1.add_trace(go.Bar(
                    name="Retenido",
                    x=df_comp["Estrategia"],
                    y=df_comp["Retenido_num"],
                    marker_color="#1f77b4",
                    text=df_comp["Retenido_num"].apply(lambda x: f"${x:,.0f}"),
                    textposition="outside",
                ))
                fig_comp1.add_trace(go.Bar(
                    name="Recuperado",
                    x=df_comp["Estrategia"],
                    y=df_comp["Recuperacion_num"],
                    marker_color="#2ca02c",
                    text=df_comp["Recuperacion_num"].apply(lambda x: f"${x:,.0f}"),
                    textposition="outside",
                ))
                fig_comp1.update_layout(
                    title="Retención vs Recuperación",
                    barmode="group",
                    yaxis_title="Monto (MXN)",
                    height=400,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                )
                st.plotly_chart(fig_comp1, use_container_width=True)

            with col_g2:
                fig_comp2 = go.Figure()
                fig_comp2.add_trace(go.Bar(
                    name="Costo reaseguro",
                    x=df_comp["Estrategia"],
                    y=df_comp["Costo_num"],
                    marker_color="#ff7f0e",
                    text=df_comp["Costo_num"].apply(lambda x: f"${x:,.0f}"),
                    textposition="outside",
                ))
                fig_comp2.add_trace(go.Bar(
                    name="Resultado neto",
                    x=df_comp["Estrategia"],
                    y=df_comp["Neto_num"],
                    marker_color="#9467bd",
                    text=df_comp["Neto_num"].apply(lambda x: f"${x:,.0f}"),
                    textposition="outside",
                ))
                fig_comp2.update_layout(
                    title="Costo vs Resultado neto",
                    barmode="group",
                    yaxis_title="Monto (MXN)",
                    height=400,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                )
                st.plotly_chart(fig_comp2, use_container_width=True)

        except Exception as e:
            st.error(f"Error: {e}")

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Tipos de reaseguro")
    st.markdown("""
**Quota Share** (Proporcional)
El reasegurador acepta un % fijo de cada riesgo. Simple y predecible.

**Excess of Loss** (No proporcional)
Protege contra siniestros individuales grandes que excedan la retención.

**Stop Loss** (No proporcional)
Protege cuando la siniestralidad agregada excede un umbral.
""")
    st.markdown("---")
    st.markdown(f"**Siniestros de ejemplo:** {len(SAMPLE_CLAIMS)}")
    st.markdown(f"**Total siniestros:** ${sum(float(s.monto_bruto) for s in SAMPLE_CLAIMS):,.0f}")
