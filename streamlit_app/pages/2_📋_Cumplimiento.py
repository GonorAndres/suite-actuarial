"""
Dashboard de Cumplimiento Regulatorio - Mexican Insurance Analytics Suite

Monitor de cumplimiento con normativa mexicana: RCS, CNSF, SAT, S-11.4.
"""

import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Agregar src al path para imports
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

from mexican_insurance.core.validators import (
    ConfiguracionRCSDanos,
    ConfiguracionRCSInversion,
    ConfiguracionRCSVida,
)
from mexican_insurance.regulatorio.agregador_rcs import AgregadorRCS
from mexican_insurance.regulatorio.reservas_tecnicas.models import (
    ConfiguracionRM,
    ConfiguracionRRC,
)
from mexican_insurance.regulatorio.reservas_tecnicas.reserva_matematica import (
    CalculadoraRM,
)
from mexican_insurance.regulatorio.reservas_tecnicas.reserva_riesgos_curso import (
    CalculadoraRRC,
)
from mexican_insurance.regulatorio.validaciones_sat.models import TipoSeguroFiscal
from mexican_insurance.regulatorio.validaciones_sat.validador_primas import (
    ValidadorPrimasDeducibles,
)
from mexican_insurance.regulatorio.validaciones_sat.validador_retenciones import (
    CalculadoraRetencionesISR,
)
from mexican_insurance.regulatorio.validaciones_sat.validador_siniestros import (
    ValidadorSiniestrosGravables,
)

# Configuración de la página
st.set_page_config(
    page_title="Cumplimiento Regulatorio - Mexican Insurance",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Título
st.title("📋 Dashboard de Cumplimiento Regulatorio")
st.markdown("""
Monitor de cumplimiento con las principales normativas del mercado asegurador mexicano.
""")

# ============================================================================
# VISTA PRINCIPAL: TABS POR REGULACIÓN
# ============================================================================

tab1, tab2, tab3, tab4 = st.tabs([
    "🏦 RCS - Solvencia",
    "📊 Reservas S-11.4",
    "💰 SAT - Deducibilidad",
    "💳 SAT - Retenciones",
])

# ============================================================================
# TAB 1: RCS - REQUERIMIENTOS DE CAPITAL DE SOLVENCIA
# ============================================================================

with tab1:
    st.header("🏦 Requerimientos de Capital de Solvencia (RCS)")

    st.markdown("""
    El **RCS** es el capital mínimo que debe mantener una aseguradora para cubrir
    riesgos no esperados, basado en Solvencia II adaptado a México.
    """)

    st.markdown("---")

    # Formulario de entrada
    st.subheader("📊 Datos de la Aseguradora")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Vida**")
        suma_asegurada_vida = st.number_input(
            "Suma Asegurada Total Vida (Millones MXN)",
            min_value=10.0,
            max_value=100_000.0,
            value=500.0,
            step=50.0,
            format="%.2f",
        )
        reserva_matematica_input = st.number_input(
            "Reserva Matematica (Millones MXN)",
            min_value=0.0,
            max_value=100_000.0,
            value=350.0,
            step=50.0,
            format="%.2f",
        )
        edad_promedio = st.slider(
            "Edad Promedio Asegurados",
            min_value=18,
            max_value=100,
            value=45,
        )
        duracion_promedio = st.slider(
            "Duracion Promedio Polizas (anios)",
            min_value=1,
            max_value=50,
            value=15,
        )
        numero_asegurados = st.number_input(
            "Numero de Asegurados",
            min_value=1,
            max_value=500_000,
            value=10_000,
            step=500,
        )

    with col2:
        st.markdown("**Danos**")
        primas_retenidas = st.number_input(
            "Primas Retenidas 12m (Millones MXN)",
            min_value=10.0,
            max_value=50_000.0,
            value=250.0,
            step=50.0,
            format="%.2f",
        )
        reserva_siniestros_input = st.number_input(
            "Reserva de Siniestros (Millones MXN)",
            min_value=0.0,
            max_value=50_000.0,
            value=180.0,
            step=50.0,
            format="%.2f",
        )
        coef_variacion = st.slider(
            "Coeficiente de Variacion (%)",
            min_value=5.0,
            max_value=50.0,
            value=15.0,
            step=1.0,
            help="Volatilidad historica de la siniestralidad",
        ) / 100
        numero_ramos = st.slider(
            "Numero de Ramos",
            min_value=1,
            max_value=20,
            value=5,
        )

    with col3:
        st.markdown("**Inversion**")
        valor_acciones = st.number_input(
            "Acciones (Millones MXN)",
            min_value=0.0,
            max_value=50_000.0,
            value=50.0,
            step=10.0,
            format="%.2f",
        )
        valor_bonos_gub = st.number_input(
            "Bonos Gubernamentales (Millones MXN)",
            min_value=0.0,
            max_value=100_000.0,
            value=300.0,
            step=50.0,
            format="%.2f",
        )
        valor_bonos_corp = st.number_input(
            "Bonos Corporativos (Millones MXN)",
            min_value=0.0,
            max_value=50_000.0,
            value=150.0,
            step=50.0,
            format="%.2f",
        )
        valor_inmuebles_input = st.number_input(
            "Inmuebles (Millones MXN)",
            min_value=0.0,
            max_value=50_000.0,
            value=100.0,
            step=10.0,
            format="%.2f",
        )
        duracion_bonos = st.slider(
            "Duracion Promedio Bonos (anios)",
            min_value=0.5,
            max_value=30.0,
            value=7.5,
            step=0.5,
        )
        calificacion_bonos = st.selectbox(
            "Calificacion Promedio Bonos",
            options=["AAA", "AA", "A", "BBB", "BB", "B", "CCC", "CC", "C"],
            index=1,
        )

    st.markdown("---")
    capital_pagado = st.number_input(
        "Capital Minimo Pagado (Millones MXN)",
        min_value=1.0,
        max_value=100_000.0,
        value=800.0,
        step=50.0,
        format="%.2f",
    )

    # Cálculo de RCS
    if st.button("🔍 Calcular RCS", type="primary"):
        try:
            # Convertir millones a unidades (la API trabaja en unidades)
            M = Decimal("1000000")

            config_vida = ConfiguracionRCSVida(
                suma_asegurada_total=Decimal(str(suma_asegurada_vida)) * M,
                reserva_matematica=Decimal(str(reserva_matematica_input)) * M,
                edad_promedio_asegurados=edad_promedio,
                duracion_promedio_polizas=duracion_promedio,
                numero_asegurados=numero_asegurados,
            )

            config_danos = ConfiguracionRCSDanos(
                primas_retenidas_12m=Decimal(str(primas_retenidas)) * M,
                reserva_siniestros=Decimal(str(reserva_siniestros_input)) * M,
                coeficiente_variacion=Decimal(str(coef_variacion)),
                numero_ramos=numero_ramos,
            )

            config_inversion = ConfiguracionRCSInversion(
                valor_acciones=Decimal(str(valor_acciones)) * M,
                valor_bonos_gubernamentales=Decimal(str(valor_bonos_gub)) * M,
                valor_bonos_corporativos=Decimal(str(valor_bonos_corp)) * M,
                valor_inmuebles=Decimal(str(valor_inmuebles_input)) * M,
                duracion_promedio_bonos=Decimal(str(duracion_bonos)),
                calificacion_promedio_bonos=calificacion_bonos,
            )

            agregador = AgregadorRCS(
                config_vida=config_vida,
                config_danos=config_danos,
                config_inversion=config_inversion,
                capital_minimo_pagado=Decimal(str(capital_pagado)) * M,
            )

            resultado_rcs = agregador.calcular_rcs_completo()

            # Mostrar resultados
            st.markdown("---")
            st.subheader("✅ Resultados del Cálculo")

            # Métricas principales
            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

            capital_disponible = float(resultado_rcs.capital_minimo_pagado) / 1e6
            rcs_total = float(resultado_rcs.rcs_total) / 1e6
            # ratio_solvencia is RCS/Capital; cobertura is Capital/RCS
            ratio_solvencia_val = float(resultado_rcs.ratio_solvencia)
            ratio_cobertura = (1.0 / ratio_solvencia_val * 100) if ratio_solvencia_val > 0 else 0.0
            superavit = float(resultado_rcs.excedente_solvencia) / 1e6

            with metric_col1:
                st.metric(
                    "Capital Disponible",
                    f"${capital_disponible:,.0f}M",
                    help="Fondos propios ajustados",
                )

            with metric_col2:
                st.metric(
                    "RCS Requerido",
                    f"${rcs_total:,.0f}M",
                    help="Capital mínimo regulatorio",
                )

            with metric_col3:
                st.metric(
                    "Ratio de Cobertura",
                    f"{ratio_cobertura:.1f}%",
                    delta=f"{ratio_cobertura - 100:.1f}% vs mínimo",
                    delta_color="normal" if ratio_cobertura >= 100 else "inverse",
                    help="Capital Disponible / RCS (mínimo: 100%)",
                )

            with metric_col4:
                st.metric(
                    "Superávit/Déficit",
                    f"${superavit:,.0f}M",
                    delta="Cumple" if resultado_rcs.cumple_regulacion else "Déficit",
                    delta_color="normal" if resultado_rcs.cumple_regulacion else "inverse",
                )

            # Desglose por componente de riesgo
            st.markdown("---")
            st.subheader("📊 Desglose de Riesgos")

            col_left, col_right = st.columns([3, 2])

            with col_left:
                # Build desglose dict from resultado fields (in millions)
                componentes = {
                    "Vida - Mortalidad": float(resultado_rcs.rcs_mortalidad) / 1e6,
                    "Vida - Longevidad": float(resultado_rcs.rcs_longevidad) / 1e6,
                    "Vida - Invalidez": float(resultado_rcs.rcs_invalidez) / 1e6,
                    "Vida - Gastos": float(resultado_rcs.rcs_gastos) / 1e6,
                    "Danos - Prima": float(resultado_rcs.rcs_prima) / 1e6,
                    "Danos - Reserva": float(resultado_rcs.rcs_reserva) / 1e6,
                    "Inv - Mercado": float(resultado_rcs.rcs_mercado) / 1e6,
                    "Inv - Credito": float(resultado_rcs.rcs_credito) / 1e6,
                    "Inv - Concentracion": float(resultado_rcs.rcs_concentracion) / 1e6,
                }
                # Filter out zero components
                componentes = {k: v for k, v in componentes.items() if v > 0}

                labels = list(componentes.keys())
                values = list(componentes.values())

                fig_componentes = go.Figure(
                    go.Bar(
                        x=labels,
                        y=values,
                        marker=dict(
                            color=[
                                "#1f77b4",
                                "#ff7f0e",
                                "#2ca02c",
                                "#d62728",
                                "#9467bd",
                                "#8c564b",
                                "#e377c2",
                                "#7f7f7f",
                                "#bcbd22",
                            ][:len(labels)]
                        ),
                        text=[f"${v:,.0f}M" for v in values],
                        textposition="outside",
                    )
                )

                fig_componentes.update_layout(
                    title="Componentes del RCS (Millones MXN)",
                    xaxis_title="Tipo de Riesgo",
                    yaxis_title="RCS (Millones MXN)",
                    height=400,
                )

                st.plotly_chart(fig_componentes, use_container_width=True)

            with col_right:
                # Pie chart de distribución por categoría agregada
                cat_labels = ["Suscripcion Vida", "Suscripcion Danos", "Inversion"]
                cat_values = [
                    float(resultado_rcs.rcs_suscripcion_vida) / 1e6,
                    float(resultado_rcs.rcs_suscripcion_danos) / 1e6,
                    float(resultado_rcs.rcs_inversion) / 1e6,
                ]

                fig_pie = go.Figure(
                    go.Pie(
                        labels=cat_labels,
                        values=cat_values,
                        hole=0.4,
                        textinfo="label+percent",
                    )
                )

                fig_pie.update_layout(
                    title="Distribución de Riesgos",
                    height=400,
                )

                st.plotly_chart(fig_pie, use_container_width=True)

            # Tabla detallada
            with st.expander("📋 Ver desglose detallado"):
                rcs_total_val = float(resultado_rcs.rcs_total) / 1e6
                df_riesgos = pd.DataFrame({
                    "Componente de Riesgo": labels,
                    "RCS Requerido (M MXN)": values,
                    "% del Total": [(v / rcs_total_val * 100) if rcs_total_val > 0 else 0.0 for v in values],
                })

                df_riesgos["RCS Requerido (M MXN)"] = df_riesgos[
                    "RCS Requerido (M MXN)"
                ].apply(lambda x: f"${x:,.2f}")
                df_riesgos["% del Total"] = df_riesgos["% del Total"].apply(
                    lambda x: f"{x:.2f}%"
                )

                st.dataframe(df_riesgos, use_container_width=True, hide_index=True)

            # Semáforo regulatorio
            st.markdown("---")
            st.subheader("🚦 Evaluación Regulatoria")

            if ratio_cobertura >= 200:
                st.success(f"""
                ✅ **EXCELENTE** - Ratio de Cobertura: {ratio_cobertura:.1f}%

                La aseguradora tiene un colchón de capital muy robusto (>200% del RCS mínimo).
                Posición de solvencia muy sólida.
                """)
            elif ratio_cobertura >= 150:
                st.success(f"""
                ✅ **BUENO** - Ratio de Cobertura: {ratio_cobertura:.1f}%

                La aseguradora cumple holgadamente con el RCS (>150% del mínimo).
                Posición de solvencia sólida.
                """)
            elif ratio_cobertura >= 100:
                st.warning(f"""
                ⚠️ **CUMPLE** - Ratio de Cobertura: {ratio_cobertura:.1f}%

                La aseguradora cumple con el RCS mínimo, pero tiene poco margen.
                Se recomienda fortalecer el capital.
                """)
            else:
                st.error(f"""
                ❌ **DÉFICIT** - Ratio de Cobertura: {ratio_cobertura:.1f}%

                La aseguradora **NO CUMPLE** con el RCS mínimo.
                Requiere capitalización inmediata o plan de regularización.
                """)

        except Exception as e:
            st.error(f"Error en el cálculo de RCS: {e}")

# ============================================================================
# TAB 2: RESERVAS TÉCNICAS S-11.4
# ============================================================================

with tab2:
    st.header("📊 Reservas Técnicas según Circular S-11.4")

    st.markdown("""
    Cálculo de **Reserva de Riesgos en Curso (RRC)** y **Reserva Matemática (RM)**
    según la normativa de la CNSF.
    """)

    st.markdown("---")

    # Formulario de entrada
    st.subheader("📝 Datos de la Póliza")

    col1, col2 = st.columns(2)

    with col1:
        tipo_seguro_reserva = st.selectbox(
            "Tipo de Seguro",
            options=["VIDA", "DAÑOS"],
            help="Tipo de seguro para cálculo de reservas",
        )

        suma_asegurada_res = st.number_input(
            "Suma Asegurada (MXN)",
            min_value=100_000,
            max_value=10_000_000,
            value=1_000_000,
            step=100_000,
            format="%d",
        )

        prima_emitida = st.number_input(
            "Prima Total Pagada (MXN)",
            min_value=1_000,
            max_value=500_000,
            value=50_000,
            step=1_000,
            format="%d",
        )

    with col2:
        dias_transcurridos = st.slider(
            "Días transcurridos desde inicio",
            min_value=0,
            max_value=365,
            value=180,
            help="Días desde que inició la vigencia de la póliza",
        )

        plazo_total_dias = st.number_input(
            "Plazo Total (días)",
            min_value=30,
            max_value=7300,  # ~20 años
            value=365,
            step=30,
            help="Duración total de la póliza en días",
        )

        if tipo_seguro_reserva == "VIDA":
            edad_asegurado_res = st.slider(
                "Edad del Asegurado",
                min_value=18,
                max_value=80,
                value=35,
            )

            tasa_interes_res = st.slider(
                "Tasa de Interés Técnico (%)",
                min_value=1.0,
                max_value=10.0,
                value=5.5,
                step=0.5,
            ) / 100
        else:
            edad_asegurado_res = None
            tasa_interes_res = 0.055

    # Cálculo de reservas
    if st.button("🔍 Calcular Reservas S-11.4", type="primary"):
        try:
            # --- RRC: Reserva de Riesgos en Curso ---
            # prima_devengada is estimated from days elapsed
            fraccion_devengada = Decimal(str(dias_transcurridos)) / Decimal(str(plazo_total_dias))
            prima_devengada_calc = Decimal(str(prima_emitida)) * fraccion_devengada

            config_rrc = ConfiguracionRRC(
                prima_emitida=Decimal(str(prima_emitida)),
                prima_devengada=prima_devengada_calc.quantize(Decimal("0.01")),
                fecha_calculo=date.today(),
                dias_promedio_vigencia=plazo_total_dias,
                dias_promedio_transcurridos=dias_transcurridos,
            )

            calc_rrc = CalculadoraRRC(config_rrc)
            resultado_rrc = calc_rrc.calcular()

            # --- RM: Reserva Matematica (solo vida) ---
            rm_val = Decimal("0")
            resultado_rm = None
            if tipo_seguro_reserva == "VIDA" and edad_asegurado_res is not None:
                # Estimate edad_contratacion from dias_transcurridos
                anios_transcurridos = dias_transcurridos // 365
                edad_contratacion_est = max(edad_asegurado_res - anios_transcurridos, 18)
                # Estimate prima nivelada anual from prima emitida and plazo
                plazo_anios = max(plazo_total_dias // 365, 1)
                prima_nivelada_est = Decimal(str(prima_emitida)) / Decimal(str(plazo_anios)) if plazo_anios > 0 else Decimal(str(prima_emitida))

                config_rm = ConfiguracionRM(
                    suma_asegurada=Decimal(str(suma_asegurada_res)),
                    edad_asegurado=edad_asegurado_res,
                    edad_contratacion=edad_contratacion_est,
                    tasa_interes_tecnico=Decimal(str(tasa_interes_res)),
                    prima_nivelada_anual=prima_nivelada_est.quantize(Decimal("0.01")),
                )

                calc_rm = CalculadoraRM(config_rm)
                resultado_rm = calc_rm.calcular()
                rm_val = resultado_rm.reserva_matematica

            # Mostrar resultados
            st.markdown("---")
            st.subheader("✅ Reservas Calculadas")

            # Métricas
            res_col1, res_col2, res_col3, res_col4 = st.columns(4)

            rrc = float(resultado_rrc.reserva_calculada)
            rm = float(rm_val)
            reserva_total = rrc + rm
            pct_prima = (reserva_total / float(prima_emitida)) * 100 if prima_emitida > 0 else 0.0

            with res_col1:
                st.metric(
                    "RRC",
                    f"${rrc:,.2f}",
                    help="Reserva de Riesgos en Curso",
                )

            with res_col2:
                st.metric(
                    "RM",
                    f"${rm:,.2f}",
                    help="Reserva Matemática",
                )

            with res_col3:
                st.metric(
                    "Reserva Total",
                    f"${reserva_total:,.2f}",
                    help="RRC + RM",
                )

            with res_col4:
                st.metric(
                    "% de Prima",
                    f"{pct_prima:.1f}%",
                    help="Reserva como % de prima emitida",
                )

            # Visualización de reservas
            st.markdown("---")

            # Gráfico de evolución (simulado)
            dias_rango = list(range(0, plazo_total_dias + 1, 30))
            rrcs = []
            rms = []

            for dia in dias_rango:
                frac_dev = Decimal(str(dia)) / Decimal(str(plazo_total_dias))
                prima_dev_temp = (Decimal(str(prima_emitida)) * frac_dev).quantize(Decimal("0.01"))

                config_rrc_temp = ConfiguracionRRC(
                    prima_emitida=Decimal(str(prima_emitida)),
                    prima_devengada=prima_dev_temp,
                    fecha_calculo=date.today(),
                    dias_promedio_vigencia=plazo_total_dias,
                    dias_promedio_transcurridos=dia,
                )

                res_rrc_temp = CalculadoraRRC(config_rrc_temp).calcular()
                rrcs.append(float(res_rrc_temp.reserva_calculada))

                # RM is constant for a given policy (depends on age, not days elapsed in short term)
                rms.append(rm)

            # Gráfico
            fig_evolucion = go.Figure()

            fig_evolucion.add_trace(
                go.Scatter(
                    x=dias_rango,
                    y=rrcs,
                    mode="lines",
                    name="RRC",
                    fill="tozeroy",
                    line=dict(color="#1f77b4", width=2),
                )
            )

            fig_evolucion.add_trace(
                go.Scatter(
                    x=dias_rango,
                    y=rms,
                    mode="lines",
                    name="RM",
                    fill="tozeroy",
                    line=dict(color="#ff7f0e", width=2),
                )
            )

            # Marcar día actual
            fig_evolucion.add_vline(
                x=dias_transcurridos,
                line_dash="dash",
                line_color="red",
                annotation_text="Hoy",
            )

            fig_evolucion.update_layout(
                title="Evolución de Reservas a lo largo de la Vigencia",
                xaxis_title="Días desde inicio de póliza",
                yaxis_title="Reserva (MXN)",
                hovermode="x unified",
                height=450,
            )

            st.plotly_chart(fig_evolucion, use_container_width=True)

            # Interpretación
            st.info(f"""
            **RRC (Reserva de Riesgos en Curso):** ${rrc:,.2f}

            Representa la prima no devengada. Para seguros de corto plazo (daños),
            decrece linealmente conforme transcurre el tiempo.

            **RM (Reserva Matemática):** ${rm:,.2f}

            Para seguros de vida de largo plazo, representa el valor presente de
            obligaciones futuras menos primas futuras.

            **Fundamento Legal:** Circular Única de Seguros y Fianzas - Disposición S-11.4
            """)

        except Exception as e:
            st.error(f"Error en el cálculo de reservas: {e}")

# ============================================================================
# TAB 3: SAT - DEDUCIBILIDAD DE PRIMAS
# ============================================================================

with tab3:
    st.header("💰 SAT - Deducibilidad de Primas")

    st.markdown("""
    Valida si las **primas de seguro pagadas** son **deducibles** para efectos del
    Impuesto Sobre la Renta (ISR) según la LISR.
    """)

    st.markdown("---")

    # Formulario
    st.subheader("📝 Datos de la Prima")

    col1, col2 = st.columns(2)

    with col1:
        tipo_contribuyente = st.selectbox(
            "Tipo de Contribuyente",
            options=["Persona Física", "Persona Moral"],
            help="Determina el régimen fiscal aplicable",
        )

        tipo_seguro_sat = st.selectbox(
            "Tipo de Seguro",
            options=[
                "Gastos Médicos",
                "Vida",
                "Pensiones",
                "Daños",
                "Invalidez",
            ],
            help="Tipo de seguro contratado",
        )

    with col2:
        monto_prima_anual = st.number_input(
            "Prima Anual Pagada (MXN)",
            min_value=1_000,
            max_value=500_000,
            value=50_000,
            step=1_000,
            format="%d",
        )

        if tipo_contribuyente == "Persona Física":
            uma_anual = st.number_input(
                "UMA Anual (MXN)",
                min_value=30_000,
                max_value=50_000,
                value=37_500,
                step=500,
                format="%d",
                help="Unidad de Medida y Actualización anual",
            )
        else:
            uma_anual = 37_500  # Valor por defecto

    # Validar deducibilidad
    if st.button("🔍 Validar Deducibilidad", type="primary"):
        # Mapear tipo de seguro a enum
        tipo_map = {
            "Gastos Médicos": TipoSeguroFiscal.GASTOS_MEDICOS,
            "Vida": TipoSeguroFiscal.VIDA,
            "Pensiones": TipoSeguroFiscal.PENSIONES,
            "Daños": TipoSeguroFiscal.DANOS,
            "Invalidez": TipoSeguroFiscal.INVALIDEZ,
        }

        tipo_fiscal = tipo_map[tipo_seguro_sat]
        es_pf = tipo_contribuyente == "Persona Física"

        # Validar
        validador_primas = ValidadorPrimasDeducibles(uma_anual=Decimal(str(uma_anual)))
        resultado_deducibilidad = validador_primas.validar_deducibilidad(
            tipo_seguro=tipo_fiscal,
            monto_prima=Decimal(str(monto_prima_anual)),
            es_persona_fisica=es_pf,
        )

        # Mostrar resultados
        st.markdown("---")
        st.subheader("✅ Resultado de la Validación")

        # Métricas
        ded_col1, ded_col2, ded_col3 = st.columns(3)

        es_deducible = resultado_deducibilidad.es_deducible
        monto_deducible = float(resultado_deducibilidad.monto_deducible)
        monto_no_deducible = float(resultado_deducibilidad.monto_no_deducible)

        with ded_col1:
            st.metric(
                "¿Es Deducible?",
                "SÍ" if es_deducible else "NO",
                delta="Cumple" if es_deducible else "No cumple",
                delta_color="normal" if es_deducible else "inverse",
            )

        with ded_col2:
            st.metric(
                "Monto Deducible",
                f"${monto_deducible:,.2f}",
                help="Monto que puede deducirse en la declaración",
            )

        with ded_col3:
            st.metric(
                "Monto NO Deducible",
                f"${monto_no_deducible:,.2f}",
                help="Monto que NO puede deducirse",
            )

        # Fundamento legal
        st.markdown("---")
        st.subheader("📋 Fundamento Legal")

        fundamento = resultado_deducibilidad.fundamento_legal

        if es_deducible:
            st.success(f"""
            ✅ **PRIMA DEDUCIBLE**

            **Fundamento:** {fundamento}

            **Monto deducible:** ${monto_deducible:,.2f} MXN

            La prima puede deducirse en la declaración anual del ISR conforme
            a la Ley del Impuesto Sobre la Renta.
            """)
        else:
            st.warning(f"""
            ❌ **PRIMA NO DEDUCIBLE**

            **Fundamento:** {fundamento}

            Las primas de este tipo de seguro NO son deducibles para ISR según
            la legislación fiscal mexicana vigente.
            """)

        # Recomendaciones
        if es_pf and tipo_seguro_sat == "Gastos Médicos":
            st.info("""
            💡 **Recomendación:** Los gastos médicos mayores son 100% deducibles
            para personas físicas sin límite. Conserva tus comprobantes fiscales.
            """)
        elif es_pf and tipo_seguro_sat == "Pensiones":
            limite_umas = 5 * uma_anual
            st.info(f"""
            💡 **Recomendación:** Las primas de pensiones son deducibles hasta
            **5 UMAs anuales** (${limite_umas:,.2f} MXN).
            """)

# ============================================================================
# TAB 4: SAT - RETENCIONES ISR
# ============================================================================

with tab4:
    st.header("💳 SAT - Retenciones de ISR en Pagos")

    st.markdown("""
    Calcula las **retenciones de ISR** que debe aplicar la aseguradora en pagos
    de siniestros y otros beneficios.
    """)

    st.markdown("---")

    # Formulario
    st.subheader("📝 Datos del Pago")

    col1, col2 = st.columns(2)

    with col1:
        tipo_seguro_ret = st.selectbox(
            "Tipo de Seguro (Retención)",
            options=[
                "Vida",
                "Pensiones - Renta Vitalicia",
                "Pensiones - Retiro Ahorro",
                "Gastos Médicos",
                "Daños",
            ],
            help="Tipo de seguro y pago",
        )

        monto_pago = st.number_input(
            "Monto del Pago (MXN)",
            min_value=10_000,
            max_value=10_000_000,
            value=500_000,
            step=10_000,
            format="%d",
        )

    with col2:
        monto_gravable_pct = st.slider(
            "% Gravable del Pago",
            min_value=0,
            max_value=100,
            value=50,
            step=10,
            help="Porcentaje del pago que está gravado (resto exento)",
        )

        monto_gravable = monto_pago * (monto_gravable_pct / 100)

        st.metric(
            "Monto Gravable Calculado",
            f"${monto_gravable:,.2f}",
            help="Monto sobre el que se calcula la retención",
        )

    # Calcular retención
    if st.button("🔍 Calcular Retención ISR", type="primary"):
        # Determinar flags
        es_renta = "Renta Vitalicia" in tipo_seguro_ret
        es_retiro = "Retiro Ahorro" in tipo_seguro_ret

        # Mapear tipo
        if "Vida" in tipo_seguro_ret or "Retiro" in tipo_seguro_ret:
            tipo_fiscal_ret = TipoSeguroFiscal.VIDA
        elif "Pensiones" in tipo_seguro_ret:
            tipo_fiscal_ret = TipoSeguroFiscal.PENSIONES
        elif "Gastos" in tipo_seguro_ret:
            tipo_fiscal_ret = TipoSeguroFiscal.GASTOS_MEDICOS
        else:
            tipo_fiscal_ret = TipoSeguroFiscal.DANOS

        # Calcular
        calculadora_ret = CalculadoraRetencionesISR()
        resultado_retencion = calculadora_ret.calcular_retencion(
            tipo_seguro=tipo_fiscal_ret,
            monto_pago=Decimal(str(monto_pago)),
            monto_gravable=Decimal(str(monto_gravable)),
            es_renta_vitalicia=es_renta,
            es_retiro_ahorro=es_retiro,
        )

        # Mostrar resultados
        st.markdown("---")
        st.subheader("✅ Cálculo de Retención")

        # Métricas
        ret_col1, ret_col2, ret_col3, ret_col4 = st.columns(4)

        requiere_ret = resultado_retencion.requiere_retencion
        monto_retencion = float(resultado_retencion.monto_retencion)
        tasa_ret = float(resultado_retencion.tasa_retencion) * 100
        monto_neto = float(resultado_retencion.monto_neto_pagar)

        with ret_col1:
            st.metric(
                "¿Requiere Retención?",
                "SÍ" if requiere_ret else "NO",
                delta="Retiene" if requiere_ret else "No retiene",
                delta_color="inverse" if requiere_ret else "normal",
            )

        with ret_col2:
            st.metric(
                "Tasa de Retención",
                f"{tasa_ret:.1f}%",
                help="Porcentaje de retención ISR aplicable",
            )

        with ret_col3:
            st.metric(
                "Monto a Retener",
                f"${monto_retencion:,.2f}",
                help="ISR a retener del pago",
            )

        with ret_col4:
            st.metric(
                "Pago Neto",
                f"${monto_neto:,.2f}",
                delta=f"-${monto_retencion:,.2f}",
                help="Monto neto a entregar al beneficiario",
            )

        # Visualización
        st.markdown("---")

        # Gráfico de cascada
        fig_waterfall = go.Figure(go.Waterfall(
            x=["Pago Bruto", "Retención ISR", "Pago Neto"],
            y=[monto_pago, -monto_retencion, monto_neto],
            text=[
                f"${monto_pago:,.2f}",
                f"-${monto_retencion:,.2f}",
                f"${monto_neto:,.2f}",
            ],
            textposition="outside",
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            decreasing={"marker": {"color": "#d62728"}},
            increasing={"marker": {"color": "#2ca02c"}},
            totals={"marker": {"color": "#1f77b4"}},
        ))

        fig_waterfall.update_layout(
            title="Desglose del Pago con Retención ISR",
            yaxis_title="Monto (MXN)",
            showlegend=False,
            height=400,
        )

        st.plotly_chart(fig_waterfall, use_container_width=True)

        # Explicación
        st.markdown("---")
        st.subheader("📋 Fundamento y Explicación")

        if requiere_ret:
            st.warning(f"""
            ⚠️ **REQUIERE RETENCIÓN DE ISR**

            **Tasa de retención:** {tasa_ret:.1f}%

            **Base de retención:** ${monto_gravable:,.2f} (monto gravable)

            **Retención calculada:** ${monto_retencion:,.2f}

            **Pago neto al beneficiario:** ${monto_neto:,.2f}

            La aseguradora debe retener el ISR y enterarlo al SAT conforme
            a la Ley del ISR. El beneficiario recibirá constancia de retención.
            """)
        else:
            st.success(f"""
            ✅ **NO REQUIERE RETENCIÓN**

            Este tipo de pago está **exento** de retención de ISR.

            **Pago íntegro al beneficiario:** ${monto_pago:,.2f}

            No se requiere retención ni emisión de constancia fiscal.
            """)

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9em;">
    Cálculos basados en normativa vigente: CNSF, LISR, Circular S-11.4 |
    Mexican Insurance Analytics Suite
</div>
""", unsafe_allow_html=True)
