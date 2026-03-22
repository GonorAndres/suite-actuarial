"""
Cumplimiento Regulatorio -- Demo interactivo del módulo regulatorio.

Muestra el uso de AgregadorRCS, reservas técnicas y validaciones SAT
de la librería suite_actuarial.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR / "src"))

from decimal import Decimal

import plotly.graph_objects as go
import streamlit as st

from suite_actuarial.regulatorio import AgregadorRCS
from suite_actuarial.core.validators import (
    ConfiguracionRCSDanos,
    ConfiguracionRCSInversion,
    ConfiguracionRCSVida,
)
from suite_actuarial.config import cargar_config

# ---------------------------------------------------------------------------
# Configuracion de pagina
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Regulatorio", layout="wide")

st.title("Cumplimiento Regulatorio")
st.markdown(
    "Herramientas de cálculo regulatorio para aseguradoras mexicanas: "
    "RCS (CNSF), reservas técnicas y validaciones fiscales (SAT)."
)

# ---------------------------------------------------------------------------
# Sidebar: selector de anio de configuracion
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Configuración")
    anio_config = st.selectbox(
        "Año regulatorio",
        options=[2024, 2025, 2026],
        index=2,
        key="anio_reg",
    )
    try:
        cfg = cargar_config(anio_config)
        st.success(f"Configuración {anio_config} cargada")
        st.markdown(f"- UMA diaria: ${cfg.uma.uma_diaria}")
        st.markdown(f"- UMA anual: ${cfg.uma.uma_anual}")
        st.markdown(f"- ISR PM: {float(cfg.tasas_sat.tasa_isr_personas_morales)*100:.0f}%")
        st.markdown(f"- IVA: {float(cfg.tasas_sat.tasa_iva)*100:.0f}%")
    except Exception as e:
        st.error(f"Error cargando configuración: {e}")
        cfg = None

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_rcs, tab_reservas, tab_sat = st.tabs(
    ["RCS", "Reservas Técnicas", "Validaciones SAT"]
)

# ===== TAB 1: RCS ==========================================================
with tab_rcs:
    st.header("Requerimiento de Capital de Solvencia (RCS)")
    st.markdown(
        "Cálculo del RCS agregado con matriz de correlación CNSF, "
        "combinando riesgos de suscripción (vida y daños) e inversión."
    )

    col_vida, col_danos, col_inv = st.columns(3)

    with col_vida:
        st.subheader("RCS Vida")
        sa_total = st.number_input(
            "Suma asegurada total (MDP)",
            min_value=100.0,
            max_value=100000.0,
            value=500.0,
            step=50.0,
            key="rcs_sa",
        )
        reserva_mat = st.number_input(
            "Reserva matemática (MDP)",
            min_value=0.0,
            max_value=100000.0,
            value=350.0,
            step=50.0,
            key="rcs_rm",
        )
        edad_prom = st.slider("Edad promedio asegurados", 18, 80, 45, key="rcs_edad")
        dur_prom = st.slider("Duración promedio pólizas (años)", 1, 40, 15, key="rcs_dur")
        num_aseg = st.number_input(
            "Número de asegurados", min_value=1, max_value=1000000, value=10000, key="rcs_naseg"
        )

    with col_danos:
        st.subheader("RCS Daños")
        primas_ret = st.number_input(
            "Primas retenidas 12m (MDP)",
            min_value=1.0,
            max_value=100000.0,
            value=250.0,
            step=50.0,
            key="rcs_primas",
        )
        reserva_sin = st.number_input(
            "Reserva de siniestros (MDP)",
            min_value=0.0,
            max_value=100000.0,
            value=180.0,
            step=25.0,
            key="rcs_ressini",
        )
        cv = st.slider(
            "Coeficiente de variación",
            min_value=0.05,
            max_value=0.50,
            value=0.15,
            step=0.01,
            key="rcs_cv",
        )

    with col_inv:
        st.subheader("RCS Inversión")
        v_acciones = st.number_input("Acciones (MDP)", min_value=0.0, value=50.0, step=10.0, key="rcs_acc")
        v_gob = st.number_input("Bonos gubernamentales (MDP)", min_value=0.0, value=300.0, step=50.0, key="rcs_gob")
        v_corp = st.number_input("Bonos corporativos (MDP)", min_value=0.0, value=150.0, step=25.0, key="rcs_corp")
        v_inm = st.number_input("Inmuebles (MDP)", min_value=0.0, value=100.0, step=25.0, key="rcs_inm")
        dur_bonos = st.slider("Duración promedio bonos (años)", 1.0, 25.0, 7.5, step=0.5, key="rcs_durbonos")
        calif = st.selectbox("Calificación promedio", ["AAA", "AA", "A", "BBB", "BB", "B"], index=1, key="rcs_calif")

    st.markdown("---")
    capital_min = st.number_input(
        "Capital mínimo pagado (MDP)",
        min_value=1.0,
        max_value=500000.0,
        value=1000.0,
        step=100.0,
        key="rcs_capital",
    )

    if st.button("Calcular RCS", key="btn_rcs"):
        try:
            factor = Decimal("1000000")  # MDP -> pesos

            config_vida = ConfiguracionRCSVida(
                suma_asegurada_total=Decimal(str(sa_total)) * factor,
                reserva_matematica=Decimal(str(reserva_mat)) * factor,
                edad_promedio_asegurados=edad_prom,
                duracion_promedio_polizas=dur_prom,
                numero_asegurados=num_aseg,
            )
            config_danos = ConfiguracionRCSDanos(
                primas_retenidas_12m=Decimal(str(primas_ret)) * factor,
                reserva_siniestros=Decimal(str(reserva_sin)) * factor,
                coeficiente_variacion=Decimal(str(cv)),
            )
            config_inv = ConfiguracionRCSInversion(
                valor_acciones=Decimal(str(v_acciones)) * factor,
                valor_bonos_gubernamentales=Decimal(str(v_gob)) * factor,
                valor_bonos_corporativos=Decimal(str(v_corp)) * factor,
                valor_inmuebles=Decimal(str(v_inm)) * factor,
                duracion_promedio_bonos=Decimal(str(dur_bonos)),
                calificacion_promedio_bonos=calif,
            )

            agreg = AgregadorRCS(
                config_vida=config_vida,
                config_danos=config_danos,
                config_inversion=config_inv,
                capital_minimo_pagado=Decimal(str(capital_min)) * factor,
            )
            resultado = agreg.calcular_rcs_completo()

            # Metricas principales
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("RCS Total (MDP)", f"${float(resultado.rcs_total) / 1e6:,.1f}")
            m2.metric("Capital (MDP)", f"${float(resultado.capital_minimo_pagado) / 1e6:,.1f}")
            m3.metric("Excedente (MDP)", f"${float(resultado.excedente_solvencia) / 1e6:,.1f}")
            if resultado.cumple_regulacion:
                m4.metric("Cumplimiento", "SI CUMPLE")
            else:
                m4.metric("Cumplimiento", "NO CUMPLE")

            # Desglose por componente
            st.subheader("Desglose del RCS por componente")
            col_tabla, col_pie = st.columns([1, 1])

            with col_tabla:
                componentes = {
                    "Suscripción Vida": float(resultado.rcs_suscripcion_vida) / 1e6,
                    "Suscripción Daños": float(resultado.rcs_suscripcion_danos) / 1e6,
                    "Inversión": float(resultado.rcs_inversion) / 1e6,
                }
                import pandas as pd
                df_comp = pd.DataFrame(
                    {"Componente": list(componentes.keys()), "RCS (MDP)": list(componentes.values())}
                )
                df_comp["% del Total"] = df_comp["RCS (MDP)"] / (float(resultado.rcs_total) / 1e6) * 100
                df_comp["RCS (MDP)"] = df_comp["RCS (MDP)"].apply(lambda x: f"${x:,.1f}")
                df_comp["% del Total"] = df_comp["% del Total"].apply(lambda x: f"{x:.1f}%")
                st.dataframe(df_comp, use_container_width=True, hide_index=True)

            with col_pie:
                fig_pie = go.Figure(data=[go.Pie(
                    labels=list(componentes.keys()),
                    values=list(componentes.values()),
                    hole=0.4,
                    textinfo="label+percent",
                    marker_colors=["#1f77b4", "#ff7f0e", "#2ca02c"],
                )])
                fig_pie.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig_pie, use_container_width=True)

            # Desglose detallado
            st.subheader("Desglose detallado por tipo de riesgo")
            detalles = {
                "Mortalidad": float(resultado.rcs_mortalidad) / 1e6,
                "Longevidad": float(resultado.rcs_longevidad) / 1e6,
                "Invalidez": float(resultado.rcs_invalidez) / 1e6,
                "Gastos": float(resultado.rcs_gastos) / 1e6,
                "Prima": float(resultado.rcs_prima) / 1e6,
                "Reserva": float(resultado.rcs_reserva) / 1e6,
                "Mercado": float(resultado.rcs_mercado) / 1e6,
                "Credito": float(resultado.rcs_credito) / 1e6,
                "Concentracion": float(resultado.rcs_concentracion) / 1e6,
            }
            detalles_filtrados = {k: v for k, v in detalles.items() if v > 0}

            if detalles_filtrados:
                fig_bar = go.Figure(data=[go.Bar(
                    x=list(detalles_filtrados.keys()),
                    y=list(detalles_filtrados.values()),
                    marker_color="#1f77b4",
                    text=[f"${v:,.1f}" for v in detalles_filtrados.values()],
                    textposition="outside",
                )])
                fig_bar.update_layout(
                    xaxis_title="Tipo de riesgo",
                    yaxis_title="RCS (MDP)",
                    height=400,
                )
                st.plotly_chart(fig_bar, use_container_width=True)

        except Exception as e:
            st.error(f"Error en el cálculo: {e}")

    with st.expander("Código de ejemplo -- RCS"):
        st.code(
            """from decimal import Decimal
from suite_actuarial.regulatorio import AgregadorRCS
from suite_actuarial.core.validators import (
    ConfiguracionRCSVida, ConfiguracionRCSDanos, ConfiguracionRCSInversion,
)

config_vida = ConfiguracionRCSVida(
    suma_asegurada_total=Decimal("500000000"),
    reserva_matematica=Decimal("350000000"),
    edad_promedio_asegurados=45,
    duracion_promedio_polizas=15,
    numero_asegurados=10000,
)
config_danos = ConfiguracionRCSDanos(
    primas_retenidas_12m=Decimal("250000000"),
    reserva_siniestros=Decimal("180000000"),
    coeficiente_variacion=Decimal("0.15"),
)
config_inversion = ConfiguracionRCSInversion(
    valor_acciones=Decimal("50000000"),
    valor_bonos_gubernamentales=Decimal("300000000"),
    valor_bonos_corporativos=Decimal("150000000"),
    valor_inmuebles=Decimal("100000000"),
    duracion_promedio_bonos=Decimal("7.5"),
    calificacion_promedio_bonos="AA",
)

agreg = AgregadorRCS(
    config_vida=config_vida,
    config_danos=config_danos,
    config_inversion=config_inversion,
    capital_minimo_pagado=Decimal("1000000000"),
)
resultado = agreg.calcular_rcs_completo()

print(f"RCS Total: ${resultado.rcs_total:,.2f}")
print(f"Cumple regulacion: {resultado.cumple_regulacion}")
print(f"Ratio solvencia: {resultado.ratio_solvencia:.2%}")
""",
            language="python",
        )

# ===== TAB 2: Reservas Tecnicas ============================================
with tab_reservas:
    st.header("Reservas Técnicas")
    st.markdown(
        "Calculadoras de Reserva Matemática (RM) y Reserva de Riesgos en Curso (RRC) "
        "conforme a la Circular S-11.4 de la CNSF."
    )

    col_rm, col_rrc = st.columns(2)

    with col_rm:
        st.subheader("Reserva Matemática (RM)")
        st.markdown(
            "La reserva matemática es el pasivo actuarial que respalda las obligaciones "
            "futuras de seguros de vida de largo plazo."
        )

        rm_sa = st.number_input("Suma asegurada ($)", min_value=10000, value=1000000, step=50000, key="rm_sa")
        rm_edad = st.slider("Edad del asegurado", 18, 80, 35, key="rm_edad")
        rm_plazo = st.slider("Plazo de la póliza (años)", 5, 30, 20, key="rm_plazo")
        rm_anios = st.slider("Años transcurridos", 0, rm_plazo, 5, key="rm_anios")
        rm_tasa = st.slider("Tasa técnica (%)", 1.0, 8.0, 5.5, step=0.5, key="rm_tasa")

        if st.button("Calcular Reserva Matemática", key="btn_rm"):
            try:
                from suite_actuarial.vida import VidaTemporal
                from suite_actuarial.actuarial.mortality.tablas import TablaMortalidad
                from suite_actuarial.core.validators import Asegurado, ConfiguracionProducto, Sexo

                tabla = TablaMortalidad()
                config_prod = ConfiguracionProducto(
                    nombre_producto="Temporal demo",
                    plazo_years=rm_plazo,
                    tasa_interes_tecnico=Decimal(str(rm_tasa / 100)),
                )
                producto = VidaTemporal(config_prod, tabla)
                asegurado = Asegurado(
                    edad=rm_edad,
                    sexo=Sexo.HOMBRE,
                    suma_asegurada=Decimal(str(rm_sa)),
                )

                reserva = producto.calcular_reserva(asegurado, anio=rm_anios)
                st.metric("Reserva Matemática", f"${float(reserva):,.2f}")
                st.metric("% de Suma Asegurada", f"{float(reserva) / rm_sa * 100:.2f}%")

                if cfg:
                    margen = float(cfg.factores_tecnicos.margen_seguridad_s114)
                    rm_con_margen = float(reserva) * (1 + margen)
                    st.metric(
                        f"RM con margen S-11.4 ({margen*100:.0f}%)",
                        f"${rm_con_margen:,.2f}",
                    )

            except Exception as e:
                st.error(f"Error: {e}")

    with col_rrc:
        st.subheader("Reserva de Riesgos en Curso (RRC)")
        st.markdown(
            "La RRC se calcula como la parte proporcional de la prima no devengada "
            "más un margen de seguridad conforme a la regulación."
        )

        rrc_prima = st.number_input("Prima emitida ($)", min_value=1000, value=120000, step=5000, key="rrc_prima")
        rrc_inicio = st.date_input("Fecha inicio vigencia", key="rrc_inicio")
        rrc_fin = st.date_input("Fecha fin vigencia", key="rrc_fin")
        rrc_hoy = st.date_input("Fecha de cálculo", key="rrc_hoy")

        if st.button("Calcular RRC", key="btn_rrc"):
            dias_total = (rrc_fin - rrc_inicio).days
            dias_transcurridos = (rrc_hoy - rrc_inicio).days

            if dias_total > 0 and 0 <= dias_transcurridos <= dias_total:
                fraccion_no_devengada = (dias_total - dias_transcurridos) / dias_total
                rrc_base = rrc_prima * fraccion_no_devengada

                st.metric("Dias totales", f"{dias_total}")
                st.metric("Dias transcurridos", f"{dias_transcurridos}")
                st.metric("Fracción no devengada", f"{fraccion_no_devengada:.4f}")
                st.metric("RRC base", f"${rrc_base:,.2f}")

                if cfg:
                    margen = float(cfg.factores_tecnicos.margen_seguridad_s114)
                    rrc_con_margen = rrc_base * (1 + margen)
                    st.metric(
                        f"RRC con margen S-11.4 ({margen*100:.0f}%)",
                        f"${rrc_con_margen:,.2f}",
                    )
            else:
                st.warning("Las fechas no son consistentes. Verifica los valores.")

    with st.expander("Código de ejemplo -- Reservas Técnicas"):
        st.code(
            """from decimal import Decimal
from suite_actuarial.vida import VidaTemporal
from suite_actuarial.actuarial.mortality.tablas import TablaMortalidad
from suite_actuarial.core.validators import (
    Asegurado, ConfiguracionProducto, Sexo,
)
from suite_actuarial.config import cargar_config

# Reserva matematica
tabla = TablaMortalidad()
config = ConfiguracionProducto(
    nombre_producto="Temporal 20",
    plazo_years=20,
    tasa_interes_tecnico=Decimal("0.055"),
)
producto = VidaTemporal(config, tabla)
asegurado = Asegurado(edad=35, sexo=Sexo.HOMBRE, suma_asegurada=Decimal("1000000"))
reserva = producto.calcular_reserva(asegurado, anio=5)
print(f"Reserva Matematica (anio 5): ${reserva:,.2f}")

# Margen S-11.4 desde configuracion regulatoria
cfg = cargar_config(2026)
margen = cfg.factores_tecnicos.margen_seguridad_s114
rm_regulatoria = reserva * (1 + margen)
print(f"RM con margen S-11.4: ${rm_regulatoria:,.2f}")
""",
            language="python",
        )

# ===== TAB 3: Validaciones SAT =============================================
with tab_sat:
    st.header("Validaciones SAT")
    st.markdown(
        "Calculadoras de deducibilidad fiscal y retención de ISR "
        "conforme a la Ley del Impuesto Sobre la Renta (LISR)."
    )

    col_ded, col_isr = st.columns(2)

    with col_ded:
        st.subheader("Verificador de deducibilidad")
        st.markdown(
            "Las primas de seguros de vida con componente de ahorro son deducibles "
            "hasta el límite de UMAs anuales establecido en el Art. 151 LISR."
        )

        ded_prima = st.number_input(
            "Prima pagada ($)", min_value=0, value=50000, step=1000, key="ded_prima"
        )
        ded_ingresos = st.number_input(
            "Ingresos anuales ($)", min_value=0, value=800000, step=50000, key="ded_ingresos"
        )

        if st.button("Verificar deducibilidad", key="btn_ded"):
            if cfg:
                uma_anual = float(cfg.uma.uma_anual)
                limite_umas = cfg.tasas_sat.limite_deducciones_pf_umas
                limite_deduccion = uma_anual * limite_umas
                limite_15_pct = ded_ingresos * 0.15

                tope = min(limite_deduccion, limite_15_pct)
                deducible = min(ded_prima, tope)
                no_deducible = ded_prima - deducible

                st.markdown("---")
                st.markdown(f"**Límite por UMAs:** {limite_umas} UMAs anuales = ${limite_deduccion:,.2f}")
                st.markdown(f"**Límite 15% ingresos:** ${limite_15_pct:,.2f}")
                st.markdown(f"**Tope aplicable:** ${tope:,.2f}")
                st.markdown("---")

                m1, m2 = st.columns(2)
                m1.metric("Monto deducible", f"${deducible:,.2f}")
                m2.metric("Monto NO deducible", f"${no_deducible:,.2f}")

                # Grafico
                fig_ded = go.Figure(data=[go.Pie(
                    labels=["Deducible", "No deducible"],
                    values=[deducible, max(no_deducible, 0)],
                    hole=0.4,
                    marker_colors=["#2ca02c", "#d62728"],
                    textinfo="label+value",
                    texttemplate="%{label}: $%{value:,.0f}",
                )])
                fig_ded.update_layout(height=350, showlegend=False)
                st.plotly_chart(fig_ded, use_container_width=True)
            else:
                st.warning("No se pudo cargar la configuración regulatoria.")

    with col_isr:
        st.subheader("Calculadora de retención ISR")
        st.markdown(
            "Cálculo de la retención de ISR sobre pagos de rentas vitalicias "
            "y retiros de planes de ahorro."
        )

        tipo_pago = st.selectbox(
            "Tipo de pago",
            options=["Renta vitalicia", "Retiro de ahorro"],
            key="isr_tipo",
        )
        monto_pago = st.number_input(
            "Monto del pago ($)", min_value=0, value=50000, step=5000, key="isr_monto"
        )

        if st.button("Calcular retención", key="btn_isr"):
            if cfg:
                if tipo_pago == "Renta vitalicia":
                    tasa = float(cfg.tasas_sat.tasa_retencion_rentas_vitalicias)
                else:
                    tasa = float(cfg.tasas_sat.tasa_retencion_retiros_ahorro)

                retencion = monto_pago * tasa
                neto = monto_pago - retencion

                st.markdown("---")
                st.markdown(f"**Tasa de retención:** {tasa*100:.0f}%")

                m1, m2, m3 = st.columns(3)
                m1.metric("Monto bruto", f"${monto_pago:,.2f}")
                m2.metric("Retención ISR", f"${retencion:,.2f}")
                m3.metric("Pago neto", f"${neto:,.2f}")

                # Grafico
                fig_isr = go.Figure(data=[go.Bar(
                    x=["Bruto", "Retención ISR", "Neto"],
                    y=[monto_pago, retencion, neto],
                    marker_color=["#1f77b4", "#d62728", "#2ca02c"],
                    text=[f"${monto_pago:,.0f}", f"${retencion:,.0f}", f"${neto:,.0f}"],
                    textposition="outside",
                )])
                fig_isr.update_layout(
                    yaxis_title="Monto (MXN)",
                    height=400,
                )
                st.plotly_chart(fig_isr, use_container_width=True)
            else:
                st.warning("No se pudo cargar la configuración regulatoria.")

    with st.expander("Código de ejemplo -- Validaciones SAT"):
        st.code(
            """from suite_actuarial.config import cargar_config

# Cargar configuracion regulatoria del anio
cfg = cargar_config(2026)

# Deducibilidad de primas
uma_anual = float(cfg.uma.uma_anual)
limite = cfg.tasas_sat.limite_deducciones_pf_umas
tope_umas = uma_anual * limite
print(f"Tope deduccion por UMAs ({limite} UMAs): ${tope_umas:,.2f}")

# Retencion ISR sobre renta vitalicia
tasa_rv = float(cfg.tasas_sat.tasa_retencion_rentas_vitalicias)
pago = 50000
retencion = pago * tasa_rv
print(f"Retencion ISR ({tasa_rv*100:.0f}%): ${retencion:,.2f}")

# Retencion ISR sobre retiro de ahorro
tasa_ahorro = float(cfg.tasas_sat.tasa_retencion_retiros_ahorro)
retencion_ahorro = pago * tasa_ahorro
print(f"Retencion retiro ({tasa_ahorro*100:.0f}%): ${retencion_ahorro:,.2f}")
""",
            language="python",
        )
