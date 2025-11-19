# Claude Code - Instrucciones y Contexto del Proyecto

> Documento de referencia con todas las instrucciones, condiciones y contexto utilizados en el desarrollo del proyecto Mexican Insurance Analytics Suite.

---

## REGLA CRÍTICA: NO USAR EMOJIS

**IMPORTANTE**: No usar emojis en ninguna comunicación con el usuario a menos que el usuario lo solicite explícitamente.

- No usar emojis en respuestas de texto
- No usar emojis en mensajes al usuario
- No usar emojis en archivos de código (a menos que sean parte del nombre del archivo como en Streamlit)
- No usar emojis en comentarios de código
- No usar emojis en commits
- No usar emojis en documentación

**Excepciones**:
- Nombres de archivos de Streamlit (ej: `1_📊_Productos_Vida.py`) - estos son requeridos por convención de Streamlit
- Cuando el usuario explícitamente pida usar emojis
- En archivos existentes que ya los contengan (no eliminarlos)

---

## Información General del Proyecto

### Proyecto
**Mexican Insurance Analytics Suite** - Suite de herramientas actuariales para el mercado asegurador mexicano

### Repositorio
- **Owner**: GonorAndres
- **Repo**: Analisis_Seguros_Mexico
- **Branch de desarrollo**: `claude/review-workflow-plan-01KdR8QXYSTdi9Fo6Fu7nPmd`
- **Directorio de trabajo**: `/home/user/Analisis_Seguros_Mexico`

### Estado del Proyecto
El proyecto ha completado las Fases 1-6:
- ✅ Fase 1: Fundamentos (tablas mortalidad, vida temporal)
- ✅ Fase 2: Expansión de Productos (Ordinario, Dotal)
- ✅ Fase 3: Reaseguro (Quota Share, XoL, Stop Loss)
- ✅ Fase 4: Reservas Avanzadas (Chain Ladder, B-F, Bootstrap)
- ✅ Fase 5: Cumplimiento Regulatorio (RCS, CNSF, SAT)
- ✅ Fase 6: Dashboards Interactivos (Streamlit)

---

## Condiciones y Requisitos Técnicos

### 1. Desarrollo en Branch Específico

**CRÍTICO**: Todo el desarrollo debe realizarse en el branch:
```
claude/review-workflow-plan-01KdR8QXYSTdi9Fo6Fu7nPmd
```

**Reglas del branch**:
- ✅ Desarrollar TODOS los cambios en este branch
- ✅ Hacer commit con mensajes descriptivos
- ✅ Push al branch específico con `-u origin <branch-name>`
- ❌ NUNCA push a otro branch sin permiso explícito
- ❌ NUNCA push a main/master directamente

**Validación del branch**:
- El branch DEBE empezar con `claude/` y terminar con el session ID
- Si el push falla con error 403, verificar que el nombre del branch sea correcto

### 2. Operaciones Git

#### Git Push
```bash
# Siempre usar -u origin <branch-name>
git push -u origin claude/review-workflow-plan-01KdR8QXYSTdi9Fo6Fu7nPmd

# Retry con exponential backoff si falla por red (2s, 4s, 8s, 16s)
# Máximo 4 intentos
```

#### Git Fetch/Pull
```bash
# Preferir fetch de branches específicos
git fetch origin <branch-name>

# Para pulls
git pull origin <branch-name>

# Retry con exponential backoff si falla (2s, 4s, 8s, 16s)
```

#### Git Commits

**NUNCA**:
- Actualizar git config
- Comandos destructivos (push --force, hard reset) sin permiso explícito
- Skip hooks (--no-verify, --no-gpg-sign) sin permiso
- Force push a main/master
- Commit sin permiso explícito del usuario

**Commits bien formados**:
```bash
git commit -m "$(cat <<'EOF'
tipo: Título corto descriptivo

Descripción detallada del cambio con:
- Bullets explicando qué se implementó
- Por qué se hizo
- Qué problema resuelve

Tecnologías: Lista de techs usadas
Referencias: #Tags #Relacionados
EOF
)"
```

**Tipos de commit válidos**:
- `feat`: Nueva funcionalidad
- `fix`: Corrección de bugs
- `docs`: Cambios en documentación
- `refactor`: Refactorización sin cambio funcional
- `test`: Añadir o modificar tests
- `chore`: Tareas de mantenimiento

### 3. GitHub CLI

**GitHub CLI (`gh`) NO está disponible**. Para GitHub issues:
- Pedir al usuario que proporcione información directamente
- No intentar usar comandos `gh`

---

## Stack Tecnológico

### Backend (Python 3.11+)
- **Pydantic**: Validación de modelos
- **Decimal**: Precisión financiera
- **Pandas**: Manipulación de datos
- **NumPy**: Cálculos numéricos
- **Pytest**: Testing (>90% cobertura)

### Librerías Actuariales
- **chainladder**: Métodos de reservas
- **lifelines**: Análisis de supervivencia
- **scipy**: Funciones estadísticas

### Frontend (Streamlit)
- **Streamlit 1.51.0**: Framework de dashboards
- **Plotly 6.5.0**: Visualizaciones interactivas
- **Pandas**: Data manipulation

### Estructura del Paquete
```
src/mexican_insurance/
├── core/                    # Validadores base
├── actuarial/              # Tablas mortalidad, reservas
├── products/               # Productos de seguros
│   └── vida/              # Temporal, Ordinario, Dotal
├── reinsurance/           # Estrategias de reaseguro
└── regulatorio/           # Cumplimiento CNSF/SAT
    ├── rcs/              # Solvencia
    ├── reportes_cnsf/    # Reportes trimestrales
    ├── reservas_tecnicas/ # S-11.4
    └── validaciones_sat/  # Fiscales
```

---

## Estándares de Código

### 1. Arquitectura y Patrones

**Principios SOLID**:
- Single Responsibility: Cada clase una responsabilidad
- Open/Closed: Abierto a extensión, cerrado a modificación
- Liskov Substitution: Subtipos intercambiables
- Interface Segregation: Interfaces específicas
- Dependency Inversion: Depender de abstracciones

**Patrones Utilizados**:
- **Strategy Pattern**: Para métodos de reservas (Chain Ladder, B-F, Bootstrap)
- **Factory Pattern**: Para creación de productos de seguros
- **Composition over Inheritance**: Preferir composición

### 2. Validación con Pydantic

Todos los modelos DEBEN usar Pydantic:
```python
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal

class Asegurado(BaseModel):
    edad: int = Field(ge=18, le=100)
    sexo: Sexo
    suma_asegurada: Decimal = Field(gt=0)

    @field_validator('suma_asegurada')
    @classmethod
    def validar_suma_minima(cls, v: Decimal) -> Decimal:
        if v < Decimal('10000'):
            raise ValueError("Suma mínima: $10,000")
        return v
```

### 3. Precisión Financiera

**SIEMPRE usar `Decimal` para cálculos financieros**:
```python
from decimal import Decimal, ROUND_HALF_UP

# ✅ CORRECTO
prima = Decimal('1234.56')
tasa = Decimal('0.055')

# ❌ INCORRECTO
prima = 1234.56  # float - pérdida de precisión
```

### 4. Documentación

**Docstrings obligatorios**:
```python
def calcular_prima(
    self,
    asegurado: Asegurado,
    frecuencia_pago: str = "anual",
) -> ResultadoPrima:
    """
    Calcula la prima para un asegurado según configuración.

    Args:
        asegurado: Datos del asegurado validados
        frecuencia_pago: 'anual', 'mensual', 'trimestral'

    Returns:
        ResultadoPrima con prima neta, total y desglose

    Raises:
        ValueError: Si frecuencia no es válida

    Example:
        >>> producto.calcular_prima(asegurado, 'mensual')
        ResultadoPrima(prima_neta=Decimal('100.00'), ...)
    """
```

### 5. Testing

**Requisitos**:
- Cobertura > 90%
- Tests unitarios con pytest
- Tests de integración para flujos completos
- Fixtures para datos de prueba

```python
import pytest
from decimal import Decimal

@pytest.fixture
def asegurado_ejemplo():
    return Asegurado(
        edad=35,
        sexo=Sexo.HOMBRE,
        suma_asegurada=Decimal('1000000'),
    )

def test_calculo_prima(asegurado_ejemplo):
    """Test cálculo básico de prima."""
    # Arrange
    producto = VidaTemporal(config, tabla)

    # Act
    resultado = producto.calcular_prima(asegurado_ejemplo)

    # Assert
    assert resultado.prima_neta > 0
    assert resultado.prima_total > resultado.prima_neta
```

---

## Streamlit - Patrones y Mejores Prácticas

### 1. Estructura de Página

```python
import streamlit as st

# 1. Config (DEBE ser lo primero)
st.set_page_config(
    page_title="Título",
    page_icon="📊",
    layout="wide",
)

# 2. Imports del paquete
from mexican_insurance.products.vida.temporal import VidaTemporal

# 3. Caching
@st.cache_resource
def cargar_tabla():
    return TablaMortalidad.cargar_emssa09()

# 4. Sidebar
with st.sidebar:
    edad = st.slider("Edad", 18, 80, 35)

# 5. Main content
st.title("Título Principal")

# 6. Tabs
tab1, tab2 = st.tabs(["Tab 1", "Tab 2"])
with tab1:
    st.write("Contenido")
```

### 2. Caching Estratégico

```python
# Para datos (DataFrames, listas, dicts)
@st.cache_data
def load_data():
    return pd.read_csv("data.csv")

# Para recursos (modelos, conexiones, objetos complejos)
@st.cache_resource
def load_model():
    return TablaMortalidad.cargar_emssa09()
```

### 3. Session State

```python
# Inicializar
if "ejecutado" not in st.session_state:
    st.session_state["ejecutado"] = False

# Usar
if st.button("Ejecutar"):
    st.session_state["ejecutado"] = True
    st.rerun()
```

### 4. Layout Responsive

```python
# Columnas
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Métrica", "$1,000")

# Tabs
tab1, tab2 = st.tabs(["📊 Análisis", "📋 Detalle"])

# Expanders
with st.expander("Ver detalles"):
    st.dataframe(df)
```

---

## Normativa y Fundamentos Regulatorios

### CNSF (Comisión Nacional de Seguros y Fianzas)

**Circular Única de Seguros y Fianzas**:
- **RCS**: Requerimientos de Capital de Solvencia (basado en Solvencia II)
- **Reportes Trimestrales**: Formatos RT-XX
- **S-11.4**: Reservas técnicas (RRC y RM)

**Cálculos RCS**:
- Riesgo de mercado (tasas, acciones, inmuebles)
- Riesgo de suscripción (mortalidad, longevidad, gastos)
- Riesgo de crédito
- Correlación entre riesgos

### SAT (Servicio de Administración Tributaria)

**LISR (Ley del Impuesto Sobre la Renta)**:
- Deducibilidad de primas
- Gravabilidad de siniestros
- Retenciones ISR

**Reglas**:
- Gastos Médicos: 100% deducible (PF)
- Pensiones: Hasta 5 UMAs anuales
- Retenciones: Según tipo de pago y persona

### Tablas de Mortalidad

**EMSSA-09**: Tabla oficial mexicana
- Separada por sexo (Hombre/Mujer)
- Edades 0-120 años
- Probabilidades de muerte qx
- Base para cálculos actuariales

---

## Workflow de Desarrollo

### 1. Planificación

Usar **TodoWrite** para tareas complejas:
```python
todos = [
    {
        "content": "Crear estructura de directorios",
        "activeForm": "Creando estructura de directorios",
        "status": "in_progress"
    },
    {
        "content": "Implementar Dashboard 1",
        "activeForm": "Implementando Dashboard 1",
        "status": "pending"
    }
]
```

**Reglas**:
- Marcar como `in_progress` ANTES de empezar
- Marcar como `completed` INMEDIATAMENTE al terminar
- Solo UNA tarea en `in_progress` a la vez

### 2. Implementación

**Orden de operaciones**:
1. Leer archivos existentes relacionados (si aplica)
2. Crear/modificar archivos
3. Actualizar tests (si aplica)
4. Actualizar documentación
5. Commit y push

### 3. Testing

```bash
# Ejecutar tests
pytest tests/ -v

# Con cobertura
pytest tests/ --cov=src --cov-report=html

# Tests específicos
pytest tests/unit/test_vida_temporal.py -v
```

### 4. Documentación

Mantener actualizado:
- `README.md`: Overview y inicio rápido
- `docs/JOURNAL.md`: Decisiones técnicas
- `docs/resumen_ejecutivo.html`: Para portfolio
- Docstrings en código
- Type hints completos

---

## Convenciones de Nombres

### Archivos y Directorios
```
snake_case para archivos Python
kebab-case para archivos de config
PascalCase para clases
```

### Variables y Funciones
```python
# Variables
edad_asegurado: int
suma_asegurada: Decimal

# Constantes
TASA_MINIMA: Final[Decimal] = Decimal('0.01')

# Funciones
def calcular_prima_neta() -> Decimal:
    pass

# Clases
class VidaTemporal:
    pass

# Enums
class Sexo(str, Enum):
    HOMBRE = "H"
    MUJER = "M"
```

---

## Errores Comunes a Evitar

### 1. No usar Decimal para dinero
```python
# ❌ MAL
prima = 1234.56 * 1.15

# ✅ BIEN
prima = Decimal('1234.56') * Decimal('1.15')
```

### 2. No validar inputs
```python
# ❌ MAL
def calcular(edad):
    return edad * 100

# ✅ BIEN
def calcular(asegurado: Asegurado) -> Decimal:
    # Pydantic ya validó edad entre 18-100
    return asegurado.edad * Decimal('100')
```

### 3. Imports circulares
```python
# ✅ BIEN - Usar TYPE_CHECKING
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .producto import Producto
```

### 4. No usar caching en Streamlit
```python
# ❌ MAL - Recarga tabla en cada interacción
def main():
    tabla = TablaMortalidad.cargar_emssa09()

# ✅ BIEN
@st.cache_resource
def cargar_tabla():
    return TablaMortalidad.cargar_emssa09()

def main():
    tabla = cargar_tabla()
```

---

## Recursos de Referencia

### Documentación Oficial
- [Python 3.11 Docs](https://docs.python.org/3.11/)
- [Pydantic Docs](https://docs.pydantic.dev/)
- [Streamlit Docs](https://docs.streamlit.io/)
- [Plotly Python](https://plotly.com/python/)

### Normativa Mexicana
- CNSF: Circular Única de Seguros y Fianzas
- LISR: Ley del Impuesto Sobre la Renta
- Circular S-11.4: Reservas Técnicas

### Actuarial
- EMSSA: Experiencia Mexicana de Seguridad Social
- SOA: Society of Actuaries resources

---

## Objetivos de Calidad

### Código
- ✅ Type hints completos
- ✅ Docstrings en funciones públicas
- ✅ Tests con >90% cobertura
- ✅ Sin warnings de linters
- ✅ Pydantic para validación

### Documentación
- ✅ README actualizado
- ✅ JOURNAL con decisiones técnicas
- ✅ Ejemplos de uso
- ✅ Comentarios explicativos en código complejo

### Git
- ✅ Commits descriptivos
- ✅ Branch strategy seguida
- ✅ No commits de archivos temporales
- ✅ .gitignore actualizado

### UX (Streamlit)
- ✅ Tooltips explicativos
- ✅ Mensajes de error claros
- ✅ Loading states
- ✅ Responsive layout

---

## Resumen de Conversaciones Previas

### Contexto Inicial
Este proyecto comenzó con la Fase 1 (Fundamentos) y ha evolucionado hasta completar la Fase 6 (Dashboards).

### Fase 6: Dashboards con Streamlit
**Objetivo**: Crear interfaz visual para análisis actuariales

**Implementado**:
1. **Home.py**: Página principal con overview del proyecto
2. **Dashboard Productos de Vida**: Calculadora interactiva
3. **Dashboard Cumplimiento**: Monitor regulatorio
4. **Dashboard Reservas**: Análisis con métodos avanzados
5. **Utilities**: Funciones reutilizables de cálculos y visualización

**Características**:
- 3,550 líneas de código nuevo
- Integración completa con paquete backend
- Caching optimizado
- Visualizaciones Plotly interactivas
- Documentación completa

---

## Próximos Pasos (Fase 7)

### Opciones para Expandir
1. **Validaciones SIPRES**: Sistema de Información Prudencial de Seguros
2. **Reportes Anuales CNSF**: Formatos anuales adicionales
3. **API REST con FastAPI**: Endpoints para integración
4. **CLI Interactivo**: Herramienta de línea de comandos
5. **Seguros de Daños**: Autos, GMM, incendio

---

## Checklist de Inicio de Sesión

Cuando se continúe el proyecto en una nueva sesión:

- [ ] Verificar que estoy en el branch correcto: `claude/review-workflow-plan-01KdR8QXYSTdi9Fo6Fu7nPmd`
- [ ] Leer este documento `claude.md` para contexto
- [ ] Revisar estado de TODOs si hay tareas pendientes
- [ ] Verificar que dependencias estén instaladas
- [ ] Ejecutar tests para confirmar que todo funciona
- [ ] Revisar últimos commits para entender trabajo reciente

---

## Contacto y Contribución

Para este proyecto:
- Seguir estándares definidos en este documento
- Commits descriptivos siguiendo convenciones
- Tests para nueva funcionalidad
- Documentación actualizada
- Pull request al branch correcto

---

**Última actualización**: Fase 6 completada - Dashboards Interactivos con Streamlit

**Versión del documento**: 1.0

**Estado del proyecto**: Fase 6/7 completada, listo para Fase 7 o mejoras adicionales
