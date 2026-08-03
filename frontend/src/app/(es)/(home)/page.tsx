"use client";

import Link from "next/link";
import { useLanguage } from "@/lib/i18n/LanguageContext";

const GITHUB_URL = "https://github.com/GonorAndres/suite-actuarial";

const COPY = {
  es: {
    kicker: "Modelación actuarial en código abierto · México",
    title: "Construye, prueba y entiende modelos actuariales con el código a la vista.",
    intro:
      "suite_actuarial reúne los métodos y los ejemplos que hacen falta para pasar de una pregunta de producto a un modelo que otra persona pueda reproducir. Cada caso deja a la vista el beneficio, los supuestos, el cálculo y las pruebas que lo sostienen.",
    primary: "Ver el ejemplo guiado",
    secondary: "Explorar la biblioteca",
    note: "Hecho desde el mercado asegurador mexicano, con métodos clásicos y fuentes citadas.",
    processKicker: "Método de trabajo",
    processTitle: "Cada modelo pasa por las mismas seis etapas",
    videoKicker: "Demostración",
    videoTitle: "Dotal educativo 20/10, paso a paso",
    videoText:
      "El recorrido sigue el mismo ejemplo que está en el código: la promesa contractual, la base de mortalidad, la tasa, la prima, la reserva año por año y las comprobaciones finales.",
    featuredKicker: "Ejemplo guiado · Vida",
    featuredTitle: "Seguro dotal a 20 años con primas durante 10",
    featuredText:
      "El caso parte de una meta de ahorro educativo y define un beneficio que se paga por fallecimiento o por supervivencia. Puedes cambiar los supuestos, calcular la prima neta, seguir la reserva año por año y comprobar las identidades que la sostienen.",
    featuredCta: "Abrir el ejemplo",
    coverageLabel: "Cobertura: 20 años",
    premiumLabel: "Pago de primas: 10 años",
    modelsKicker: "Biblioteca actuarial",
    modelsTitle: "Modelos ordenados por la pregunta que ayudan a responder",
    evidenceKicker: "Trazabilidad",
    evidenceTitle: "Supuestos, fuentes, pruebas y límites junto al resultado",
    evidenceText:
      "Cada ejemplo declara de dónde salen sus datos, hasta dónde se validó y qué queda fuera. Con eso se distingue una implementación reproducible de un modelo listo para uso profesional.",
    validation: "Pruebas e identidades",
    provenance: "Fuentes y contexto",
    limitations: "Alcance declarado",
    openKicker: "Trabajo abierto",
    openTitle: "Una base común sobre la que construir",
    openText:
      "El repositorio está abierto para estudiar los modelos que ya existen, cambiarles la base técnica y construir ejemplos nuevos, sea para una tesis, un curso o un proyecto de trabajo.",
    github: "Ver el repositorio",
  },
  en: {
    kicker: "Open actuarial platform · Mexico",
    title: "Build, test, and understand actuarial models with the code in view.",
    intro:
      "suite_actuarial brings together the methods and examples needed to move from a product question to a model someone else can reproduce. Each case keeps the benefit, the assumptions, the calculation, and the tests behind it in view.",
    primary: "See the guided example",
    secondary: "Explore the library",
    note: "Built from the Mexican insurance market, with classical methods and cited sources.",
    processKicker: "How the work is done",
    processTitle: "Every model goes through the same six stages",
    videoKicker: "Demonstration",
    videoTitle: "20/10 education endowment, step by step",
    videoText:
      "The walkthrough follows the same example that lives in the code: the contractual promise, the mortality basis, the rate, the premium, the year-by-year reserve, and the closing checks.",
    featuredKicker: "Guided example · Life",
    featuredTitle: "20-year endowment with premiums paid for 10 years",
    featuredText:
      "The case starts from an education savings goal and defines a benefit paid on death or on survival. You can change the assumptions, calculate the net premium, follow the reserve year by year, and check the identities behind it.",
    featuredCta: "Open the example",
    coverageLabel: "Coverage: 20 years",
    premiumLabel: "Premium payments: 10 years",
    modelsKicker: "Actuarial library",
    modelsTitle: "Models organized by the question they help answer",
    evidenceKicker: "Traceability",
    evidenceTitle: "Assumptions, sources, tests, and limits beside the result",
    evidenceText:
      "Each example states where its data comes from, how far it was validated, and what is left out. That is what distinguishes a reproducible implementation from a model ready for professional use.",
    validation: "Tests and identities",
    provenance: "Sources and context",
    limitations: "Declared scope",
    openKicker: "Open work",
    openTitle: "A common base to build on",
    openText:
      "The repository is open for studying the models already here, replacing their technical basis, and building new examples, whether for a thesis, a course, or work.",
    github: "View the repository",
  },
} as const;

const PROCESS = {
  es: ["Propósito", "Beneficios", "Supuestos", "Método", "Resultados", "Validación"],
  en: ["Purpose", "Benefits", "Assumptions", "Method", "Results", "Validation"],
};

const MODELS = {
  es: [
    ["¿Cómo se financia un beneficio?", "Vida", "Temporal, ordinario, dotal y reservas matemáticas", "/vida"],
    ["¿Cómo se forma una pérdida agregada?", "Daños", "Tarificación, frecuencia-severidad, credibilidad y bonus-malus", "/danos"],
    ["¿Cómo se reparte un gasto médico?", "Salud", "GMM, deducible, coaseguro y accidentes", "/salud"],
    ["¿Cómo se convierte el ahorro en ingreso vitalicio?", "Pensiones", "Ley 73/97, rentas vitalicias y conmutación", "/pensiones"],
    ["¿Cuánto falta por pagar de los siniestros ya ocurridos?", "Reservas", "Chain Ladder, Bornhuetter-Ferguson y bandas ilustrativas de dispersión", "/reservas"],
    ["¿Cómo se transfiere el riesgo de cola?", "Reaseguro", "Cuota parte, exceso de pérdida y stop loss", "/reaseguro"],
    ["¿Cómo se examina la solvencia?", "Referencia regulatoria", "RCS, reservas técnicas, SAT y configuración anual vigente", "/regulatorio"],
  ],
  en: [
    ["How is a benefit funded?", "Life", "Term, whole life, endowment, and mathematical reserves", "/vida"],
    ["How does an aggregate loss build up?", "P&C", "Rating, frequency-severity, credibility, and bonus-malus", "/danos"],
    ["How is a medical bill shared?", "Health", "Major medical, deductibles, coinsurance, and accidents", "/salud"],
    ["How do savings become lifetime income?", "Pensions", "Ley 73/97, life annuities, and commutation", "/pensiones"],
    ["How much is still to be paid on claims already incurred?", "Reserves", "Chain Ladder, Bornhuetter-Ferguson, and illustrative dispersion bands", "/reservas"],
    ["How is tail risk transferred?", "Reinsurance", "Quota share, excess of loss, and stop loss", "/reaseguro"],
    ["How is solvency examined?", "Regulatory reference", "RCS, technical reserves, SAT, and the year's configuration", "/regulatorio"],
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
  const { lang, href: localHref } = useLanguage();
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
            <Link href={localHref("/biblioteca")} className="primary-action">{copy.secondary}</Link>
            <Link href={localHref("/lab")} className="secondary-action">{copy.primary}</Link>
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
        <div><p className="eyebrow">{copy.featuredKicker}</p><h2>{copy.featuredTitle}</h2><p>{copy.featuredText}</p><Link href={localHref("/lab")}>{copy.featuredCta} →</Link></div>
        <div className="contract-diagram"><span>{copy.coverageLabel}</span><div className="timeline"><i /><i /></div><span>{copy.premiumLabel}</span></div>
      </section>

      {videoId && (
        <section className="video-section">
          <div><p className="eyebrow">{copy.videoKicker}</p><h2>{copy.videoTitle}</h2><p>{copy.videoText}</p></div>
          <DemoVideo lang={lang} videoId={videoId} />
        </section>
      )}

      <section id="models" className="models-section">
        <p className="eyebrow">{copy.modelsKicker}</p><h2>{copy.modelsTitle}</h2><Link href={localHref("/biblioteca")} className="inline-block mt-3 text-terracotta font-semibold">{lang === "es" ? "Ver biblioteca completa" : "View complete library"} →</Link>
        <div className="model-index">{MODELS[lang].map(([question, domain, detail, href], index) => <Link href={localHref(href)} key={href}><span>{String(index + 1).padStart(2, "0")}</span><div><p>{domain}</p><h3>{question}</h3><small>{detail}</small></div><b>↗</b></Link>)}</div>
      </section>

      <section id="evidence" className="evidence-section">
        <div><p className="eyebrow">{copy.evidenceKicker}</p><h2>{copy.evidenceTitle}</h2><p>{copy.evidenceText}</p><Link href={localHref("/evidencia")} className="inline-block mt-4 text-terracotta font-semibold">{lang === "es" ? "Examinar evidencia y límites" : "Examine evidence and limits"} →</Link></div>
        <ol><li><span>01</span>{copy.validation}</li><li><span>02</span>{copy.provenance}</li><li><span>03</span>{copy.limitations}</li></ol>
      </section>

      <section className="open-section">
        <p className="eyebrow">{copy.openKicker}</p><h2>{copy.openTitle}</h2><p>{copy.openText}</p><a href={GITHUB_URL} target="_blank" rel="noopener noreferrer">{copy.github} →</a>
      </section>
    </div>
  );
}
