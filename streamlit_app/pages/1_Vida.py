"""
Demo: Módulo de Vida -- suite_actuarial

Calculadora interactiva de productos de seguros de vida
(Temporal, Ordinario, Dotal) con tabla EMSSA-09.
"""

import sys
from decimal import Decimal
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR / "src"))
sys.path.insert(0, str(ROOT_DIR / "streamlit_app"))

from utils.calculations import (
    calcular_prima_dotal,
    calcular_prima_ordinario,
    calcular_prima_temporal,
    generar_tabla_comparacion,
    proyeccion_reservas,
)
from utils.theme import apply_studio_theme, render_workbench_intro
from suite_actuarial import Asegurado, ConfiguracionProducto, TablaMortalidad
from suite_actuarial.core.models.common import Sexo
from suite_actuarial.vida import VidaDotal

st.set_page_config(page_title="Vida -- suite_actuarial", layout="wide")

apply_studio_theme()
render_workbench_intro(
    "MODEL WORKBENCH · VIDA",
    "¿Cómo se financia una promesa de seguro?",
    "Construye beneficios de fallecimiento y supervivencia, selecciona mortalidad y "
    "descuento, y examina primas, reservas y sensibilidad.",
)


# -----------------------------------------------------------------------
# Carga de tabla de mortalidad (cacheada)
# -----------------------------------------------------------------------
@st.cache_data(show_spinner="Cargando tabla EMSSA-09...")
def cargar_tabla():
    return TablaMortalidad.cargar_emssa09()


tabla = cargar_tabla()

# -----------------------------------------------------------------------
# Inputs comunes en sidebar
# -----------------------------------------------------------------------
with st.sidebar:
    st.header("Parámetros del asegurado")
    edad = st.slider("Edad", 18, 70, 35)
    sexo = st.radio("Sexo", ["Hombre", "Mujer"], horizontal=True)
    suma_asegurada = st.number_input(
        "Suma asegurada (MXN)",
        min_value=100_000,
        max_value=50_000_000,
        value=1_000_000,
        step=100_000,
        format="%d",
    )
    plazo = st.slider("Plazo (años)", 5, 40, 20)
    tasa_interes = st.slider(
        "Tasa de interés técnico (%)",
        min_value=1.0,
        max_value=10.0,
        value=5.0,
        step=0.25,
    )
    tasa_decimal = tasa_interes / 100.0

# -----------------------------------------------------------------------
# Tabs
# -----------------------------------------------------------------------
tab_lab, tab_calc, tab_comp, tab_reservas = st.tabs(
    ["Laboratorio dotal", "Productos", "Comparación", "Reservas"]
)

# ===== TAB 0: Laboratorio dotal limitado =====
with tab_lab:
    st.subheader("Dotal educativo con pago limitado")
    st.markdown(
        "Define un beneficio pagadero por fallecimiento durante el plazo o por "
        "supervivencia al vencimiento. Las primas se concentran en un periodo menor."
    )
    plazo_pago = st.slider("Años de pago de prima", 1, plazo, min(10, plazo))
    sexo_modelo = Sexo.HOMBRE if sexo == "Hombre" else Sexo.MUJER
    try:
        config_lab = ConfiguracionProducto(
            nombre_producto=f"Dotal educativo {plazo}/{plazo_pago}",
            plazo_years=plazo,
            tasa_interes_tecnico=Decimal(str(tasa_decimal)),
        )
        asegurado_lab = Asegurado(
            edad=edad,
            sexo=sexo_modelo,
            suma_asegurada=Decimal(str(suma_asegurada)),
        )
        producto_lab = VidaDotal(config_lab, tabla, plazo_pago=plazo_pago)
        analisis_lab = producto_lab.analizar_producto(asegurado_lab)

        metrica_1, metrica_2, metrica_3 = st.columns(3)
        metrica_1.metric(
            "Prima neta anual",
            f"${analisis_lab.prima_neta_anual_equivalente:,.2f}",
        )
        metrica_2.metric(
            "VP beneficio por muerte",
            f"${analisis_lab.vp_beneficio_muerte:,.2f}",
        )
        metrica_3.metric(
            "VP beneficio por supervivencia",
            f"${analisis_lab.vp_beneficio_supervivencia:,.2f}",
        )

        reservas_lab = pd.DataFrame(
            [punto.model_dump(mode="json") for punto in analisis_lab.reservas]
        )
        st.line_chart(reservas_lab, x="anio", y="reserva", color="#176B74")

        checks_lab = analisis_lab.verificaciones
        st.markdown("#### Verificaciones")
        st.caption(
            "Cada verificación contrasta el motor de valuación contra una ruta de "
            "cálculo independiente: las funciones de conmutación (Dx/Nx/Mx) para la "
            "descomposición del beneficio, y la recursión de Fackler —retrospectiva— "
            "para la trayectoria de la reserva, que se calcula de forma prospectiva."
        )
        st.write(
            {
                "Muerte + supervivencia = beneficio total": checks_lab.descomposicion_beneficios,
                "Principio de equivalencia": checks_lab.principio_equivalencia,
                "Reserva inicial = 0": checks_lab.reserva_inicial_cero,
                "Reserva final = suma asegurada": checks_lab.reserva_final_igual_beneficio,
                "Recursion de Fackler entre reservas": checks_lab.recursion_fackler,
            }
        )
        with st.expander("Ver Python reproducible"):
            st.code(
                "producto = VidaDotal(config, tabla, plazo_pago=10)\n"
                "analisis = producto.analizar_producto(asegurado)",
                language="python",
            )
    except ValueError as exc:
        st.warning(str(exc))

# ===== TAB 1: Calculadora =====
with tab_calc:
    st.subheader("Prima por producto")

    col_t, col_o, col_d = st.columns(3)

    @st.cache_data(show_spinner=False)
    def _prima_temporal(e, s, sa, p, t, _tabla_nombre):
        return calcular_prima_temporal(e, s, sa, p, t, tabla)

    @st.cache_data(show_spinner=False)
    def _prima_ordinario(e, s, sa, t, _tabla_nombre):
        return calcular_prima_ordinario(e, s, sa, None, t, tabla)

    @st.cache_data(show_spinner=False)
    def _prima_dotal(e, s, sa, p, t, _tabla_nombre):
        return calcular_prima_dotal(e, s, sa, p, t, tabla)

    res_temporal = _prima_temporal(edad, sexo, suma_asegurada, plazo, tasa_decimal, tabla.nombre)
    res_ordinario = _prima_ordinario(edad, sexo, suma_asegurada, tasa_decimal, tabla.nombre)
    res_dotal = _prima_dotal(edad, sexo, suma_asegurada, plazo, tasa_decimal, tabla.nombre)

    with col_t:
        st.markdown("#### Vida Temporal")
        st.metric("Prima neta mensual", f"${res_temporal['prima_neta']:,.2f}")
        st.metric("Prima total mensual", f"${res_temporal['prima_total']:,.2f}")
        st.caption(f"Plazo: {plazo} años -- solo cobertura por muerte")

    with col_o:
        st.markdown("#### Vida Ordinario")
        st.metric("Prima neta mensual", f"${res_ordinario['prima_neta']:,.2f}")
        st.metric("Prima total mensual", f"${res_ordinario['prima_total']:,.2f}")
        st.caption("Cobertura vitalicia -- pago de primas vitalicio")

    with col_d:
        st.markdown("#### Vida Dotal")
        st.metric("Prima neta mensual", f"${res_dotal['prima_neta']:,.2f}")
        st.metric("Prima total mensual", f"${res_dotal['prima_total']:,.2f}")
        st.caption(f"Plazo: {plazo} años -- muerte + supervivencia")

    with st.expander("Ver código Python"):
        st.code(
            f'''from decimal import Decimal
from suite_actuarial import (
    VidaTemporal, VidaOrdinario, VidaDotal,
    TablaMortalidad, Asegurado, ConfiguracionProducto,
)
from suite_actuarial.core.validators import Sexo

tabla = TablaMortalidad.cargar_emssa09()

asegurado = Asegurado(
    edad={edad},
    sexo=Sexo.{"HOMBRE" if sexo == "Hombre" else "MUJER"},
    suma_asegurada=Decimal("{suma_asegurada}"),
)

# -- Temporal --
config_temp = ConfiguracionProducto(
    nombre_producto="Temporal {plazo}",
    plazo_years={plazo},
    tasa_interes_tecnico=Decimal("{tasa_decimal}"),
)
temporal = VidaTemporal(config_temp, tabla)
res_temp = temporal.calcular_prima(asegurado, frecuencia_pago="mensual")
print(f"Temporal -- prima total mensual: ${{res_temp.prima_total:,.2f}}")

# -- Ordinario --
config_ord = ConfiguracionProducto(
    nombre_producto="Ordinario",
    plazo_years=20,
    tasa_interes_tecnico=Decimal("{tasa_decimal}"),
)
ordinario = VidaOrdinario(config_ord, tabla, plazo_pago_vitalicio=True)
res_ord = ordinario.calcular_prima(asegurado, frecuencia_pago="mensual")
print(f"Ordinario -- prima total mensual: ${{res_ord.prima_total:,.2f}}")

# -- Dotal --
config_dot = ConfiguracionProducto(
    nombre_producto="Dotal {plazo}",
    plazo_years={plazo},
    tasa_interes_tecnico=Decimal("{tasa_decimal}"),
)
dotal = VidaDotal(config_dot, tabla)
res_dot = dotal.calcular_prima(asegurado, frecuencia_pago="mensual")
print(f"Dotal -- prima total mensual: ${{res_dot.prima_total:,.2f}}")
''',
            language="python",
        )


# ===== TAB 2: Comparación =====
with tab_comp:
    st.subheader("Comparación entre productos")

    @st.cache_data(show_spinner=False)
    def _tabla_comparacion(e, s, sa, p, t, _tn):
        return generar_tabla_comparacion(e, s, sa, p, t, tabla)

    df_comp = _tabla_comparacion(edad, sexo, suma_asegurada, plazo, tasa_decimal, tabla.nombre)

    st.dataframe(df_comp, use_container_width=True, hide_index=True)

    # Bar chart
    primas_data = {
        "Producto": ["Temporal", "Ordinario", "Dotal"],
        "Prima Total": [
            res_temporal["prima_total"],
            res_ordinario["prima_total"],
            res_dotal["prima_total"],
        ],
    }
    df_bar = pd.DataFrame(primas_data)
    fig = px.bar(
        df_bar,
        x="Producto",
        y="Prima Total",
        title="Prima total mensual por producto",
        text_auto="$.2f",
        color="Producto",
        color_discrete_sequence=["#2196F3", "#4CAF50", "#FF9800"],
    )
    fig.update_layout(showlegend=False, yaxis_title="MXN / mes")
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Ver código Python"):
        st.code(
            f'''from suite_actuarial import (
    VidaTemporal, VidaOrdinario, VidaDotal,
    TablaMortalidad, Asegurado, ConfiguracionProducto,
)
from suite_actuarial.core.validators import Sexo
from decimal import Decimal
import pandas as pd

tabla = TablaMortalidad.cargar_emssa09()

asegurado = Asegurado(
    edad={edad},
    sexo=Sexo.{"HOMBRE" if sexo == "Hombre" else "MUJER"},
    suma_asegurada=Decimal("{suma_asegurada}"),
)
tasa = Decimal("{tasa_decimal}")
plazo = {plazo}

productos = {{}}
for nombre, Cls, kwargs in [
    ("Temporal", VidaTemporal, {{}},),
    ("Ordinario", VidaOrdinario, {{"plazo_pago_vitalicio": True}}),
    ("Dotal", VidaDotal, {{}}),
]:
    cfg = ConfiguracionProducto(
        nombre_producto=nombre, plazo_years=plazo,
        tasa_interes_tecnico=tasa,
    )
    prod = Cls(cfg, tabla, **kwargs)
    res = prod.calcular_prima(asegurado, frecuencia_pago="mensual")
    productos[nombre] = float(res.prima_total)

df = pd.DataFrame([
    {{"Producto": k, "Prima Total": v}} for k, v in productos.items()
])
print(df.to_string(index=False))
''',
            language="python",
        )


# ===== TAB 3: Reservas =====
with tab_reservas:
    st.subheader("Proyección de reservas matemáticas")

    producto_reserva = st.selectbox(
        "Producto para reservas",
        ["Temporal", "Ordinario", "Dotal"],
    )

    @st.cache_data(show_spinner="Calculando reservas...")
    def _reservas(prod, e, s, sa, p, t, _tn):
        return proyeccion_reservas(prod, e, s, sa, p, t, tabla)

    df_res = _reservas(
        producto_reserva, edad, sexo, suma_asegurada, plazo, tasa_decimal, tabla.nombre
    )

    fig_res = go.Figure()
    fig_res.add_trace(
        go.Scatter(
            x=df_res["Año"],
            y=df_res["Reserva Matemática"],
            mode="lines+markers",
            name="Reserva (MXN)",
            line=dict(color="#1976D2", width=2),
        )
    )
    fig_res.update_layout(
        title=f"Reserva matemática -- {producto_reserva} (edad {edad}, plazo {plazo})",
        xaxis_title="Año de póliza",
        yaxis_title="Reserva (MXN)",
        hovermode="x unified",
    )
    st.plotly_chart(fig_res, use_container_width=True)

    with st.expander("Tabla de reservas"):
        st.dataframe(
            df_res.style.format({"Reserva Matemática": "${:,.2f}", "% Suma Asegurada": "{:.2f}%"}),
            use_container_width=True,
            hide_index=True,
        )

    with st.expander("Ver código Python"):
        sexo_enum = "HOMBRE" if sexo == "Hombre" else "MUJER"
        st.code(
            f'''from decimal import Decimal
from suite_actuarial import (
    VidaTemporal, VidaOrdinario, VidaDotal,
    TablaMortalidad, Asegurado, ConfiguracionProducto,
)
from suite_actuarial.core.validators import Sexo

tabla = TablaMortalidad.cargar_emssa09()

config = ConfiguracionProducto(
    nombre_producto="{producto_reserva}",
    plazo_years={plazo},
    tasa_interes_tecnico=Decimal("{tasa_decimal}"),
)
asegurado = Asegurado(
    edad={edad},
    sexo=Sexo.{sexo_enum},
    suma_asegurada=Decimal("{suma_asegurada}"),
)

# Elegir producto
producto = {"{'VidaTemporal' if producto_reserva == 'Temporal' else 'VidaOrdinario' if producto_reserva == 'Ordinario' else 'VidaDotal'}"}(config, tabla)

# Calcular reserva para cada ano
for anio in range({plazo} + 1):
    reserva = producto.calcular_reserva(asegurado, anio=anio)
    print(f"Ano {{anio:>2d}}: ${{float(reserva):>12,.2f}}")
''',
            language="python",
        )
