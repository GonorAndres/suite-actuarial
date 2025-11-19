"""
Dashboard de Productos de Vida - Mexican Insurance Analytics Suite

Calculadora interactiva y análisis de productos de seguros de vida.
"""

import sys
from pathlib import Path

import streamlit as st

# Agregar src al path para imports
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

from mexican_insurance.actuarial.mortality.tablas import TablaMortalidad

from utils.calculations import (
    analisis_sensibilidad_edad,
    analisis_sensibilidad_tasa,
    calcular_prima_dotal,
    calcular_prima_ordinario,
    calcular_prima_temporal,
    generar_tabla_comparacion,
    proyeccion_reservas,
)
from utils.visualizations import (
    crear_grafico_comparacion_productos,
    crear_grafico_desglose_recargos,
    crear_grafico_reservas,
    crear_grafico_sensibilidad_edad,
    crear_grafico_sensibilidad_tasa,
    crear_tabla_metricas_producto,
)

# Configuración de la página
st.set_page_config(
    page_title="Productos de Vida - Mexican Insurance",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Título
st.title("📊 Dashboard de Productos de Vida")
st.markdown("""
Calculadora interactiva para productos de seguros de vida con análisis
de sensibilidad y visualización de reservas matemáticas.
""")

# ============================================================================
# CACHE: Cargar tabla de mortalidad (solo una vez)
# ============================================================================


@st.cache_resource
def cargar_tabla_mortalidad():
    """Carga tabla EMSSA-09 (se cachea para no recargar)."""
    return TablaMortalidad.cargar_emssa09()


tabla = cargar_tabla_mortalidad()

# ============================================================================
# SIDEBAR: Parámetros de entrada
# ============================================================================

with st.sidebar:
    st.header("⚙️ Parámetros del Seguro")

    # Datos del asegurado
    st.subheader("👤 Asegurado")

    edad = st.slider(
        "Edad",
        min_value=18,
        max_value=80,
        value=35,
        help="Edad actual del asegurado",
    )

    sexo = st.selectbox(
        "Sexo",
        options=["Hombre", "Mujer"],
        help="Sexo del asegurado (afecta tabla de mortalidad)",
    )

    suma_asegurada = st.number_input(
        "Suma Asegurada (MXN)",
        min_value=100_000,
        max_value=10_000_000,
        value=1_000_000,
        step=100_000,
        format="%d",
        help="Monto a pagar en caso de siniestro",
    )

    st.markdown("---")

    # Configuración del producto
    st.subheader("🎯 Producto")

    tipo_producto = st.selectbox(
        "Tipo de Producto",
        options=["Temporal", "Ordinario", "Dotal"],
        help="Tipo de seguro de vida",
    )

    # Plazo (solo para Temporal y Dotal)
    if tipo_producto in ["Temporal", "Dotal"]:
        plazo = st.slider(
            "Plazo (años)",
            min_value=5,
            max_value=40,
            value=20,
            help="Duración del seguro en años",
        )
    else:
        plazo = None

        # Opción de pago limitado para Ordinario
        pago_limitado = st.checkbox(
            "Pago Limitado",
            value=False,
            help="Limitar pagos hasta cierta edad",
        )

        if pago_limitado:
            edad_pago_limitado = st.slider(
                "Edad límite de pago",
                min_value=edad + 10,
                max_value=100,
                value=65,
                help="Edad hasta la cual se pagan primas",
            )
        else:
            edad_pago_limitado = None

    st.markdown("---")

    # Parámetros técnicos
    st.subheader("🔧 Técnicos")

    tasa_interes = st.slider(
        "Tasa de Interés Técnico (%)",
        min_value=1.0,
        max_value=10.0,
        value=5.5,
        step=0.5,
        help="Tasa técnica para cálculos actuariales",
    ) / 100

    st.markdown("---")

    st.info("""
    **💡 Información:**

    - **Temporal**: Protección solo en caso de fallecimiento durante el plazo
    - **Ordinario**: Protección vitalicia o con pago limitado
    - **Dotal**: Protección + ahorro (paga al final si sobrevive)
    """)

# ============================================================================
# CÁLCULOS PRINCIPALES
# ============================================================================

# Calcular prima según el tipo de producto
if tipo_producto == "Temporal":
    resultado = calcular_prima_temporal(
        edad=edad,
        sexo=sexo,
        suma_asegurada=suma_asegurada,
        plazo=plazo,
        tasa_interes=tasa_interes,
        tabla=tabla,
    )
    producto_nombre = f"Vida Temporal {plazo} años"
    plazo_display = plazo

elif tipo_producto == "Ordinario":
    resultado = calcular_prima_ordinario(
        edad=edad,
        sexo=sexo,
        suma_asegurada=suma_asegurada,
        edad_pago_limitado=edad_pago_limitado if pago_limitado else None,
        tasa_interes=tasa_interes,
        tabla=tabla,
    )
    if pago_limitado:
        producto_nombre = f"Vida Ordinario (Pago hasta {edad_pago_limitado} años)"
    else:
        producto_nombre = "Vida Ordinario (Pago vitalicio)"
    plazo_display = 20  # Para cálculos de métricas

elif tipo_producto == "Dotal":
    resultado = calcular_prima_dotal(
        edad=edad,
        sexo=sexo,
        suma_asegurada=suma_asegurada,
        plazo=plazo,
        tasa_interes=tasa_interes,
        tabla=tabla,
    )
    producto_nombre = f"Vida Dotal {plazo} años"
    plazo_display = plazo

# Calcular métricas
metricas = crear_tabla_metricas_producto(
    producto=tipo_producto,
    prima_neta=resultado["prima_neta"],
    prima_total=resultado["prima_total"],
    suma_asegurada=suma_asegurada,
    plazo=plazo_display,
)

# ============================================================================
# VISTA PRINCIPAL: TABS
# ============================================================================

tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Cotización",
    "📊 Comparación",
    "📈 Análisis de Sensibilidad",
    "💰 Reservas Matemáticas",
])

# ============================================================================
# TAB 1: COTIZACIÓN INDIVIDUAL
# ============================================================================

with tab1:
    st.header(f"💳 Cotización: {producto_nombre}")

    # Métricas principales en cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Prima Mensual",
            value=metricas["prima_mensual"],
            delta=metricas["recargos"],
            delta_color="off",
            help="Prima total mensual a pagar",
        )

    with col2:
        st.metric(
            label="Prima Anual",
            value=metricas["prima_anual"],
            help="Prima total anual (mensual × 12)",
        )

    with col3:
        st.metric(
            label=f"Total {plazo_display} años",
            value=metricas["total_plazo"],
            help=f"Total a pagar en {plazo_display} años",
        )

    with col4:
        st.metric(
            label="Ratio Prima/Suma",
            value=metricas["ratio_prima_suma"],
            help="Total primas como % de suma asegurada",
        )

    st.markdown("---")

    # Desglose detallado
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("📊 Desglose de Prima")

        # Tabla detallada
        prima_neta = resultado["prima_neta"]
        prima_total = resultado["prima_total"]
        recargos = resultado["recargos"]

        st.markdown(f"""
        | Concepto | Monto |
        |----------|------:|
        | **Prima Neta** | ${prima_neta:,.2f} |
        | Gastos de Administración | ${recargos.get('gastos_admin', 0):,.2f} |
        | Gastos de Adquisición | ${recargos.get('gastos_adquisicion', 0):,.2f} |
        | Utilidad | ${recargos.get('utilidad', 0):,.2f} |
        | **Prima Total** | **${prima_total:,.2f}** |
        """)

        st.info(f"""
        **Prima Neta:** Costo puro del riesgo según tabla de mortalidad EMSSA-09

        **Recargos ({metricas['porcentaje_recargos']}):** Costos operativos y margen
        """)

    with col_right:
        st.subheader("🥧 Composición")

        # Gráfico de pie con recargos
        if recargos:
            fig_pie = crear_grafico_desglose_recargos(recargos)
            st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")

    # Resumen de cobertura
    st.subheader("🛡️ Resumen de Cobertura")

    if tipo_producto == "Temporal":
        st.success(f"""
        ✅ **Cobertura:** Solo en caso de **fallecimiento** durante los **{plazo} años**

        ✅ **Beneficio:** ${suma_asegurada:,.0f} MXN a los beneficiarios

        ❌ **Sin beneficio** si sobrevive al plazo
        """)

    elif tipo_producto == "Ordinario":
        if pago_limitado:
            st.success(f"""
            ✅ **Cobertura:** **Vitalicia** por fallecimiento

            ✅ **Beneficio:** ${suma_asegurada:,.0f} MXN a los beneficiarios

            💰 **Pago de primas:** Solo hasta los {edad_pago_limitado} años
            """)
        else:
            st.success(f"""
            ✅ **Cobertura:** **Vitalicia** por fallecimiento

            ✅ **Beneficio:** ${suma_asegurada:,.0f} MXN a los beneficiarios

            💰 **Pago de primas:** Mientras viva el asegurado
            """)

    elif tipo_producto == "Dotal":
        st.success(f"""
        ✅ **Cobertura Dual:** Fallecimiento **O** supervivencia

        ✅ **Beneficio muerte:** ${suma_asegurada:,.0f} MXN a beneficiarios (si fallece en {plazo} años)

        ✅ **Beneficio vida:** ${suma_asegurada:,.0f} MXN al asegurado (si sobrevive {plazo} años)
        """)

# ============================================================================
# TAB 2: COMPARACIÓN DE PRODUCTOS
# ============================================================================

with tab2:
    st.header("⚖️ Comparación de Productos")

    st.markdown("""
    Compara los **3 productos de vida** con los mismos parámetros
    (edad, sexo, suma asegurada, plazo de 20 años).
    """)

    # Generar tabla comparativa
    df_comparacion = generar_tabla_comparacion(
        edad=edad,
        sexo=sexo,
        suma_asegurada=suma_asegurada,
        plazo=20,  # Plazo estándar para comparación
        tasa_interes=tasa_interes,
        tabla=tabla,
    )

    # Mostrar tabla
    st.dataframe(
        df_comparacion,
        use_container_width=True,
        hide_index=True,
    )

    # Gráfico comparativo
    fig_comparacion = crear_grafico_comparacion_productos(df_comparacion)
    st.plotly_chart(fig_comparacion, use_container_width=True)

    # Análisis de diferencias
    st.markdown("---")
    st.subheader("💡 Análisis")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info("""
        **Temporal**
        - ✅ Prima más baja
        - ✅ Protección pura
        - ❌ Sin valor de rescate
        - ❌ Sin beneficio por supervivencia
        """)

    with col2:
        st.info("""
        **Ordinario**
        - ✅ Protección vitalicia
        - ✅ Valor de rescate creciente
        - ⚠️ Prima media
        - ❌ Solo paga por muerte
        """)

    with col3:
        st.info("""
        **Dotal**
        - ✅ Doble beneficio
        - ✅ Componente de ahorro
        - ❌ Prima más alta
        - ✅ Garantiza pago
        """)

# ============================================================================
# TAB 3: ANÁLISIS DE SENSIBILIDAD
# ============================================================================

with tab3:
    st.header("📈 Análisis de Sensibilidad")

    st.markdown("""
    Analiza cómo cambia la prima al variar diferentes parámetros.
    """)

    # Sub-tabs para diferentes análisis
    subtab1, subtab2 = st.tabs(["👤 Sensibilidad por Edad", "📊 Sensibilidad por Tasa"])

    # Análisis de sensibilidad por edad
    with subtab1:
        st.subheader("👤 Impacto de la Edad")

        # Controles
        col_ctrl1, col_ctrl2 = st.columns(2)
        with col_ctrl1:
            edad_min_sens = st.number_input(
                "Edad mínima", min_value=18, max_value=70, value=25
            )
        with col_ctrl2:
            edad_max_sens = st.number_input(
                "Edad máxima", min_value=edad_min_sens + 5, max_value=80, value=65
            )

        # Calcular sensibilidad
        with st.spinner("Calculando sensibilidad por edad..."):
            df_edad = analisis_sensibilidad_edad(
                producto_tipo=tipo_producto,
                edad_min=edad_min_sens,
                edad_max=edad_max_sens,
                sexo=sexo,
                suma_asegurada=suma_asegurada,
                plazo=plazo if tipo_producto in ["Temporal", "Dotal"] else 20,
                tasa_interes=tasa_interes,
                tabla=tabla,
            )

        # Gráfico
        fig_edad = crear_grafico_sensibilidad_edad(df_edad)
        st.plotly_chart(fig_edad, use_container_width=True)

        # Insights
        incremento = df_edad["Prima Total"].iloc[-1] - df_edad["Prima Total"].iloc[0]
        pct_incremento = (incremento / df_edad["Prima Total"].iloc[0]) * 100

        st.info(f"""
        📊 **Insight:** De {edad_min_sens} a {edad_max_sens} años, la prima total aumenta
        **${incremento:,.2f} MXN** (**+{pct_incremento:.1f}%**)

        La edad es el factor de riesgo más importante en seguros de vida.
        """)

    # Análisis de sensibilidad por tasa
    with subtab2:
        st.subheader("📊 Impacto de la Tasa de Interés")

        st.markdown("""
        La tasa de interés técnico afecta el valor presente de los pagos futuros.
        Una **tasa mayor** resulta en **primas menores**.
        """)

        # Calcular sensibilidad
        with st.spinner("Calculando sensibilidad por tasa..."):
            df_tasa = analisis_sensibilidad_tasa(
                producto_tipo=tipo_producto,
                edad=edad,
                sexo=sexo,
                suma_asegurada=suma_asegurada,
                plazo=plazo if tipo_producto in ["Temporal", "Dotal"] else 20,
                tasa_min=0.02,
                tasa_max=0.10,
                step=0.005,
                tabla=tabla,
            )

        # Gráfico
        fig_tasa = crear_grafico_sensibilidad_tasa(df_tasa)
        st.plotly_chart(fig_tasa, use_container_width=True)

        # Insights
        prima_tasa_baja = df_tasa["Prima Total"].iloc[0]
        prima_tasa_alta = df_tasa["Prima Total"].iloc[-1]
        reduccion = prima_tasa_baja - prima_tasa_alta
        pct_reduccion = (reduccion / prima_tasa_baja) * 100

        st.info(f"""
        📊 **Insight:** Al aumentar la tasa de 2% a 10%, la prima total se reduce
        **${reduccion:,.2f} MXN** (**-{pct_reduccion:.1f}%**)

        Tasas de interés más altas permiten primas más bajas por el mayor rendimiento
        esperado de las inversiones.
        """)

# ============================================================================
# TAB 4: RESERVAS MATEMÁTICAS
# ============================================================================

with tab4:
    st.header("💰 Reservas Matemáticas")

    st.markdown("""
    La **reserva matemática** representa la obligación de la aseguradora en cada momento.
    Es la diferencia entre el valor presente de beneficios futuros y primas futuras.
    """)

    # Solo calcular para productos con plazo definido o limitar a 20 años para Ordinario
    if tipo_producto in ["Temporal", "Dotal"]:
        plazo_reserva = plazo
    else:
        plazo_reserva = 20
        st.warning("Para Vida Ordinario, se muestra proyección de 20 años.")

    # Calcular proyección de reservas
    with st.spinner("Calculando proyección de reservas..."):
        df_reservas = proyeccion_reservas(
            producto_tipo=tipo_producto,
            edad=edad,
            sexo=sexo,
            suma_asegurada=suma_asegurada,
            plazo=plazo_reserva,
            tasa_interes=tasa_interes,
            tabla=tabla,
        )

    # Gráfico de evolución
    fig_reservas = crear_grafico_reservas(df_reservas, suma_asegurada)
    st.plotly_chart(fig_reservas, use_container_width=True)

    # Tabla de datos
    with st.expander("📋 Ver datos detallados"):
        # Formatear DataFrame para mostrar
        df_display = df_reservas.copy()
        df_display["Reserva Matemática"] = df_display["Reserva Matemática"].apply(
            lambda x: f"${x:,.2f}"
        )
        df_display["% Suma Asegurada"] = df_display["% Suma Asegurada"].apply(
            lambda x: f"{x:.2f}%"
        )

        st.dataframe(df_display, use_container_width=True, hide_index=True)

    # Insights
    st.markdown("---")
    st.subheader("💡 Interpretación")

    reserva_inicial = df_reservas["Reserva Matemática"].iloc[0]
    reserva_final = df_reservas["Reserva Matemática"].iloc[-1]
    reserva_max = df_reservas["Reserva Matemática"].max()
    ano_max = df_reservas.loc[
        df_reservas["Reserva Matemática"].idxmax(), "Año"
    ]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Reserva Inicial",
            f"${reserva_inicial:,.2f}",
            help="Reserva al inicio de la póliza",
        )

    with col2:
        st.metric(
            "Reserva Máxima",
            f"${reserva_max:,.2f}",
            delta=f"Año {int(ano_max)}",
            help="Máxima reserva durante la vigencia",
        )

    with col3:
        st.metric(
            "Reserva Final",
            f"${reserva_final:,.2f}",
            help="Reserva al final del plazo",
        )

    # Explicación por tipo de producto
    if tipo_producto == "Temporal":
        st.info("""
        **Vida Temporal:** La reserva crece hasta un punto y luego puede decrecer
        conforme se acerca el final del plazo, ya que la probabilidad de muerte
        aumenta pero el tiempo restante disminuye.
        """)
    elif tipo_producto == "Ordinario":
        st.info("""
        **Vida Ordinario:** La reserva crece continuamente conforme el asegurado
        envejece, ya que la probabilidad de muerte aumenta mientras las primas
        se mantienen niveladas.
        """)
    elif tipo_producto == "Dotal":
        st.info("""
        **Vida Dotal:** La reserva crece consistentemente hasta llegar a la suma
        asegurada al final del plazo, ya que se garantiza el pago por muerte o
        supervivencia.
        """)

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9em;">
    Cálculos basados en tabla de mortalidad <strong>EMSSA-09</strong> |
    Mexican Insurance Analytics Suite
</div>
""", unsafe_allow_html=True)
