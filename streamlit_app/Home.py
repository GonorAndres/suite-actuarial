"""
Dashboard Principal - Mexican Insurance Analytics Suite

Página principal de la suite de herramientas actuariales para el mercado
asegurador mexicano.
"""

import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Mexican Insurance Analytics Suite",
    page_icon="H",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Título principal
st.title("Mexican Insurance Analytics Suite")
st.markdown("### Suite de Herramientas Actuariales para el Mercado Mexicano")

# Bienvenida
st.markdown("""
Bienvenido a la **Mexican Insurance Analytics Suite**, un conjunto de herramientas
en Python para análisis actuarial, cálculo de primas, reservas técnicas y cumplimiento
regulatorio para el mercado de seguros en México.
""")

# Columnas para estadísticas del proyecto
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Productos de Vida",
        value="3",
        delta="Temporal, Ordinario, Dotal",
    )

with col2:
    st.metric(
        label="Estrategias de Reaseguro",
        value="3",
        delta="QS, XoL, Stop Loss",
    )

with col3:
    st.metric(
        label="Métodos de Reservas",
        value="3",
        delta="Chain Ladder, B-F, Bootstrap",
    )

with col4:
    st.metric(
        label="Módulos Regulatorios",
        value="4",
        delta="RCS, CNSF, S-11.4, SAT",
    )

# Sección de información
st.markdown("---")
st.header("Dashboards Disponibles")

# Crear tres columnas para los dashboards
dash_col1, dash_col2, dash_col3 = st.columns(3)

with dash_col1:
    st.markdown("""
    ### Productos de Vida

    Calculadora interactiva de productos de seguros de vida:
    - **Vida Temporal**: Protección por plazo definido
    - **Vida Ordinario**: Protección vitalicia o pago limitado
    - **Vida Dotal**: Ahorro + protección

    **Características:**
    - Cálculo de primas netas y comerciales
    - Comparación entre productos
    - Análisis de sensibilidad
    - Visualización de reservas matemáticas
    """)

with dash_col2:
    st.markdown("""
    ### Cumplimiento Regulatorio

    Monitor de cumplimiento normativo mexicano:
    - **RCS**: Requerimientos de Capital de Solvencia
    - **CNSF**: Reportes trimestrales automatizados
    - **SAT**: Validaciones fiscales ISR
    - **S-11.4**: Reservas técnicas normativas

    **Características:**
    - Calculadoras de indicadores
    - Validación de deducibilidad
    - Reportes automatizados
    """)

with dash_col3:
    st.markdown("""
    ### Reservas Técnicas

    Análisis avanzado de reservas para siniestros:
    - **Chain Ladder**: Método clásico de triángulos
    - **Bornhuetter-Ferguson**: Combinación datos/esperados
    - **Bootstrap**: Estimación de incertidumbre

    **Características:**
    - Triángulos de desarrollo
    - Proyecciones de reservas
    - Comparación de métodos
    - Intervalos de confianza
    """)

# Información técnica
st.markdown("---")
st.header("Información Técnica")

tech_col1, tech_col2 = st.columns(2)

with tech_col1:
    st.markdown("""
    #### Tecnologías Utilizadas
    - **Python 3.11+**: Lenguaje base
    - **Pydantic**: Validación de datos
    - **Decimal**: Precisión financiera
    - **Pytest**: Suite de testing (>90% cobertura)
    - **Streamlit**: Dashboards interactivos
    - **Plotly**: Visualizaciones interactivas
    """)

with tech_col2:
    st.markdown("""
    #### Fundamentos Regulatorios
    - **CNSF**: Circular Única de Seguros y Fianzas
    - **LISR**: Ley del Impuesto Sobre la Renta
    - **Circular S-11.4**: Reservas técnicas
    - **Solvencia II adaptado**: RCS mexicano
    - **EMSSA-09**: Tablas de mortalidad
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <p><strong>Nota Legal:</strong> Esta librería es para propósitos educativos y de análisis.
    Para uso en producción en una aseguradora, valida los resultados con un actuario certificado
    y asegúrate de cumplir con todas las regulaciones de la CNSF.</p>
    <p>Para preguntas o reportar bugs, abre un issue en GitHub.</p>
    <p>Mexican Insurance Analytics Suite | MIT License</p>
</div>
""", unsafe_allow_html=True)

# Sidebar con información adicional
with st.sidebar:
    st.header("Inicio Rápido")

    st.markdown("""
    **Navega usando el menú lateral:**

    1. **Productos de Vida**: Calcula primas y compara productos
    2. **Cumplimiento**: Valida requisitos regulatorios
    3. **Reservas**: Analiza reservas técnicas
    """)

    st.markdown("---")

    st.header("Recursos")

    st.markdown("""
    - [Documentación](../docs/JOURNAL.md)
    - [Resumen Ejecutivo](../docs/resumen_ejecutivo.html)
    - [GitHub](https://github.com/GonorAndres/Analisis_Seguros_Mexico)
    """)

    st.markdown("---")

    st.markdown("""
    **Versión:** 1.0.0

    **Fases Completadas:**
    - [OK] Fase 1: Fundamentos
    - [OK] Fase 2: Productos
    - [OK] Fase 3: Reaseguro
    - [OK] Fase 4: Reservas
    - [OK] Fase 5A-D: Regulatorio
    - Fase 6: Dashboards
    """)
