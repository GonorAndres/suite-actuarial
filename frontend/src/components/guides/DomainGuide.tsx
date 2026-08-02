"use client";

import type { ReactNode } from "react";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import {
  DOMAIN_GUIDES,
  GUIDE_STATUS_LABELS,
  type DomainId,
  type LocalizedText,
} from "@/lib/domain-guides";

const LABELS = {
  es: {
    kicker: "Caso actuarial explicado",
    purpose: "Propósito",
    flows: "Beneficios y flujos",
    assumptions: "Supuestos",
    method: "Método",
    results: "Resultados e interpretación",
    validation: "Validación y límites",
    decision: "Decisión que informa",
    assumption: "Supuesto",
    value: "Valor / unidad",
    source: "Fuente y estado",
    evidence: "Qué se comprueba",
    limits: "Qué no demuestra",
  },
  en: {
    kicker: "Actuarial case explained",
    purpose: "Purpose",
    flows: "Benefits and cash flows",
    assumptions: "Assumptions",
    method: "Method",
    results: "Results and interpretation",
    validation: "Validation and limits",
    decision: "Decision informed",
    assumption: "Assumption",
    value: "Value / unit",
    source: "Source and status",
    evidence: "What is checked",
    limits: "What it does not prove",
  },
} as const;

function local(value: LocalizedText, lang: "es" | "en") {
  return value[lang];
}

export function DomainGuide({ domain, children }: { domain: DomainId; children: ReactNode }) {
  const { lang } = useLanguage();
  const guide = DOMAIN_GUIDES[domain];
  const labels = LABELS[lang];

  return (
    <article className="border-y border-navy/15 bg-white/35 -mx-6 px-6 py-8" aria-labelledby={`${domain}-guide-title`}>
      <div className="flex flex-col gap-3 mb-7">
        <p className="kicker">{labels.kicker}</p>
        <h2 id={`${domain}-guide-title`} className="font-heading text-2xl md:text-3xl font-bold text-navy max-w-4xl">
          {local(guide.question, lang)}
        </h2>
      </div>

      <div className="space-y-10">
        <section id={`${domain}-step-1`} className="grid md:grid-cols-[10rem_1fr] gap-4 scroll-mt-28">
          <GuideHeading title={labels.purpose} />
          <div className="border-l-2 border-terracotta pl-5">
            <p className="text-sm uppercase tracking-wider font-semibold text-navy/50 mb-2">{labels.decision}</p>
            <p className="text-lg leading-relaxed text-navy/85">{local(guide.decision, lang)}</p>
          </div>
        </section>

        <section id={`${domain}-step-2`} className="grid md:grid-cols-[10rem_1fr] gap-4 scroll-mt-28">
          <GuideHeading title={labels.flows} />
          <ol className="grid md:grid-cols-3 gap-3">
            {guide.flows.map((flow, index) => <li key={flow.es} className="border border-navy/10 bg-white px-4 py-4 text-sm leading-relaxed text-navy/75"><span className="block font-mono text-terracotta mb-2">{index + 1}</span>{local(flow, lang)}</li>)}
          </ol>
        </section>

        <section id={`${domain}-step-3`} className="grid md:grid-cols-[10rem_1fr] gap-4 scroll-mt-28">
          <GuideHeading title={labels.assumptions} />
          <div className="overflow-x-auto border border-navy/10 bg-white">
            <table className="w-full text-left text-sm">
              <thead className="bg-navy text-offwhite"><tr><th className="px-4 py-3">{labels.assumption}</th><th className="px-4 py-3">{labels.value}</th><th className="px-4 py-3">{labels.source}</th></tr></thead>
              <tbody>{guide.assumptions.map((item) => <tr key={item.name.es} className="border-t border-navy/10 align-top"><th className="px-4 py-3 text-navy">{local(item.name, lang)}</th><td className="px-4 py-3 text-navy/75">{local(item.value, lang)}</td><td className="px-4 py-3 text-navy/65"><span className="inline-block text-[0.68rem] font-bold uppercase tracking-wider text-terracotta mb-1">{local(GUIDE_STATUS_LABELS[item.status], lang)}</span><br />{local(item.source, lang)}</td></tr>)}</tbody>
            </table>
          </div>
        </section>

        <section id={`${domain}-step-4`} className="grid md:grid-cols-[10rem_1fr] gap-4 scroll-mt-28">
          <GuideHeading title={labels.method} />
          <div className="grid lg:grid-cols-[1fr_auto] gap-5 items-center border border-navy/10 bg-white px-5 py-5">
            <div><h3 className="font-heading font-bold text-xl text-navy mb-2">{local(guide.method.name, lang)}</h3><p className="text-sm leading-relaxed text-navy/70">{local(guide.method.explanation, lang)}</p></div>
            <code className="block bg-navy text-offwhite px-5 py-4 font-mono text-sm md:text-base whitespace-nowrap overflow-x-auto">{guide.method.formula}</code>
          </div>
        </section>

        <section id={`${domain}-step-5`} className="scroll-mt-28">
          <div className="grid md:grid-cols-[10rem_1fr] gap-4 mb-4"><GuideHeading title={labels.results} /><p className="text-navy/70 leading-relaxed">{local(guide.interpretation, lang)}</p></div>
          {children}
        </section>

        <section id={`${domain}-step-6`} className="grid md:grid-cols-[10rem_1fr] gap-4 scroll-mt-28">
          <GuideHeading title={labels.validation} />
          <div className="grid lg:grid-cols-2 gap-4">
            <EvidenceList title={labels.evidence} items={guide.validation.map((item) => local(item, lang))} tone="navy" />
            <EvidenceList title={labels.limits} items={guide.limitations.map((item) => local(item, lang))} tone="terracotta" />
          </div>
        </section>
      </div>

    </article>
  );
}

function GuideHeading({ title }: { title: string }) {
  return <h3 className="font-heading font-bold text-navy">{title}</h3>;
}

function EvidenceList({ title, items, tone }: { title: string; items: string[]; tone: "navy" | "terracotta" }) {
  return <div className={`border-t-2 ${tone === "navy" ? "border-navy" : "border-terracotta"} bg-white border-x border-b border-navy/10 px-5 py-4`}><h4 className="font-heading font-bold text-navy mb-3">{title}</h4><ul className="space-y-2">{items.map((item) => <li key={item} className="flex gap-3 text-sm leading-relaxed text-navy/70"><span className={tone === "navy" ? "text-navy" : "text-terracotta"}>—</span>{item}</li>)}</ul></div>;
}
