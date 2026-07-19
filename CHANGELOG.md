# Changelog

## 2.1.0 (2026-07-19)

- Added effective-dated regulatory profiles with source references, hashes,
  support tiers, and deterministic date loading.
- Corrected 2026 UMA to 117.31 daily / 3,566.22 monthly / 42,794.64 annual
  from 1 February, and IMSS Ley 97 transition weeks to 825/850/875.
- Corrected 2024/2025 UMA anual to the official INEGI figures 39,606.36 and
  41,273.52 (annual = monthly x 12 per Ley UMA Art. 4; previous values used
  daily x 365).
- Config coverage now ends at the last profile's effective_to (31 January
  2027), derived from the bundled profiles instead of a hardcoded date;
  dates outside coverage raise explicitly.
- cargar_config() without arguments now delegates to cargar_config_fecha(),
  so January dates resolve to the prior year's UMA on both public paths.
- Added auditable life cash-flow valuation, calculation metadata, Mack-style
  reserve diagnostics, and explicit experimental-model warnings.
- Fiscal validation now exposes eligible/not_eligible/indeterminate status;
  legacy boolean fields remain for compatibility.
- Added examples/casos/: seven self-verifying worked cases (one per domain)
  with realistic Mexican scenarios, asserted actuarial identities, and cited
  sources; fixed stale README/CLI usage snippets to match the real API.
- Added an interactive illustrative case to each frontend domain page: a
  concrete scenario with sliders that recalculate against the API in real
  time, followed by a technical reading of the result (ES/EN).
- Fixed Chain Ladder tail factor: manual and calculated tail factors were
  appended to the factor list but never applied, so ultimates and reserves
  ignored them; the tail now scales each projected ultimate (with tests).

## 2.0.0 (2026-03-22)

### Nuevo
- Dominio Danos: SeguroAuto con tablas AMIS, ModeloColectivo, credibilidad Buhlmann
- Dominio Salud: GMM con bandas quinquenales, AccidentesEnfermedades
- Dominio Pensiones: Conmutacion, RentaVitalicia, PensionLey73, PensionLey97 con tablas IMSS completas
- Sistema de configuracion regulatoria versionada (config_2024, config_2025, config_2026)
- Modulo de tasas de interes (CurvaRendimiento)
- Demo interactivo con 7 paginas Streamlit mostrando uso de la libreria

### Cambiado
- Renombrado paquete: mexican_insurance -> suite_actuarial
- Dividido validators.py (1297 lineas) en core/models/ submodulos
- Aplanado products/vida/ -> vida/, reinsurance/ -> reaseguro/
- RCS inversion usa correlacion 0.75 (antes 1.0 suma simple)
- RCS vida usa matriz de correlacion CNSF (antes correlacion cero)

### Corregido
- validador_siniestros.py: nombres de campo Pydantic incorrectos (crasheaba PM)
- Tasa de aportacion AFORE: 6.5% -> 10.775% (era 40% menor)
- reserva_matematica.py: soporte para tabla EMSSA-09 real + duracion de poliza
- UMA 2024 anual: 39628.08 -> 39628.05

## 1.0.0 (2026-03-18)
- Lanzamiento inicial con Vida, Reaseguro, Reservas, Regulatorio
- 307 tests, 87% cobertura
