/**
 * schema.org graphs for the statically exported site.
 *
 * Scope rule, and the reason several obvious types are missing: this site is an
 * educational and experimental laboratory. It sells nothing, quotes nothing, and
 * certifies nothing. So no `FinancialProduct`, `Service`, `Offer`,
 * `AggregateRating`, `Dataset` (no distribution exists and the mortality basis is
 * synthetic), `FAQPage` (there are no question/answer blocks), or
 * `EducationalOccupationalProgram` (there is no provider and no credential).
 * `Person` rather than `Organization`: there is no entity behind the site, and on
 * an insurance domain an Organization reads as an actuarial firm.
 *
 * Every `CreativeWork` node carries `creativeWorkStatus: "Experimental"` and
 * `usageInfo` pointing at the disclosure node, so the declared scope travels with
 * the markup instead of living only in the prose.
 *
 * Language: every route exists as a Spanish document at its original URL and an
 * English one under `/en/`. Each graph function takes the document's language,
 * localizes page-level ids and text to it, and keeps the site-level ids
 * (`#website`, `#person`, `#software`) shared across both trees so crawlers see
 * one entity. The disclosure node is per-language — each document's creative
 * works point at the disclosure a reader of that document can actually read.
 *
 * Values come from real page content: `DOMAIN_GUIDES` for the domain questions,
 * `labCopy` for the guided case, `translations` for domain labels, the verbatim
 * scope text from /evidencia/, and the route's own `Metadata` description.
 */

import type { JsonLdNode } from "@/components/StructuredData";
import { DOMAIN_GUIDES, type DomainId } from "@/lib/domain-guides";
import { SCOPE_TEXT } from "@/lib/evidence-content";
import { labCopy } from "@/lib/i18n/labCopy";
import { translations, type Lang } from "@/lib/i18n/translations";
import { SITE_NAME, SITE_URL, twinPaths } from "@/lib/site-metadata";
import pkg from "../../package.json";

const REPO_URL = "https://github.com/GonorAndres/suite-actuarial";
const MIT_LICENSE = "https://opensource.org/licenses/MIT";

const LANGUAGE_TAG: Record<Lang, string> = { es: "es-MX", en: "en-US" };

const WEBSITE_ID = `${SITE_URL}/#website`;
const PERSON_ID = `${SITE_URL}/#person`;
const SOFTWARE_ID = `${SITE_URL}/#software`;

/** Trailing slash to match `trailingSlash: true` and the canonical tags. */
const url = (path: string) => `${SITE_URL}${path}`;

/** Absolute URL of a route in the given language tree. */
const localizedUrl = (lang: Lang, path: string) => url(twinPaths(path)[lang]);

const SITE_DESCRIPTION: Record<Lang, string> = {
  es: "Modelos actuariales explicados y calculadoras reproducibles, con sus fuentes y sus límites, desde el mercado asegurador mexicano.",
  en: "Actuarial models explained and reproducible calculators, with their sources and their limits, from the Mexican insurance market.",
};

/*
 * The scope disclosure (`SCOPE_TEXT`, imported above) is the body of the third
 * support level on /evidencia/. It used to be quoted here by hand — with a
 * comment begging both copies to move together — because the page held its
 * levels inline; the content now lives in `lib/evidence-content.ts`, so the
 * verbatim rule holds by construction.
 */

/** Route name of /evidencia/, per language tree (see its layout metadata). */
const SCOPE_NAME: Record<Lang, string> = {
  es: "Evidencia, validación y límites",
  en: "Evidence, validation, and limits",
};

const BROWSER_REQUIREMENTS: Record<Lang, string> = {
  es: "Requiere JavaScript; el cálculo consulta api-suite.gonor.me.",
  en: "Requires JavaScript; calculations query api-suite.gonor.me.",
};

/**
 * The six section headings rendered by components/guides/DomainGuide.tsx
 * (its `LABELS` constant). Quoted per language for the same verbatim reason
 * as `SCOPE_TEXT`.
 */
const ARTICLE_SECTIONS: Record<Lang, string[]> = {
  es: [
    "Propósito",
    "Beneficios y flujos",
    "Supuestos",
    "Método",
    "Resultados e interpretación",
    "Validación y límites",
  ],
  en: [
    "Purpose",
    "Benefits and cash flows",
    "Assumptions",
    "Method",
    "Results and interpretation",
    "Validation and limits",
  ],
};

const domainLabel = (lang: Lang, domain: DomainId): string =>
  translations[lang][`nav_${domain}`];

/** Same order the library page lists them in. */
export const DOMAIN_ORDER: DomainId[] = [
  "vida",
  "danos",
  "salud",
  "pensiones",
  "reservas",
  "reaseguro",
  "regulatorio",
];

/** The disclosure node of the tree this document belongs to. */
const scopeId = (lang: Lang) => `${localizedUrl(lang, "/evidencia/")}#alcance`;

const scopeRef = (lang: Lang) => ({ "@id": scopeId(lang) });
const personRef = { "@id": PERSON_ID };

/**
 * Declared once in each tree's root layout, which wraps every route, so
 * route-level nodes can reference these ids inside the same document. The
 * site-level ids are shared across both trees; only the text and the
 * disclosure node are per-language.
 */
export function siteGraph(lang: Lang): JsonLdNode[] {
  return [
    {
      "@type": "Person",
      "@id": PERSON_ID,
      // The only named party on the site, from the footer credit line.
      name: "Andrés González Ortega",
      url: url("/"),
      sameAs: ["https://github.com/GonorAndres"],
    },
    {
      "@type": "WebSite",
      "@id": WEBSITE_ID,
      name: SITE_NAME,
      url: url("/"),
      description: SITE_DESCRIPTION[lang],
      // The site ships both language trees; the WebSite entity is bilingual.
      inLanguage: [LANGUAGE_TAG.es, LANGUAGE_TAG.en],
      author: personRef,
      publisher: personRef,
      license: MIT_LICENSE,
      creativeWorkStatus: "Experimental",
      usageInfo: scopeRef(lang),
      // No `potentialAction: SearchAction`: the site has no search.
    },
    {
      "@type": "SoftwareSourceCode",
      "@id": SOFTWARE_ID,
      name: SITE_NAME,
      description:
        lang === "es"
          ? "Paquete de Python, servicio FastAPI y tablero para construir, probar y explicar modelos actuariales."
          : "Python package, FastAPI service, and dashboard to build, test, and explain actuarial models.",
      codeRepository: REPO_URL,
      programmingLanguage: ["Python", "TypeScript"],
      runtimePlatform: "Python 3.11+",
      license: MIT_LICENSE,
      version: pkg.version,
      author: personRef,
      isAccessibleForFree: true,
      inLanguage: [LANGUAGE_TAG.es, LANGUAGE_TAG.en],
      creativeWorkStatus: "Experimental",
      usageInfo: scopeRef(lang),
      // No `downloadUrl` / `installUrl`: the package is not published to an index.
    },
    {
      "@type": "CreativeWork",
      "@id": scopeId(lang),
      url: localizedUrl(lang, "/evidencia/"),
      name: SCOPE_NAME[lang],
      description: SCOPE_TEXT[lang],
      inLanguage: LANGUAGE_TAG[lang],
      author: personRef,
    },
  ];
}

interface PageOptions {
  lang: Lang;
  /** Path in the Spanish tree, with a leading and trailing slash, e.g. "/vida/". */
  path: string;
  name: string;
  description: string;
  /** Defaults to WebPage. */
  type?: "WebPage" | "CollectionPage";
  mainEntityId?: string;
}

function webPage({ lang, path, name, description, type = "WebPage", mainEntityId }: PageOptions): JsonLdNode {
  const pageUrl = localizedUrl(lang, path);
  return {
    "@type": type,
    "@id": `${pageUrl}#webpage`,
    url: pageUrl,
    name,
    description,
    isPartOf: { "@id": WEBSITE_ID },
    inLanguage: LANGUAGE_TAG[lang],
    author: personRef,
    creativeWorkStatus: "Experimental",
    usageInfo: scopeRef(lang),
    ...(mainEntityId ? { mainEntity: { "@id": mainEntityId } } : {}),
  };
}

/**
 * The workbench tab of a domain page. It is a real calculator, but it only
 * appears after hydration, so the node describes the tool and never presents its
 * output as page content.
 */
function workbench(lang: Lang, domain: DomainId): JsonLdNode {
  const pageUrl = localizedUrl(lang, `/${domain}/`);
  return {
    "@type": "WebApplication",
    "@id": `${pageUrl}#workbench`,
    name: `Workbench · ${domainLabel(lang, domain)}`,
    url: `${pageUrl}?view=workbench#workbench`,
    // Not FinanceApplication: that categorises the tool as finance software.
    applicationCategory: "EducationalApplication",
    operatingSystem: "Any",
    browserRequirements: BROWSER_REQUIREMENTS[lang],
    isAccessibleForFree: true,
    inLanguage: LANGUAGE_TAG[lang],
    author: personRef,
    creativeWorkStatus: "Experimental",
    usageInfo: scopeRef(lang),
  };
}

export function homeGraph(name: string, description: string, lang: Lang = "es"): JsonLdNode[] {
  return [webPage({ lang, path: "/", name, description, mainEntityId: SOFTWARE_ID })];
}

export function libraryGraph(name: string, description: string, lang: Lang = "es"): JsonLdNode[] {
  const listId = `${localizedUrl(lang, "/biblioteca/")}#modelos`;
  return [
    webPage({ lang, path: "/biblioteca/", name, description, type: "CollectionPage", mainEntityId: listId }),
    {
      "@type": "ItemList",
      "@id": listId,
      name: lang === "es" ? "Dominios actuariales explicados" : "Actuarial domains explained",
      numberOfItems: DOMAIN_ORDER.length,
      itemListOrder: "https://schema.org/ItemListOrderAscending",
      itemListElement: DOMAIN_ORDER.map((domain, index) => ({
        "@type": "ListItem",
        position: index + 1,
        name: domainLabel(lang, domain),
        url: localizedUrl(lang, `/${domain}/`),
      })),
    },
  ];
}

export function domainGraph(
  domain: DomainId,
  name: string,
  description: string,
  lang: Lang = "es",
): JsonLdNode[] {
  const guide = DOMAIN_GUIDES[domain];
  const path = `/${domain}/`;
  const pageUrl = localizedUrl(lang, path);
  const articleId = `${pageUrl}#caso`;

  return [
    webPage({ lang, path, name, description, mainEntityId: articleId }),
    {
      "@type": "TechArticle",
      "@id": articleId,
      headline: guide.question[lang],
      description: guide.decision[lang],
      about: { "@type": "Thing", name: domainLabel(lang, domain) },
      // The six section headings rendered by components/guides/DomainGuide.tsx.
      articleSection: ARTICLE_SECTIONS[lang],
      mainEntityOfPage: { "@id": `${pageUrl}#webpage` },
      hasPart: { "@id": `${pageUrl}#workbench` },
      isAccessibleForFree: true,
      inLanguage: LANGUAGE_TAG[lang],
      author: personRef,
      creativeWorkStatus: "Experimental",
      usageInfo: scopeRef(lang),
    },
    workbench(lang, domain),
  ];
}

export function labGraph(name: string, description: string, lang: Lang = "es"): JsonLdNode[] {
  const path = "/lab/";
  const pageUrl = localizedUrl(lang, path);
  const articleId = `${pageUrl}#caso`;
  const appId = `${pageUrl}#calculadora`;

  return [
    webPage({ lang, path, name, description, mainEntityId: articleId }),
    {
      "@type": "TechArticle",
      // Not HowTo: the six stages are views over one continuous model, not steps
      // the reader performs.
      "@id": articleId,
      additionalType: "https://schema.org/LearningResource",
      learningResourceType: lang === "es" ? "Ejemplo guiado" : "Guided example",
      headline: labCopy[lang].title,
      description: labCopy[lang].subtitle,
      about: { "@type": "Thing", name: domainLabel(lang, "vida") },
      mainEntityOfPage: { "@id": `${pageUrl}#webpage` },
      hasPart: { "@id": appId },
      isAccessibleForFree: true,
      inLanguage: LANGUAGE_TAG[lang],
      author: personRef,
      creativeWorkStatus: "Experimental",
      usageInfo: scopeRef(lang),
    },
    {
      "@type": "WebApplication",
      "@id": appId,
      name: labCopy[lang].title,
      url: pageUrl,
      applicationCategory: "EducationalApplication",
      operatingSystem: "Any",
      browserRequirements: BROWSER_REQUIREMENTS[lang],
      isAccessibleForFree: true,
      inLanguage: LANGUAGE_TAG[lang],
      author: personRef,
      creativeWorkStatus: "Experimental",
      usageInfo: scopeRef(lang),
    },
  ];
}

export function evidenceGraph(name: string, description: string, lang: Lang = "es"): JsonLdNode[] {
  const path = "/evidencia/";
  const pageUrl = localizedUrl(lang, path);
  const articleId = `${pageUrl}#articulo`;

  return [
    webPage({ lang, path, name, description, mainEntityId: articleId }),
    {
      "@type": "TechArticle",
      "@id": articleId,
      // The route's own name, not a headline written for the markup. An earlier
      // version invented one that appeared nowhere on the page, which is the
      // thing this file's own rule forbids.
      headline: name,
      description,
      about: {
        "@type": "Thing",
        name: lang === "es" ? "Validación y límites de los modelos" : "Validation and limits of the models",
      },
      mainEntityOfPage: { "@id": `${pageUrl}#webpage` },
      isAccessibleForFree: true,
      inLanguage: LANGUAGE_TAG[lang],
      author: personRef,
      creativeWorkStatus: "Experimental",
      usageInfo: scopeRef(lang),
    },
  ];
}

export function apiDocsGraph(name: string, description: string, lang: Lang = "es"): JsonLdNode[] {
  const path = "/api-docs/";
  const pageUrl = localizedUrl(lang, path);
  const articleId = `${pageUrl}#referencia`;

  return [
    webPage({ lang, path, name, description, mainEntityId: articleId }),
    {
      "@type": "APIReference",
      "@id": articleId,
      headline: name,
      description,
      targetPlatform: "REST/HTTP JSON",
      assemblyVersion: pkg.version,
      about: {
        "@type": "Thing",
        name: lang === "es" ? "API REST de suite_actuarial" : "suite_actuarial REST API",
      },
      mainEntityOfPage: { "@id": `${pageUrl}#webpage` },
      isAccessibleForFree: true,
      inLanguage: LANGUAGE_TAG[lang],
      author: personRef,
      creativeWorkStatus: "Experimental",
      usageInfo: scopeRef(lang),
    },
  ];
}
