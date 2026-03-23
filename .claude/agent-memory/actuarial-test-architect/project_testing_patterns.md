---
name: suite_actuarial testing patterns
description: Key patterns discovered while writing rigorous tests for the suite_actuarial library
type: project
---

EMSSA-09 mortality table starts at age 18 (not 0) and ends at age 100 with qx < 1.0 (does NOT force certainty of death at omega).

**Why:** The table represents the Mexican social security population (workers), not general population from birth. The terminal qx of ~0.442 at age 100 means the table simply stops rather than forcing q_omega=1. This affects the Ax + d*ax = 1 identity, which holds strictly only if q_omega=1.

**How to apply:** When testing commutation identities on EMSSA-09, use ages >= 18 and be aware that whole-life identities may have small deviations near the terminal age. For strict identity tests, use the synthetic simple mortality table which does have q_omega=1.

Additional findings:
- ConfiguracionBootstrap requires num_simulaciones >= 100 (Pydantic validation)
- ProductoSeguro base class rejects SA > 50M MXN (automatic underwriting limit)
- GMM age bands: infant bands (0-14) have U-shaped cost curve, monotonicity only holds from 15+
- Config loader caches by year (same object returned for same year)
