"""
Demo del módulo de Salud de suite_actuarial.

Gastos Médicos Mayores (GMM): calculadora, simulador de gasto
y curva de prima por edad.
"""

import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR / "src"))
sys.path.insert(0, str(ROOT_DIR / "streamlit_app"))

from utils.theme import apply_studio_theme, render_workbench_intro

from suite_actuarial.salud import GMM, NivelHospitalario, ZonaGeografica

st.set_page_config(page_title="Salud -- suite_actuarial", layout="wide")

apply_studio_theme()
render_workbench_intro(
    "MODEL WORKBENCH · SALUD",
    "¿Cómo se comparte un gasto médico incierto?",
    "Examina el efecto de edad, zona, nivel hospitalario, deducible y coaseguro "
    "sobre primas y pagos entre asegurado y aseguradora.",
)

# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------
ZONAS_LABELS = {
    ZonaGeografica.METRO: "Metro (CDMX, MTY, GDL)",
    ZonaGeografica.URBANO: "Urbano",
    ZonaGeografica.FORANEO: "Foráneo",
}

NIVELES_LABELS = {
    NivelHospitalario.ESTANDAR: "Estándar",
    NivelHospitalario.MEDIO: "Medio",
    NivelHospitalario.ALTO: "Alto",
}

DEDUCIBLES_DISPONIBLES = [10_000, 25_000, 50_000, 100_000, 250_000, 500_000]

# -----------------------------------------------------------------------
# Tabs
# -----------------------------------------------------------------------
tab_calc, tab_gasto, tab_edad = st.tabs(["Calculadora GMM", "Simulador de Gasto", "Prima por Edad"])

# ===== TAB 1: Calculadora GMM =====
with tab_calc:
    st.subheader("Calculadora de prima GMM")

    c1, c2 = st.columns(2)
    with c1:
        edad = st.slider("Edad del asegurado", 0, 85, 35, key="gmm_edad")
        sexo = st.radio(
            "Sexo",
            ["masculino", "femenino"],
            format_func=lambda x: "Masculino" if x == "masculino" else "Femenino",
            horizontal=True,
            key="gmm_sexo",
        )
        sa = st.number_input(
            "Suma asegurada (MXN)",
            min_value=1_000_000,
            max_value=100_000_000,
            value=5_000_000,
            step=1_000_000,
            format="%d",
            key="gmm_sa",
        )

    with c2:
        deducible = st.select_slider(
            "Deducible (MXN)",
            options=DEDUCIBLES_DISPONIBLES,
            value=50_000,
            format_func=lambda x: f"${x:,.0f}",
        )
        coaseguro_pct = st.select_slider(
            "Coaseguro (%)",
            options=[10, 20, 30],
            value=10,
            format_func=lambda x: f"{x}%",
        )
        zona = st.selectbox(
            "Zona geográfica",
            options=list(ZONAS_LABELS.keys()),
            format_func=lambda x: ZONAS_LABELS[x],
            index=1,
        )
        nivel = st.selectbox(
            "Nivel hospitalario",
            options=list(NIVELES_LABELS.keys()),
            format_func=lambda x: NIVELES_LABELS[x],
            index=1,
        )

    gmm = GMM(
        edad=edad,
        sexo=sexo,
        suma_asegurada=Decimal(str(sa)),
        deducible=Decimal(str(deducible)),
        coaseguro_pct=Decimal(str(coaseguro_pct / 100)),
        zona=zona,
        nivel=nivel,
    )

    desglose = gmm.desglose_prima()

    # Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Prima base", f"${float(desglose['tarificacion']['prima_base']):,.2f}")
    m2.metric("Prima ajustada", f"${float(desglose['tarificacion']['prima_ajustada']):,.2f}")
    m3.metric("Siniestralidad esperada", f"${float(desglose['siniestralidad_esperada']):,.2f}")

    # Factor breakdown table
    factores_data = [
        {
            "Factor": "Banda de edad",
            "Clave": desglose["asegurado"]["banda_edad"],
            "Valor": str(desglose["tarificacion"]["tasa_banda_edad"]),
        },
        {
            "Factor": "Zona",
            "Clave": desglose["producto"]["zona"],
            "Valor": str(desglose["tarificacion"]["factor_zona"]),
        },
        {
            "Factor": "Nivel hospitalario",
            "Clave": desglose["producto"]["nivel"],
            "Valor": str(desglose["tarificacion"]["factor_nivel"]),
        },
        {
            "Factor": "Deducible",
            "Clave": f"${deducible:,.0f}",
            "Valor": str(desglose["tarificacion"]["factor_deducible"]),
        },
        {
            "Factor": "Coaseguro",
            "Clave": f"{coaseguro_pct}%",
            "Valor": str(desglose["tarificacion"]["factor_coaseguro"]),
        },
    ]
    df_factores = pd.DataFrame(factores_data)
    st.dataframe(df_factores, use_container_width=True, hide_index=True)

    # Bar chart of factors
    fig_factors = px.bar(
        df_factores,
        x="Factor",
        y=df_factores["Valor"].astype(float),
        title="Factores de ajuste aplicados",
        text="Valor",
        color="Factor",
    )
    fig_factors.add_hline(y=1.0, line_dash="dash", line_color="gray")
    fig_factors.update_layout(showlegend=False, yaxis_title="Multiplicador")
    st.plotly_chart(fig_factors, use_container_width=True)

    st.caption(
        "Prima ilustrativa. Las tasas base por banda de edad no representan datos "
        "del mercado asegurador mexicano, y la siniestralidad esperada se deriva "
        "de la propia prima como prima/(1+margen) con margen de 30%: no es una "
        "estimación independiente ni sale de frecuencia, severidad o tendencia "
        "médica. El sexo se captura pero no altera la prima. No es una cotización."
    )

    with st.expander("Ver código Python"):
        st.code(
            f'''from decimal import Decimal
from suite_actuarial.salud import GMM, ZonaGeografica, NivelHospitalario

gmm = GMM(
    edad={edad},
    sexo="{sexo}",
    suma_asegurada=Decimal("{sa}"),
    deducible=Decimal("{deducible}"),
    coaseguro_pct=Decimal("{coaseguro_pct / 100}"),
    zona=ZonaGeografica.{zona.name},
    nivel=NivelHospitalario.{nivel.name},
)

# Prima ajustada
print(f"Prima ajustada: ${{gmm.calcular_prima_ajustada():,.2f}}")

# Desglose completo
desglose = gmm.desglose_prima()
for seccion, datos in desglose.items():
    print(f"\\n-- {{seccion}} --")
    if isinstance(datos, dict):
        for k, v in datos.items():
            print(f"  {{k}}: {{v}}")
    else:
        print(f"  {{datos}}")
''',
            language="python",
        )


# ===== TAB 2: Simulador de Gasto =====
with tab_gasto:
    st.subheader("Simulador de gasto médico")
    st.markdown(
        "Ingresa un monto de reclamación y observa cómo se reparte entre "
        "deducible, coaseguro del asegurado y pago de la aseguradora."
    )

    # El tope de coaseguro no viene de la calculadora de la pestaña anterior:
    # esta página lo fija en 10% de la suma asegurada. Es un supuesto de la
    # demo, no un parámetro del producto ni una cifra normativa, y el reparto
    # del gasto depende de él, así que se declara donde el usuario lo lee.
    TOPE_COASEGURO_PCT = Decimal("0.10")
    tope_coaseguro = (Decimal(str(sa)) * TOPE_COASEGURO_PCT).quantize(Decimal("0.01"))
    st.info(
        "**Supuesto de esta página:** tope de coaseguro = 10% de la suma "
        f"asegurada = ${float(tope_coaseguro):,.2f}. Es un valor elegido para la "
        "demostración: no es una cifra normativa, ni un valor por omisión del "
        "producto, ni una referencia de mercado verificada. El modelo admite "
        "cualquier tope, incluso ninguno, y el tope acota lo que paga el "
        "asegurado por coaseguro, así que mueve directamente el reparto de abajo."
    )

    monto_reclamacion = st.number_input(
        "Monto de la reclamación médica (MXN)",
        min_value=0,
        max_value=50_000_000,
        value=500_000,
        step=50_000,
        format="%d",
        key="gasto_monto",
    )

    # Reuse GMM from tab 1 inputs
    gmm_gasto = GMM(
        edad=edad,
        sexo=sexo,
        suma_asegurada=Decimal(str(sa)),
        deducible=Decimal(str(deducible)),
        coaseguro_pct=Decimal(str(coaseguro_pct / 100)),
        tope_coaseguro=tope_coaseguro,
        zona=zona,
        nivel=nivel,
    )

    sim = gmm_gasto.simular_gasto_medico(Decimal(str(monto_reclamacion)))

    # Metrics
    g1, g2, g3 = st.columns(3)
    g1.metric("Pago aseguradora", f"${float(sim['pago_aseguradora']):,.2f}")
    g2.metric("Pago asegurado (total)", f"${float(sim['pago_total_asegurado']):,.2f}")
    g3.metric("Exceso no cubierto", f"${float(sim['exceso_no_cubierto']):,.2f}")

    # Waterfall chart
    waterfall_data: list[dict[str, Any]] = [
        {
            "Concepto": "Reclamacion total",
            "Monto": float(sim["monto_reclamacion"]),
            "Tipo": "total",
        },
        {"Concepto": "Deducible", "Monto": -float(sim["deducible_aplicado"]), "Tipo": "asegurado"},
        {
            "Concepto": "Coaseguro asegurado",
            "Monto": -float(sim["coaseguro_asegurado"]),
            "Tipo": "asegurado",
        },
        {
            "Concepto": "Exceso no cubierto",
            "Monto": -float(sim["exceso_no_cubierto"]),
            "Tipo": "asegurado",
        },
        {
            "Concepto": "Pago aseguradora",
            "Monto": float(sim["pago_aseguradora"]),
            "Tipo": "aseguradora",
        },
    ]

    fig_waterfall = go.Figure(
        go.Waterfall(
            x=[d["Concepto"] for d in waterfall_data],
            y=[d["Monto"] for d in waterfall_data],
            measure=["absolute", "relative", "relative", "relative", "total"],
            textposition="outside",
            text=[f"${abs(d['Monto']):,.0f}" for d in waterfall_data],
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            decreasing={"marker": {"color": "#E53935"}},
            increasing={"marker": {"color": "#43A047"}},
            totals={"marker": {"color": "#1E88E5"}},
        )
    )
    fig_waterfall.update_layout(
        title="Distribución del gasto médico",
        yaxis_title="MXN",
        showlegend=False,
    )
    st.plotly_chart(fig_waterfall, use_container_width=True)

    # Detail table
    detalle = {
        "Concepto": [
            "Monto de reclamación",
            "Deducible aplicado",
            "Monto excedente",
            "Coaseguro asegurado",
            "Pago aseguradora",
            "Pago total asegurado",
            "Exceso no cubierto",
        ],
        "Monto (MXN)": [
            float(sim["monto_reclamacion"]),
            float(sim["deducible_aplicado"]),
            float(sim["monto_excedente"]),
            float(sim["coaseguro_asegurado"]),
            float(sim["pago_aseguradora"]),
            float(sim["pago_total_asegurado"]),
            float(sim["exceso_no_cubierto"]),
        ],
    }
    st.dataframe(
        pd.DataFrame(detalle).style.format({"Monto (MXN)": "${:,.2f}"}),
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "El reparto aplica deducible, coaseguro y tope tal como los define la "
        "póliza que configuraste, sobre un monto de reclamación que tú eliges: "
        "no hay distribución de siniestros detrás, así que esto no dice qué tan "
        "probable es ese gasto. Tampoco modela red hospitalaria, padecimientos "
        "preexistentes, periodos de espera ni exclusiones del condicionado."
    )

    with st.expander("Ver código Python"):
        st.code(
            f'''from decimal import Decimal
from suite_actuarial.salud import GMM, ZonaGeografica, NivelHospitalario

gmm = GMM(
    edad={edad},
    sexo="{sexo}",
    suma_asegurada=Decimal("{sa}"),
    deducible=Decimal("{deducible}"),
    coaseguro_pct=Decimal("{coaseguro_pct / 100}"),
    tope_coaseguro=Decimal("{tope_coaseguro}"),  # supuesto: 10% de la suma asegurada
    zona=ZonaGeografica.{zona.name},
    nivel=NivelHospitalario.{nivel.name},
)

resultado = gmm.simular_gasto_medico(Decimal("{monto_reclamacion}"))

for k, v in resultado.items():
    print(f"{{k}}: ${{v:,.2f}}")
''',
            language="python",
        )


# ===== TAB 3: Prima por Edad =====
with tab_edad:
    st.subheader("Curva de prima GMM por edad")
    st.markdown(
        "Prima ajustada por banda de edad quinquenal, manteniendo fijos el resto de los parámetros."
    )

    # Compute primas for all age bands
    @st.cache_data(show_spinner="Calculando primas por banda de edad...")
    def _primas_por_edad(
        sa_val: float,
        ded_val: float,
        coa_val: float,
        zona_val: ZonaGeografica,
        nivel_val: NivelHospitalario,
        sexo_val: str,
    ) -> pd.DataFrame:
        bandas = list(GMM.TASAS_BANDA_EDAD.keys())
        resultados = []
        # Use midpoint of each band for the GMM constructor
        for banda in bandas:
            if banda == "65+":
                edad_rep = 67
            else:
                partes = banda.split("-")
                edad_rep = (int(partes[0]) + int(partes[1])) // 2

            g = GMM(
                edad=edad_rep,
                sexo=sexo_val,
                suma_asegurada=Decimal(str(sa_val)),
                deducible=Decimal(str(ded_val)),
                coaseguro_pct=Decimal(str(coa_val)),
                zona=zona_val,
                nivel=nivel_val,
            )
            resultados.append(
                {
                    "Banda de edad": banda,
                    "Edad representativa": edad_rep,
                    "Prima base": float(g.calcular_prima_base()),
                    "Prima ajustada": float(g.calcular_prima_ajustada()),
                }
            )
        return pd.DataFrame(resultados)

    df_edades = _primas_por_edad(sa, deducible, coaseguro_pct / 100, zona, nivel, sexo)

    fig_edad = px.bar(
        df_edades,
        x="Banda de edad",
        y="Prima ajustada",
        title=f"Prima ajustada anual por banda de edad (SA=${sa:,.0f}, deducible=${deducible:,.0f})",
        text_auto="$,.0f",
        color="Prima ajustada",
        color_continuous_scale="YlOrRd",
    )
    fig_edad.update_layout(yaxis_title="Prima anual (MXN)", showlegend=False)
    st.plotly_chart(fig_edad, use_container_width=True)

    st.caption(
        "La curva reproduce las tasas ilustrativas por banda quinquenal del "
        "módulo: la pendiente muestra la forma que se les dio, no una curva de "
        "morbilidad observada. Dentro de cada banda la prima es plana, y el "
        "tramo 65+ agrupa todas las edades superiores en una sola tasa."
    )

    st.dataframe(
        df_edades.style.format(
            {
                "Prima base": "${:,.2f}",
                "Prima ajustada": "${:,.2f}",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    with st.expander("Ver código Python"):
        st.code(
            f'''from decimal import Decimal
from suite_actuarial.salud import GMM, ZonaGeografica, NivelHospitalario

bandas_edad = list(GMM.TASAS_BANDA_EDAD.keys())

for banda in bandas_edad:
    if banda == "65+":
        edad_rep = 67
    else:
        partes = banda.split("-")
        edad_rep = (int(partes[0]) + int(partes[1])) // 2

    gmm = GMM(
        edad=edad_rep,
        sexo="{sexo}",
        suma_asegurada=Decimal("{sa}"),
        deducible=Decimal("{deducible}"),
        coaseguro_pct=Decimal("{coaseguro_pct / 100}"),
        zona=ZonaGeografica.{zona.name},
        nivel=NivelHospitalario.{nivel.name},
    )
    prima = gmm.calcular_prima_ajustada()
    print(f"Banda {{banda:>5s}}: ${{prima:>12,.2f}}")
''',
            language="python",
        )
