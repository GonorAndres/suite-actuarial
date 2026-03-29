"""
suite_actuarial -- Demo de la librería actuarial para México.

Página principal: visión general de la librería, dominios y módulos.
"""

import streamlit as st

st.set_page_config(
    page_title="suite_actuarial -- Librería Actuarial",
    layout="wide",
)

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
    st.markdown("**Versión:** 2.0.0")
    st.markdown("**Autor:** Andrés González Ortega")
    st.markdown("**Licencia:** MIT")

    st.markdown("---")
    st.subheader("Instalación")
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
st.title("suite_actuarial -- Librería Actuarial para México")

st.markdown(
    """
**suite_actuarial** es una librería en Python que implementa modelos actuariales
completos para el mercado asegurador mexicano. Cubre las cuatro ramas principales
de seguros, más módulos transversales de reservas, reaseguro y cumplimiento regulatorio.

Esta aplicación es una **demo interactiva** de la librería. Cada página muestra
los resultados de la API en vivo junto con el código Python necesario para
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
- Reservas matemáticas prospectivas por año de póliza
"""
    )

with col2:
    st.subheader("Daños")
    st.markdown(
        """
- Seguro de **auto** con tarificación AMIS (grupos, zonas, factores)
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
- Bootstrap con intervalos de confianza
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
- RCS (Capital de Solvencia)
- Reportes CNSF trimestrales
- Validaciones fiscales SAT / ISR
- Reservas técnicas S-11.4
"""
    )

# -----------------------------------------------------------------------
# Quick example
# -----------------------------------------------------------------------
st.markdown("---")
st.header("Ejemplo rápido")

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
    <p><strong>Nota legal:</strong> Esta librería es para propósitos educativos y de análisis.
    Para uso en producción, valida los resultados con un actuario certificado
    y verifica el cumplimiento con las regulaciones vigentes de la CNSF.</p>
    <p>suite_actuarial v2.0.0 | MIT License</p>
</div>
""",
    unsafe_allow_html=True,
)
