import { expect, test } from "@playwright/test";
import { DOMAIN_GUIDES } from "../src/lib/domain-guides";
import { WORKBENCH_GUIDES } from "../src/lib/workbench-guides";
import { translations } from "../src/lib/i18n/translations";

test("the translation dictionaries hold exact key parity", () => {
  // `t()` falls back to the raw key, so a missing English key would render
  // `hero_titulo` as indexable text on /en/. TypeScript already rejects a key
  // that exists in one dictionary and not the other; this keeps the guarantee
  // visible and gated even if the typing changes shape.
  expect(Object.keys(translations.en).sort()).toEqual(Object.keys(translations.es).sort());
});

test("every domain guide is bilingual and decision-complete", () => {
  const guides = Object.values(DOMAIN_GUIDES);
  expect(guides).toHaveLength(7);
  for (const guide of guides) {
    for (const value of [guide.question, guide.decision, guide.interpretation]) {
      expect(value.es.trim()).not.toBe("");
      expect(value.en.trim()).not.toBe("");
    }
    expect(guide.flows).toHaveLength(3);
    expect(guide.assumptions.length).toBeGreaterThanOrEqual(3);
    expect(guide.method.formula.trim()).not.toBe("");
    expect(guide.validation.length).toBeGreaterThanOrEqual(2);
    expect(guide.limitations.length).toBeGreaterThanOrEqual(2);
    expect(guide.workbenchModel.trim()).not.toBe("");
    for (const assumption of guide.assumptions) {
      expect(assumption.source.es.trim()).not.toBe("");
      expect(assumption.source.en.trim()).not.toBe("");
    }
  }
});

test("every workbench model explains calculation, use, and scope in both languages", () => {
  const expectedModels = {
    vida: ["temporal", "ordinario", "dotal", "comparar"],
    danos: ["auto", "incendio", "rc", "bonus_malus", "freq_sev"],
    salud: ["gmm", "accidentes"],
    pensiones: ["ley73", "ley97", "renta_vitalicia", "conmutacion"],
    reservas: ["chainladder", "bornhuetter", "bootstrap"],
    reaseguro: ["quotashare", "xl", "stoploss"],
    regulatorio: ["rcs", "deducibilidad", "retenciones"],
  } as const;

  for (const [domain, models] of Object.entries(expectedModels)) {
    expect(Object.keys(WORKBENCH_GUIDES[domain as keyof typeof WORKBENCH_GUIDES])).toEqual(models);
    for (const model of models) {
      const guide = WORKBENCH_GUIDES[domain as keyof typeof WORKBENCH_GUIDES][model];
      for (const field of [guide.title, guide.calculation, guide.use, guide.scope]) {
        expect(field.es.trim()).not.toBe("");
        expect(field.en.trim()).not.toBe("");
      }
    }
  }
});
