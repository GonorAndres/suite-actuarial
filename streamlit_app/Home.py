"""
suite_actuarial -- Demo de la libreria actuarial para Mexico.

Pagina principal: vision general de la libreria, dominios y modulos.
"""

import streamlit as st

st.set_page_config(
    page_title="suite_actuarial -- Libreria Actuarial",
    layout="wide",
)

# -----------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------
with st.sidebar:
    st.header("Configuracion")

    anio_config = st.selectbox(
        "Ano regulatorio",
        options=[2024, 2025, 2026],
        index=2,
        help="Ano de parametros regulatorios (UMA, pension garantizada, etc.)",
    )

    st.markdown("---")
    st.markdown("**Version:** 2.0.0")
    st.markdown("**Autor:** Andres Gonzalez Ortega")
    st.markdown("**Licencia:** MIT")

    st.markdown("---")
    st.subheader("Instalacion")
    st.code(
        "pip install suite-actuarial",
        language="bash",
    )
    st.caption(
        "O bien clona el repositorio y usa:\n"
        "`pip install -e ./src`"
    )

# -----------------------------------------------------------------------
# Titulo
# -----------------------------------------------------------------------
st.title("suite_actuarial -- Libreria Actuarial para Mexico")

st.markdown(
    """
**suite_actuarial** es una libreria en Python que implementa modelos actuariales
completos para el mercado asegurador mexicano. Cubre las cuatro ramas principales
de seguros, mas modulos transversales de reservas, reaseguro y cumplimiento regulatorio.

Esta aplicacion es una **demo interactiva** de la libreria. Cada pagina muestra
los resultados de la API en vivo junto con el codigo Python necesario para
reproducirlos en tu propio proyecto.
"""
)

# -----------------------------------------------------------------------
# 4 domain cards (2 x 2)
# -----------------------------------------------------------------------
st.markdown("---")
st.header("Dominios de seguros")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Vida")
    st.markdown(
        """
- **3 productos**: Temporal, Ordinario, Dotal
- Mortalidad **EMSSA-09** (tabla oficial mexicana)
- Primas netas y comerciales con desglose de recargos
- Reservas matematicas prospectivas por ano de poliza
"""
    )

with col2:
    st.subheader("Danos")
    st.markdown(
        """
- Seguro de **auto** con tarificacion AMIS (grupos, zonas, factores)
- Modelo colectivo **frecuencia-severidad** (Monte Carlo)
- Sistema **Bonus-Malus** escala mexicana
- **Credibilidad** de Buhlmann y Buhlmann-Straub
"""
    )

col3, col4 = st.columns(2)

with col3:
    st.subheader("Salud")
    st.markdown(
        """
- **Gastos Medicos Mayores** (GMM): prima por banda de edad, zona, nivel
- Simulador deducible / coaseguro / tope
- **Accidentes y Enfermedades** (A&E)
- Bandas quinquenales de tarificacion
"""
    )

with col4:
    st.subheader("Pensiones")
    st.markdown(
        """
- Pension **IMSS Ley 73**: beneficio definido, tabla Art. 167
- Pension **IMSS Ley 97**: contribucion definida, AFORE
- **Renta vitalicia**: inmediata, diferida, con periodo cierto
- **Funciones de conmutacion**: Dx, Nx, Cx, Mx (Bowers et al.)
"""
    )

# -----------------------------------------------------------------------
# Cross-cutting modules
# -----------------------------------------------------------------------
st.markdown("---")
st.header("Modulos transversales")

m1, m2, m3 = st.columns(3)

with m1:
    st.subheader("Reservas")
    st.markdown(
        """
- Chain Ladder (triangulos de desarrollo)
- Bornhuetter-Ferguson
- Bootstrap con intervalos de confianza
"""
    )

with m2:
    st.subheader("Reaseguro")
    st.markdown(
        """
- Cuota parte (Quota Share)
- Exceso de perdida (Excess of Loss)
- Stop Loss
"""
    )

with m3:
    st.subheader("Regulatorio")
    st.markdown(
        """
- RCS (Capital de Solvencia)
- Reportes CNSF trimestrales
- Validaciones fiscales SAT / ISR
- Reservas tecnicas S-11.4
"""
    )

# -----------------------------------------------------------------------
# Quick example
# -----------------------------------------------------------------------
st.markdown("---")
st.header("Ejemplo rapido")

st.code(
    '''from suite_actuarial import (
    VidaTemporal, SeguroAuto, GMM, RentaVitalicia,
    TablaConmutacion, TablaMortalidad,
    Asegurado, ConfiguracionProducto,
    cargar_config,
)
from suite_actuarial.danos import ModeloColectivo, CalculadoraBonusMalus
from suite_actuarial.pensiones import PensionLey73, PensionLey97
from decimal import Decimal

# --- Vida: prima de un temporal 20 anos ---
tabla = TablaMortalidad.cargar_emssa09()
config = ConfiguracionProducto(
    nombre_producto="Temporal 20",
    plazo_years=20,
    tasa_interes_tecnico=Decimal("0.05"),
)
producto = VidaTemporal(config, tabla)
asegurado = Asegurado(edad=35, sexo="H", suma_asegurada=Decimal("1000000"))
resultado = producto.calcular_prima(asegurado, frecuencia_pago="mensual")
print(f"Prima mensual: ${resultado.prima_total:,.2f}")

# --- Danos: cotizacion de auto ---
auto = SeguroAuto(
    valor_vehiculo=Decimal("400000"),
    tipo_vehiculo="sedan_mediano",
    antiguedad_anos=2,
    zona="guadalajara",
    edad_conductor=35,
)
cotizacion = auto.generar_cotizacion()
print(f"Prima total auto: ${cotizacion['prima_total']:,.2f}")

# --- Salud: prima GMM ---
from suite_actuarial.salud import GMM, ZonaGeografica, NivelHospitalario
gmm = GMM(
    edad=40, sexo="M",
    suma_asegurada=Decimal("5000000"),
    deducible=Decimal("50000"),
    coaseguro_pct=Decimal("0.10"),
    zona=ZonaGeografica.METRO,
    nivel=NivelHospitalario.ALTO,
)
print(f"Prima GMM: ${gmm.calcular_prima_ajustada():,.2f}")

# --- Pensiones: Ley 73 ---
pension = PensionLey73(
    semanas_cotizadas=1200,
    salario_promedio_5_anos=Decimal("800"),
    edad_retiro=65,
)
print(f"Pension mensual: ${pension.calcular_pension_mensual():,.2f}")
''',
    language="python",
)

# -----------------------------------------------------------------------
# Footer
# -----------------------------------------------------------------------
st.markdown("---")
st.markdown(
    """
<div style="text-align: center; color: #666;">
    <p><strong>Nota legal:</strong> Esta libreria es para propositos educativos y de analisis.
    Para uso en produccion, valida los resultados con un actuario certificado
    y verifica el cumplimiento con las regulaciones vigentes de la CNSF.</p>
    <p>suite_actuarial v2.0.0 | MIT License</p>
</div>
""",
    unsafe_allow_html=True,
)
