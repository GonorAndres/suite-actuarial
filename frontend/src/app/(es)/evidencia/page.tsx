"use client";

import Link from "next/link";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import { DOMAIN_GUIDES } from "@/lib/domain-guides";
import {
  ASKS,
  AUDIT_URL,
  CLAIM,
  CONTRIBUTE_STEPS,
  CONTRIBUTING_URL,
  DOMAIN_STATUS,
  INVENTORY_URL,
  LEVELS,
  RECEIPT_DATE,
  RECEIPT_EXAMPLES,
  RECEIPT_FIGURES,
  VALIDATION_URL,
} from "@/lib/evidence-content";

const externalLink = {
  target: "_blank",
  rel: "noopener noreferrer",
} as const;

export default function EvidencePage() {
  const { lang, href } = useLanguage();
  const caseLabel = lang === "es" ? "Caso" : "Case";
  return (
    <div className="max-w-6xl mx-auto px-6 py-12 space-y-14">
      <header className="max-w-4xl">
        <p className="kicker mb-3">{lang === "es" ? "Cómo leer este proyecto" : "How to read this project"}</p>
        <h1 className="font-heading text-4xl md:text-5xl font-bold text-navy mb-4">{lang === "es" ? "Aquí puedes explorar modelos sabiendo qué respalda cada número" : "Explore the models knowing what backs each number"}</h1>
        <p className="text-lg leading-relaxed text-navy/65">{lang === "es" ? "Cada resultado tiene su propio nivel de respaldo. La pregunta no es si el código calcula, sino qué se puede afirmar del número y qué le haría falta a una aseguradora para usarlo." : "Each result has its own level of support. The question is not whether the code calculates, but what can be claimed about the number and what an insurer would still need to use it."}</p>
      </header>

      {/* The id doubles as the anchor of the JSON-LD disclosure node (#alcance). */}
      <section id="alcance" className="border-l-4 border-terracotta bg-terracotta/5 px-5 py-6 md:px-7">
        <p className="kicker mb-3">{lang === "es" ? "Dónde está parada la biblioteca" : "Where the library stands"}</p>
        <p className="font-heading text-2xl md:text-3xl font-bold text-navy leading-snug max-w-4xl">{CLAIM.headline[lang]}</p>
        <p className="mt-3 leading-relaxed text-navy/70 max-w-3xl">{CLAIM.support[lang]}</p>
      </section>

      <section>
        <p className="kicker mb-2">{lang === "es" ? "Los tres niveles" : "The three levels"}</p>
        <h2 className="font-heading text-2xl font-bold text-navy mb-5">{lang === "es" ? "¿Qué significa cada nivel?" : "What does each level mean?"}</h2>
        <div className="grid md:grid-cols-3 gap-5">
          {LEVELS.map((level) => (
            <article key={level.n} className="border-t-2 border-navy bg-white border-x border-b border-navy/10 p-5">
              <span className="font-mono text-xs text-terracotta">{level.n}</span>
              <h3 className="font-heading font-bold text-xl text-navy mt-2 mb-3">{level.title[lang]}</h3>
              <p className="text-sm leading-relaxed text-navy/65">{level.body[lang]}</p>
            </article>
          ))}
        </div>
      </section>

      <section id="estado">
        <p className="kicker mb-2">{lang === "es" ? "Lo concreto" : "The concrete part"}</p>
        <h2 className="font-heading text-2xl font-bold text-navy mb-3">{lang === "es" ? "El estado por dominio" : "Status by domain"}</h2>
        <p className="text-navy/65 leading-relaxed max-w-3xl mb-6">{lang === "es" ? "Qué prueba sujeta cada dominio, qué dato le pone el techo y cuál es su límite principal. Cada fila enlaza el caso explicado y la calculadora del dominio." : "Which check pins each domain, which data sets its ceiling, and its primary limit. Each row links the domain's explained case and its calculator."}</p>

        <div className="hidden md:block border border-navy/15 bg-white overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-navy text-offwhite">
              <tr>
                <th className="px-4 py-3">{lang === "es" ? "Dominio" : "Domain"}</th>
                <th className="px-4 py-3">{lang === "es" ? "Qué se valida" : "What is validated"}</th>
                <th className="px-4 py-3">{lang === "es" ? "Límite de los datos" : "Data ceiling"}</th>
                <th className="px-4 py-3">{lang === "es" ? "Límite principal" : "Primary limit"}</th>
                <th className="px-4 py-3">{lang === "es" ? "Explorar" : "Explore"}</th>
              </tr>
            </thead>
            <tbody>
              {DOMAIN_STATUS.map((row) => (
                <tr key={row.id} className="border-t border-navy/10 align-top">
                  <th className="px-4 py-4 text-navy whitespace-nowrap">{row.name[lang]}</th>
                  <td className="px-4 py-4 text-navy/70 max-w-xs">{row.validation[lang]}</td>
                  <td className="px-4 py-4"><span className="text-xs font-bold uppercase tracking-wider text-terracotta">{row.data[lang]}</span></td>
                  <td className="px-4 py-4 text-navy/65 max-w-sm">{DOMAIN_GUIDES[row.id].limitations[0][lang]}</td>
                  <td className="px-4 py-4 whitespace-nowrap">
                    <div className="flex flex-col gap-2">
                      <Link href={href(`/${row.id}/`)} className="text-xs font-bold uppercase tracking-wider text-navy hover:text-terracotta">{caseLabel} →</Link>
                      <a href={`${href(`/${row.id}/`)}?model=${DOMAIN_GUIDES[row.id].workbenchModel}&view=workbench#workbench`} className="text-xs font-bold uppercase tracking-wider text-navy hover:text-terracotta">Workbench →</a>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="md:hidden space-y-4">
          {DOMAIN_STATUS.map((row) => (
            <article key={row.id} className="bg-white border border-navy/15 border-t-2 border-t-navy p-5">
              <div className="flex items-start justify-between gap-3 mb-3">
                <h3 className="font-heading font-bold text-lg text-navy">{row.name[lang]}</h3>
                <span className="text-[0.65rem] font-bold uppercase tracking-wider text-terracotta text-right">{row.data[lang]}</span>
              </div>
              <p className="text-sm leading-relaxed text-navy/70 mb-2">{row.validation[lang]}</p>
              <p className="text-sm leading-relaxed text-navy/65 mb-4">{DOMAIN_GUIDES[row.id].limitations[0][lang]}</p>
              <div className="flex flex-wrap gap-4">
                <Link href={href(`/${row.id}/`)} className="text-xs font-bold uppercase tracking-wider text-navy hover:text-terracotta">{caseLabel} →</Link>
                <a href={`${href(`/${row.id}/`)}?model=${DOMAIN_GUIDES[row.id].workbenchModel}&view=workbench#workbench`} className="text-xs font-bold uppercase tracking-wider text-navy hover:text-terracotta">Workbench →</a>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section id="recibos">
        <p className="kicker mb-2">{lang === "es" ? "Los números" : "The numbers"}</p>
        <h2 className="font-heading text-2xl font-bold text-navy mb-5">{lang === "es" ? "Qué respalda la afirmación" : "What backs the claim"}</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-5">
          {RECEIPT_FIGURES.map((figure) => (
            <div key={figure.value} className="border-t-2 border-navy bg-white border-x border-b border-navy/10 p-5">
              <p className="font-mono text-3xl font-bold text-navy">{figure.value}</p>
              <p className="text-sm leading-relaxed text-navy/65 mt-2">{figure.label[lang]}</p>
            </div>
          ))}
        </div>
        <ul className="mt-6 space-y-2 max-w-3xl">
          {RECEIPT_EXAMPLES.map((example) => (
            <li key={example.es} className="text-sm leading-relaxed text-navy/70 border-l-2 border-navy/20 pl-4">{example[lang]}</li>
          ))}
        </ul>
        <p className="mt-4 text-xs text-navy/50">{lang === "es" ? `Cifras tomadas el ${RECEIPT_DATE} corriendo la suite completa.` : `Figures taken on ${RECEIPT_DATE} by running the full suite.`}</p>
        <div className="mt-4 flex flex-wrap gap-4">
          <a href={VALIDATION_URL} {...externalLink} className="text-xs font-bold uppercase tracking-wider text-navy hover:text-terracotta">{lang === "es" ? "Ver los benchmarks" : "See the benchmarks"} →</a>
          <a href={AUDIT_URL} {...externalLink} className="text-xs font-bold uppercase tracking-wider text-navy hover:text-terracotta">{lang === "es" ? "Leer la auditoría" : "Read the audit"} →</a>
        </div>
      </section>

      <section id="ayuda">
        <p className="kicker mb-2">{lang === "es" ? "Los techos, convertidos en tareas" : "The ceilings, turned into tasks"}</p>
        <h2 className="font-heading text-2xl font-bold text-navy mb-3">{lang === "es" ? "Qué ayuda hace falta" : "What help is needed"}</h2>
        <p className="text-navy/65 leading-relaxed max-w-3xl mb-6">
          {lang === "es" ? "Cada tarea sale del " : "Each task comes from the "}
          <a href={INVENTORY_URL} {...externalLink} className="underline decoration-terracotta/50 underline-offset-2 hover:text-terracotta">{lang === "es" ? "inventario Clase B de la auditoría" : "audit's Class B inventory"}</a>
          {lang === "es" ? ": el registro de cada supuesto con su fuente, su límite y su ruta de sustitución. Es donde un profesional externo aporta más que el propio proyecto." : ": the record of every assumption with its source, its limit, and its replacement path. It is where an outside professional adds more than the project itself can."}
        </p>
        <div className="grid md:grid-cols-2 gap-5">
          {ASKS.map((ask, index) => (
            <article key={ask.id} className="bg-white border border-navy/15 border-t-2 border-t-terracotta p-5 flex flex-col">
              <span className="font-mono text-xs text-terracotta">{String(index + 1).padStart(2, "0")}</span>
              <h3 className="font-heading font-bold text-xl text-navy mt-2 mb-3">{ask.title[lang]}</h3>
              <p className="text-sm leading-relaxed text-navy/70 mb-2"><span className="font-bold text-navy">{lang === "es" ? "Hoy: " : "Today: "}</span>{ask.today[lang]}</p>
              <p className="text-sm leading-relaxed text-navy/70 mb-4"><span className="font-bold text-navy">{lang === "es" ? "El aporte: " : "The contribution: "}</span>{ask.contribution[lang]}</p>
              <a href={ask.first.href} {...externalLink} className="mt-auto text-xs font-bold uppercase tracking-wider text-navy hover:text-terracotta">{ask.first.label[lang]} →</a>
            </article>
          ))}
        </div>
      </section>

      <section id="contribuir" className="bg-navy text-offwhite p-7 md:p-9">
        <div className="md:flex md:items-start md:justify-between md:gap-10">
          <div className="max-w-xl">
            <h2 className="font-heading text-2xl font-bold mb-3">{lang === "es" ? "Cómo se ve una contribución" : "What a contribution looks like"}</h2>
            <p className="text-offwhite/65 leading-relaxed mb-6">{lang === "es" ? "CONTRIBUTING.md pide describir un modelo en seis pasos, en este orden. Un resultado sin fuente o sin límite explícito se marca como ilustrativo; nada se presenta como vigente sin evidencia verificable." : "CONTRIBUTING.md asks for a model described in six steps, in this order. A result without a source or an explicit limit is marked illustrative; nothing is presented as current without verifiable evidence."}</p>
            <div className="flex flex-wrap gap-3">
              <a href={CONTRIBUTING_URL} {...externalLink} className="bg-amber text-navy px-5 py-3 text-xs font-bold uppercase tracking-wider hover:bg-offwhite">{lang === "es" ? "Proponer una contribución" : "Propose a contribution"} →</a>
              <a href={AUDIT_URL} {...externalLink} className="border border-offwhite/30 px-5 py-3 text-xs font-bold uppercase tracking-wider text-offwhite hover:border-amber hover:text-amber">{lang === "es" ? "Leer auditoría" : "Read audit"} →</a>
            </div>
          </div>
          <ol className="mt-8 md:mt-0 space-y-3 md:max-w-md">
            {CONTRIBUTE_STEPS.map((step, index) => (
              <li key={step.es} className="flex gap-3 text-sm leading-relaxed text-offwhite/75">
                <span className="font-mono text-amber shrink-0">{String(index + 1).padStart(2, "0")}</span>
                <span>{step[lang]}</span>
              </li>
            ))}
          </ol>
        </div>
      </section>
    </div>
  );
}
