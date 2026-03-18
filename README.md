# Mexican Insurance Analytics Suite

> Suite actuarial en Python para el mercado asegurador mexicano: tarificacion, reaseguro, reservas, cumplimiento regulatorio y dashboards interactivos.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-307%20passed-brightgreen.svg)]()
[![Coverage](https://img.shields.io/badge/coverage-87%25-green.svg)]()
[![Lint](https://img.shields.io/badge/ruff-0%20errors-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**307 tests** | **87% cobertura** | **34 modulos** | **6 fases completas** | **30+ modelos Pydantic**

---

## Que es esto

Una libreria Python que cubre el ciclo operativo de una aseguradora mexicana: desde la tabla de mortalidad EMSSA-09 hasta el reporte trimestral CNSF, pasando por tarificacion de tres productos de vida, optimizacion de reaseguro, tres metodos de reservas y calculo completo de RCS.

## Arquitectura

```
                          core/
                    (validators, base_product)
                    /     |      \         \
                   /      |       \         \
         products/vida  reinsurance  reservas  regulatorio
         (temporal,     (QS, XoL,   (CL, BF,   (RCS, CNSF,
          ordinario,     SL)         Bootstrap)  S-11.4, SAT)
          dotal)                                     |
                                                  reportes
                                               (generadores,
                                                exportadores)
```

Dependencias unidireccionales: `core` no importa de ningun otro modulo. Cada modulo solo depende de `core` y opcionalmente de modulos al mismo nivel. `reportes` depende de `regulatorio`.

## Fases del Proyecto

| Fase | Modulo | Descripcion |
|------|--------|-------------|
| 1 | Fundamentos | Tablas de mortalidad EMSSA-09, validadores Pydantic, clase base abstracta |
| 2 | Productos de Vida | Temporal, Ordinario (vida entera), Dotal (mixto/endowment) |
| 3 | Reaseguro | Quota Share, Excess of Loss, Stop Loss |
| 4 | Reservas Avanzadas | Chain Ladder, Bornhuetter-Ferguson, Bootstrap Monte Carlo |
| 5 | Cumplimiento Regulatorio | RCS (solvencia), reportes CNSF, reservas tecnicas S-11.4, validaciones SAT |
| 6 | Dashboards | Tres dashboards interactivos con Streamlit + Plotly |

## Cobertura Regulatoria

| Regulacion | Implementacion |
|------------|---------------|
| **LISF/CUSF** | Calculo de RCS: riesgo vida (mortalidad, longevidad, invalidez, gastos), riesgo danos (primas, reservas), riesgo inversion (mercado, credito). Agregacion con matriz de correlacion. |
| **Circular S-11.4** | Reserva Matematica (RM), Reserva de Riesgos en Curso (RRC), validacion de suficiencia |
| **LISR Art. 93/142/146/151** | Deducibilidad de primas, gravabilidad de siniestros, retenciones ISR |
| **Reportes CNSF** | Generacion automatizada de reportes trimestrales: suscripcion, siniestros, inversiones, RCS |

## Inicio Rapido

### Instalacion

```bash
git clone https://github.com/GonorAndres/Analisis_Seguros_Mexico.git
cd Analisis_Seguros_Mexico

python -m venv .venv
source .venv/bin/activate

pip install -e ".[dev]"
```

### Ejemplo: Calcular prima de vida temporal

```python
from decimal import Decimal
from mexican_insurance.actuarial.mortality.tablas import TablaMortalidad
from mexican_insurance.products.vida.temporal import VidaTemporal
from mexican_insurance.core.validators import (
    Asegurado, ConfiguracionProducto, Sexo
)

# Cargar tabla de mortalidad EMSSA-09
tabla = TablaMortalidad.cargar_emssa09()

# Configurar producto: Vida Temporal 20 anios
config = ConfiguracionProducto(
    nombre_producto="Vida Temporal 20",
    plazo_years=20,
    tasa_interes_tecnico=Decimal("0.055"),  # 5.5%
)

producto = VidaTemporal(config, tabla)

asegurado = Asegurado(
    edad=35,
    sexo=Sexo.HOMBRE,
    suma_asegurada=Decimal("1000000"),  # 1M MXN
)

resultado = producto.calcular_prima(asegurado)
print(f"Prima Neta:  ${resultado.prima_neta:,.2f} MXN")
print(f"Prima Total: ${resultado.prima_total:,.2f} MXN")
```

### Dashboards Interactivos

```bash
pip install -e ".[viz]"
streamlit run streamlit_app/Home.py
```

Tres dashboards disponibles en `http://localhost:8501`:
- **Productos de Vida**: Calculadora interactiva, comparacion entre productos, analisis de sensibilidad
- **Cumplimiento**: Monitor RCS con desglose por riesgo, validaciones SAT, reservas S-11.4
- **Reservas**: Triangulos de desarrollo, Chain Ladder, BF, Bootstrap con distribucion completa

## Estructura del Proyecto

```
src/mexican_insurance/
  core/
    base_product.py              # Clase abstracta ProductoSeguro (ABC)
    validators.py                # 30+ modelos Pydantic (1,300 lineas de validacion)
  actuarial/
    mortality/tablas.py          # Carga y manejo de tablas EMSSA-09
    pricing/vida_pricing.py      # Formulas actuariales (equivalencia, anualidades)
  products/vida/
    temporal.py                  # Seguro de vida temporal (riesgo puro)
    ordinario.py                 # Vida entera / whole life
    dotal.py                     # Endowment / seguro mixto
  reinsurance/
    base_reinsurance.py          # Contrato base abstracto
    quota_share.py               # Reaseguro proporcional
    excess_of_loss.py            # Exceso de perdida por siniestro
    stop_loss.py                 # Proteccion agregada por cartera
  reservas/
    chain_ladder.py              # Metodo clasico de factores de desarrollo
    bornhuetter_ferguson.py      # Combinacion observado + a priori
    bootstrap.py                 # Monte Carlo para intervalos de confianza
    triangulo.py                 # Utilidades para triangulos de desarrollo
  regulatorio/
    rcs_vida.py                  # Riesgo vida: mortalidad, longevidad, invalidez, gastos
    rcs_danos.py                 # Riesgo danos: primas, reservas
    rcs_inversion.py             # Riesgo inversion: mercado, credito
    agregador_rcs.py             # Agregacion con matriz de correlacion CNSF
    reservas_tecnicas/           # RM, RRC y validador de suficiencia (S-11.4)
    validaciones_sat/            # Deducibilidad, gravabilidad, retenciones ISR
  reportes/
    generador_rcs.py             # Reporte trimestral RCS
    generador_suscripcion.py     # Reporte de suscripcion
    generador_siniestros.py      # Reporte de siniestros
    generador_inversiones.py     # Reporte de inversiones
    exportadores.py              # Exportacion a Excel/CSV
  cli.py                         # CLI: seguros demo

streamlit_app/
  Home.py                        # Landing page
  pages/
    1_Productos_Vida.py          # Dashboard productos
    2_Cumplimiento.py            # Dashboard regulatorio
    3_Reservas.py                # Dashboard reservas
  utils/
    calculations.py              # Funciones auxiliares
    visualizations.py            # Graficas Plotly

tests/unit/                      # 16 archivos, 307 tests
data/mortality_tables/
  emssa_09.csv                   # Tabla EMSSA-09 (edades 18-120, H/M)
```

## Tests y Calidad

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=mexican_insurance --cov-report=html

# Lint
ruff check src/ tests/

# Type checking
mypy src/ --ignore-missing-imports
```

| Metrica | Valor |
|---------|-------|
| Tests | 307 passing |
| Cobertura | 87% |
| Lint (ruff) | 0 errores |
| CI | GitHub Actions (Python 3.11 + 3.12) |

## Stack Tecnologico

| Categoria | Herramientas |
|-----------|-------------|
| Core | Python 3.11+, Pydantic v2, Decimal |
| Numerico | NumPy, SciPy, Pandas |
| Actuarial | chainladder, lifelines |
| Visualizacion | Streamlit, Plotly, Matplotlib |
| Testing | pytest, pytest-cov, Hypothesis |
| Calidad | ruff, mypy, pre-commit, GitHub Actions |

## Licencia

MIT License - ver [LICENSE](LICENSE)

---

**Nota Legal**: Esta libreria es para propositos educativos y de analisis. Para uso en produccion en una aseguradora, valida los resultados con un actuario certificado y cumple con todas las regulaciones de la CNSF.
