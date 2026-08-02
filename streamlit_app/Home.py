"""
suite_actuarial -- Demo de la librería actuarial para México.

Página principal: visión general de la librería, dominios y módulos.
"""

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "streamlit_app"))

from utils.theme import apply_studio_theme, render_workbench_intro

st.set_page_config(
    page_title="suite_actuarial -- Analyst Sandbox",
    layout="wide",
)

apply_studio_theme()

# -----------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------
with st.sidebar:
    st.header("Configuración")

    anio_config = st.selectbox(
        "Año regulatorio",
        options=[2024, 2025, 2026],
        index=2,
        help="Año de parámetros regulatorios (UMA, pensión garantizada, etc.)",
    )

    st.markdown("---")
    st.markdown("**Versión:** 2.1.0")
    st.markdown("**Autor:** Andrés González Ortega")
    st.markdown("**Licencia:** MIT")

    st.markdown("---")
    st.subheader("Instalación")
    st.code(
        "pip install suite-actuarial",
        language="bash",
    )
    st.caption("O bien clona el repositorio y usa:\n`pip install -e ./src`")

# -----------------------------------------------------------------------
# Titulo
# -----------------------------------------------------------------------
render_workbench_intro(
    "BANCO DE TRABAJO · MÉXICO",
    "Construye, prueba y entiende modelos actuariales",
    "Espacio de exploración libre para mover supuestos, comparar métodos y revisar "
    "evidencia. El recorrido guiado principal está en la plataforma web; esta "
    "interfaz está pensada para análisis rápidos y densos.",
)

st.markdown(
    '<div class="studio-note"><strong>Método común:</strong> propósito → beneficios '
    "→ supuestos → cálculo → sensibilidad → validación. Los modelos ilustrativos no "
    "sustituyen métodos registrados ni revisión actuarial independiente.</div>",
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------
# 4 domain cards (2 x 2)
# -----------------------------------------------------------------------
st.markdown("---")
st.header("Biblioteca de preguntas actuariales")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Vida")
    st.markdown(
        """
- **3 productos**: Temporal, Ordinario, Dotal
- Mortalidad **EMSSA-09** (versión simplificada e ilustrativa)
- Primas netas y comerciales con desglose de recargos
- Reservas matemáticas prospectivas por año de póliza
"""
    )

with col2:
    st.subheader("Daños")
    st.markdown(
        """
- Seguro de **auto**: estructura tarifaria por grupo, zona y factores (tasas ilustrativas)
- Modelo colectivo **frecuencia-severidad** (Monte Carlo)
- Sistema **Bonus-Malus** escala mexicana
- **Credibilidad** de Bühlmann y Bühlmann-Straub
"""
    )

col3, col4 = st.columns(2)

with col3:
    st.subheader("Salud")
    st.markdown(
        """
- **Gastos Médicos Mayores** (GMM): prima por banda de edad, zona, nivel
- Simulador deducible / coaseguro / tope
- **Accidentes y Enfermedades** (A&E)
- Bandas quinquenales de tarificación
"""
    )

with col4:
    st.subheader("Pensiones")
    st.markdown(
        """
- Pensión **IMSS Ley 73**: beneficio definido, tabla Art. 167
- Pensión **IMSS Ley 97**: contribución definida, AFORE
- **Renta vitalicia**: inmediata, diferida, con periodo cierto
- **Funciones de conmutación**: Dx, Nx, Cx, Mx (Bowers et al.)
"""
    )

# -----------------------------------------------------------------------
# Cross-cutting modules
# -----------------------------------------------------------------------
st.markdown("---")
st.header("Módulos transversales")

m1, m2, m3 = st.columns(3)

with m1:
    st.subheader("Reservas")
    st.markdown(
        """
- Chain Ladder (triángulos de desarrollo)
- Bornhuetter-Ferguson
- Bootstrap ODP (England-Verrall) y error de predicción de Mack (1993)
"""
    )

with m2:
    st.subheader("Reaseguro")
    st.markdown(
        """
- Cuota parte (Quota Share)
- Exceso de pérdida (Excess of Loss)
- Stop Loss
"""
    )

with m3:
    st.subheader("Regulatorio")
    st.markdown(
        """
- Escenarios de referencia RCS (Capital de Solvencia)
- Estructuras de datos para reportes; no XML oficial CNSF
- Validaciones de referencia SAT / ISR
- Referencias de reservas técnicas S-11.4
"""
    )

# -----------------------------------------------------------------------
# Quick example
# -----------------------------------------------------------------------
st.markdown("---")
st.header("Código reproducible")

st.code(
    """from suite_actuarial import (
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
asegurado = Asegurado(edad=35, sexo="masculino", suma_asegurada=Decimal("1000000"))
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
    edad=40, sexo="masculino",
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
""",
    language="python",
)

# -----------------------------------------------------------------------
# Footer
# -----------------------------------------------------------------------
st.markdown("---")
st.markdown(
    """
<div style="text-align: center; color: #666;">
    <p><strong>Nota de alcance:</strong> Esta librería es para propósitos educativos,
    de referencia y de análisis profesional. Los modelos simplificados y los datos
    ilustrativos no sustituyen métodos registrados, asesoría fiscal ni determinaciones
    oficiales de CNSF, SAT o IMSS. Valida los resultados con un actuario certificado
    antes de usarlos en producción.</p>
    <p>suite_actuarial v2.1.0 | MIT License</p>
</div>
""",
    unsafe_allow_html=True,
)
