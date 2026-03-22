"""
Demo: Módulo de Pensiones -- suite_actuarial

Calculadoras IMSS (Ley 73 / Ley 97), rentas vitalicias
y funciones de conmutación.
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

from suite_actuarial import TablaMortalidad
from suite_actuarial.pensiones import (
    PensionLey73,
    PensionLey97,
    RentaVitalicia,
    TablaConmutacion,
)
from suite_actuarial.pensiones.tablas_imss import (
    LEY73_FACTORES_EDAD,
    LEY73_PORCENTAJES,
    SEMANAS_MINIMAS_LEY73,
)

st.set_page_config(page_title="Pensiones -- suite_actuarial", layout="wide")

st.title("Pensiones")
st.markdown(
    "Calculadoras del sistema de pensiones mexicano (`suite_actuarial.pensiones`): "
    "IMSS Ley 73 y Ley 97, rentas vitalicias y funciones de conmutación."
)


@st.cache_data(show_spinner="Cargando tabla EMSSA-09...")
def cargar_tabla():
    return TablaMortalidad.cargar_emssa09()


tabla_mortalidad = cargar_tabla()

# -----------------------------------------------------------------------
# Tabs
# -----------------------------------------------------------------------
tab_imss, tab_rv, tab_conm = st.tabs(
    ["Calculadora IMSS", "Renta Vitalicia", "Funciones de Conmutación"]
)

# ===== TAB 1: Calculadora IMSS =====
with tab_imss:
    st.subheader("Calculadora de pensión IMSS")

    regimen = st.radio(
        "Régimen de pensión",
        ["Ley 73 (antes de julio 1997)", "Ley 97 (después de julio 1997)"],
        horizontal=True,
    )

    if regimen.startswith("Ley 73"):
        st.markdown(
            "**Ley 73**: pensión de beneficio definido. Se calcula como porcentaje "
            "del salario promedio de las últimas 250 semanas, multiplicado por "
            "un factor según la edad de retiro."
        )

        cl1, cl2 = st.columns(2)
        with cl1:
            semanas = st.number_input(
                "Semanas cotizadas",
                min_value=500,
                max_value=3000,
                value=1200,
                step=52,
            )
            salario_promedio = st.number_input(
                "Salario promedio diario (últimas 250 semanas, MXN)",
                min_value=100.0,
                max_value=10_000.0,
                value=800.0,
                step=50.0,
            )
        with cl2:
            edad_retiro = st.slider(
                "Edad de retiro", 60, 65, 65, key="ley73_edad"
            )
            st.markdown("**Factores por edad de retiro (Art. 171):**")
            for e, f in LEY73_FACTORES_EDAD.items():
                marca = " <--" if e == edad_retiro else ""
                st.text(f"  {e} años: {float(f)*100:.0f}%{marca}")

        pension73 = PensionLey73(
            semanas_cotizadas=semanas,
            salario_promedio_5_anos=Decimal(str(salario_promedio)),
            edad_retiro=edad_retiro,
        )
        resumen = pension73.resumen()

        p1, p2, p3 = st.columns(3)
        p1.metric("Pensión mensual", f"${float(resumen['pension_mensual']):,.2f}")
        p2.metric("Aguinaldo anual", f"${float(resumen['aguinaldo_anual']):,.2f}")
        p3.metric("Pensión anual total", f"${float(resumen['pension_anual_total']):,.2f}")

        # Detail table
        detalle_73 = {
            "Concepto": [
                "Semanas cotizadas",
                "Salario promedio diario",
                "Porcentaje de pensión",
                "Factor por edad",
                "Pensión mensual",
                "Aguinaldo anual",
                "Pensión anual total",
            ],
            "Valor": [
                str(resumen["semanas_cotizadas"]),
                f"${float(resumen['salario_promedio_diario']):,.2f}",
                f"{float(resumen['porcentaje_pension'])*100:.2f}%",
                f"{float(resumen['factor_edad'])*100:.0f}%",
                f"${float(resumen['pension_mensual']):,.2f}",
                f"${float(resumen['aguinaldo_anual']):,.2f}",
                f"${float(resumen['pension_anual_total']):,.2f}",
            ],
        }
        st.dataframe(pd.DataFrame(detalle_73), use_container_width=True, hide_index=True)

        with st.expander("Ver código Python"):
            st.code(
                f'''from decimal import Decimal
from suite_actuarial.pensiones import PensionLey73

pension = PensionLey73(
    semanas_cotizadas={semanas},
    salario_promedio_5_anos=Decimal("{salario_promedio}"),
    edad_retiro={edad_retiro},
)

resumen = pension.resumen()
print(f"Pension mensual:    ${{resumen['pension_mensual']:,.2f}}")
print(f"Aguinaldo anual:    ${{resumen['aguinaldo_anual']:,.2f}}")
print(f"Pension anual total: ${{resumen['pension_anual_total']:,.2f}}")
print(f"Porcentaje pension: {{float(resumen['porcentaje_pension'])*100:.2f}}%")
print(f"Factor edad:        {{float(resumen['factor_edad'])*100:.0f}}%")
''',
                language="python",
            )

    else:
        # Ley 97
        st.markdown(
            "**Ley 97**: pensión de contribución definida. El saldo de la AFORE "
            "se usa para comprar una renta vitalicia o un retiro programado."
        )

        cl1, cl2 = st.columns(2)
        with cl1:
            saldo_afore = st.number_input(
                "Saldo actual en AFORE (MXN)",
                min_value=100_000,
                max_value=20_000_000,
                value=1_500_000,
                step=100_000,
                format="%d",
            )
            salario_actual = st.number_input(
                "Salario mensual actual (MXN)",
                min_value=5_000.0,
                max_value=200_000.0,
                value=25_000.0,
                step=1_000.0,
            )
        with cl2:
            edad_97 = st.slider("Edad actual", 30, 64, 45, key="ley97_edad")
            semanas_97 = st.number_input(
                "Semanas cotizadas",
                min_value=500,
                max_value=3000,
                value=1000,
                step=52,
                key="ley97_semanas",
            )
            rendimiento = st.slider(
                "Rendimiento real esperado AFORE (%)",
                min_value=2.0,
                max_value=8.0,
                value=4.5,
                step=0.5,
            )

        edad_retiro_97 = 65
        anos_restantes = max(0, edad_retiro_97 - edad_97)

        pension97 = PensionLey97(
            saldo_afore=Decimal(str(saldo_afore)),
            edad=edad_retiro_97,
            sexo="H",
            semanas_cotizadas=semanas_97,
            tabla_mortalidad=tabla_mortalidad,
        )

        # Project AFORE balance
        @st.cache_data(show_spinner="Proyectando saldo AFORE...")
        def _proyectar(saldo, sal, rend, anos, _ed, _sem, _tn):
            p = PensionLey97(
                saldo_afore=Decimal(str(saldo)),
                edad=_ed - anos,
                sexo="H",
                semanas_cotizadas=_sem,
                tabla_mortalidad=tabla_mortalidad,
            )
            return p.proyectar_saldo_afore(
                salario_actual=Decimal(str(sal)),
                rendimiento_anual=Decimal(str(rend / 100)),
                anos_restantes=anos,
            )

        proyeccion = _proyectar(
            saldo_afore, salario_actual, rendimiento,
            anos_restantes, edad_retiro_97, semanas_97, tabla_mortalidad.nombre,
        )
        df_proy = pd.DataFrame(proyeccion)
        df_proy["saldo_afore"] = df_proy["saldo_afore"].apply(float)
        df_proy["aportacion_anual"] = df_proy["aportacion_anual"].apply(float)

        saldo_final = df_proy.iloc[-1]["saldo_afore"]

        # Recalculate pension with projected balance
        pension97_final = PensionLey97(
            saldo_afore=Decimal(str(saldo_final)),
            edad=edad_retiro_97,
            sexo="H",
            semanas_cotizadas=semanas_97,
            tabla_mortalidad=tabla_mortalidad,
        )
        comparacion = pension97_final.comparar_modalidades()

        st.markdown(f"**Saldo proyectado al retiro (edad {edad_retiro_97}):** ${saldo_final:,.2f}")

        q1, q2 = st.columns(2)
        q1.metric(
            "Renta vitalicia (mensual)",
            f"${float(comparacion['renta_vitalicia']['pension_mensual']):,.2f}",
            help="Pensión garantizada de por vida con una aseguradora",
        )
        q2.metric(
            "Retiro programado (mensual)",
            f"${float(comparacion['retiro_programado']['pension_mensual']):,.2f}",
            help="Se recalcula anualmente, puede agotarse",
        )
        st.info(f"Recomendación: **{comparacion['recomendacion']}**")

        # Projection chart
        fig_proy = go.Figure()
        fig_proy.add_trace(
            go.Scatter(
                x=df_proy["edad"],
                y=df_proy["saldo_afore"],
                mode="lines+markers",
                name="Saldo AFORE",
                line=dict(color="#1976D2", width=2),
                fill="tozeroy",
                fillcolor="rgba(25, 118, 210, 0.1)",
            )
        )
        fig_proy.update_layout(
            title=f"Proyección de saldo AFORE (rendimiento {rendimiento}% real)",
            xaxis_title="Edad",
            yaxis_title="Saldo (MXN)",
            hovermode="x unified",
        )
        st.plotly_chart(fig_proy, use_container_width=True)

        # Comparison table
        comp_df = pd.DataFrame([
            {
                "Modalidad": "Renta vitalicia",
                "Pensión mensual": float(comparacion["renta_vitalicia"]["pension_mensual"]),
                "Pensión anual": float(comparacion["renta_vitalicia"]["pension_anual"]),
                "Característica": comparacion["renta_vitalicia"]["tipo"],
            },
            {
                "Modalidad": "Retiro programado",
                "Pensión mensual": float(comparacion["retiro_programado"]["pension_mensual"]),
                "Pensión anual": float(comparacion["retiro_programado"]["pension_anual"]),
                "Característica": comparacion["retiro_programado"]["tipo"],
            },
        ])
        st.dataframe(
            comp_df.style.format({
                "Pensión mensual": "${:,.2f}",
                "Pensión anual": "${:,.2f}",
            }),
            use_container_width=True,
            hide_index=True,
        )

        with st.expander("Ver código Python"):
            st.code(
                f'''from decimal import Decimal
from suite_actuarial import TablaMortalidad
from suite_actuarial.pensiones import PensionLey97

tabla = TablaMortalidad.cargar_emssa09()

pension = PensionLey97(
    saldo_afore=Decimal("{saldo_afore}"),
    edad={edad_retiro_97},
    sexo="H",
    semanas_cotizadas={semanas_97},
    tabla_mortalidad=tabla,
)

# Proyeccion de saldo AFORE
proyeccion = pension.proyectar_saldo_afore(
    salario_actual=Decimal("{salario_actual}"),
    rendimiento_anual=Decimal("{rendimiento / 100}"),
    anos_restantes={anos_restantes},
)
for row in proyeccion:
    print(f"Edad {{row['edad']}}: saldo ${{row['saldo_afore']:,.2f}}")

# Comparar modalidades
comparacion = pension.comparar_modalidades()
print(f"\\nRenta vitalicia: ${{comparacion['renta_vitalicia']['pension_mensual']:,.2f}} / mes")
print(f"Retiro programado: ${{comparacion['retiro_programado']['pension_mensual']:,.2f}} / mes")
print(f"Recomendacion: {{comparacion['recomendacion']}}")
''',
                language="python",
            )


# ===== TAB 2: Renta Vitalicia =====
with tab_rv:
    st.subheader("Renta vitalicia")
    st.markdown(
        "Calcula la prima única para comprar una renta vitalicia y genera "
        "la tabla de pagos proyectados con probabilidades de supervivencia."
    )

    rv1, rv2 = st.columns(2)
    with rv1:
        edad_rv = st.slider("Edad del rentista", 55, 90, 65, key="rv_edad")
        sexo_rv = st.radio(
            "Sexo",
            ["Hombre", "Mujer"],
            horizontal=True,
            key="rv_sexo",
        )
        sexo_rv_code = "H" if sexo_rv == "Hombre" else "M"
    with rv2:
        monto_mensual_rv = st.number_input(
            "Monto mensual deseado (MXN)",
            min_value=1_000,
            max_value=200_000,
            value=15_000,
            step=1_000,
            format="%d",
        )
        tasa_rv = st.slider(
            "Tasa de interés técnico (%)",
            min_value=2.0,
            max_value=8.0,
            value=4.0,
            step=0.25,
            key="rv_tasa",
        )

    rv = RentaVitalicia(
        edad=edad_rv,
        sexo=sexo_rv_code,
        monto_mensual=Decimal(str(monto_mensual_rv)),
        tabla_mortalidad=tabla_mortalidad,
        tasa_interes=Decimal(str(tasa_rv / 100)),
    )

    prima_unica = rv.calcular_prima_unica()
    factor_renta = rv.calcular_factor_renta()

    pu1, pu2 = st.columns(2)
    pu1.metric("Prima única", f"${float(prima_unica):,.2f}")
    pu2.metric("Factor de renta", f"{float(factor_renta):,.4f}")

    # Payment projection
    @st.cache_data(show_spinner="Generando tabla de pagos...")
    def _tabla_pagos(e, s, m, t, _tn):
        _rv = RentaVitalicia(
            edad=e, sexo=s,
            monto_mensual=Decimal(str(m)),
            tabla_mortalidad=tabla_mortalidad,
            tasa_interes=Decimal(str(t)),
        )
        return _rv.tabla_pagos(anos=35)

    pagos = _tabla_pagos(edad_rv, sexo_rv_code, monto_mensual_rv, tasa_rv / 100, tabla_mortalidad.nombre)
    df_pagos = pd.DataFrame(pagos)
    df_pagos["pago_anual"] = df_pagos["pago_anual"].apply(float)
    df_pagos["pago_esperado"] = df_pagos["pago_esperado"].apply(float)
    df_pagos["reserva"] = df_pagos["reserva"].apply(float)
    df_pagos["prob_supervivencia"] = df_pagos["prob_supervivencia"].apply(float)

    # Chart: pagos + reserva
    fig_rv = go.Figure()
    fig_rv.add_trace(
        go.Bar(
            x=df_pagos["edad"],
            y=df_pagos["pago_esperado"],
            name="Pago esperado",
            marker_color="#4CAF50",
        )
    )
    fig_rv.add_trace(
        go.Scatter(
            x=df_pagos["edad"],
            y=df_pagos["reserva"],
            mode="lines",
            name="Reserva matemática",
            line=dict(color="#E91E63", width=2),
            yaxis="y2",
        )
    )
    fig_rv.update_layout(
        title="Pagos esperados y reserva por edad",
        xaxis_title="Edad",
        yaxis=dict(title="Pago esperado (MXN)", side="left"),
        yaxis2=dict(title="Reserva (MXN)", side="right", overlaying="y"),
        hovermode="x unified",
        legend=dict(x=0.7, y=1),
    )
    st.plotly_chart(fig_rv, use_container_width=True)

    with st.expander("Tabla completa de pagos"):
        st.dataframe(
            df_pagos[["ano", "edad", "pago_anual", "prob_supervivencia", "pago_esperado", "reserva"]].rename(
                columns={
                    "ano": "Año",
                    "edad": "Edad",
                    "pago_anual": "Pago anual",
                    "prob_supervivencia": "P(supervivencia)",
                    "pago_esperado": "Pago esperado",
                    "reserva": "Reserva",
                }
            ).style.format({
                "Pago anual": "${:,.2f}",
                "P(supervivencia)": "{:.4f}",
                "Pago esperado": "${:,.2f}",
                "Reserva": "${:,.2f}",
            }),
            use_container_width=True,
            hide_index=True,
        )

    with st.expander("Ver código Python"):
        st.code(
            f'''from decimal import Decimal
from suite_actuarial import TablaMortalidad
from suite_actuarial.pensiones import RentaVitalicia

tabla = TablaMortalidad.cargar_emssa09()

rv = RentaVitalicia(
    edad={edad_rv},
    sexo="{sexo_rv_code}",
    monto_mensual=Decimal("{monto_mensual_rv}"),
    tabla_mortalidad=tabla,
    tasa_interes=Decimal("{tasa_rv / 100}"),
)

print(f"Prima unica: ${{rv.calcular_prima_unica():,.2f}}")
print(f"Factor de renta: {{rv.calcular_factor_renta():.4f}}")

# Tabla de pagos proyectados
pagos = rv.tabla_pagos(anos=35)
for p in pagos[:10]:
    print(
        f"Edad {{p['edad']}}: pago ${{p['pago_anual']:,.2f}}, "
        f"prob surv {{p['prob_supervivencia']:.4f}}, "
        f"reserva ${{p['reserva']:,.2f}}"
    )
''',
            language="python",
        )


# ===== TAB 3: Funciones de Conmutacion =====
with tab_conm:
    st.subheader("Funciones de conmutación")
    st.markdown(
        "Tabla clásica (Bowers et al.) basada en la mortalidad EMSSA-09. "
        "Dx, Nx, Sx, Cx, Mx, Rx para un sexo y tasa de interés dados."
    )

    tc1, tc2, tc3 = st.columns(3)
    with tc1:
        sexo_tc = st.radio(
            "Sexo",
            ["Hombre", "Mujer"],
            horizontal=True,
            key="tc_sexo",
        )
        sexo_tc_code = "H" if sexo_tc == "Hombre" else "M"
    with tc2:
        tasa_tc = st.slider(
            "Tasa de interés (%)",
            min_value=1.0,
            max_value=10.0,
            value=5.0,
            step=0.25,
            key="tc_tasa",
        )
    with tc3:
        edad_desde = st.slider("Edad desde", 0, 90, 20, key="tc_desde")
        edad_hasta = st.slider("Edad hasta", edad_desde + 1, 110, min(edad_desde + 30, 100), key="tc_hasta")

    @st.cache_data(show_spinner="Construyendo tabla de conmutación...")
    def _build_tc(sexo_code, tasa, _tn):
        tc = TablaConmutacion(
            tabla_mortalidad=tabla_mortalidad,
            sexo=sexo_code,
            tasa_interes=tasa,
        )
        return tc

    tc = _build_tc(sexo_tc_code, tasa_tc / 100, tabla_mortalidad.nombre)

    # Build values table
    filas = []
    for x in range(edad_desde, edad_hasta + 1):
        try:
            filas.append({
                "Edad": x,
                "Dx": float(tc.Dx(x)),
                "Nx": float(tc.Nx(x)),
                "Cx": float(tc.Cx(x)),
                "Mx": float(tc.Mx(x)),
            })
        except ValueError:
            break

    df_tc = pd.DataFrame(filas)

    st.dataframe(
        df_tc.style.format({
            "Dx": "{:,.4f}",
            "Nx": "{:,.4f}",
            "Cx": "{:,.4f}",
            "Mx": "{:,.4f}",
        }),
        use_container_width=True,
        hide_index=True,
    )

    # Chart: Dx and Nx
    fig_tc = go.Figure()
    fig_tc.add_trace(
        go.Scatter(
            x=df_tc["Edad"],
            y=df_tc["Dx"],
            mode="lines",
            name="Dx",
            line=dict(color="#1976D2", width=2),
        )
    )
    fig_tc.add_trace(
        go.Scatter(
            x=df_tc["Edad"],
            y=df_tc["Nx"],
            mode="lines",
            name="Nx",
            line=dict(color="#E91E63", width=2),
            yaxis="y2",
        )
    )
    fig_tc.update_layout(
        title=f"Funciones Dx y Nx ({sexo_tc}, tasa {tasa_tc}%)",
        xaxis_title="Edad",
        yaxis=dict(title="Dx", side="left"),
        yaxis2=dict(title="Nx", side="right", overlaying="y"),
        hovermode="x unified",
        legend=dict(x=0.8, y=1),
    )
    st.plotly_chart(fig_tc, use_container_width=True)

    with st.expander("Ver código Python"):
        st.code(
            f'''from suite_actuarial import TablaMortalidad
from suite_actuarial.pensiones import TablaConmutacion

tabla = TablaMortalidad.cargar_emssa09()

tc = TablaConmutacion(
    tabla_mortalidad=tabla,
    sexo="{sexo_tc_code}",
    tasa_interes={tasa_tc / 100},
)

# Consultar valores para un rango de edades
for x in range({edad_desde}, {edad_hasta + 1}):
    print(
        f"Edad {{x:>3d}}: "
        f"Dx={{float(tc.Dx(x)):>12,.4f}}  "
        f"Nx={{float(tc.Nx(x)):>14,.4f}}  "
        f"Cx={{float(tc.Cx(x)):>10,.4f}}  "
        f"Mx={{float(tc.Mx(x)):>12,.4f}}"
    )

# Valores actuariales derivados
print(f"\\nAnualidad vitalicia ax(65): {{tc.ax(65):.4f}}")
print(f"Seguro vida completa Ax(65): {{tc.Ax(65):.4f}}")
print(f"Dotal puro 10E65: {{tc.nEx(65, 10):.4f}}")
print(f"Prima nivelada Px(65): {{tc.Px(65):.6f}}")
''',
            language="python",
        )
