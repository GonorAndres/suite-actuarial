# Mexican Insurance Analytics Suite - Streamlit Dashboards

Dashboard interactivo para análisis actuarial del mercado asegurador mexicano.

## 🚀 Inicio Rápido

### 1. Instalar Dependencias

Desde el directorio raíz del proyecto:

```bash
# Instalar el paquete principal en modo desarrollo
pip install -e .

# Instalar dependencias de Streamlit
cd streamlit_app
pip install -r requirements.txt
```

### 2. Ejecutar el Dashboard

```bash
# Desde streamlit_app/
streamlit run Home.py
```

El dashboard se abrirá en tu navegador en `http://localhost:8501`

## 📊 Dashboards Disponibles

### 1. Productos de Vida 📊

Calculadora interactiva de seguros de vida con análisis completo:

- **Productos soportados:**
  - Vida Temporal (protección temporal)
  - Vida Ordinario (protección vitalicia)
  - Vida Dotal (ahorro + protección)

- **Características:**
  - Cálculo de primas netas y comerciales
  - Comparación entre productos
  - Análisis de sensibilidad (edad, tasa de interés)
  - Proyección de reservas matemáticas
  - Visualizaciones interactivas

### 2. Cumplimiento Regulatorio 📋

Monitor de cumplimiento normativo mexicano:

- **RCS (Solvencia):**
  - Cálculo de Requerimientos de Capital de Solvencia
  - Desglose por tipo de riesgo
  - Ratio de cobertura
  - Evaluación regulatoria

- **Reservas S-11.4:**
  - Reserva de Riesgos en Curso (RRC)
  - Reserva Matemática (RM)
  - Evolución durante vigencia
  - Cumplimiento Circular S-11.4

- **SAT - Validaciones Fiscales:**
  - Deducibilidad de primas (LISR)
  - Gravabilidad de siniestros
  - Cálculo de retenciones ISR
  - Fundamentos legales

### 3. Reservas Técnicas 📈

Análisis avanzado de reservas para siniestros:

- **Métodos implementados:**
  - **Chain Ladder:** Método clásico de factores de desarrollo
  - **Bornhuetter-Ferguson:** Combinación datos + expectativa
  - **Bootstrap:** Estimación de incertidumbre

- **Características:**
  - Triángulos de desarrollo interactivos
  - Proyecciones de reservas IBNR
  - Comparación entre métodos
  - Intervalos de confianza (Bootstrap)
  - Escenarios pre-configurados

## 🎯 Estructura de Archivos

```
streamlit_app/
├── Home.py                        # Página principal
├── pages/                         # Páginas del dashboard
│   ├── 1_📊_Productos_Vida.py    # Dashboard 1
│   ├── 2_📋_Cumplimiento.py      # Dashboard 2
│   └── 3_📈_Reservas.py          # Dashboard 3
├── utils/                         # Utilidades compartidas
│   ├── __init__.py
│   ├── calculations.py           # Funciones de cálculo
│   └── visualizations.py         # Gráficos reutilizables
├── .streamlit/                    # Configuración
│   └── config.toml               # Tema y settings
├── requirements.txt               # Dependencias
└── README.md                      # Esta documentación
```

## ⚙️ Configuración

### Tema y Apariencia

El tema se configura en `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#1f77b4"      # Color primario
backgroundColor = "#ffffff"    # Fondo
secondaryBackgroundColor = "#f0f2f6"  # Fondo secundario
textColor = "#262730"         # Texto
font = "sans serif"           # Fuente
```

### Puerto y Servidor

Por defecto, Streamlit corre en `localhost:8501`. Para cambiar:

```bash
streamlit run Home.py --server.port 8080
```

## 📚 Uso de los Dashboards

### Dashboard 1: Productos de Vida

1. Ajusta los parámetros en el sidebar:
   - Edad del asegurado
   - Sexo
   - Suma asegurada
   - Tipo de producto
   - Plazo (para Temporal/Dotal)
   - Tasa de interés técnico

2. Explora las tabs:
   - **Cotización:** Cálculo detallado de prima
   - **Comparación:** Compara los 3 productos
   - **Sensibilidad:** Analiza impacto de edad y tasa
   - **Reservas:** Proyección de reservas matemáticas

### Dashboard 2: Cumplimiento

1. **Tab RCS:**
   - Ingresa datos de la aseguradora
   - Haz clic en "Calcular RCS"
   - Revisa ratio de cobertura y semáforo

2. **Tab Reservas S-11.4:**
   - Ingresa datos de la póliza
   - Calcula RRC y RM
   - Visualiza evolución

3. **Tabs SAT:**
   - Valida deducibilidad de primas
   - Calcula retenciones ISR
   - Revisa fundamentos legales

### Dashboard 3: Reservas

1. Selecciona escenario de triángulo en sidebar
2. Configura parámetros (loss ratio, simulaciones Bootstrap)
3. Explora las tabs:
   - **Triángulo:** Visualiza datos de entrada
   - **Chain Ladder:** Método clásico
   - **Bornhuetter-Ferguson:** Método combinado
   - **Bootstrap:** Análisis de incertidumbre

## 🔧 Desarrollo

### Agregar Nueva Funcionalidad

1. **Nueva calculadora** → Agrega en `utils/calculations.py`
2. **Nueva visualización** → Agrega en `utils/visualizations.py`
3. **Nuevo dashboard** → Crea en `pages/` con nombre `N_emoji_Nombre.py`

### Caché de Datos

Usa decoradores de Streamlit para optimizar:

```python
@st.cache_data  # Para DataFrames, listas
def load_data():
    return pd.read_csv("data.csv")

@st.cache_resource  # Para modelos, conexiones
def load_model():
    return TablaMortalidad.cargar_emssa09()
```

### Session State

Para mantener estado entre interacciones:

```python
if "bootstrap_ejecutado" not in st.session_state:
    st.session_state["bootstrap_ejecutado"] = False

if st.button("Ejecutar"):
    st.session_state["bootstrap_ejecutado"] = True
```

## 📋 Requisitos del Sistema

- Python 3.11+
- 4GB RAM mínimo (8GB recomendado para Bootstrap con muchas simulaciones)
- Navegador moderno (Chrome, Firefox, Safari, Edge)

## 🐛 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'mexican_insurance'"

**Solución:** Instala el paquete principal:

```bash
cd /home/user/Analisis_Seguros_Mexico
pip install -e .
```

### Dashboard muy lento

**Soluciones:**
- Reduce número de simulaciones Bootstrap
- Usa `@st.cache_data` para cálculos costosos
- Cierra otras aplicaciones

### Gráficos no se muestran

**Solución:** Actualiza Plotly:

```bash
pip install --upgrade plotly
```

## 📖 Recursos

- [Documentación Streamlit](https://docs.streamlit.io)
- [Plotly Docs](https://plotly.com/python/)
- [Journal Técnico](../docs/JOURNAL.md) del proyecto
- [Resumen Ejecutivo](../docs/resumen_ejecutivo.html)

## 🤝 Contribuir

Para agregar nuevos dashboards o features:

1. Crea nueva página en `pages/`
2. Sigue la estructura de tabs existente
3. Usa utilidades de `utils/` para consistencia
4. Documenta nuevos parámetros
5. Agrega tests si aplica

## 📝 Notas

- Los cálculos usan tabla de mortalidad EMSSA-09
- Tasas y parámetros son configurables
- Resultados son indicativos, validar con actuario certificado para producción
- Cumple normativa CNSF vigente a la fecha de desarrollo

## 📄 Licencia

MIT License - ver archivo [LICENSE](../LICENSE)

---

**Mexican Insurance Analytics Suite** | Análisis Actuarial para el Mercado Mexicano
