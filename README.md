# Mexican Insurance Analytics Suite

> Suite de herramientas actuariales para el mercado asegurador mexicano

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Un conjunto de herramientas en Python para análisis actuarial, cálculo de primas, reservas técnicas y cumplimiento regulatorio para el mercado de seguros en México.

## Características

### Fase 1 (Actual) - Fundamentos [Completada]
- **Tablas de Mortalidad**: Carga y manejo de EMSSA-09 y otras tablas mexicanas
- **Seguros de Vida**: Cálculo de primas para seguros temporales
- **Reservas Técnicas**: Cálculo de reservas matemáticas
- **Validación de Datos**: Modelos Pydantic para garantizar consistencia
- **Tests Completos**: Suite de tests con pytest (>90% cobertura)

### Fase 2 - Expansión de Productos [Completada]
- **Vida Ordinario**: Seguro de vida entera con pago limitado o vitalicio
- **Vida Dotal**: Seguro mixto con componente de ahorro y protección
- **Tests Completos**: Suite de tests con >92% cobertura

### Fase 3 - Reaseguro [Completada]
- **Quota Share**: Reaseguro proporcional con cesión fija
- **Exceso de Pérdida**: Protección por siniestro individual
- **Stop Loss**: Protección agregada por cartera

### Fase 4 - Reservas Avanzadas [Completada]
- **Chain Ladder**: Método clásico de triángulos de desarrollo
- **Bornhuetter-Ferguson**: Combinación de datos históricos y esperados
- **Bootstrap**: Estimación de incertidumbre en reservas

### Fase 5 - Cumplimiento Regulatorio [Completada]
- **5A - RCS (Solvencia)**: Cálculo de requerimientos de capital [✓]
- **5B - Reportes CNSF**: Reportes trimestrales automatizados [✓]
- **5C - Reservas Técnicas S-11.4**: RRC y RM según normativa [✓]
- **5D - Validaciones SAT**: Deducibilidad, gravabilidad y retenciones ISR [✓]

### Fase 6 - Dashboards Interactivos [Completada]
- **Dashboard Productos de Vida**: Calculadora y análisis de sensibilidad [✓]
- **Dashboard Cumplimiento**: Monitor regulatorio RCS, SAT, S-11.4 [✓]
- **Dashboard Reservas**: Análisis con Chain Ladder, B-F, Bootstrap [✓]

### Próximamente
- **API REST**: Endpoints para integración con sistemas
- **Seguros de Daños**: Expansión a autos, GMM, incendio

## Inicio Rápido

### Instalación

```bash
# Clonar el repositorio
git clone https://github.com/TuUsuario/Analisis_Seguros_Mexico.git
cd Analisis_Seguros_Mexico

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar en modo desarrollo
pip install -e ".[dev]"
```

### Ejemplo Básico

```python
from decimal import Decimal
from mexican_insurance.actuarial.mortality.tablas import TablaMortalidad
from mexican_insurance.products.vida.temporal import VidaTemporal
from mexican_insurance.core.validators import (
    Asegurado,
    ConfiguracionProducto,
    Sexo
)

# Cargar tabla de mortalidad EMSSA-09
tabla = TablaMortalidad.cargar_emssa09()

# Configurar producto: Vida Temporal 20 años
config = ConfiguracionProducto(
    nombre_producto="Vida Temporal 20 años",
    plazo_years=20,
    tasa_interes_tecnico=Decimal("0.055"),  # 5.5%
)

# Crear el producto
producto = VidaTemporal(config, tabla)

# Definir asegurado
asegurado = Asegurado(
    edad=35,
    sexo=Sexo.HOMBRE,
    suma_asegurada=Decimal("1000000")  # 1 millón de pesos
)

# Calcular prima
resultado = producto.calcular_prima(asegurado, frecuencia_pago="mensual")

print(f"Prima Neta: ${resultado.prima_neta:,.2f} MXN")
print(f"Prima Total: ${resultado.prima_total:,.2f} MXN")
print(f"\nDesglose de Recargos:")
for concepto, monto in resultado.desglose_recargos.items():
    print(f"  - {concepto}: ${monto:,.2f}")
```

### Ejecutar Dashboards Interactivos

Los dashboards de Streamlit proporcionan una interfaz visual para análisis:

```bash
# Instalar dependencias de Streamlit
cd streamlit_app
pip install -r requirements.txt

# Ejecutar dashboard
streamlit run Home.py
```

El dashboard se abrirá en `http://localhost:8501` con tres secciones:
- **📊 Productos de Vida**: Calculadora interactiva y análisis
- **📋 Cumplimiento**: Monitor regulatorio (RCS, SAT, S-11.4)
- **📈 Reservas**: Métodos actuariales avanzados

Ver [documentación completa](streamlit_app/README.md) de los dashboards.

## Notebooks de Ejemplo

Aprende a usar la librería con **7 notebooks interactivos** que cubren todos los aspectos del análisis actuarial:

### Notebooks Disponibles

1. **[Introducción y Productos de Vida](examples/01_introduccion_productos_vida.ipynb)**
   - Tablas de mortalidad EMSSA-09
   - Seguros Temporal, Ordinario y Dotal
   - Comparativas y análisis de sensibilidad

2. **[Reaseguro](examples/02_reaseguro.ipynb)**
   - Quota Share, Excess of Loss, Stop Loss
   - Optimización de estructuras
   - Análisis comparativo

3. **[Reservas Técnicas](examples/03_reservas_tecnicas.ipynb)**
   - Chain Ladder, Bornhuetter-Ferguson, Bootstrap
   - Intervalos de confianza
   - Estimación de incertidumbre

4. **[Cumplimiento CNSF](examples/04_cumplimiento_cnsf.ipynb)**
   - RCS Vida y Daños
   - Reservas Técnicas S-11.4
   - Dashboard de solvencia

5. **[Validaciones SAT](examples/05_validaciones_sat.ipynb)**
   - Deducibilidad de primas
   - Requisitos fiscales de siniestros
   - Retenciones ISR

6. **[Reportes CNSF](examples/06_reportes_cnsf.ipynb)**
   - Reportes automatizados
   - Exportación a Excel/PDF
   - Cumplimiento regulatorio

7. **[Casos Prácticos End-to-End](examples/07_casos_practicos_completos.ipynb)**
   - Workflow completo: Producto → Reaseguro → Reservas → Reportes
   - Casos de negocio reales
   - Integración de todos los módulos

### Ejecutar los Notebooks

```bash
# Instalar Jupyter
pip install -e ".[viz]"

# Iniciar Jupyter Lab
jupyter lab

# Navegar a examples/ y abrir cualquier notebook
```

Ver [guía completa de notebooks](examples/README.md) para más detalles.

## Documentación

### Resumen Ejecutivo para Portafolio

**¿Necesitas entender el proyecto sin profundizar en el código?**

Hemos creado un [**Resumen Ejecutivo en HTML**](docs/resumen_ejecutivo.html) que explica:

- **Visión general** del proyecto y problema que resuelve
- **Arquitectura** y diseño del sistema
- **Conceptos actuariales** traducidos a lenguaje de negocio
- **Fases 1 y 2 completadas** con explicaciones detalladas de cada componente
- **Valor de negocio** y beneficios cuantificables
- **Roadmap futuro** con siguientes fases

**Ideal para:**
- Presentar el proyecto en portafolio profesional
- Explicar la solución a stakeholders no técnicos
- Compartir con equipos de negocio o actuariales
- Documentar decisiones de diseño y arquitectura

**[Ver Resumen Ejecutivo](docs/resumen_ejecutivo.html)** - Se puede abrir en cualquier navegador y exportar a PDF.

### Journal Técnico de Desarrollo

Para entender las decisiones técnicas y la lógica detrás de cada implementación, consulta el [**Journal Técnico**](docs/JOURNAL.md) que documenta:

- Arquitectura y patrones de diseño utilizados
- Decisiones técnicas y su justificación
- Fórmulas actuariales implementadas
- Proceso de desarrollo paso a paso
- Lecciones aprendidas y mejores prácticas

## Estructura del Proyecto

```
mexican-insurance-suite/
├── src/mexican_insurance/       # Código fuente principal
│   ├── core/                    # Clases base y validadores
│   │   ├── base_product.py     # Clase abstracta ProductoSeguro
│   │   └── validators.py       # Modelos Pydantic
│   ├── products/vida/           # Seguros de vida
│   │   ├── temporal.py         # Vida temporal
│   │   ├── ordinario.py        # Vida ordinario
│   │   └── dotal.py            # Vida dotal
│   ├── actuarial/               # Herramientas actuariales
│   │   ├── mortality/          # Tablas de mortalidad
│   │   └── pricing/            # Fórmulas de tarificación
│   └── regulatory/              # Cumplimiento regulatorio
├── data/mortality_tables/       # Tablas de mortalidad
│   └── emssa_09.csv            # EMSSA-09
├── tests/                       # Suite de tests
│   ├── unit/                   # Tests unitarios
│   └── integration/            # Tests de integración
└── docs/                        # Documentación
    ├── resumen_ejecutivo.html  # Resumen para portafolio
    └── JOURNAL.md              # Journal técnico de desarrollo
```

## Tests

El proyecto incluye una suite completa de tests:

```bash
# Ejecutar todos los tests
pytest

# Con reporte de cobertura
pytest --cov=mexican_insurance --cov-report=html

# Solo tests específicos
pytest tests/unit/test_vida_temporal.py -v
```

**Cobertura actual**: >90% en módulos core

## Desarrollo

### Configuración del Entorno

```bash
# Instalar todas las dependencias
pip install -e ".[all]"

# Instalar pre-commit hooks
pre-commit install

# Ejecutar linting
ruff check src/ tests/

# Type checking
mypy src/
```

## Roadmap

### Fase 1: Fundamentos [Completada]
- [x] Estructura base del proyecto
- [x] Tablas de mortalidad
- [x] Seguros de vida temporal
- [x] Tests unitarios

### Fase 2: Expansión de Productos [Completada]
- [x] Vida Ordinario
- [x] Vida Dotal
- [x] Tests exhaustivos

### Fase 3: Reaseguro [Completada]
- [x] Quota Share
- [x] Exceso de Pérdida
- [x] Stop Loss

### Fase 4: Reservas Avanzadas [Completada]
- [x] Chain Ladder
- [x] Bornhuetter-Ferguson
- [x] Bootstrap

### Fase 5: Cumplimiento Regulatorio [Completada]
- [x] 5A - Cálculo de RCS (Solvencia)
- [x] 5B - Reportes Trimestrales CNSF
- [x] 5C - Reservas Técnicas S-11.4
- [x] 5D - Validaciones Fiscales SAT

### Fase 6: Dashboards Interactivos [Completada]
- [x] Dashboard Productos de Vida
- [x] Dashboard Cumplimiento Regulatorio
- [x] Dashboard Reservas Técnicas

### Fase 7: Expansiones Futuras
- [ ] 5E - Validaciones SIPRES
- [ ] 5F - Reportes Anuales CNSF
- [ ] API REST
- [ ] CLI Interactivo
- [ ] Seguros de Daños (Autos, GMM)

## Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork el repositorio
2. Crea una rama para tu feature
3. Escribe tests para tu código
4. Asegúrate que todos los tests pasen
5. Abre un Pull Request

## Licencia

MIT License - ver archivo [LICENSE](LICENSE)

## Contacto

Para preguntas o reportar bugs, abre un issue en GitHub.

---

**Nota Legal**: Esta librería es para propósitos educativos y de análisis. Para uso en producción en una aseguradora, valida los resultados con un actuario certificado y asegúrate de cumplir con todas las regulaciones de la CNSF.
