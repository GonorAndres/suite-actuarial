import type { Lang } from "@/lib/i18n/translations";

export type DomainId =
  | "vida"
  | "danos"
  | "salud"
  | "pensiones"
  | "reservas"
  | "reaseguro"
  | "regulatorio";

export type LocalizedText = Record<Lang, string>;

export interface GuideAssumption {
  name: LocalizedText;
  value: LocalizedText;
  source: LocalizedText;
  status: "sourced" | "illustrative" | "synthetic" | "method";
}

export interface DomainGuideDefinition {
  id: DomainId;
  question: LocalizedText;
  decision: LocalizedText;
  flows: LocalizedText[];
  assumptions: GuideAssumption[];
  method: {
    name: LocalizedText;
    formula: string;
    explanation: LocalizedText;
  };
  interpretation: LocalizedText;
  validation: LocalizedText[];
  limitations: LocalizedText[];
  workbenchModel: string;
}

const text = (es: string, en: string): LocalizedText => ({ es, en });

export const DOMAIN_GUIDES: Record<DomainId, DomainGuideDefinition> = {
  vida: {
    id: "vida",
    question: text(
      "¿Qué prima financia un beneficio por fallecimiento durante un plazo definido?",
      "What premium funds a death benefit during a defined term?",
    ),
    decision: text(
      "Comparar costo, duración de protección y patrón de reservas antes de elegir temporal, vida entera o dotal.",
      "Compare cost, protection period, and reserve pattern before choosing term, whole life, or endowment coverage.",
    ),
    flows: [
      text("Primas mientras la póliza esté vigente.", "Premiums while the policy remains in force."),
      text("Suma asegurada al final del año de fallecimiento cubierto.", "Sum assured at the end of the covered year of death."),
      text("El temporal no paga supervivencia ni acumula rescate en este modelo.", "The term model pays no survival benefit and builds no surrender value."),
    ],
    assumptions: [
      { name: text("Mortalidad", "Mortality"), value: text("EMSSA-09 incluida", "Bundled EMSSA-09"), source: text("Tabla sintética del laboratorio", "Synthetic laboratory table"), status: "synthetic" },
      { name: text("Tasa técnica", "Technical rate"), value: text("5.5% anual", "5.5% yearly"), source: text("Supuesto ilustrativo, modificable", "Illustrative, editable assumption"), status: "illustrative" },
      { name: text("Momento del beneficio", "Benefit timing"), value: text("Fin del año de fallecimiento", "End of year of death"), source: text("Convención del modelo", "Model convention"), status: "method" },
    ],
    method: {
      name: text("Principio de equivalencia", "Equivalence principle"),
      formula: "P · äₓ:ₙ = SA · A¹ₓ:ₙ",
      explanation: text("La prima neta iguala el valor presente actuarial de primas y beneficios; los recargos se muestran por separado.", "The net premium equates the actuarial present value of premiums and benefits; loadings are shown separately."),
    },
    interpretation: text("La sensibilidad separa el efecto de exposición —suma y plazo— del efecto biométrico de la edad.", "Sensitivity separates exposure effects—amount and term—from the biometric effect of age."),
    validation: [text("Identidades de conmutación y equivalencia.", "Commutation and equivalence identities."), text("Recursión de Fackler para reservas del dotal.", "Fackler recursion for endowment reserves.")],
    limitations: [text("La tabla de mortalidad es sintética y no valida una tarifa profesional.", "The mortality table is synthetic and does not validate a professional tariff."), text("Los recargos son ilustrativos y no representan gastos observados.", "Loadings are illustrative and do not represent observed expenses.")],
    workbenchModel: "temporal",
  },
  danos: {
    id: "danos",
    question: text("¿Cómo cambian la prima y la retención cuando cambia el deducible?", "How do premium and retention change when the deductible changes?"),
    decision: text("Elegir cuánto riesgo conserva el asegurado sin confundir menor prima con menor costo total del riesgo.", "Choose how much risk the insured retains without confusing a lower premium with a lower total cost of risk."),
    flows: [text("Prima anual a la aseguradora.", "Annual premium to the insurer."), text("Deducible pagado por el asegurado en cada pérdida cubierta.", "Deductible paid by the insured on each covered loss."), text("Indemnización sujeta a cobertura y límites.", "Indemnity subject to coverage and limits.")],
    assumptions: [
      { name: text("Tarifa base", "Base tariff"), value: text("Factores vehiculares y de zona", "Vehicle and zone factors"), source: text("Tablas representativas, no oficiales", "Representative, non-official tables"), status: "illustrative" },
      { name: text("Deducible", "Deductible"), value: text("Porcentaje del valor del vehículo", "Percentage of vehicle value"), source: text("Diseño del ejemplo", "Example design"), status: "method" },
      { name: text("Moneda", "Currency"), value: text("MXN nominal", "Nominal MXN"), source: text("Unidad declarada", "Declared unit"), status: "method" },
    ],
    method: { name: text("Tarificación multiplicativa", "Multiplicative rating"), formula: "Prima = Tasa base × Exposición × Factores", explanation: text("Cada factor modifica una tasa base; el deducible reduce la parte esperada transferida.", "Each factor modifies a base rate; the deductible reduces the expected transferred portion.") },
    interpretation: text("La prima baja al aumentar el deducible, pero la pérdida retenida por evento aumenta.", "Premium falls as the deductible rises, but retained loss per event increases."),
    validation: [text("Pruebas de monotonicidad y límites de factores.", "Monotonicity and factor-boundary tests."), text("Casos calculados a mano para coberturas y bonus-malus.", "Hand-calculated coverage and bonus-malus cases.")],
    limitations: [text("Las tablas de tarifa no son datos AMIS oficiales vigentes.", "Rating tables are not current official AMIS data."), text("La RC de terceros usa una aproximación pedagógica documentada.", "Third-party liability uses a documented pedagogical approximation.")],
    workbenchModel: "auto",
  },
  salud: {
    id: "salud",
    question: text("¿Cómo se reparte un gasto médico entre asegurado y aseguradora?", "How is a medical expense shared between insured and insurer?"),
    decision: text("Examinar conjuntamente prima, deducible, coaseguro, tope y suma asegurada.", "Examine premium, deductible, coinsurance, cap, and sum insured together."),
    flows: [text("Deducible inicial a cargo del asegurado.", "Initial deductible borne by the insured."), text("Coaseguro sobre el gasto elegible restante.", "Coinsurance on remaining eligible expense."), text("Pago de la aseguradora sujeto al límite contractual.", "Insurer payment subject to the contractual limit.")],
    assumptions: [
      { name: text("Morbilidad", "Morbidity"), value: text("Bandas por edad", "Age bands"), source: text("Tasas ilustrativas del laboratorio", "Illustrative laboratory rates"), status: "illustrative" },
      { name: text("Nivel hospitalario", "Hospital level"), value: text("Factor relativo", "Relative factor"), source: text("Supuesto del modelo", "Model assumption"), status: "illustrative" },
      { name: text("Tendencia médica", "Medical trend"), value: text("No modelada", "Not modeled"), source: text("Límite explícito", "Explicit limitation"), status: "method" },
    ],
    method: { name: text("Costo compartido", "Cost sharing"), formula: "Pago aseguradora = min(SA, (Gasto − Deducible) × (1 − coaseguro))", explanation: text("La estructura contractual se calcula por separado de la tarifa ilustrativa.", "The contractual cost-sharing structure is calculated separately from the illustrative tariff.") },
    interpretation: text("Una prima por edad no es una proyección de renovación: el motor no incorpora experiencia ni tendencia médica.", "An age-based premium is not a renewal projection: the engine includes neither experience nor medical trend."),
    validation: [text("Fronteras de deducible, coaseguro y suma asegurada.", "Deductible, coinsurance, and sum-insured boundaries."), text("Contrastes de indemnización para accidentes.", "Accident indemnity cross-checks.")],
    limitations: [text("No existe modelo de frecuencia-severidad con datos de experiencia.", "There is no frequency-severity model based on experience data."), text("La siniestralidad derivada de prima es circular y sólo ilustrativa.", "Loss ratio derived from premium is circular and illustrative only.")],
    workbenchModel: "gmm",
  },
  pensiones: {
    id: "pensiones",
    question: text("¿Cómo se transforma historial laboral o ahorro en ingreso de retiro?", "How does employment history or savings become retirement income?"),
    decision: text("Distinguir un beneficio definido por reglas de una renta financiada por saldo individual.", "Distinguish a rule-defined benefit from an annuity funded by an individual balance."),
    flows: [text("Ley 73: pensión ligada a semanas, salario y edad.", "Ley 73: benefit tied to weeks, wage, and age."), text("Ley 97: saldo individual convertido en renta.", "Ley 97: individual balance converted into an annuity."), text("La renta transfiere riesgo de longevidad al proveedor.", "The annuity transfers longevity risk to the provider.")],
    assumptions: [
      { name: text("Régimen", "Regime"), value: text("Ley 73 o Ley 97", "Ley 73 or Ley 97"), source: text("Fecha de afiliación declarada por el caso", "Enrollment date declared by the case"), status: "sourced" },
      { name: text("Mortalidad de renta", "Annuity mortality"), value: text("EMSSA-09 incluida", "Bundled EMSSA-09"), source: text("Tabla sintética", "Synthetic table"), status: "synthetic" },
      { name: text("Fraccionamiento", "Payment frequency"), value: text("Corrección 1/m", "1/m correction"), source: text("Aproximación de Woolhouse, primer término", "First-term Woolhouse approximation"), status: "method" },
    ],
    method: { name: text("Conmutación y anualidades", "Commutation and annuities"), formula: "Renta anual = Saldo / äₓ", explanation: text("El factor de renta combina supervivencia y descuento; Ley 73 sigue una ruta reglada distinta.", "The annuity factor combines survival and discounting; Ley 73 follows a separate rule-based path.") },
    interpretation: text("El mismo saldo compra una renta distinta cuando cambian mortalidad, tasa o frecuencia de pago.", "The same balance buys a different annuity when mortality, rate, or payment frequency changes."),
    validation: [text("Identidad a interés cero: äₓ = 1 + eₓ.", "Zero-interest identity: äₓ = 1 + eₓ."), text("Casos Ley 73 con semanas mínimas y factores de edad.", "Ley 73 cases for minimum weeks and age factors.")],
    limitations: [text("Ley 97 omite el seguro de sobrevivencia requerido en un modelo completo.", "Ley 97 omits survivor insurance required in a complete model."), text("Ley 73 simplifica la tabla por nivel salarial.", "Ley 73 simplifies the wage-level table.")],
    workbenchModel: "ley73",
  },
  reservas: {
    id: "reservas",
    question: text("¿Qué costo de siniestros aún no aparece en los pagos observados?", "Which claims cost has not yet emerged in observed payments?"),
    decision: text("Seleccionar un estimador central y declarar por separado desarrollo, cola e incertidumbre.", "Select a central estimate and separately disclose development, tail, and uncertainty."),
    flows: [text("Pagos o incurridos observados por origen y desarrollo.", "Observed paid or incurred claims by origin and development."), text("Celdas futuras proyectadas hasta el ultimate.", "Future cells projected to ultimate."), text("Reserva igual a ultimate menos observado.", "Reserve equals ultimate less observed." )],
    assumptions: [
      { name: text("Triángulo", "Triangle"), value: text("Acumulado, millones MXN", "Cumulative, MXN millions"), source: text("Caso reproducible 2019–2024", "Reproducible 2019–2024 case"), status: "illustrative" },
      { name: text("Patrón", "Pattern"), value: text("Estable entre años de origen", "Stable across origin years"), source: text("Supuesto Chain Ladder", "Chain Ladder assumption"), status: "method" },
      { name: text("Cola", "Tail"), value: text("Declarada o Sherman", "Declared or Sherman"), source: text("Extrapolación explícita", "Explicit extrapolation"), status: "method" },
    ],
    method: { name: text("Chain Ladder ponderado", "Volume-weighted Chain Ladder"), formula: "Reserva = Σ(Ultimateᵢ − Observadoᵢ)", explanation: text("Los factores desarrollan cada diagonal; Mack y bootstrap ODP cuantifican error condicionado al modelo.", "Factors develop each diagonal; Mack and ODP bootstrap quantify error conditional on the model.") },
    interpretation: text("El factor de cola puede mover materialmente la reserva aunque ninguna celda observada lo identifique por sí sola.", "The tail factor can materially move the reserve even though no observed cell identifies it by itself."),
    validation: [text("Mack reproduce Taylor & Ashe al peso.", "Mack reproduces Taylor & Ashe to the currency unit."), text("Bootstrap ODP reproduce φ publicado y concilia con Chain Ladder.", "ODP bootstrap reproduces published φ and reconciles with Chain Ladder.")],
    limitations: [text("Mack y ODP no cubren riesgo de modelo, cambio de mezcla ni inflación no observada.", "Mack and ODP do not cover model risk, mix change, or unobserved inflation."), text("Toda cola es extrapolación y requiere justificación externa.", "Every tail is extrapolation and requires external justification.")],
    workbenchModel: "chainladder",
  },
  reaseguro: {
    id: "reaseguro",
    question: text("¿Cómo se reparte una pérdida catastrófica entre cedente y reasegurador?", "How is a catastrophe loss split between cedent and reinsurer?"),
    decision: text("Elegir prioridad, capacidad y agregado coherentes con la cola que se desea transferir.", "Choose attachment, capacity, and aggregate consistent with the tail to be transferred."),
    flows: [text("La cedente retiene la prioridad por evento.", "The cedent retains the per-event attachment."), text("El reasegurador paga el exceso hasta el límite de capa.", "The reinsurer pays excess loss up to layer capacity."), text("Pérdidas sobre el agotamiento vuelven a la cedente.", "Loss above exhaustion returns to the cedent.")],
    assumptions: [
      { name: text("Capa", "Layer"), value: text("$80M xs $20M", "$80M xs $20M"), source: text("Contrato ilustrativo 2026", "Illustrative 2026 contract"), status: "illustrative" },
      { name: text("Límite agregado", "Aggregate limit"), value: text("Capacidad × reinstalaciones", "Capacity × reinstatements"), source: text("Convención contractual implementada", "Implemented contract convention"), status: "method" },
      { name: text("Prima de reinstalación", "Reinstatement premium"), value: text("Pro rata a cantidad", "Pro rata as to amount"), source: text("Simplificación declarada", "Declared simplification"), status: "method" },
    ],
    method: { name: text("Exceso de pérdida", "Excess of loss"), formula: "Recuperación = min(max(0, S − prioridad), capacidad)", explanation: text("La identidad se aplica por ocurrencia y luego contra el agregado disponible.", "The identity applies per occurrence and then against remaining aggregate capacity.") },
    interpretation: text("La capa protege el intervalo contratado; no elimina la retención inferior ni la pérdida superior al agotamiento.", "The layer protects the contracted interval; it removes neither the lower retention nor loss above exhaustion."),
    validation: [text("Capas canónicas calculadas a mano: 5 xs 5, 5 xs 10 y 10 xs 20.", "Canonical hand-calculated layers: 5 xs 5, 5 xs 10, and 10 xs 20."), text("Pruebas de erosión agregada y reinstalaciones.", "Aggregate erosion and reinstatement tests.")],
    limitations: [text("El prorrateo de reinstalación no considera tiempo ni tasas escalonadas.", "Reinstatement proration considers neither time nor tiered rates."), text("La semántica de resultado neto difiere entre contratos y permanece inventariada.", "Net-result semantics differ across treaties and remain inventoried." )],
    workbenchModel: "xl",
  },
  regulatorio: {
    id: "regulatorio",
    question: text("¿Cuánto capital disponible cubre un requerimiento agregado de riesgo?", "How much available capital covers an aggregate risk requirement?"),
    decision: text("Interpretar cobertura y diversificación sin presentar una heurística como cálculo CNSF vigente.", "Interpret coverage and diversification without presenting a heuristic as a current CNSF calculation."),
    flows: [text("Módulos de vida, daños e inversión.", "Life, P&C, and investment modules."), text("Agregación con correlaciones pedagógicas.", "Aggregation with pedagogical correlations."), text("Capital disponible comparado con RCS total.", "Available capital compared with total RCS.")],
    assumptions: [
      { name: text("Factores RCS", "RCS factors"), value: text("Rampas y porcentajes simplificados", "Simplified ramps and percentages"), source: text("Heurísticas pedagógicas, no CNSF", "Pedagogical heuristics, not CNSF"), status: "illustrative" },
      { name: text("Correlaciones", "Correlations"), value: text("Matriz fija", "Fixed matrix"), source: text("Supuesto del laboratorio", "Laboratory assumption"), status: "illustrative" },
      { name: text("Cobertura", "Coverage"), value: text("Capital / RCS", "Capital / RCS"), source: text("Definición canónica del paquete", "Canonical package definition"), status: "method" },
    ],
    method: { name: text("Agregación cuadrática", "Quadratic aggregation"), formula: "RCS = √(rᵀ · ρ · r)", explanation: text("La matriz reconoce dependencia entre módulos; la cobertura se calcula después de agregar.", "The matrix recognizes dependence across modules; coverage is calculated after aggregation." ) },
    interpretation: text("Un índice mayor que 1 cubre el requerimiento del escenario, no certifica solvencia regulatoria.", "A ratio above 1 covers this scenario's requirement; it does not certify regulatory solvency."),
    validation: [text("Orientación capital/RCS probada por escala, frontera e insuficiencia.", "Capital/RCS orientation tested by scale, boundary, and insufficiency."), text("Identidad: agregado no excede la suma de módulos bajo la matriz usada.", "Identity: aggregate does not exceed the module sum under the matrix used." )],
    limitations: [text("Los factores no implementan el modelo estocástico completo de la CNSF.", "Factors do not implement the complete CNSF stochastic model."), text("Las rutas SAT contienen tasas y citas aún sin verificar; deben mostrarse como indeterminadas.", "SAT paths contain unverified rates and citations and must be shown as indeterminate." )],
    workbenchModel: "rcs",
  },
};

export const GUIDE_STATUS_LABELS: Record<GuideAssumption["status"], LocalizedText> = {
  sourced: text("Con fuente", "Sourced"),
  illustrative: text("Ilustrativo", "Illustrative"),
  synthetic: text("Sintético", "Synthetic"),
  method: text("Convención", "Convention"),
};
