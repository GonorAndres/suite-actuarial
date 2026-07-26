export const meta = {
  name: 'knowledge-docs',
  description: 'Author and adversarially verify the actuarial concept inventory for the two LaTeX knowledge documents',
  phases: [
    { title: 'Inventory', detail: 'fast repo sweep for a per-domain concept checklist', model: 'opus' },
    { title: 'Author', detail: 'one Opus agent per domain writes full concept entries', model: 'opus' },
    { title: 'Verify', detail: 'skeptical Opus reviewer checks formulas vs code, sources vs docs, writes final JSON', model: 'opus' },
  ],
}

const REPO = args.repo
const OUT = args.outDir

const DOMAINS = [
  { key: 'foundations', title: 'Actuarial foundations (interest, mortality, commutation, EPV)', paths: 'src/suite_actuarial/actuarial/, src/suite_actuarial/core/, src/suite_actuarial/data/' },
  { key: 'vida', title: 'Life insurance (vida)', paths: 'src/suite_actuarial/vida/' },
  { key: 'danos', title: 'Property and casualty (danos)', paths: 'src/suite_actuarial/danos/' },
  { key: 'salud', title: 'Health insurance (salud)', paths: 'src/suite_actuarial/salud/' },
  { key: 'pensiones', title: 'Pensions (pensiones)', paths: 'src/suite_actuarial/pensiones/' },
  { key: 'reservas', title: 'Technical reserves (reservas)', paths: 'src/suite_actuarial/reservas/' },
  { key: 'reaseguro', title: 'Reinsurance (reaseguro)', paths: 'src/suite_actuarial/reaseguro/' },
  { key: 'regulatorio', title: 'Regulatory and solvency (regulatorio + annual config)', paths: 'src/suite_actuarial/regulatorio/, src/suite_actuarial/config/' },
  { key: 'engineering', title: 'Engineering and architecture (API, Decimal policy, validation, testing, reporting)', paths: 'src/suite_actuarial/api/, src/suite_actuarial/reportes/, src/suite_actuarial/core/, AGENTS.md, frontend/src/lib/' },
]

const CONCEPT_FIELDS = {
  name: { type: 'string' },
  intuition: { type: 'string' },
  analogy: { type: 'string' },
  in_project: { type: 'string' },
  formula_latex: { type: 'string' },
  source: { type: 'string' },
  code_path: { type: 'string' },
  test_path: { type: 'string' },
}

const CONCEPTS_SCHEMA = {
  type: 'object',
  required: ['domain', 'concepts'],
  properties: {
    domain: { type: 'string' },
    concepts: {
      type: 'array',
      items: {
        type: 'object',
        required: ['name', 'intuition', 'analogy', 'in_project', 'formula_latex', 'source', 'code_path', 'test_path'],
        properties: CONCEPT_FIELDS,
      },
    },
  },
}

const INV_SCHEMA = {
  type: 'object',
  required: ['domains'],
  properties: {
    domains: {
      type: 'array',
      items: {
        type: 'object',
        required: ['key', 'concepts'],
        properties: {
          key: { type: 'string' },
          concepts: { type: 'array', items: { type: 'string' } },
        },
      },
    },
  },
}

phase('Inventory')
const inventory = await agent(
  `Fast concept sweep of the repository ${REPO} (a Python actuarial toolkit for the Mexican insurance market).\n\n` +
  `For each of these domain keys, skim the corresponding code (module and file names, docstrings, class/function names) and list the concept names that domain implements:\n` +
  DOMAINS.map(d => `- ${d.key}: ${d.title} -> ${d.paths}`).join('\n') +
  `\n\nAlso skim README.md, docs/REGULATORY.md and docs/VALIDATION.md for concepts the code names implicitly (regulatory reserves, RCS/SCR, UMA, mortality tables, etc.).\n` +
  `Return concept NAMES only (short strings, English, Spanish term in parentheses where the code uses it). 5-15 per domain. Skim; do not deep-read implementations.`,
  { label: 'inventory', model: 'opus', schema: INV_SCHEMA }
)

const checklistFor = (key) => {
  const found = ((inventory && inventory.domains) || []).find(x => x.key === key)
  return found && found.concepts && found.concepts.length ? found.concepts.join('; ') : '(no checklist available - build your own from the code)'
}

const authorPrompt = (d) =>
  `You are an actuarial documentation author working in the repository ${REPO} (Python actuarial toolkit for the Mexican insurance market).\n\n` +
  `Domain assigned to you: ${d.title}.\nPrimary code locations: ${d.paths}.\n\n` +
  `Task: produce the definitive concept inventory for this domain. It feeds two LaTeX documents: an intuitive interview companion (plain English) and a technical reference (formulas + sources + code map).\n\n` +
  `Method:\n` +
  `1. Read the module code under the primary locations, the matching tests under tests/unit/ and tests/integration/, and docs/REGULATORY.md / docs/VALIDATION.md where relevant.\n` +
  `2. Cover every substantive concept the code implements. Use this checklist from a prior sweep as a floor, not a ceiling: ${checklistFor(d.key)}\n` +
  `3. For each concept fill ALL fields:\n` +
  `   - name: concise English name (keep the Spanish domain term in parentheses when the code uses it).\n` +
  `   - intuition: 2-3 plain-English sentences a non-technical interviewer would understand. No jargon, no formulas.\n` +
  `   - analogy: one everyday-life analogy.\n` +
  `   - in_project: one sentence on what this suite actually does with the concept.\n` +
  `   - formula_latex: the key formula in LaTeX math notation (math-mode content only, NO $ delimiters, no custom macros), matching what the code actually implements. Empty string if the concept is genuinely non-mathematical.\n` +
  `   - source: regulatory or actuarial source (CNSF/CUSF chapter, named mortality table, or a standard reference such as Bowers et al.). Never invent a citation; if unsure, describe the source generically and honestly.\n` +
  `   - code_path: repo-relative path(s) to the implementing module (add the function/class name after a colon).\n` +
  `   - test_path: repo-relative path(s) to the test file(s) verifying it.\n\n` +
  `Accuracy over quantity: every formula must match the implementation and every path must exist. Aim for the 6-14 concepts that genuinely define this domain.`

const verifyPrompt = (d, authored, outFile) =>
  `You are a skeptical actuarial reviewer working in the repository ${REPO}.\n\n` +
  `Below is a JSON concept inventory for the domain "${d.title}" produced by another agent. Verify it, correct it, and persist it.\n\n` +
  `For EVERY concept:\n` +
  `1. Open the claimed code_path and test_path. Fix any path that does not exist by locating the real one; delete the entry only if the concept is not implemented anywhere.\n` +
  `2. Check formula_latex against the actual implementation (formula shape, rounding, Decimal usage). Correct mismatches so the document matches the code, and make sure it is valid LaTeX math content without $ delimiters or custom macros.\n` +
  `3. Check source claims against docs/REGULATORY.md and docs/VALIDATION.md. Downgrade any citation you cannot substantiate to a generic but honest description.\n` +
  `4. Ensure intuition and analogy are plain English, jargon-free, and factually right.\n` +
  `5. Add any obviously missing core concept of this domain that the author skipped (fully filled in and verified the same way).\n\n` +
  `Then use the Write tool to save the corrected JSON, same shape {"domain": ..., "concepts": [...]}, to this EXACT file path: ${outFile}\n\n` +
  `Return only a short plain-text summary: how many concepts were kept/added/removed and a bullet list of corrections made.\n\n` +
  `JSON to verify:\n${JSON.stringify(authored)}`

async function pool(items, limit, fn) {
  const results = new Array(items.length)
  let next = 0
  async function worker() {
    while (next < items.length) {
      const idx = next
      next = next + 1
      try {
        results[idx] = await fn(items[idx], idx)
      } catch (e) {
        results[idx] = null
      }
    }
  }
  const workers = []
  const n = Math.min(limit, items.length)
  for (let i = 0; i < n; i++) workers.push(worker())
  await Promise.all(workers)
  return results
}

log('Inventory done; running 9 domain chains (author -> verify) with max 4 concurrent agents')

const results = await pool(DOMAINS, 4, async (d) => {
  const authored = await agent(authorPrompt(d), { label: `author:${d.key}`, phase: 'Author', model: 'opus', schema: CONCEPTS_SCHEMA })
  if (!authored || !authored.concepts || !authored.concepts.length) return { domain: d.key, file: null, note: 'author returned nothing' }
  const outFile = `${OUT}/${d.key}.json`
  const note = await agent(verifyPrompt(d, authored, outFile), { label: `verify:${d.key}`, phase: 'Verify', model: 'opus' })
  return { domain: d.key, file: outFile, authoredCount: authored.concepts.length, verifierNote: note }
})

return results.filter(Boolean)
