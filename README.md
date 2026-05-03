# suite_actuarial

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-977%20passed-brightgreen.svg)]()
[![Coverage](https://img.shields.io/badge/coverage-93%25-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Beta](https://img.shields.io/badge/status-Beta-orange.svg)]()

Open-source actuarial library for the Mexican insurance market. Covers life, P&C,
health, pensions, reserves, reinsurance, and regulatory compliance (CNSF, SAT, IMSS).
Usable as a Python library, a REST API with 26 endpoints, or a bilingual (ES/EN)
web dashboard.

---

## Quick Start

### As a Python library

```bash
pip install git+https://github.com/GonorAndres/suite-actuarial.git
```

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
```

### As a web application

```bash
git clone https://github.com/GonorAndres/suite-actuarial.git
cd suite-actuarial
docker-compose up
```

- Frontend: http://localhost:3000
- API docs (Swagger): http://localhost:8000/docs

---

## Features

- **8 actuarial domains** -- vida, danos, salud, pensiones, reservas, regulatorio, reaseguro, config
- **26 REST API endpoints** via FastAPI with automatic OpenAPI documentation
- **Next.js bilingual dashboard** (ES/EN) with 9 pages and CSV export on every page
- **977 tests, 93% coverage** -- unit, integration, property-based (Hypothesis), and actuarial rigor tests
- **EMSSA-09 mortality tables** bundled as package data
- **Mexican regulatory compliance** -- CNSF circulars, SAT articles, IMSS pension laws
- **Versioned configuration** -- regulatory parameters for 2024, 2025, and 2026

---

## Architecture

```
src/suite_actuarial/
    vida/               -- 3 life insurance products (temporal, ordinario, dotal)
    danos/              -- auto, incendio, RC, collective model, credibility, bonus-malus
    salud/              -- GMM, accidents & illness
    pensiones/          -- commutation tables, IMSS Ley 73/97, life annuities
    reservas/           -- Chain Ladder, Bornhuetter-Ferguson, Bootstrap
    reaseguro/          -- quota share, excess of loss, stop loss
    regulatorio/        -- RCS (vida, danos, inversion), technical reserves, SAT fiscal
    config/             -- versioned regulatory parameters (2024-2026)
    actuarial/          -- mortality tables EMSSA-09, interest rates, morbidity
    core/               -- Pydantic models, base product class, validators
    api/                -- FastAPI REST endpoints (26 endpoints across 8 routers)
    reportes/           -- report generators (RCS, claims, underwriting)

frontend/               -- Next.js 16 + React 19 + Tailwind CSS 4 + Recharts
    src/app/            -- 9 pages: home, vida, danos, salud, pensiones,
                           reservas, regulatorio, reaseguro + layout
```

---

## Domains

| Domain | Module | Key Classes | API Endpoints |
|---|---|---|---|
| Vida | `vida/` | `VidaTemporal`, `VidaOrdinario`, `VidaDotal` | `/api/v1/pricing/*` |
| Danos | `danos/` | `SeguroAuto`, `SeguroIncendio`, `SeguroRC`, `ModeloColectivo` | `/api/v1/danos/*` |
| Salud | `salud/` | `GMM`, `AccidentesEnfermedades` | `/api/v1/salud/*` |
| Pensiones | `pensiones/` | `PensionLey73`, `PensionLey97`, `RentaVitalicia` | `/api/v1/pensiones/*` |
| Reservas | `reservas/` | `ChainLadder`, `BornhuetterFerguson`, `Bootstrap` | `/api/v1/reserves/*` |
| Reaseguro | `reaseguro/` | `QuotaShare`, `ExcessOfLoss`, `StopLoss` | `/api/v1/reinsurance/*` |
| Regulatorio | `regulatorio/` | `RCSVida`, `RCSDanos`, `AgregadorRCS`, `CalculadoraRRC` | `/api/v1/regulatory/*` |
| Config | `config/` | `cargar_config`, `config_vigente`, `ConfigAnual` | `/api/v1/config/*` |

---

## Installation

### Library only

```bash
pip install git+https://github.com/GonorAndres/suite-actuarial.git
```

### Full stack (Docker)

```bash
git clone https://github.com/GonorAndres/suite-actuarial.git
cd suite-actuarial
docker-compose up
```

Services:
- `api` -- FastAPI on port 8000 (with hot reload)
- `frontend` -- Next.js dev server on port 3000

### Development

```bash
git clone https://github.com/GonorAndres/suite-actuarial.git
cd suite-actuarial
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,api]"
```

For the frontend:

```bash
cd frontend
npm ci
npm run dev
```

### Dependencies

| Package | Min Version | Purpose |
|---|---|---|
| pandas | 2.1.0 | Tabular data manipulation |
| numpy | 1.25.0 | Numerical computation |
| scipy | 1.11.0 | Statistical distributions |
| pydantic | 2.5.0 | Data model validation |
| polars | 0.19.0 | High-performance DataFrames |
| chainladder | 0.8.18 | Reserve development triangles |
| lifelines | 0.27.8 | Survival analysis |
| fastapi | 0.109.0 | REST API framework |

Optional groups: `dev` (pytest, ruff, mypy, hypothesis), `viz` (plotly, matplotlib),
`db` (sqlalchemy, duckdb), `api` (fastapi, uvicorn).

---

## API Documentation

Start the API server:

```bash
uvicorn suite_actuarial.api.main:app --reload
```

Visit http://localhost:8000/docs for the interactive Swagger UI. All endpoints
accept and return JSON. Example:

```bash
curl -X POST http://localhost:8000/api/v1/pricing/vida-temporal \
  -H "Content-Type: application/json" \
  -d '{"edad": 35, "sexo": "hombre", "suma_asegurada": 1000000, "plazo_years": 20}'
```

---

## Examples

### Pension calculation (IMSS Ley 73)

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
print(f"Pension mensual: ${resultado.pension_mensual:,.2f}")
```

### Major medical (GMM)

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
```

### Regulatory configuration

```python
from suite_actuarial import cargar_config

cfg = cargar_config(2026)
print(f"UMA diaria: ${cfg.uma.uma_diaria}")
print(f"Tasa ISR PM: {cfg.tasas_sat.tasa_isr_personas_morales}")
print(f"Tasa tecnica vida: {cfg.factores_tecnicos.tasa_interes_tecnico_vida}")
```

Configurations available: **2024**, **2025**, **2026**.

---

## Configuration

The regulatory configuration system stores official parameters for each fiscal year:
UMA values, SAT tax rates (ISR, IVA, withholdings), CNSF factors, and technical
actuarial parameters.

To add a new year (e.g. 2027), create `src/suite_actuarial/config/config_2027.py`
following the structure of `config_2026.py` and register it in the loader.

---

## Regulatory Compliance

### CNSF (Comision Nacional de Seguros y Fianzas)

- **Circular S-11.4**: RRC and Mathematical Reserve (`CalculadoraRRC`, `CalculadoraRM`)
- **RCS**: Solvency Capital Requirement for vida, danos, and investment risk
  (`RCSVida`, `RCSDanos`, `RCSInversion`, `AgregadorRCS`)

### SAT (Servicio de Administracion Tributaria)

- **Art. 93 LISR**: Tax exemption for life and medical insurance indemnities
- **Art. 142 LISR**: Taxable income from P&C claims
- **Art. 151 LISR**: Deductibility of insurance premiums (GMM, life)
- **Art. 158 LISR**: ISR withholdings on endowment insurance returns

---

## Tests

977 tests including actuarial rigor tests validated against published tables.

```bash
# Run all tests
pytest

# With coverage report
pytest --cov=suite_actuarial --cov-report=term-missing

# Single domain
pytest tests/unit/test_vida*.py
pytest tests/integration/test_api_*.py
```

Test categories: unit tests by domain, API integration tests (67 endpoints),
CLI tests (19), property-based tests (Hypothesis), and EMSSA-09 table verification.

---

## Development

```bash
ruff check src/ tests/         # linter
ruff format src/ tests/        # formatter
mypy src/suite_actuarial/      # type checking
```

GitHub Actions runs Python tests (3.11 + 3.12) and frontend build on every push.

---

## Repository Name

The GitHub repository is named `suite-actuarial` (original name).
The package has been `suite_actuarial` since v2.0:

```python
import suite_actuarial
from suite_actuarial import VidaTemporal, SeguroAuto, GMM, cargar_config
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## Author

**Andres Gonzalez Ortega** -- Licenciatura en Actuaria, UNAM
(Universidad Nacional Autonoma de Mexico).

---

## License

MIT License. See [LICENSE](LICENSE) for details.
