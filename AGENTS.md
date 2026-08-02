# AGENTS.md

Guidance for coding agents working on `suite_actuarial`. This file captures the
project's purpose, the conventions that serve it, and the guardrails that keep it
defensible. Read it before making changes.

For the vision, audience, and what a good contribution looks like, read
[`docs/PROJECT_VISION.md`](docs/PROJECT_VISION.md) and
[`CONTRIBUTING.md`](CONTRIBUTING.md). This file is the operational summary; those two
are canonical.

**Audit status:** [`docs/AUDIT.md`](docs/AUDIT.md) records an actuarial correctness
audit (2026-07-22). All six remediation phases closed on 2026-07-25: the ten Class A
defects are fixed, each with a test whose expected value comes from an external
source, an actuarial identity, or a hand calculation — not from restating the formula
under test. Read the [closure record](docs/AUDIT.md#registro-de-cierre) before
touching reserves, pensions, life, reinsurance, or credibility: it states the residual
limit that survived each fix.

The [Class B inventory](docs/AUDIT.md#inventario-clase-b-fase-5) is the standing
constraint. Every entry names a datum or assumption, its source, its currency, the
simplification, where it is disclosed, and what replacing it would take. Synthetic
mortality and heuristic RCS factors sit under most life, pension, and capital figures,
so a verified result is still not a professionally valid one. Keep those disclosures
attached to the numbers, and extend the inventory when a change adds a new ceiling.
One Class A item remains open inside that table: the LISR Art. 151 row is marked
"pendiente Clase A de deducibilidad" — `validador_primas.py` returns GMM as 100%
deducible without the global cap, and the current test pins that unverified behavior.

## Central idea

`suite_actuarial` is an open laboratory for building, testing, and understanding
actuarial models. Every model connects a product question to benefits, assumptions,
method, results, tests, and reproducible code.

The audience is students going from a formula to a full product, early-career actuaries
experimenting with assumptions, teachers and researchers who need reproducible
benchmarks, and developers who work with actuaries and need clear contracts. Much of the
work here is helping a contributor develop a product, write an exercise, or share a
method. The guardrails below are what let that shared work be trusted.

The project is rooted in the Mexican insurance market, but its methods are meant
to be generalizable. Its scope is educational and experimental: professional use
requires validated data, internal governance, approved methods, and responsible
actuarial judgment.

## What every model must answer

A shared model is useful only if it can answer six questions:

1. What problem does it solve?
2. What does it promise to pay and under which events?
3. What was assumed and where does it come from?
4. How does the method transform those assumptions?
5. What does the result mean and how does it change?
6. What identity, contrast, or limit makes it trustworthy?

This shapes the codebase: assumptions, sources, and validation must stay visible;
methods must stay in the package where they can be inspected; tests must document
both the behavior and the level of validation reached.

## Communication and form

The form should match the content: plain, exact, honest. Write and edit to this style.

- **Reason first, then mechanics.** Give the actuarial meaning — purpose, benefit,
  assumption, method, result — before the code that computes it.

- **Be exact about numbers and sources.** Name units, dates, and sources. Mark a figure
  as illustrative when it is not sourced. Do not present a regulatory or market parameter
  as current without verifiable evidence.

- **State limitations in the open.** Put scope and caveats where the reader sees them,
  not in a footnote.

- **Direct, honest, good faith.** No overhype, no selling, no filler phrases. Say what a
  model does and what it does not do. If something is uncertain or unfinished, say so.

- **Language split.** Domain terms and narrative docs in Spanish; agent guidance (this
  file, `frontend/AGENTS.md`) in English; dashboard UI copy in ES and EN through i18n
  (`streamlit_app/` is Spanish-only today and has no i18n layer). Identifiers
  stay ASCII; Spanish prose keeps its accents.

- **Plain structure.** Short sentences. Imperative for guardrails ("Do not alter...",
  "Use..."). A list beats a dense paragraph. No emojis unless asked.

## What this project is technically

A Python 3.11+ actuarial toolkit for the Mexican insurance market. It ships as a
Python package, a FastAPI service, a Next.js dashboard, and a secondary Streamlit
app. Treat the actuarial formulas and regulatory parameters as controlled inputs; do
not tweak them to make a test pass.

Deployment is split (see [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)): the dashboard
static-exports to Cloudflare Pages, and the Docker image is API-only on Cloud Run —
FastAPI no longer serves the frontend in production. Breaking numeric changes are
recorded in [`CHANGELOG.md`](CHANGELOG.md); telemetry setup is in
[`docs/ANALYTICS.md`](docs/ANALYTICS.md).

## Structural conventions

- **Spanish module names, English API router names.** Domain packages live under
  `src/suite_actuarial/` with Spanish names (`vida/`, `danos/`, `salud/`, `pensiones/`,
  `reservas/`, `reaseguro/`, `regulatorio/`, `config/`). The FastAPI routers that
  expose them use English names (`pricing.py`, `danos.py`, `salud.py`, `pensiones.py`,
  `reserves.py`, `reinsurance.py`, `regulatory.py`, `config.py`). Keep this mapping;
  do not introduce mixed naming in new modules or routers. Three shared packages sit
  outside the Spanish-name rule: `core/` (Pydantic models, validators, product base),
  `actuarial/` (English-named: mortality table loader, yield curves, life-pricing
  formulas under `mortality/`, `interest/`, `pricing/`), and `api/` (the FastAPI
  service). New shared actuarial machinery belongs in `actuarial/`; new domain
  products belong in the Spanish packages.

- **Domain logic lives in the package.** Routers validate requests and
  translate them into domain objects. Actuarial calculations, rounding, and
  regulatory formulas belong in `src/suite_actuarial/` where they remain inspectable.

- **Shared validation stays in `core/`.** Do not duplicate domain rules in routers,
  frontend code, or Streamlit pages. Reuse `core/validators.py`, `core/models/`, and
  `core/base_product.py`. This is the target, not the current state: `danos/` and
  `salud/` do not yet use `core/` at all, and they encode sex as `M`/`F` while
  `core/models/common.py` uses `H`/`M` — so `"M"` means male in `/api/v1/salud/*`
  but female in `/api/v1/pricing/*`. Do not spread either divergence further; new
  code follows `core/`.

- **Use `Decimal` for money, rates, reserves, and regulatory amounts.** Construct from
  strings (`Decimal("0.055")`). Convert to `float` only at explicit API/UI boundaries
  where the existing contract already requires it.

- **Annual regulatory configuration is versioned by year.** A new year belongs in
  `config/config_<year>.py` and must satisfy `config/schema.py`. Update the loader
  and add tests if the schema changes.

- **Reports are separate from routers.** The `reportes/` module generates regulatory
  outputs (RCS, underwriting, investments, claims). Do not move report logic into
  API handlers.

- **Shared knowledge has a home.** Reproducible walkthroughs — the way a contributor
  develops and explains a product or exercise — live as runnable code in
  `examples/labs/` with their narrative in `docs/labs/`; self-verifying worked cases
  per domain live in `examples/casos/`. Prefer extending these over adding one-off
  scripts, and keep the actuarial logic they exercise in the package, not in the
  example. Know the limit: no gate executes these scripts today — ruff and mypy read
  them, but pytest and CI never run their asserts, so a runtime break in a caso
  ships green. If you touch the package code a caso exercises, run the script.

## Actuarial guardrails

- Do not alter mortality tables, regulatory factors, rounding rules, units, or legal
  thresholds without a documented source or rationale and a matching test.

- Do not update test expectations merely to make a failure pass. First confirm the
  formula, units, rounding, and source data.

- When in doubt, prefer the conservative actuarial interpretation. The codebase is a
  laboratory, but the numbers must still be defensible.

## API and frontend contract

- Preserve the `/api/v1` contract. When a request or response changes, update the
  integration tests in `tests/integration/` and the frontend types in
  `frontend/src/lib/types.ts` in the same change.

- Convert `Decimal` values deliberately when serializing. Preserve useful validation
  errors and avoid exposing internal tracebacks.

- The frontend Next.js dashboard is covered by `frontend/AGENTS.md`. Follow it for UI
  conventions, design tokens, i18n, and the typed API client.

- **Standing to-do: validate every API realm.** Each `/api/v1` realm (pricing, danos,
  salud, pensiones, reserves, reinsurance, regulatory, config) must reach the same
  bar before it counts as done: typed response models (no `dict[str, Any]`), values
  backed by an oracle or identity a test enforces, `disclaimer`/`validation_tier`
  present wherever an assumption is illustrative, and enumerated inputs rejected at
  the boundary with a 422 naming the valid set. Realms below the bar today: `danos`
  and `salud` (untyped responses, no disclosures, free-form enum inputs). When you
  touch a realm, leave it at the bar or record in the session handoff exactly what
  still fails it.

## CLI

The package exposes a `seguros` CLI:

```bash
seguros --help
seguros demo
seguros api
seguros config
seguros validate-config
```

## Verification

Run these before considering a change complete, from the project virtualenv:

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ruff check src/ tests/ examples/ streamlit_app/
.venv/bin/python -m ruff format --check src/ tests/ examples/ streamlit_app/
.venv/bin/python -m mypy src/ tests/ examples/ streamlit_app/
```

All four trees are covered, not just `src/` and `tests/`. `examples/` holds the labs and
the worked cases that this file calls shared knowledge; leaving it outside the gate meant
the code a reader is told to trust was the code nothing checked. The type gate found a
real defect there the first time it ran: `streamlit_app/pages/6_Regulatorio.py` built
`TablaMortalidad()` with no arguments, which raises `TypeError` on the way in.

Use the interpreter explicitly. The optional API extras (`fastapi`, `httpx`) live only
in the virtualenv; running a bare `pytest` against the system interpreter makes the
111 integration tests skip silently instead of running. To turn a missing extra into a
failure rather than a skip, set `SUITE_REQUIRE_API=1`. CI sets it.

Refresh the virtualenv when the extras change; an existing `.venv` does not pick up a
newly declared dependency on its own:

```bash
.venv/bin/python -m pip install -e ".[dev,api,viz]"
```

`viz` carries streamlit and plotly, without which `streamlit_app/` cannot be checked.
A stale environment does not announce itself here — it makes a check disappear while
the run still reports green. Both times this repo lost a check that way, the shape was
the same: `openpyxl` missing made two Excel tests skip, and missing API extras made the
integration tests skip. If a gate suddenly has less to check, suspect the environment
before believing the green.

The four gates must be green. All four also run in CI, on every branch. Two notes on
the type gate, both of which cost the project a real check in the past:

- `mypy` reads its settings from `pyproject.toml`. Do not pass `--ignore-missing-imports`
  on the command line: it silences errors the config would surface.
- The config pins `python_version = "3.12"` even though the package supports 3.11.
  Under `3.11` mypy refuses to parse numpy's PEP 695 stubs and aborts the whole run
  before reading any project file, which reads as a broken gate rather than a clean one.
  The 3.11 job in CI runs the real suite, so genuine 3.11 incompatibilities still fail.

For frontend work, run from `frontend/`:

```bash
npm run lint
npm run build
npm run test:e2e
```

All three run in CI. `test:e2e` is the only check on the Playwright specs in
`frontend/tests/` (bilingual content integrity and public exposition); it serves the
static export from `frontend/out/`, so it requires a prior `npm run build`.

## Working practices

- Make focused changes. Do not edit generated artifacts (`frontend/.next/`, coverage
  output, caches, installed dependencies).

- Do not add dependencies unless the change justifies the tradeoff.

- Do not add emojis to code, docs, or user-facing copy unless explicitly requested.

- Never commit, push, create branches, or perform other git operations unless the user
  explicitly asks for that action.
