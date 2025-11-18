"""
Dashboard de Cumplimiento Regulatorio - Mexican Insurance Analytics Suite

Monitor de cumplimiento con normativa mexicana: RCS, CNSF, SAT, S-11.4.
"""

import sys
from decimal import Decimal
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Agregar src al path para imports
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

from mexican_insurance.regulatorio.rcs.calculadora_rcs import CalculadoraRCS
from mexican_insurance.regulatorio.rcs.models import (
    DatosAseguradora,
    ParametrosRCS,
    RiesgoSuscripcion,
)
from mexican_insurance.regulatorio.reservas_tecnicas.calculadora_s11_4 import (
    CalculadoraReservasTecnicasS11_4,
)
from mexican_insurance.regulatorio.reservas_tecnicas.models import (
    ConfiguracionReserva,
    DatosPoliza,
    TipoSeguro as TipoSeguroReservas,
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

    col1, col2 = st.columns(2)

    with col1:
        activos = st.number_input(
            "Activos Totales (Millones MXN)",
            min_value=100.0,
            max_value=100_000.0,
            value=5_000.0,
            step=100.0,
            format="%.2f",
        )

        pasivos = st.number_input(
            "Pasivos Totales (Millones MXN)",
            min_value=50.0,
            max_value=90_000.0,
            value=3_500.0,
            step=100.0,
            format="%.2f",
        )

        capital_pagado = st.number_input(
            "Capital Pagado (Millones MXN)",
            min_value=100.0,
            max_value=10_000.0,
            value=800.0,
            step=50.0,
            format="%.2f",
        )

    with col2:
        primas_emitidas = st.number_input(
            "Primas Emitidas Anuales (Millones MXN)",
            min_value=100.0,
            max_value=50_000.0,
            value=2_000.0,
            step=100.0,
            format="%.2f",
        )

        siniestralidad = st.slider(
            "Siniestralidad (%)",
            min_value=30.0,
            max_value=95.0,
            value=65.0,
            step=1.0,
            help="Porcentaje de primas pagadas como siniestros",
        ) / 100

        volatilidad_primas = st.slider(
            "Volatilidad de Primas (%)",
            min_value=5.0,
            max_value=50.0,
            value=15.0,
            step=1.0,
            help="Desviación estándar de primas año a año",
        ) / 100

    # Cálculo de RCS
    if st.button("🔍 Calcular RCS", type="primary"):
        # Crear objetos para cálculo
        datos_aseguradora = DatosAseguradora(
            activos=Decimal(str(activos)),
            pasivos=Decimal(str(pasivos)),
            capital_pagado=Decimal(str(capital_pagado)),
            primas_emitidas=Decimal(str(primas_emitidas)),
        )

        parametros_rcs = ParametrosRCS(
            riesgo_tasa_interes=Decimal("0.15"),  # 15% shock tasa
            riesgo_accionario=Decimal("0.39"),  # 39% shock acciones
            riesgo_inmobiliario=Decimal("0.25"),  # 25% shock inmuebles
            riesgo_credito=Decimal("0.05"),  # 5% default
            factor_correlacion=Decimal("0.5"),  # Correlación entre riesgos
        )

        # Calcular
        calculadora = CalculadoraRCS()
        resultado_rcs = calculadora.calcular_rcs_completo(
            datos=datos_aseguradora,
            parametros=parametros_rcs,
        )

        # Mostrar resultados
        st.markdown("---")
        st.subheader("✅ Resultados del Cálculo")

        # Métricas principales
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

        capital_disponible = float(resultado_rcs.capital_disponible)
        rcs_total = float(resultado_rcs.rcs_total)
        ratio_cobertura = float(resultado_rcs.ratio_cobertura)
        superavit = capital_disponible - rcs_total

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
                delta="Cumple" if superavit >= 0 else "Déficit",
                delta_color="normal" if superavit >= 0 else "inverse",
            )

        # Desglose por componente de riesgo
        st.markdown("---")
        st.subheader("📊 Desglose de Riesgos")

        col_left, col_right = st.columns([3, 2])

        with col_left:
            # Gráfico de waterfall de componentes RCS
            componentes = resultado_rcs.desglose_riesgos

            labels = list(componentes.keys())
            values = [float(v) for v in componentes.values()]

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
            # Pie chart de distribución
            fig_pie = go.Figure(
                go.Pie(
                    labels=labels,
                    values=values,
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
            df_riesgos = pd.DataFrame({
                "Componente de Riesgo": labels,
                "RCS Requerido (M MXN)": values,
                "% del Total": [(v / rcs_total * 100) for v in values],
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
        # Crear objetos
        tipo_enum = (
            TipoSeguroReservas.VIDA
            if tipo_seguro_reserva == "VIDA"
            else TipoSeguroReservas.DANOS
        )

        datos_poliza = DatosPoliza(
            tipo_seguro=tipo_enum,
            suma_asegurada=Decimal(str(suma_asegurada_res)),
            prima_emitida=Decimal(str(prima_emitida)),
            dias_transcurridos=dias_transcurridos,
            plazo_total_dias=plazo_total_dias,
            edad_asegurado=edad_asegurado_res,
        )

        configuracion = ConfiguracionReserva(
            tasa_interes_tecnico=Decimal(str(tasa_interes_res)),
            factor_gastos_admin=Decimal("0.25"),  # 25% de prima para gastos
        )

        # Calcular
        calculadora_reservas = CalculadoraReservasTecnicasS11_4()
        resultado_reservas = calculadora_reservas.calcular_reservas(
            poliza=datos_poliza,
            config=configuracion,
        )

        # Mostrar resultados
        st.markdown("---")
        st.subheader("✅ Reservas Calculadas")

        # Métricas
        res_col1, res_col2, res_col3, res_col4 = st.columns(4)

        rrc = float(resultado_reservas.reserva_riesgos_curso)
        rm = float(resultado_reservas.reserva_matematica)
        reserva_total = float(resultado_reservas.reserva_total)
        pct_prima = (reserva_total / float(prima_emitida)) * 100

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
            poliza_temp = DatosPoliza(
                tipo_seguro=tipo_enum,
                suma_asegurada=Decimal(str(suma_asegurada_res)),
                prima_emitida=Decimal(str(prima_emitida)),
                dias_transcurridos=dia,
                plazo_total_dias=plazo_total_dias,
                edad_asegurado=edad_asegurado_res,
            )

            res_temp = calculadora_reservas.calcular_reservas(
                poliza=poliza_temp,
                config=configuracion,
            )

            rrcs.append(float(res_temp.reserva_riesgos_curso))
            rms.append(float(res_temp.reserva_matematica))

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
