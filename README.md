# suite_actuarial

Librería actuarial fundamental para el mercado mexicano de seguros.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-674%20passed-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Beta](https://img.shields.io/badge/status-Beta-orange.svg)]()

---

## Qué es suite_actuarial

suite_actuarial es una librería de código abierto escrita en Python que implementa
los cálculos actuariales fundamentales que requiere la industria aseguradora mexicana.
Cubre ocho dominios: vida, daños, salud, pensiones, reservas, reaseguro, regulatorio
y configuración fiscal-regulatoria. Cada dominio expone clases con interfaces claras
basadas en modelos Pydantic, lo que garantiza validación estricta de datos de entrada
y resultados reproducibles.

La librería existe porque los actuarios mexicanos enfrentan un problema concreto:
la regulación de la CNSF (Comisión Nacional de Seguros y Fianzas) y las disposiciones
fiscales del SAT (Servicio de Administración Tributaria) definen parámetros específicos
--tablas de mortalidad EMSSA-09, valores de la UMA, tasas técnicas, límites de
deducibilidad-- que cambian cada año fiscal. suite_actuarial centraliza estos parámetros
en un sistema de configuración versionada (2024-2026) y los aplica de forma consistente
en todos los cálculos, eliminando errores de transcripción y facilitando auditorías.

Para actuarios en ejercicio, suite_actuarial proporciona un motor de cálculo validado
que se integra como librería Python, API REST (FastAPI) o aplicación interactiva
(Streamlit). Para estudiantes de actuaría, sirve como referencia educativa: cada
módulo refleja la teoría tal como se enseña en la UNAM, con documentación en español.

Frente a herramientas comerciales como Prophet (FIS), MoSes (WTW) o AXIS (Moody's),
suite_actuarial no reemplaza plataformas empresariales. Es gratuita, de código abierto,
específica para México y legible: un actuario puede inspeccionar cada línea del cálculo
de prima o del RCS, algo imposible en una caja negra comercial.

---

## Instalación

```bash
pip install suite-actuarial
```

Para desarrollo con todas las dependencias:

```bash
git clone https://github.com/GonorAndres/Analisis_Seguros_Mexico.git
cd suite-actuarial
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,viz]"
```

### Dependencias principales

| Paquete       | Versión mínima | Uso                                      |
|---------------|---------------|------------------------------------------|
| pandas        | 2.1.0         | Manipulación de datos tabulares          |
| numpy         | 1.25.0        | Cálculos numéricos                       |
| scipy         | 1.11.0        | Distribuciones estadísticas              |
| pydantic      | 2.5.0         | Validación de modelos de datos           |
| polars        | 0.19.0        | DataFrames de alto rendimiento           |
| chainladder   | 0.8.18        | Triángulos de desarrollo para reservas   |
| lifelines     | 0.27.8        | Análisis de supervivencia                |
| openpyxl      | 3.1.0         | Lectura y escritura de archivos Excel    |

Opcionales: `plotly`, `streamlit`, `matplotlib`, `seaborn` (grupo `viz`);
`pytest`, `hypothesis`, `ruff`, `mypy` (grupo `dev`).

---

## Dominios

### Vida

| Clase          | Descripción                                      | Método principal  |
|----------------|--------------------------------------------------|-------------------|
| VidaTemporal   | Seguro temporal con mortalidad EMSSA-09           | calcular_prima()  |
| VidaOrdinario  | Seguro de vida vitalicio (ordinario de vida)      | calcular_prima()  |
| VidaDotal      | Dotal mixto: muerte + supervivencia al vencimiento| calcular_prima()  |

### Daños

| Clase                  | Descripción                                      | Método principal  |
|------------------------|--------------------------------------------------|-------------------|
| SeguroAuto             | Cotización de auto con tablas AMIS               | cotizar()         |
| SeguroIncendio         | Seguro de incendio para inmuebles                | cotizar()         |
| SeguroRC               | Responsabilidad civil general                    | cotizar()         |
| ModeloColectivo        | Modelo frecuencia-severidad (Poisson-Gamma, etc.)| simular()         |
| FactorCredibilidad     | Credibilidad clásica (Buhlmann, limitada)        | calcular()        |
| CalculadoraBonusMalus  | Sistema de bonus-malus para auto                 | calcular_factor() |

### Salud

| Clase                    | Descripción                                    | Método principal  |
|--------------------------|------------------------------------------------|-------------------|
| GMM                      | Gastos Médicos Mayores con deducible y coaseguro| calcular_prima() |
| AccidentesEnfermedades   | Accidentes y enfermedades (pérdidas orgánicas)  | calcular_prima() |

### Pensiones

| Clase              | Descripción                                        | Método principal  |
|--------------------|----------------------------------------------------|-------------------|
| TablaConmutacion   | Funciones de conmutación (Dx, Nx, Cx, Mx)          | calcular()        |
| RentaVitalicia     | Renta vitalicia inmediata y diferida                | calcular()        |
| PensionLey73       | Pensión IMSS régimen Ley 1973                       | calcular()        |
| PensionLey97       | Pensión IMSS régimen Ley 1997 (Afore + complemento) | calcular()       |
| CalculadoraIMSS    | Utilidades de cálculo para semanas cotizadas y cuantía básica | calcular() |

### Reservas

| Clase                | Descripción                                        | Método principal  |
|----------------------|----------------------------------------------------|-------------------|
| ChainLadder          | Método Chain Ladder estándar (factores de desarrollo)| estimar()        |
| BornhuetterFerguson  | Método BF: experiencia observada + estimado a priori | estimar()        |
| Bootstrap            | Simulación Monte Carlo sobre triángulos de desarrollo| simular()        |

### Reaseguro

| Clase            | Descripción                                          | Método principal  |
|------------------|------------------------------------------------------|-------------------|
| QuotaShare       | Reaseguro proporcional cuota parte                    | aplicar()        |
| ExcessOfLoss     | Reaseguro no proporcional exceso de pérdida (XL)      | aplicar()        |
| StopLoss         | Reaseguro no proporcional stop loss (SL)              | aplicar()        |
| ContratoReaseguro| Clase base abstracta para contratos de reaseguro      | aplicar()        |

### Regulatorio

| Clase                      | Descripción                                      | Método principal  |
|----------------------------|--------------------------------------------------|-------------------|
| RCSVida                    | Requerimiento de Capital de Solvencia -- vida     | calcular()       |
| RCSDanos                   | Requerimiento de Capital de Solvencia -- daños    | calcular()       |
| RCSInversion               | RCS por riesgos de mercado y crédito              | calcular()       |
| AgregadorRCS               | Agregación de RCS con matriz de correlaciones     | calcular_total() |
| CalculadoraRRC             | Reserva de Riesgos en Curso (corto plazo)         | calcular()       |
| CalculadoraRM              | Reserva Matemática (largo plazo / vida)           | calcular()       |
| ValidadorSuficiencia       | Validación de suficiencia de reservas técnicas    | validar()        |
| ValidadorPrimasDeducibles  | Deducibilidad de primas según LISR                | validar_deducibilidad() |
| ValidadorSiniestrosGravables| Gravabilidad fiscal de indemnizaciones           | validar_gravabilidad()  |
| CalculadoraRetencionesISR  | Retenciones de ISR en pagos de seguros            | calcular_retencion()    |

### Config

| Clase          | Descripción                                            | Método principal  |
|----------------|--------------------------------------------------------|-------------------|
| cargar_config  | Carga la configuración regulatoria de un año fiscal     | cargar_config()  |
| config_vigente | Devuelve la configuración del año en curso              | config_vigente() |
| ConfigAnual    | Modelo con UMA, tasas SAT, factores CNSF y técnicos    | --               |

---

## Ejemplos rápidos

### Tarificación de seguro de vida temporal

```python
from decimal import Decimal
from suite_actuarial import VidaTemporal, TablaMortalidad, Asegurado, ConfiguracionProducto
from suite_actuarial.core.validators import Sexo

tabla = TablaMortalidad()
config = ConfiguracionProducto(
    nombre_producto="Vida Temporal 20",
    plazo_years=20,
    tasa_interes_tecnico=Decimal("0.055"),
)
producto = VidaTemporal(config, tabla)
asegurado = Asegurado(edad=35, sexo=Sexo.HOMBRE, suma_asegurada=Decimal("1000000"))
resultado = producto.calcular_prima(asegurado, frecuencia_pago="mensual")
print(f"Prima mensual: ${resultado.prima_total:,.2f}")
# Prima mensual: $1,234.56  (valor ilustrativo)
```

### Cotización de seguro de auto

```python
from decimal import Decimal
from suite_actuarial import SeguroAuto, Cobertura

auto = SeguroAuto(
    valor_vehiculo=Decimal("450000"),
    modelo_año=2024,
    uso="particular",
    zona="Ciudad de México",
)
coberturas = [Cobertura.DANOS_MATERIALES, Cobertura.ROBO_TOTAL, Cobertura.RC_OBLIGATORIA]
cotizacion = auto.cotizar(coberturas)
print(f"Prima anual: ${cotización.prima_total:,.2f}")
# Prima anual: $18,750.00  (valor ilustrativo)
```

### Prima de Gastos Médicos Mayores

```python
from decimal import Decimal
from suite_actuarial import GMM, NivelHospitalario, ZonaGeografica

gmm = GMM(
    edad=40,
    sexo="masculino",
    nivel_hospitalario=NivelHospitalario.ALTO,
    zona=ZonaGeografica.CDMX,
    suma_asegurada=Decimal("20000000"),
    deducible=Decimal("30000"),
    coaseguro=Decimal("0.10"),
)
prima = gmm.calcular_prima()
print(f"Prima anual GMM: ${prima:,.2f}")
# Prima anual GMM: $45,600.00  (valor ilustrativo)
```

### Cálculo de pensión IMSS Ley 73

```python
from decimal import Decimal
from suite_actuarial import PensionLey73, CalculadoraIMSS

calc = CalculadoraIMSS()
pension = PensionLey73(
    salario_promedio_5a=Decimal("25000"),
    semanas_cotizadas=1800,
    edad=65,
    calculadora=calc,
)
resultado = pension.calcular()
print(f"Pensión mensual Ley 73: ${resultado.pension_mensual:,.2f}")
# Pensión mensual Ley 73: $16,800.00  (valor ilustrativo)
```

---

## Sistema de configuración regulatoria

Cada configuración anual contiene parámetros oficiales vigentes: UMA, tasas SAT
(ISR, IVA, retenciones), factores CNSF y parámetros técnicos actuariales.

### Cargar configuración

```python
from suite_actuarial import cargar_config

cfg = cargar_config(2026)
print(f"UMA diaria: ${cfg.uma.uma_diaria}")
print(f"UMA anual: ${cfg.uma.uma_anual}")
print(f"ISR personas morales: {cfg.tasas_sat.tasa_isr_personas_morales}")
print(f"Tasa tecnica vida (CNSF): {cfg.factores_tecnicos.tasa_interes_tecnico_vida}")
```

Configuraciones disponibles: **2024**, **2025**, **2026**.

### Agregar un nuevo año

Para agregar 2027, cree `src/suite_actuarial/config/config_2027.py` siguiendo
la estructura de `config_2026.py`. Defina `UMAConfig`, `TasasSAT`, `FactoresCNSF`
y `FactoresTecnicos`, y registre el año en el loader.

---

## Arquitectura del proyecto

```
src/suite_actuarial/
    vida/               -- 3 productos de vida individual
    daños/              -- auto AMIS, incendio, RC, modelo colectivo, credibilidad
    salud/              -- GMM, accidentes y enfermedades
    pensiones/          -- conmutación, IMSS Ley 73/97, rentas vitalicias
    reservas/           -- Chain Ladder, Bornhuetter-Ferguson, Bootstrap
    reaseguro/          -- cuota parte, exceso de pérdida, stop loss
    regulatorio/        -- RCS (vida, daños, inversión), reservas técnicas, SAT
    config/             -- parámetros regulatorios versionados (2024-2026)
    actuarial/          -- tablas de mortalidad EMSSA-09, tasas de interés, morbilidad
    core/               -- modelos Pydantic, clase base de productos, validadores
    api/                -- FastAPI REST endpoints
    reportes/           -- generación de reportes (RCS, siniestros, suscripción)
```

La clase base `ProductoSeguro` define la interfaz común. Cada producto hereda de
ella y expone `calcular_prima()` o `cotizar()`. Los modelos de entrada y salida
usan `pydantic.BaseModel` para validación automática y serialización JSON directa.

---

## Cumplimiento regulatorio

### CNSF -- Comisión Nacional de Seguros y Fianzas

- **Circular S-11.4**: RRC y Reserva Matemática (`CalculadoraRRC`, `CalculadoraRM`),
  incluyendo validación de suficiencia.
- **RCS**: Riesgo de vida, daños e inversión con agregación por matriz de
  correlaciones (`RCSVida`, `RCSDanos`, `RCSInversion`, `AgregadorRCS`).

### SAT -- Servicio de Administración Tributaria

- **Art. 93 LISR**: Exención de indemnizaciones por seguros de vida y gastos médicos.
- **Art. 142 LISR**: Determinación de ingresos gravables por siniestros de daños.
- **Art. 151 LISR**: Deducibilidad de primas de seguros (GMM, vida) para personas físicas.
- **Art. 158 LISR**: Retenciones de ISR sobre rendimientos de seguros dotales.

### Pendiente de implementación

IFRS 17, Circular S-11.6 (fianzas), modelos internos de capital y Solvencia II
europea. La librería se enfoca exclusivamente en regulación mexicana.

---

## Demo interactivo

La suite incluye una aplicación Streamlit con 7 páginas demostrativas.

```bash
streamlit run streamlit_app/Home.py
```

Páginas: (1) Vida, (2) Daños, (3) Salud, (4) Pensiones, (5) Reservas Técnicas,
(6) Regulatorio, (7) Reaseguro.

Cada página incluye fragmentos de código Python que muestran las funciones
utilizadas, facilitando la transición de la demo al uso programático.

---

## API REST

suite_actuarial expone endpoints REST mediante FastAPI:

```bash
uvicorn suite_actuarial.api.main:app --reload
```

Swagger UI disponible en `http://localhost:8000/docs`. Los endpoints aceptan
y devuelven JSON, permitiendo integración con sistemas de cotización, ERPs
o dashboards corporativos.

---

## Tests

674 tests, incluyendo 87 de rigor actuarial validados contra tablas publicadas.

```bash
# Ejecutar todos los tests
pytest

# Con reporte de cobertura
pytest --cov=suite_actuarial --cov-report=term-missing

# Solo tests de un dominio específico
pytest tests/unit/test_vida*.py
pytest tests/unit/test_regulatorio*.py
```

Los tests cubren validaciones unitarias por dominio, integración de flujos
completos (tarificación -> reservas -> RCS), tests basados en propiedades
con Hypothesis y verificaciones contra tablas de mortalidad EMSSA-09.

---

## Desarrollo

```bash
git clone https://github.com/GonorAndres/Analisis_Seguros_Mexico.git
cd suite-actuarial
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,viz]"
```

### Lint, formato y CI

```bash
ruff check src/ tests/        # linter
ruff format src/ tests/       # formateador
mypy src/suite_actuarial/     # verificacion de tipos
```

GitHub Actions ejecuta tests y linting en cada push (Python 3.11 y 3.12).

---

## Nota sobre el nombre del repositorio

El repositorio en GitHub se llama `Analisis_Seguros_Mexico` (nombre original).
Desde la versión 2.0, el paquete es `suite_actuarial`:

```python
import suite_actuarial
from suite_actuarial import VidaTemporal, SeguroAuto, GMM, cargar_config
```

---

## Autor

**Andrés González Ortega** -- Licenciatura en Actuaría, UNAM
(Universidad Nacional Autónoma de México).

---

## Licencia

Este proyecto se distribuye bajo la licencia MIT. Consulte el archivo
[LICENSE](LICENSE) para más detalles.
