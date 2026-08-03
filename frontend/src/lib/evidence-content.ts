import type { DomainId, LocalizedText } from "@/lib/domain-guides";

/**
 * Content of /evidencia/, kept out of the page component so it can be imported
 * by tests and by the structured-data module. The page renders this; it does
 * not own it.
 *
 * The figures in `RECEIPT_FIGURES` are real measurements, not aspirations:
 * they were taken on `RECEIPT_DATE` by running the full suite and counting the
 * audit inventory. If the suite or the inventory changes materially, update
 * them here with a new date rather than letting them drift.
 */

const text = (es: string, en: string): LocalizedText => ({ es, en });

export const REPO_URL = "https://github.com/GonorAndres/suite-actuarial";
export const AUDIT_URL = `${REPO_URL}/blob/main/docs/AUDIT.md`;
export const INVENTORY_URL = `${AUDIT_URL}#inventario-clase-b-fase-5`;
export const VALIDATION_URL = `${REPO_URL}/blob/main/docs/VALIDATION.md`;
export const CONTRIBUTING_URL = `${REPO_URL}/blob/main/CONTRIBUTING.md`;
export const ISSUES_URL = `${REPO_URL}/issues`;

/**
 * The professional-scope disclosure. This exact wording is the description of
 * the `#alcance` node in `structured-data.ts` and is asserted verbatim by
 * `tests/seo-metadata.spec.ts` in both languages. Change it only deliberately,
 * knowing the markup and the test follow this constant.
 */
export const SCOPE_TEXT: LocalizedText = {
  es: "Para una decisión real todavía hacen falta datos aprobados, gobierno corporativo, un método institucional y juicio actuarial. Este repositorio no afirma tenerlos.",
  en: "A real decision still needs approved data, corporate governance, an institutional method, and actuarial judgment. This repository does not claim to have them.",
};

export interface EvidenceLevel {
  n: string;
  title: LocalizedText;
  body: LocalizedText;
}

export const LEVELS: EvidenceLevel[] = [
  {
    n: "01",
    title: text("Implementado", "Implemented"),
    body: text(
      "El cálculo está construido: valida las entradas y repite el resultado con los mismos datos.",
      "The calculation is built: it validates inputs and repeats the result with the same data.",
    ),
  },
  {
    n: "02",
    title: text("Verificado", "Verified"),
    body: text(
      "Además, una prueba independiente (una identidad, un caso hecho a mano u otro oráculo) es capaz de encontrar errores conocidos.",
      "On top of that, an independent check (an identity, a hand-worked case, or another oracle) is able to find known defects.",
    ),
  },
  {
    n: "03",
    title: text("Profesionalmente válido", "Professionally valid"),
    body: SCOPE_TEXT,
  },
];

export const CLAIM = {
  headline: text(
    "Todo el repositorio está, como máximo, en el nivel 02: verificado. Ninguna cifra alcanza el nivel 03.",
    "The entire repository sits, at most, at level 02: verified. No figure reaches level 03.",
  ),
  support: text(
    "No es un descuido: es una decisión declarada. Los datos que faltan — mortalidad publicada, factores calibrados, morbilidad con fuente — están inventariados en la auditoría, cada uno con su ruta de sustitución. Esa lista es también la lista de ayuda que este proyecto busca.",
    "It is not an oversight: it is a declared decision. The missing data — published mortality, calibrated factors, sourced morbidity — is inventoried in the audit, each entry with its replacement path. That list is also the list of help this project is looking for.",
  ),
};

export interface DomainStatus {
  id: DomainId;
  name: LocalizedText;
  validation: LocalizedText;
  data: LocalizedText;
}

export const DOMAIN_STATUS: DomainStatus[] = [
  {
    id: "vida",
    name: text("Vida", "Life"),
    validation: text(
      "Identidades de conmutación (Aₓ + d·äₓ = 1) y recursión de Fackler para las reservas del dotal.",
      "Commutation identities (Aₓ + d·äₓ = 1) and the Fackler recursion for endowment reserves.",
    ),
    data: text("Mortalidad sintética", "Synthetic mortality"),
  },
  {
    id: "danos",
    name: text("Daños", "P&C"),
    validation: text(
      "Casos calculados a mano y monotonicidad de factores y deducibles.",
      "Hand-calculated cases and monotonicity of factors and deductibles.",
    ),
    data: text("Tarifas ilustrativas", "Illustrative tariffs"),
  },
  {
    id: "salud",
    name: text("Salud", "Health"),
    validation: text(
      "Fronteras contractuales de deducible, coaseguro, tope y suma asegurada.",
      "Contract boundaries for deductible, coinsurance, cap, and sum insured.",
    ),
    data: text("Morbilidad ilustrativa", "Illustrative morbidity"),
  },
  {
    id: "pensiones",
    name: text("Pensiones", "Pensions"),
    validation: text(
      "Identidad a interés cero (äₓ = 1 + eₓ) y casos legales de Ley 73.",
      "The zero-interest identity (äₓ = 1 + eₓ) and Ley 73 legal cases.",
    ),
    data: text("Reglas simplificadas", "Simplified rules"),
  },
  {
    id: "reservas",
    name: text("Reservas", "Reserves"),
    validation: text(
      "Mack reproduce el caso publicado de Taylor y Ashe; el bootstrap ODP, el φ publicado.",
      "Mack reproduces the published Taylor–Ashe case; the ODP bootstrap, the published φ.",
    ),
    data: text("Triángulos reproducibles", "Reproducible triangles"),
  },
  {
    id: "reaseguro",
    name: text("Reaseguro", "Reinsurance"),
    validation: text(
      "Capas canónicas a mano (5 xs 5, 5 xs 10, 10 xs 20) y erosión del agregado.",
      "Canonical hand-worked layers (5 xs 5, 5 xs 10, 10 xs 20) and aggregate erosion.",
    ),
    data: text("Contratos ilustrativos", "Illustrative treaties"),
  },
  {
    id: "regulatorio",
    name: text("Regulatorio", "Regulatory"),
    validation: text(
      "Identidad de agregación: el RCS agregado nunca excede la suma de los módulos.",
      "Aggregation identity: the aggregate RCS never exceeds the sum of the modules.",
    ),
    data: text("Factores heurísticos", "Heuristic factors"),
  },
];

/** Taken on this date by running the full suite; see the module comment. */
export const RECEIPT_DATE = "2026-08-03";

export const RECEIPT_FIGURES: { value: string; label: LocalizedText }[] = [
  {
    value: "1,380",
    label: text("pruebas de Python, todas verdes", "Python tests, all green"),
  },
  {
    value: "92%",
    label: text("de cobertura de línea del paquete", "line coverage of the package"),
  },
  {
    value: "10",
    label: text(
      "defectos Clase A cerrados contra oráculo externo, identidad o cálculo a mano",
      "Class A defects closed against an external oracle, an identity, or a hand calculation",
    ),
  },
  {
    value: "36",
    label: text(
      "supuestos inventariados con fuente, límite y ruta de sustitución",
      "inventoried assumptions with source, limit, and replacement path",
    ),
  },
];

export const RECEIPT_EXAMPLES: LocalizedText[] = [
  text(
    "La identidad Aₓ + d·äₓ = 1 se cumple en las edades 18–100 con desviación máxima 0.0000000000.",
    "The identity Aₓ + d·äₓ = 1 holds across ages 18–100 with a maximum deviation of 0.0000000000.",
  ),
  text(
    "Mack reproduce el caso publicado de Taylor y Ashe hasta la unidad monetaria; el bootstrap ODP reproduce el φ publicado y concilia con Chain Ladder.",
    "Mack reproduces the published Taylor–Ashe case to the currency unit; the ODP bootstrap reproduces the published φ and reconciles with Chain Ladder.",
  ),
  text(
    "Los ejemplos de examples/casos/ corren dentro de la suite: si una de sus aserciones falla, la suite falla.",
    "The worked cases in examples/casos/ run inside the suite: if one of their assertions fails, the suite fails.",
  ),
];

export interface EvidenceAsk {
  id: string;
  title: LocalizedText;
  today: LocalizedText;
  contribution: LocalizedText;
  first: { label: LocalizedText; href: string };
}

export const ASKS: EvidenceAsk[] = [
  {
    id: "emssa",
    title: text("Tabla EMSSA-09 publicada", "Published EMSSA-09 table"),
    today: text(
      "La tabla incluida es sintética: una rampa lineal de qx con q₆₅ ≈ 0.0135 contra ≈ 0.02 de la EMSSA real. Es el techo de vida, de pensiones y de parte del capital.",
      "The bundled table is synthetic: a linear qx ramp with q₆₅ ≈ 0.0135 against ≈ 0.02 in the real EMSSA. It is the ceiling on life, pensions, and part of capital.",
    ),
    contribution: text(
      "Licenciar la tabla publicada, sustituir el CSV y actualizar su content_hash: el cargador ya verifica sha256 y rechaza un archivo que no coincida. Después, recalcular y volver a publicar los benchmarks. Es la sustitución de mayor valor en todo el proyecto.",
      "License the published table, replace the CSV, and update its content_hash: the loader already verifies sha256 and rejects a mismatched file. Then recompute and republish the benchmarks. It is the single most valuable replacement in the project.",
    ),
    first: { label: text("Ver la fila del inventario", "See the inventory row"), href: INVENTORY_URL },
  },
  {
    id: "rcs",
    title: text("Factores de RCS con calibración publicada", "RCS factors with published calibration"),
    today: text(
      "Los factores y las matrices de correlación son heurísticas pedagógicas, no el modelo de la CNSF. Todo el módulo regulatorio hereda ese techo.",
      "The factors and correlation matrices are pedagogical heuristics, not the CNSF model. The whole regulatory module inherits that ceiling.",
    ),
    contribution: text(
      "Documentar una fuente CNSF/CUSF verificable por factor y sustituir cada heurística con su prueba correspondiente.",
      "Document a verifiable CNSF/CUSF source per factor and replace each heuristic with its matching test.",
    ),
    first: { label: text("Ver la fila del inventario", "See the inventory row"), href: INVENTORY_URL },
  },
  {
    id: "margen",
    title: text("Margen de riesgo por costo de capital", "Cost-of-capital risk margin"),
    today: text(
      "El margen de riesgo usa una simplificación declarada en lugar del método de costo de capital de la CUSF.",
      "The risk margin uses a declared simplification instead of the CUSF cost-of-capital method.",
    ),
    contribution: text(
      "Implementar el método de la CUSF con su fuente citada y contrastarlo contra la simplificación actual.",
      "Implement the CUSF method with its cited source and contrast it against the current simplification.",
    ),
    first: { label: text("Proponerlo en un issue", "Propose it in an issue"), href: ISSUES_URL },
  },
  {
    id: "triangulos",
    title: text("Oráculo independiente para triángulos", "Independent oracle for triangles"),
    today: text(
      "Mack y ODP se contrastan contra casos publicados fijos; la dependencia chainladder está declarada y sin uso.",
      "Mack and ODP are checked against fixed published cases; the chainladder dependency is declared and unused.",
    ),
    contribution: text(
      "Contrastar Mack, ODP y Bornhuetter-Ferguson contra chainladder sobre triángulos arbitrarios, no sólo sobre el caso de Taylor y Ashe.",
      "Cross-check Mack, ODP, and Bornhuetter-Ferguson against chainladder on arbitrary triangles, not only the Taylor–Ashe case.",
    ),
    first: { label: text("Proponerlo en un issue", "Propose it in an issue"), href: ISSUES_URL },
  },
  {
    id: "morbilidad",
    title: text("Morbilidad de GMM con fuente", "Sourced major-medical morbidity"),
    today: text(
      "Las tasas de morbilidad son bandas ilustrativas del laboratorio; una prima de salud es hoy un ejercicio contractual, no una tarifa.",
      "Morbidity rates are illustrative laboratory bands; a health premium today is a contractual exercise, not a tariff.",
    ),
    contribution: text(
      "Aportar una fuente de morbilidad pública y utilizable, con vigencia y unidades declaradas, y las pruebas que la fijen.",
      "Contribute a public, usable morbidity source with declared validity and units, and the tests that pin it.",
    ),
    first: { label: text("Proponerlo en un issue", "Propose it in an issue"), href: ISSUES_URL },
  },
  {
    id: "revision",
    title: text("Revisión actuarial externa de un dominio", "External actuarial review of a domain"),
    today: text(
      "Ningún dominio ha sido disputado por un actuario ajeno al proyecto. Las identidades encuentran errores de cálculo, no errores de planteamiento.",
      "No domain has been disputed by an actuary from outside the project. Identities catch calculation errors, not framing errors.",
    ),
    contribution: text(
      "Leer el caso explicado de un dominio y disputarlo con el formato de seis pasos. Es la aportación de menor fricción y la única que ve lo que las identidades no ven.",
      "Read one domain's explained case and dispute it using the six-step format. It is the lowest-friction contribution and the only one that sees what identities cannot.",
    ),
    first: { label: text("Leer el formato de contribución", "Read the contribution format"), href: CONTRIBUTING_URL },
  },
];

/** The six-step model-contribution format, summarized from CONTRIBUTING.md. */
export const CONTRIBUTE_STEPS: LocalizedText[] = [
  text("Propósito: la necesidad o decisión actuarial que se estudia.", "Purpose: the actuarial need or decision under study."),
  text("Beneficios o flujos: qué se paga, cuándo y bajo qué evento.", "Benefits or flows: what is paid, when, and under which event."),
  text("Supuestos: población, datos, tasas, unidades, vigencia y fuente.", "Assumptions: population, data, rates, units, validity, and source."),
  text("Método: fórmula, algoritmo y aproximaciones.", "Method: formula, algorithm, and approximations."),
  text("Resultados: medidas que ayudan a interpretar el modelo.", "Results: measures that help interpret the model."),
  text("Validación: identidades, casos límite, comparación y limitaciones.", "Validation: identities, boundary cases, comparison, and limitations."),
];
