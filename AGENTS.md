# AGENTS.md

Guidance for coding agents working in this repository. Read this file before making
changes. A more specific `AGENTS.md` in a subdirectory supplements these instructions.

## Project overview

`suite-actuarial` is a Python 3.11+ actuarial toolkit for the Mexican insurance
market. It can be used as:

- a Python package (`src/suite_actuarial/`);
- a FastAPI service (`src/suite_actuarial/api/`);
- a Next.js dashboard (`frontend/`); or
- a legacy/secondary Streamlit dashboard (`streamlit_app/`).

The main actuarial domains are life, property and casualty, health, pensions,
reserves, reinsurance, regulatory calculations, and annual regulatory configuration.

## Repository map

- `src/suite_actuarial/`: package source and domain logic
- `src/suite_actuarial/api/`: FastAPI application and routers under `/api/v1`
- `src/suite_actuarial/core/`: shared models, validation, and product abstractions
- `src/suite_actuarial/config/`: year-specific Mexican regulatory parameters
- `src/suite_actuarial/data/`: package-bundled mortality data
- `tests/unit/`: domain, boundary, and actuarial-rigor tests
- `tests/integration/`: API contract tests
- `frontend/`: Next.js 16, React 19, and TypeScript dashboard
- `streamlit_app/`: Streamlit dashboard using the Python package directly
- `data/`: source/reference mortality-table files
- `docs/`: regulatory, validation, and project notes
- `examples/` and `notebooks/`: executable usage examples

## Set up and run

Python development environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,api]"
```

Common Python commands:

```bash
pytest
pytest tests/unit/test_vida_temporal.py
pytest tests/integration/test_api_pricing.py
ruff check src/ tests/
ruff format --check src/ tests/
mypy src/
uvicorn suite_actuarial.api.main:app --reload
```

Frontend commands (run from `frontend/`):

```bash
npm ci
npm run dev
npm run lint
npm run build
```

The frontend expects `NEXT_PUBLIC_API_URL`; locally it defaults to
`http://localhost:8000/api/v1`. The complete development stack can also be started
with `docker compose up` (API on port 8000, frontend on port 3000).

The Streamlit app requires the `viz` extra plus `streamlit_app/requirements.txt` and
starts with `streamlit run streamlit_app/Home.py`.

## Change guidelines

### Python and actuarial logic

- Follow the settings in `pyproject.toml`: Python 3.11, Ruff, 100-character lines,
  and strict type checking for function definitions.
- Use ASCII for identifiers. User-facing text and docstrings may use correct Spanish
  accents. Existing domain terminology is primarily Spanish; preserve it.
- Do not add emojis to code, documentation, or user-facing copy unless the user asks
  for them or an established filename/convention requires them.
- Add type hints to public functions and Google-style docstrings to public APIs.
- Use `Decimal`, constructed from strings, for currency, premiums, reserves, rates,
  and regulatory amounts. Convert to `float` only at explicit library/API/UI
  boundaries where the existing contract requires it.
- Keep shared validation in `core/`; do not duplicate domain rules in routers or UIs.
- Treat mortality tables and regulatory factors as controlled inputs. Do not alter
  formulas, rounding, units, table data, or legal thresholds without tests and a
  documented source or rationale.
- A new annual configuration belongs in `config/config_<year>.py` and must match
  `config/schema.py`; verify loader and API behavior with tests.

### API

- Routers should translate validated request models into domain objects. Actuarial
  calculations belong in the package, not in FastAPI handlers.
- Preserve the `/api/v1` contract. When a request or response changes, update the
  matching integration tests and the frontend types/client in the same change.
- Convert `Decimal` values deliberately when serializing. Preserve useful validation
  errors and avoid exposing internal tracebacks.

### Frontend

- Also follow `frontend/AGENTS.md`.
- Reuse `src/components/ui`, design tokens, `useCalculation`, and the typed client in
  `src/lib/api.ts`; do not issue ad hoc API requests from page components.
- Keep API interfaces in `src/lib/types.ts` aligned with Pydantic request/response
  models.
- User-visible copy must support both Spanish and English through the existing i18n
  system. Keep pages responsive and preserve loading, error, empty, and result states.

### Tests and verification

- Add or update the narrowest relevant tests for every behavior change.
- Use unit tests for formulas and domain behavior, integration tests for API contracts,
  and boundary/rigor tests for actuarial identities and edge cases.
- Prefer targeted tests while iterating. Before handing off a broad change, run the
  relevant Ruff checks and test suites; run the frontend lint/build for frontend work.
- Do not update test expectations merely to make a failure pass. Confirm the formula,
  units, rounding, and source data first.

## Working practices

- Make focused changes and preserve unrelated work already present in the workspace.
- Do not edit generated artifacts such as `frontend/.next/`, coverage output, caches,
  or installed dependencies.
- Do not add dependencies unless the task requires them and the tradeoff is justified.
- Update documentation and examples when public behavior changes.
- Never commit, push, create branches, or perform other git operations unless the user
  explicitly asks for that action.
