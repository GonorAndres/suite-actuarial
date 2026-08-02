"use client";

import { useLanguage } from "@/lib/i18n/LanguageContext";
import { DOMAIN_GUIDES, type DomainId } from "@/lib/domain-guides";

const ROWS: { id: DomainId; name: { es: string; en: string }; validation: { es: string; en: string }; data: { es: string; en: string } }[] = [
  { id: "vida", name: { es: "Vida", en: "Life" }, validation: { es: "Identidades + casos de frontera", en: "Identities + boundary cases" }, data: { es: "Mortalidad sintética", en: "Synthetic mortality" } },
  { id: "danos", name: { es: "Daños", en: "P&C" }, validation: { es: "Casos manuales + monotonicidad", en: "Hand cases + monotonicity" }, data: { es: "Tarifas ilustrativas", en: "Illustrative tariffs" } },
  { id: "salud", name: { es: "Salud", en: "Health" }, validation: { es: "Fronteras contractuales", en: "Contract boundaries" }, data: { es: "Morbilidad ilustrativa", en: "Illustrative morbidity" } },
  { id: "pensiones", name: { es: "Pensiones", en: "Pensions" }, validation: { es: "Conmutación + casos legales", en: "Commutation + legal cases" }, data: { es: "Reglas simplificadas", en: "Simplified rules" } },
  { id: "reservas", name: { es: "Reservas", en: "Reserves" }, validation: { es: "Oráculos publicados Mack/ODP", en: "Published Mack/ODP oracles" }, data: { es: "Triángulos reproducibles", en: "Reproducible triangles" } },
  { id: "reaseguro", name: { es: "Reaseguro", en: "Reinsurance" }, validation: { es: "Recuperaciones manuales", en: "Hand-calculated recoveries" }, data: { es: "Contratos ilustrativos", en: "Illustrative treaties" } },
  { id: "regulatorio", name: { es: "Regulatorio", en: "Regulatory" }, validation: { es: "Identidades de agregación", en: "Aggregation identities" }, data: { es: "Factores heurísticos", en: "Heuristic factors" } },
];

export default function EvidencePage() {
  const { lang } = useLanguage();
  return (
    <div className="max-w-6xl mx-auto px-6 py-12 space-y-12">
      <header className="max-w-4xl">
        <p className="kicker mb-3">{lang === "es" ? "Cómo leer este proyecto" : "How to read this project"}</p>
        <h1 className="font-heading text-4xl md:text-5xl font-bold text-navy mb-4">{lang === "es" ? "Aquí puedes explorar modelos con criterio" : "Explore the models with context"}</h1>
        <p className="text-lg leading-relaxed text-navy/65">{lang === "es" ? "Cada resultado tiene un nivel de respaldo. La pregunta no es sólo si el código calcula, sino qué podemos afirmar sobre el número y qué todavía necesita una aseguradora." : "Every result has a level of support. The question is not only whether the code calculates, but what we can claim about the number and what an insurer would still need."}</p>
      </header>

      <section>
        <p className="kicker mb-2">{lang === "es" ? "Primero, lo esencial" : "Start here"}</p>
        <h2 className="font-heading text-2xl font-bold text-navy mb-5">{lang === "es" ? "¿Qué significa cada nivel?" : "What does each level mean?"}</h2>
        <div className="grid md:grid-cols-3 gap-5">
          {[
            { n: "01", es: "Implementado", en: "Implemented", esText: "El cálculo está construido: valida las entradas y repite el resultado con los mismos datos.", enText: "The calculation is built: it validates inputs and repeats the result with the same data." },
            { n: "02", es: "Verificado", en: "Verified", esText: "Además, una prueba independiente —una identidad, un caso manual u otro oráculo— puede encontrar errores conocidos.", enText: "An independent check—an identity, hand case, or other oracle—can also find known defects." },
            { n: "03", es: "Profesionalmente válido", en: "Professionally valid", esText: "Para una decisión real aún hacen falta datos aprobados, gobierno, método institucional y juicio actuarial. Este repositorio no lo afirma.", enText: "A real decision still needs approved data, governance, institutional method, and actuarial judgment. This repository does not claim it." },
          ].map((item) => <article key={item.n} className="border-t-2 border-navy bg-white border-x border-b border-navy/10 p-5"><span className="font-mono text-xs text-terracotta">{item.n}</span><h3 className="font-heading font-bold text-xl text-navy mt-2 mb-3">{lang === "es" ? item.es : item.en}</h3><p className="text-sm leading-relaxed text-navy/65">{lang === "es" ? item.esText : item.enText}</p></article>)}
        </div>
      </section>

      <section className="border-l-4 border-terracotta bg-terracotta/5 px-5 py-5 md:px-7">
        <h2 className="font-heading text-2xl font-bold text-navy mb-2">{lang === "es" ? "La forma práctica de usarlo" : "The practical way to use it"}</h2>
        <p className="text-navy/75 leading-relaxed">{lang === "es" ? "Empieza por el Caso explicado para entender la promesa, los supuestos y el método. Después abre el Workbench para cambiar parámetros. Si necesitas usar un resultado fuera del laboratorio, revisa primero las limitaciones y la auditoría." : "Start with the Explained case to understand the promise, assumptions, and method. Then open the Workbench to change parameters. If you need to use a result outside the lab, review the limitations and audit first."}</p>
      </section>

      <details className="group border border-navy/15 bg-white">
        <summary className="cursor-pointer list-none px-5 py-4 font-heading font-bold text-lg text-navy flex items-center justify-between gap-4"><span>{lang === "es" ? "Ver el estado por dominio" : "View status by domain"}</span><span className="font-mono text-terracotta group-open:rotate-45 transition-transform">+</span></summary>
        <div className="border-t border-navy/10 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-navy text-offwhite"><tr><th className="px-4 py-3">{lang === "es" ? "Dominio" : "Domain"}</th><th className="px-4 py-3">{lang === "es" ? "Qué se valida" : "What is validated"}</th><th className="px-4 py-3">{lang === "es" ? "Techo de datos" : "Data ceiling"}</th><th className="px-4 py-3">{lang === "es" ? "Límite principal" : "Primary limit"}</th></tr></thead>
            <tbody>{ROWS.map((row) => <tr key={row.id} className="border-t border-navy/10 align-top"><th className="px-4 py-4 text-navy">{row.name[lang]}</th><td className="px-4 py-4 text-navy/70">{row.validation[lang]}</td><td className="px-4 py-4"><span className="text-xs font-bold uppercase tracking-wider text-terracotta">{row.data[lang]}</span></td><td className="px-4 py-4 text-navy/65 max-w-sm">{DOMAIN_GUIDES[row.id].limitations[0][lang]}</td></tr>)}</tbody>
          </table>
        </div>
      </details>

      <section className="bg-navy text-offwhite p-7 md:p-9 flex flex-col md:flex-row gap-6 md:items-center md:justify-between">
        <div className="max-w-3xl"><h2 className="font-heading text-2xl font-bold mb-2">{lang === "es" ? "¿Quieres revisar el detalle técnico?" : "Want the technical detail?"}</h2><p className="text-offwhite/65">{lang === "es" ? "El registro de auditoría contiene las fuentes, pruebas, límites residuales y rutas de sustitución." : "The audit record contains sources, tests, residual limits, and replacement paths."}</p></div>
        <a href="https://github.com/GonorAndres/suite-actuarial/blob/main/docs/AUDIT.md" target="_blank" rel="noopener noreferrer" className="shrink-0 bg-amber text-navy px-5 py-3 text-xs font-bold uppercase tracking-wider hover:bg-offwhite">{lang === "es" ? "Leer auditoría" : "Read audit"} →</a>
      </section>
    </div>
  );
}
