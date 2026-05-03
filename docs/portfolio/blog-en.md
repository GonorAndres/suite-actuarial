---
title: "Mexican Actuarial Suite: Pricing, Reinsurance, Reserves, and Regulatory Compliance in Python"
description: "Python actuarial library spanning 6 phases: EMSSA-09 mortality tables, life insurance pricing (term, whole, endowment), reinsurance (QS, XoL, SL), reserving (Chain Ladder, BF, Bootstrap), RCS under LISF, CNSF regulatory reports, and SAT tax validations. 307 tests, 87% coverage, interactive Streamlit dashboard."
date: "2026-03-19"
category: "proyectos-y-analisis"
lang: "en"
tags: ["Python", "Pydantic", "LISF", "CUSF", "CNSF", "RCS", "Reservas", "Chain Ladder", "Reaseguro", "Streamlit", "EMSSA-09", "SAT"]
---

# Mexican Actuarial Suite: Pricing, Reinsurance, Reserves, and Regulatory Compliance in Python

In the technical department of a typical Mexican insurance company, the quarterly operating cycle is fragmented across spreadsheets that do not talk to each other. One actuary prices products with an EMSSA-09 table pasted into Excel, another calculates reserves using a separate development triangle, a third fills in the RCS regulatory form by hand, and at the end someone tries to reconcile everything for the report filed with the CNSF. Every quarter, the same manual reconciliation exercise.

The **Mexican Actuarial Suite** unifies those workflows into a single Python library. It covers everything from the EMSSA-09 mortality table to the quarterly CNSF report, including life product pricing, three reinsurance strategies, advanced reserving methods, and SAT tax validations. Unlike [SIMA](/proyectos-y-analisis/sima), which builds its own mortality model from raw INEGI data via Lee-Carter, this suite uses the regulatory EMSSA-09 table directly and focuses on the breadth of the insurance cycle: products, reinsurance, reserves, compliance, and reporting.

## The Problem -- Why an Actuarial Suite in Python

The Mexican insurance market is regulated by the Comision Nacional de Seguros y Fianzas (CNSF, the national insurance and surety commission) under the framework of the Ley de Instituciones de Seguros y de Fianzas (LISF, the insurance and surety institutions law) and the Circular Unica de Seguros y Fianzas (CUSF, the unified insurance and surety regulation). This regulatory framework imposes requirements that do not exist in any other jurisdiction: country-specific mortality tables (EMSSA-09), quarterly report formats with a defined structure, a Solvency Capital Requirement (RCS) calculation calibrated to the Mexican market, and tax deductibility rules that depend on Mexico's income tax law (LISR).

Most actuarial work in Mexico is done in Excel or in proprietary systems like Prophet or MoSes. For mid-sized and small insurers, commercial licensing costs are prohibitive, and the result is usually a collection of spreadsheets where every cell is a potential point of failure. Open-source actuarial software in Python does exist -- the `chainladder` package for reserving, `lifelines` for survival analysis -- but none of it integrates Mexican regulatory requirements. There is no library that knows what an EMSSA-09 table is, that computes the RCS as defined by the LISF, or that validates premium deductibility under Article 151 of the LISR.

The suite fills that gap with two fundamental design decisions. The first is using Pydantic v2 as a domain guard: every piece of data entering the system -- insured age, sum assured, product configuration, claims triangle -- is validated before it touches a formula. An insured with a negative age, a technical interest rate of 200%, or a sum assured of zero simply cannot enter the system. The second is using `Decimal` instead of `float` throughout the entire calculation chain. In a context where rounding differences of a few cents compound across portfolios of thousands of policies, arithmetic precision is not an academic luxury -- it is an operational requirement.

## Life Products -- Term, Whole, Endowment

### Product architecture

All products in the suite inherit from an abstract base class `ProductoSeguro` that defines the common interface: `calcular_prima()`, `calcular_reserva()`, `validar_asegurabilidad()`, and `aplicar_recargos()`. The design combines two classic patterns. **Template Method** fixes the calculation sequence -- validate insurability, compute net premium, apply loadings, build result -- while each concrete product implements the specific logic of its actuarial formula. **Strategy** comes in for the averaging methods used in development factors and for reinsurance modalities.

The `aplicar_recargos()` method lives in the base class and breaks down the gross premium transparently: administration expenses (5% by default), acquisition expenses (10%), and profit margin (3%). A Pydantic `model_validator` checks that total loadings do not exceed 100% of the net premium, cutting off absurd configurations at the root.

### The EMSSA-09 table

The Experiencia Mexicana de Seguridad Social 2009 (EMSSA-09, roughly "Mexican Social Security Experience 2009") is the regulatory mortality table for life insurance in Mexico. Each record contains three fields: age, sex, and `qx` -- the probability that a person aged `x` dies before reaching age `x+1`. For a 35-year-old male, the table gives `qx = 0.001300`, meaning 1.3 deaths per thousand people of that age. At 40, the value rises to `qx = 0.001600`. This mortality progression is the fundamental input for all pricing.

The suite loads the EMSSA-09 from a CSV and wraps it in a `TablaMortalidad` model that supports interpolation for intermediate ages and automatic validation that every `qx` falls between 0 and 1.

### Pricing formulas

The net premium is calculated under the **equivalence principle**: the actuarial present value of future benefits must equal the actuarial present value of future premiums. For a term insurance of `n` years on an insured aged `x`:

- **Term insurance** A[x:n]: Sum of v^(t+1) * t_p_x * q_(x+t) for t from 0 to n-1, where v = 1/(1+i) is the discount factor at technical rate i, t_p_x is the probability of surviving t years, and q_(x+t) is the mortality at age x+t.
- **Annuity-due** a-double[x:n]: Sum of v^t * t_p_x for t from 0 to n-1. It represents the present value of one unit paid at the beginning of each year while the insured survives.
- **Level net premium**: P = A[x:n] / a-double[x:n]. This is the constant annual amount that, paid while the insured is alive within the policy term, exactly funds the expected benefit.

The technical interest rate is 5.5%, the typical maximum the CNSF allows for traditional life products in Mexico.

### Worked numerical example

Consider a 35-year-old male with a sum assured of $1,000,000 MXN under a 20-year term policy. Using the EMSSA-09 and a 5.5% technical rate:

- The annual net premium comes out to approximately $5,000 MXN. This amount reflects the fact that cumulative mortality over 20 years is relatively low for a 35-year-old male (qx starts at 0.0013 and grows gradually).
- Loadings add up to 18% (5% admin + 10% acquisition + 3% profit): roughly $900 MXN.
- The total annual premium lands at approximately $5,900 MXN.

The breakdown is stored in a `ResultadoCalculo` validated by Pydantic, which includes metadata with the table used, rate, term, and payment frequency.

### Product comparison

| Aspect | Term | Whole Life | Endowment |
|---|---|---|---|
| Coverage | Fixed term (10, 20, 30 years) | Lifetime (up to omega age) | Fixed term |
| Death benefit | Only if death occurs during the term | Guaranteed (just a matter of when) | If death occurs during the term |
| Survival benefit | None | None | Yes, at maturity |
| Relative premium | Low (pure risk) | Medium (guaranteed payout) | High (savings + protection) |
| Reserve at maturity | Zero | Grows to the sum assured | Equals the sum assured |
| Typical use | Temporary family protection | Estate and succession planning | Education savings, retirement |

Term insurance is pure risk: if the insured survives the policy term, there is no payout. Whole life is lifetime coverage -- the payout is guaranteed, it is only a matter of when. Endowment combines protection with savings: it pays the sum assured either on death or on survival at maturity. A 30-year-old parent who buys a 20-year endowment with $500,000 MXN knows that, no matter what happens, there will be $500,000 available when their child reaches college age.

## Reinsurance -- Three Risk Transfer Strategies

Reinsurance is insurance for insurers. When a company holds risks that exceed its absorption capacity -- by individual amount, by concentration, or by aggregate volatility -- it transfers part of those risks to a reinsurer in exchange for ceding part of the premiums. The suite implements three complementary strategies.

### Quota Share

The simplest and most predictable contract. The reinsurer accepts a fixed percentage of **all** policies: if the contract is 30% QS, it receives 30% of every premium and pays 30% of every claim. In return, it pays a ceding commission to the cedant (typically 25%) for acquisition expenses already incurred.

In the suite, a `QuotaShareConfig` validates that the cession percentage is between 0 and 100, the commission does not exceed 50%, and the contract term does not exceed 5 years. The calculation is straightforward: `prima_cedida = prima_bruta * (porcentaje_cesion / 100)`. The advantage of QS is simplicity and commission income generation. The disadvantage is that you cede the same proportion of all risks, including the profitable ones.

### Excess of Loss

Non-proportional protection against large claims. The reinsurer only steps in when an individual claim exceeds the cedant's retention, and pays up to a maximum limit. The standard notation is "limit xs retention": a "500 xs 200" contract means the cedant retains the first $200,000 and the reinsurer pays the excess up to an additional $500,000.

If the claim is $150,000, the cedant absorbs everything. If it is $400,000, the cedant pays $200,000 and the reinsurer pays $200,000. If it is $800,000, the cedant pays $200,000, the reinsurer pays its $500,000 limit, and the cedant absorbs the remaining $100,000.

The implementation includes **reinstatements**: the ability to reinstate the limit after it has been used, in exchange for an additional premium. A `model_validator` ensures that the limit is greater than the retention -- a condition that sounds obvious but gets violated in editable spreadsheet cells more often than anyone would like to admit.

### Stop Loss

Aggregate protection across the entire portfolio. The Stop Loss activates when total loss experience (claims / premiums) exceeds a threshold called the **attachment point**. A contract of "80% xs 20%" on $10M of subject premiums means: if the loss ratio exceeds 80%, the reinsurer covers up to an additional 20 percentage points. If claims total $9M (90% loss ratio), the reinsurer pays $1M (the 10% excess above 80%, applied to $10M of premiums). If claims reach $11M (110%), the reinsurer pays the maximum of $2M (20% of $10M).

Pydantic validates that the attachment point falls within a reasonable range (50%-200%) -- trigger points outside that range indicate a data entry error, not a real contract.

## Advanced Reserves -- Chain Ladder, Bornhuetter-Ferguson, Bootstrap

Estimating reserves for outstanding claims (IBNR -- Incurred But Not Reported) is one of the central problems in casualty actuarial practice. Anyone who has read the [Insurance Claims Dashboard post](/proyectos-y-analisis/insurance-claims-dashboard) is already familiar with the mechanics of Chain Ladder and development triangles. I am not going to repeat the explanation from scratch here. Instead, I want to focus on three aspects that distinguish this implementation.

### Custom implementation vs. the chainladder package

The suite includes `chainladder` as a dependency but implements Chain Ladder from scratch in the `reservas/chain_ladder.py` module. The reason is not to reinvent the wheel: it is to integrate Pydantic validations at every step of the process. The `ConfiguracionChainLadder` allows choosing between simple, weighted, or geometric averages for development factors, and optionally computing a tail factor for late development. Each `ResultadoReserva` includes a `model_validator` that checks the fundamental identity: ultimate = paid + reserve. If the discrepancy exceeds one cent, the model rejects the result.

### Bootstrap and uncertainty quantification

Chain Ladder produces a point estimate. Bornhuetter-Ferguson complements it by weighting with an a priori expectation (expected loss ratio), which makes it more stable for recent origin years with little development. But neither answers the most important question: "how wrong could this estimate be?"

The Bootstrap module answers with a full distribution. The process is:

1. Run Chain Ladder on the original triangle (base model).
2. Calculate Pearson residuals: (observed - expected) / sqrt(expected).
3. Resample those residuals to generate N synthetic triangles (1,000 simulations by default).
4. Run Chain Ladder on each synthetic triangle.
5. Obtain the distribution of possible reserves and compute percentiles.

The gap between the 50th percentile (median) and the 75th percentile reveals the process uncertainty. If P50 = $2.5M and P75 = $3.1M, there is a 25% probability that the required reserve is at least $600,000 higher than the median. That difference is directly relevant to how much capital to hold. In a `ConfiguracionBootstrap`, Pydantic validates that the requested percentiles fall between 1 and 99, and that the number of simulations is between 100 and 10,000.

## Regulatory Compliance -- RCS, CNSF, S-11.4, SAT

This is the section that sets the suite apart from any other open-source actuarial package. To the best of my knowledge, there is no public library that implements the Mexican RCS calculation, the rules of Circular S-11.4, or the SAT's tax validations for insurance premiums. These modules required the most research with the fewest available references.

### RCS: Solvency Capital Requirement

The RCS (Requerimiento de Capital de Solvencia) is the minimum capital an insurer must hold to absorb unexpected losses at a 99.5% confidence level (equivalent to the 99.5th percentile of the one-year loss distribution). The suite computes three risk modules:

**Life underwriting risk** (`RCSVida`). Four sub-risks:
- *Mortality*: Insureds die sooner than expected. Formula: 0.3% of total sum assured, adjusted by an age factor (1.0 at age 30, up to 3.0 at advanced ages) and a diversification factor (decreases with more insureds, by the law of large numbers).
- *Longevity*: Life annuity policyholders live longer than expected. Formula: 0.2% of the mathematical reserve, adjusted by age and average policy duration.
- *Disability*: Incapacity of the insured.
- *Expenses*: Administration expenses exceed projections.

**Non-life underwriting risk** (`RCSDanos`). Two sub-risks:
- *Premium risk*: Collected premiums are insufficient to cover claims experience. Formula: alpha * retained_premiums * sigma * diversification_factor, where alpha = 3.0 (confidence factor at 99.5%) and sigma is the historical coefficient of variation of the loss ratio.
- *Reserve risk*: Outstanding claims reserves are insufficient.

**Investment risk** (`RCSInversion`). Three sub-risks:
- *Market*: Drop in asset values. Shocks calibrated by asset type: equities -35%, government bonds -5% (adjusted by duration), corporate bonds -15%, real estate -25%.
- *Credit*: Issuer default. Shocks ranging from 0.2% for AAA down to 50% for C-rated securities.
- *Concentration*: Excessive exposure to a single issuer.

The final aggregation is performed by the `AgregadorRCS` using a **correlation matrix** that avoids summing risks linearly (which would overestimate the required capital):

|  | Life | Non-life | Investment |
|---|---|---|---|
| **Life** | 1.00 | 0.00 | 0.25 |
| **Non-life** | 0.00 | 1.00 | 0.25 |
| **Investment** | 0.25 | 0.25 | 1.00 |

The life-non-life correlation is 0.00 (independent risks: someone dying is not correlated with a car crash). The life-investment and non-life-investment correlation is 0.25 (investments back the reserves of both lines; a market downturn affects the ability to meet both types of obligations). The aggregation formula is the square root of the quadratic form: RCS_total = sqrt(Rv^2 + Rd^2 + Ri^2 + 2*rho_vi*Rv*Ri + 2*rho_di*Rd*Ri), where Rv, Rd, Ri are the RCS by category and rho the correlation coefficients.

As a concrete example, using the values from the `ResultadoRCS` schema: life RCS $28M, non-life RCS $30M, investment RCS $35M. A straight sum would give $93M, but the correlation-based aggregation yields $75M -- a capital savings of $18M that reflects the diversification benefit. An insurer with $100M in capital would have a solvency ratio of 0.75 and would meet the regulatory requirement.

### Circular S-11.4: Technical Reserves

Circular S-11.4 from the CNSF defines how technical reserves must be calculated. The suite implements two key reserves:

**Mathematical Reserve (RM, Reserva Matematica)** for long-term life insurance. The `CalculadoraRM` uses the prospective method: RM = PV(Future Benefits) - PV(Future Premiums). For a 45-year-old who purchased a life policy at age 40 with an annual premium of $25,000 and a sum assured of $1,000,000, the RM reflects that 5 years of exposure have already accumulated without a claim, so future obligations net of premiums yet to be collected are positive. The reserve grows over time until it reaches the sum assured (for whole life) or drops to zero at maturity (for term).

**Reserva de Riesgos en Curso (RRC, roughly "unearned premium reserve")** for short-term insurance. It covers the unearned portion of the premium plus an inadequacy adjustment if expected claims experience exceeds what was anticipated.

Both modules include a sufficiency validator that checks whether the established reserves are adequate relative to estimated obligations.

### SAT Tax Validations

No other open-source actuarial package implements Mexican tax rules for insurance. The suite includes a `ValidadorPrimasDeducibles` that determines, given an insurance type and the taxpayer's tax regime, what portion of the premium is deductible for income tax (ISR) purposes:

- **Major medical insurance (individuals)**: 100% deductible with no limit (LISR Art. 151, Section I).
- **Life insurance (individuals)**: Not deductible.
- **Pension plans (individuals)**: Deductible up to 5 annual UMAs (LISR Art. 151, Section V).
- **Employee insurance (legal entities)**: 100% deductible -- major medical, life, and disability insurance for employees (LISR Art. 25, Section VI).
- **Property insurance (legal entities)**: 100% deductible as strictly necessary business expenses.

The validator receives the current annual UMA as a parameter, calculates limits in pesos, and returns a `ResultadoDeducibilidadPrima` with the deductible amount, percentage, and exact legal basis. This automates a lookup that typically requires an accountant to manually review the LISR.

### CNSF Reports

The reporting module structures the quarterly data that insurers file with the CNSF. Four specialized generators produce reports on underwriting (written, earned, and cancelled premiums by line of business), claims (incurred, paid, and outstanding), investments (portfolio by asset type), and RCS (full breakdown by risk type).

The `MetadatosReporte` model validates that the filing date is after the reported quarter (you cannot file the Q1 report before March ends), and the `DatosSuscripcionRamo` entries verify consistency between written, earned, and cancelled premiums. These are validations that in Excel depend on someone having placed a conditional formula in the right cell; here they are immovable business rules.

These regulatory modules benefit mutually from everything built in the earlier phases. Pricing feeds the life RCS calculations (sums assured, mathematical reserves). Advanced reserves feed the non-life RCS (claims reserves). And all three converge in the CNSF report. It is the same integration that motivated building a suite rather than standalone scripts. For a complementary view of how mortality modeling works from raw data, [SIMA](/proyectos-y-analisis/sima) walks that path using the Lee-Carter method on INEGI data.

## Engineering Decisions

The suite has 34 production modules distributed across 7 sub-packages (`core`, `actuarial`, `products`, `reinsurance`, `reservas`, `regulatorio`, `reportes`) and 16 test files with 307 tests and 87% coverage. That comes to roughly 6,500 lines of production code and 5,500 lines of tests.

**Unidirectional dependencies.** The dependency flow goes in one direction: `core` imports from nobody; `products`, `reinsurance`, `reservas`, and `regulatorio` import from `core`; `reportes` imports from `regulatorio`. There are no cycles. This allows any module to be tested in isolation.

**Over 30 Pydantic models** with `json_schema_extra` that include concrete examples. Each model doubles as executable documentation: the examples in the schema are valid instances that can be copied directly into a test or an interactive session.

**Decimal precision** throughout the chain. From the `qx` in the mortality table to the final RCS result, every calculation uses `Decimal` instead of `float`. The product configuration specifies rates as `Decimal("0.055")`, not `0.055`. Premiums are rounded to cents with `quantize(Decimal("0.01"))`.

**CI with GitHub Actions.** The suite is automatically tested against Python 3.11 and 3.12. The pipeline runs `ruff` for linting (line-length 100, target-version py311), `mypy` with the Pydantic plugin for type checking, and `pytest` with coverage measurement. The `mypy` configuration enables `disallow_untyped_defs` and `warn_return_any` -- decisions that hurt at coding time but pay dividends as the codebase grows.

**Streamlit dashboard.** Three interactive pages built with Plotly: a life product calculator (comparison between term, whole life, and endowment with sensitivity analysis), a regulatory compliance monitor (RCS calculators and SAT validations), and a technical reserves analysis view (development triangles, projections, and method comparison). The `wide` layout takes advantage of the available space for metrics and side-by-side columns.

## What I Learned

**First** lesson: Pydantic as a domain guard is qualitatively different from unit tests. A `model_validator` that checks total loadings do not exceed 100% catches an entire class of errors at the entry point, before the data ever touches a formula. With unit tests, you need to imagine and write out each invalid case. With Pydantic, you define the rule once and the model rejects everything that does not comply, including cases you never thought of. The error messages are for the user, not for the developer -- "Total loadings (115%) exceed 100%" communicates the problem immediately. This is especially valuable in actuarial software, where the user is an actuary who understands the domain but not necessarily the tech stack.

**Second** lesson: the RCS correlation matrix encodes regulatory judgment. The aggregation formula is straightforward vector algebra -- a square root of a quadratic form. The hard part is not implementing the formula but understanding **why** the CNSF chose those specific correlations: 0.00 between life and non-life, 0.25 between life and investment, 0.25 between non-life and investment. The 0.00 between life and non-life reflects the statistical independence between mortality and automobile claims. The 0.25 with investment reflects the fact that a financial crisis affects the ability to meet both types of obligations through the investment portfolio. These numbers encode the regulator's view of how risks interact in the Mexican market. Implementing the formula without understanding the logic behind the parameters is typing, not actuarial engineering.

**Third** lesson: Mexican regulatory specificity is the hard part. Chain Ladder is Chain Ladder in Mexico, France, or Japan. The annuity-due formula is identical in every jurisdiction. What makes this suite useful **specifically for Mexico** are the modules that do not exist in any other package: the EMSSA-09 as the pricing base table, Circular S-11.4 for technical reserves, the deductibility rules of Article 151 of the LISR, the CNSF report formats with their date and quarter validations. Those modules were the ones that required the most hours of research in CNSF documents, circulars, and statutory texts, with the fewest implementation references available.

## Closing

The Mexican Actuarial Suite demonstrates that it is possible to cover the complete operating cycle of an insurer -- from raw mortality to regulatory reporting -- in a single Python library with rigorous validation and decimal precision, without relying on proprietary software.

**Repository**: [github.com/GonorAndres/suite-actuarial](https://github.com/GonorAndres/suite-actuarial)
