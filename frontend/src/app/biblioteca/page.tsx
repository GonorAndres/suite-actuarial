"use client";

import Link from "next/link";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import { DOMAIN_GUIDES, type DomainId } from "@/lib/domain-guides";

const DOMAINS: { id: DomainId; name: { es: string; en: string }; models: { es: string; en: string } }[] = [
  { id: "vida", name: { es: "Vida", en: "Life" }, models: { es: "Temporal, ordinario, dotal y comparación", en: "Term, whole life, endowment, and comparison" } },
  { id: "danos", name: { es: "Daños", en: "P&C" }, models: { es: "Auto, incendio, RC, bonus-malus y frecuencia-severidad", en: "Auto, fire, liability, bonus-malus, and frequency-severity" } },
  { id: "salud", name: { es: "Salud", en: "Health" }, models: { es: "GMM y accidentes", en: "Major medical and accidents" } },
  { id: "pensiones", name: { es: "Pensiones", en: "Pensions" }, models: { es: "Ley 73/97, renta vitalicia y conmutación", en: "Ley 73/97, life annuity, and commutation" } },
  { id: "reservas", name: { es: "Reservas", en: "Reserves" }, models: { es: "Chain Ladder, Bornhuetter-Ferguson y bootstrap ODP", en: "Chain Ladder, Bornhuetter-Ferguson, and ODP bootstrap" } },
  { id: "reaseguro", name: { es: "Reaseguro", en: "Reinsurance" }, models: { es: "Cuota parte, exceso de pérdida y stop loss", en: "Quota share, excess of loss, and stop loss" } },
  { id: "regulatorio", name: { es: "Referencia regulatoria", en: "Regulatory reference" }, models: { es: "RCS, deducibilidad y retenciones", en: "RCS, deductibility, and withholding" } },
];

export default function LibraryPage() {
  const { lang } = useLanguage();
  return (
    <div className="max-w-6xl mx-auto px-6 py-12">
      <header className="max-w-3xl mb-10">
        <p className="kicker mb-3">{lang === "es" ? "Biblioteca actuarial" : "Actuarial library"}</p>
        <h1 className="font-heading text-4xl md:text-5xl font-bold text-navy mb-4">{lang === "es" ? "Modelos organizados por la decisión que ayudan a tomar" : "Models organized by the decision they inform"}</h1>
        <p className="text-lg leading-relaxed text-navy/65">{lang === "es" ? "Cada dominio tiene dos vistas. El caso explicado recorre los flujos, los supuestos, el método, el resultado y los límites; el Workbench sirve para calcular con tus propios parámetros." : "Each domain has two views. The explained case walks through the flows, assumptions, method, result, and limits; the Workbench is for calculating with your own parameters."}</p>
      </header>

      <div className="grid lg:grid-cols-2 gap-5">
        {DOMAINS.map((domain, index) => {
          const guide = DOMAIN_GUIDES[domain.id];
          return (
            <article key={domain.id} className="bg-white border border-navy/15 border-t-2 border-t-navy p-6 flex flex-col">
              <div className="flex items-start justify-between gap-4 mb-5"><div><p className="font-mono text-xs text-terracotta mb-1">{String(index + 1).padStart(2, "0")}</p><h2 className="font-heading text-2xl font-bold text-navy">{domain.name[lang]}</h2></div><span className="text-[0.65rem] uppercase tracking-wider font-bold border border-amber/60 bg-amber/10 text-navy px-2 py-1">{lang === "es" ? "Caso + calculadora" : "Case + calculator"}</span></div>
              <p className="text-lg font-heading font-semibold text-navy/90 mb-3">{guide.question[lang]}</p>
              <p className="text-sm leading-relaxed text-navy/60 mb-6">{domain.models[lang]}</p>
              <div className="mt-auto flex flex-wrap gap-3">
                <Link href={`/${domain.id}/`} className="bg-navy text-offwhite px-4 py-2.5 text-xs font-bold uppercase tracking-wider hover:bg-terracotta">{lang === "es" ? "Entender el caso" : "Understand the case"}</Link>
                <a href={`/${domain.id}/?model=${guide.workbenchModel}&view=workbench#workbench`} className="border border-navy/25 px-4 py-2.5 text-xs font-bold uppercase tracking-wider text-navy hover:border-terracotta hover:text-terracotta">{lang === "es" ? "Abrir Workbench" : "Open Workbench"}</a>
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}
