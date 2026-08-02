"use client";

import Link from "next/link";
import { useLanguage } from "@/lib/i18n/LanguageContext";

const GITHUB_URL = "https://github.com/GonorAndres/suite-actuarial";

const COPY = {
  es: {
    kicker: "Modelación actuarial en código abierto · México",
    title: "Construye, prueba y comprende modelos actuariales, en abierto.",
    intro:
      "suite_actuarial reúne métodos, ejemplos y herramientas para pasar de una pregunta de producto a un modelo reproducible. Cada análisis conecta beneficios, supuestos, cálculo, resultados y pruebas para que otros actuarios puedan revisarlo y extenderlo.",
    primary: "Revisar el ejemplo guiado",
    secondary: "Explorar la biblioteca",
    note: "Desarrollado desde el contexto asegurador mexicano, con métodos clásicos, fuentes visibles y código abierto.",
    processKicker: "Método común",
    processTitle: "Seis etapas para documentar y revisar cada modelo",
    videoKicker: "Demostración",
    videoTitle: "Dotal educativo 20/10, paso a paso",
    videoText:
      "El recorrido documenta la promesa contractual, la base de mortalidad, el descuento, la prima, la reserva, la sensibilidad y las verificaciones del mismo ejemplo disponible en código.",
    featuredKicker: "Ejemplo guiado · Vida",
    featuredTitle: "Seguro dotal a 20 años con primas durante 10",
    featuredText:
      "Este caso parte de una necesidad educativa y define un beneficio por fallecimiento o supervivencia. Permite modificar los supuestos, calcular la prima neta, seguir la reserva prospectiva y comprobar las identidades utilizadas.",
    featuredCta: "Revisar el ejemplo",
    coverageLabel: "Cobertura: 20 años",
    premiumLabel: "Pago de primas: 10 años",
    modelsKicker: "Biblioteca actuarial",
    modelsTitle: "Modelos organizados por la pregunta que ayudan a estudiar",
    evidenceKicker: "Trazabilidad",
    evidenceTitle: "Supuestos, fuentes, pruebas y límites junto al resultado",
    evidenceText:
      "Cada ejemplo identifica su base técnica, fecha o contexto de referencia, nivel de validación, comprobaciones y alcance. Así se puede distinguir entre una implementación reproducible y un modelo listo para uso profesional.",
    validation: "Pruebas e identidades",
    provenance: "Fuentes y contexto",
    limitations: "Alcance declarado",
    openKicker: "Trabajo abierto",
    openTitle: "Una base compartida para aprender, investigar y desarrollar",
    openText:
      "El repositorio permite estudiar modelos existentes, comparar resultados, proponer nuevas bases técnicas y construir ejemplos para proyectos universitarios, investigación aplicada e innovación actuarial.",
    github: "Consultar el repositorio",
  },
  en: {
    kicker: "Open actuarial platform · Mexico",
    title: "Build, test, and understand actuarial models in the open.",
    intro:
      "suite_actuarial brings together methods, examples, and tools for moving from a product question to a reproducible model. Each analysis connects benefits, assumptions, calculations, results, and tests so other actuaries can review and extend it.",
    primary: "Review the guided example",
    secondary: "Explore the library",
    note: "Built from the Mexican insurance context, with classical methods, visible sources, and open code.",
    processKicker: "Shared method",
    processTitle: "Six stages for documenting and reviewing each model",
    videoKicker: "Demonstration",
    videoTitle: "20/10 education endowment, step by step",
    videoText:
      "The walkthrough documents the contractual promise, mortality basis, discounting, premium, reserve, sensitivity, and checks for the same example available in code.",
    featuredKicker: "Guided example · Life",
    featuredTitle: "20-year endowment with premiums paid for 10 years",
    featuredText:
      "This case starts with an education need and defines a benefit on death or survival. It lets users change assumptions, calculate the net premium, follow the prospective reserve, and check the identities used.",
    featuredCta: "Review the example",
    coverageLabel: "Coverage: 20 years",
    premiumLabel: "Premium payments: 10 years",
    modelsKicker: "Actuarial library",
    modelsTitle: "Models organized by the question they help examine",
    evidenceKicker: "Traceability",
    evidenceTitle: "Assumptions, sources, tests, and limits beside the result",
    evidenceText:
      "Each example identifies its technical basis, reference date or context, validation level, checks, and scope. This distinguishes a reproducible implementation from a model ready for professional use.",
    validation: "Tests and identities",
    provenance: "Sources and context",
    limitations: "Declared scope",
    openKicker: "Open work",
    openTitle: "A shared foundation for learning, research, and development",
    openText:
      "The repository supports studying existing models, comparing results, proposing technical bases, and building examples for university projects, applied research, and actuarial innovation.",
    github: "View the repository",
  },
} as const;

const PROCESS = {
  es: ["Propósito", "Beneficios", "Supuestos", "Método", "Resultados", "Validación"],
  en: ["Purpose", "Benefits", "Assumptions", "Method", "Results", "Validation"],
};

const MODELS = {
  es: [
    ["¿Cómo financiar un beneficio?", "Vida", "Temporal, ordinario, dotal y reservas matemáticas", "/vida"],
    ["¿Cómo emerge una pérdida agregada?", "Daños", "Tarificación, frecuencia-severidad, credibilidad y bonus-malus", "/danos"],
    ["¿Cómo se comparte un gasto médico?", "Salud", "GMM, deducible, coaseguro y accidentes", "/salud"],
    ["¿Cómo convertir ahorro en ingreso vitalicio?", "Pensiones", "Ley 73/97, rentas vitalicias y conmutación", "/pensiones"],
    ["¿Qué costo falta por desarrollarse?", "Reservas", "Chain Ladder, Bornhuetter-Ferguson y bandas ilustrativas de dispersión", "/reservas"],
    ["¿Cómo transferir cola y capital?", "Reaseguro", "Cuota parte, exceso de pérdida y stop loss", "/reaseguro"],
    ["¿Cómo examinar solvencia y reglas?", "Referencia regulatoria", "RCS, reservas técnicas, SAT y configuración efectiva", "/regulatorio"],
  ],
  en: [
    ["How should a benefit be funded?", "Life", "Term, whole life, endowment, and mathematical reserves", "/vida"],
    ["How does aggregate loss emerge?", "P&C", "Rating, frequency-severity, credibility, and bonus-malus", "/danos"],
    ["How is a medical bill shared?", "Health", "Major medical, deductibles, coinsurance, and accidents", "/salud"],
    ["How does savings become lifetime income?", "Pensions", "Ley 73/97, life annuities, and commutation", "/pensiones"],
    ["Which cost remains undeveloped?", "Reserves", "Chain Ladder, Bornhuetter-Ferguson, and illustrative dispersion bands", "/reservas"],
    ["How can tail risk and capital be transferred?", "Reinsurance", "Quota share, excess of loss, and stop loss", "/reaseguro"],
    ["How can solvency and rules be examined?", "Regulatory reference", "RCS, technical reserves, SAT, and effective configuration", "/regulatorio"],
  ],
} as const;

function DemoVideo({ lang, videoId }: { lang: "es" | "en"; videoId: string }) {
  const copy = COPY[lang];

  return (
    <div className="video-frame">
      <iframe
        src={`https://www.youtube-nocookie.com/embed/${videoId}`}
        title={copy.videoTitle}
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowFullScreen
      />
    </div>
  );
}

export default function Home() {
  const { lang } = useLanguage();
  const copy = COPY[lang];
  const videoId = process.env.NEXT_PUBLIC_DEMO_VIDEO_ID;

  return (
    <div className="studio-home">
      <section className="studio-hero">
        <div>
          <p className="eyebrow">{copy.kicker}</p>
          <h1>{copy.title}</h1>
          <p className="hero-intro">{copy.intro}</p>
          <div className="hero-actions">
            <Link href="/biblioteca" className="primary-action">{copy.secondary}</Link>
            <Link href="/lab" className="secondary-action">{copy.primary}</Link>
          </div>
          <p className="hero-note">{copy.note}</p>
        </div>
        <div className="hero-model" aria-hidden="true">
          <p>MODEL / 01</p>
          <strong>A<sub>x:n</sub> = A<sup>1</sup><sub>x:n</sub> + v<sup>n</sup> · <sub>n</sub>p<sub>x</sub></strong>
          <div><span>death</span><span>survival</span></div>
          <svg viewBox="0 0 400 150"><path d="M5 138 C70 136 100 124 145 112 S210 85 260 60 S335 28 395 10" /></svg>
        </div>
      </section>

      <section className="process-section">
        <p className="eyebrow">{copy.processKicker}</p>
        <h2>{copy.processTitle}</h2>
        <div className="process-line">{PROCESS[lang].map((item, index) => <div key={item}><span>{String(index + 1).padStart(2, "0")}</span><strong>{item}</strong></div>)}</div>
      </section>

      <section className="featured-lab">
        <div><p className="eyebrow">{copy.featuredKicker}</p><h2>{copy.featuredTitle}</h2><p>{copy.featuredText}</p><Link href="/lab">{copy.featuredCta} →</Link></div>
        <div className="contract-diagram"><span>{copy.coverageLabel}</span><div className="timeline"><i /><i /></div><span>{copy.premiumLabel}</span></div>
      </section>

      {videoId && (
        <section className="video-section">
          <div><p className="eyebrow">{copy.videoKicker}</p><h2>{copy.videoTitle}</h2><p>{copy.videoText}</p></div>
          <DemoVideo lang={lang} videoId={videoId} />
        </section>
      )}

      <section id="models" className="models-section">
        <p className="eyebrow">{copy.modelsKicker}</p><h2>{copy.modelsTitle}</h2><Link href="/biblioteca" className="inline-block mt-3 text-terracotta font-semibold">{lang === "es" ? "Ver biblioteca completa" : "View complete library"} →</Link>
        <div className="model-index">{MODELS[lang].map(([question, domain, detail, href], index) => <Link href={href} key={href}><span>{String(index + 1).padStart(2, "0")}</span><div><p>{domain}</p><h3>{question}</h3><small>{detail}</small></div><b>↗</b></Link>)}</div>
      </section>

      <section id="evidence" className="evidence-section">
        <div><p className="eyebrow">{copy.evidenceKicker}</p><h2>{copy.evidenceTitle}</h2><p>{copy.evidenceText}</p><Link href="/evidencia" className="inline-block mt-4 text-terracotta font-semibold">{lang === "es" ? "Examinar evidencia y límites" : "Examine evidence and limits"} →</Link></div>
        <ol><li><span>01</span>{copy.validation}</li><li><span>02</span>{copy.provenance}</li><li><span>03</span>{copy.limitations}</li></ol>
      </section>

      <section className="open-section">
        <p className="eyebrow">{copy.openKicker}</p><h2>{copy.openTitle}</h2><p>{copy.openText}</p><a href={GITHUB_URL} target="_blank" rel="noopener noreferrer">{copy.github} →</a>
      </section>
    </div>
  );
}
