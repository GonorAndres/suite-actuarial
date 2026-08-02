"use client";

import { useLanguage } from "@/lib/i18n/LanguageContext";
import type { DomainId } from "@/lib/domain-guides";
import { WORKBENCH_GUIDES } from "@/lib/workbench-guides";

const LABELS = {
  es: { active: "Modelo activo", calculation: "Qué calcula", use: "Para qué sirve", scope: "Alcance" },
  en: { active: "Active model", calculation: "What it calculates", use: "Why use it", scope: "Scope" },
} as const;

export function WorkbenchContext({ domain, model }: { domain: DomainId; model: string }) {
  const { lang } = useLanguage();
  const guide = WORKBENCH_GUIDES[domain][model];
  if (!guide) return null;
  const labels = LABELS[lang];

  return (
    <section className="border border-navy/15 bg-white/70" aria-live="polite">
      <div className="border-b border-navy/10 px-5 py-4">
        <p className="text-xs font-bold uppercase tracking-wider text-terracotta mb-1">{labels.active}</p>
        <h3 className="font-heading text-xl font-bold text-navy">{guide.title[lang]}</h3>
      </div>
      <div className="grid md:grid-cols-3">
        {([
          [labels.calculation, guide.calculation[lang]],
          [labels.use, guide.use[lang]],
          [labels.scope, guide.scope[lang]],
        ] as const).map(([title, body], index) => (
          <div key={title} className={`px-5 py-4 ${index ? "border-t md:border-t-0 md:border-l" : ""} border-navy/10`}>
            <h4 className="text-xs font-bold uppercase tracking-wider text-navy/55 mb-2">{title}</h4>
            <p className="text-sm leading-relaxed text-navy/75">{body}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
