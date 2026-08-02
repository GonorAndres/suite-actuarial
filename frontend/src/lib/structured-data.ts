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
 * Language: the exported HTML is Spanish (English is a client-side preference with
 * no URL of its own), so every node declares `inLanguage: "es-MX"` and no
 * alternate-language node is emitted. That changes when locale routes exist.
 *
 * Values come from real page content: `DOMAIN_GUIDES` for the domain questions,
 * `labCopy` for the guided case, `translations` for domain labels, and the route's
 * own `Metadata` description for the page description.
 */

import type { JsonLdNode } from "@/components/StructuredData";
import { DOMAIN_GUIDES, type DomainId } from "@/lib/domain-guides";
import { labCopy } from "@/lib/i18n/labCopy";
import { translations } from "@/lib/i18n/translations";
import { SITE_NAME, SITE_URL } from "@/lib/site-metadata";
import pkg from "../../package.json";

const REPO_URL = "https://github.com/GonorAndres/suite-actuarial";
const MIT_LICENSE = "https://opensource.org/licenses/MIT";
const LANGUAGE = "es-MX";

const WEBSITE_ID = `${SITE_URL}/#website`;
const PERSON_ID = `${SITE_URL}/#person`;
const SOFTWARE_ID = `${SITE_URL}/#software`;
const SCOPE_ID = `${SITE_URL}/evidencia/#alcance`;

/** Trailing slash to match `trailingSlash: true` and the canonical tags. */
const url = (path: string) => `${SITE_URL}${path}`;

const SITE_DESCRIPTION =
  "Modelos actuariales explicados y calculadoras reproducibles, con sus fuentes y sus límites, desde el mercado asegurador mexicano.";

/**
 * Verbatim from the third support level on /evidencia/ (`evidencia/page.tsx`,
 * the `esText` of level "03"). Quoted rather than imported because that page is
 * a client component holding the levels inline; if the wording there changes,
 * change it here too. An earlier version of this constant prepended a sentence
 * that appeared nowhere on the site while claiming to be verbatim.
 */
const SCOPE_TEXT =
  "Para una decisión real todavía hacen falta datos aprobados, gobierno corporativo, un método institucional y juicio actuarial. Este repositorio no afirma tenerlos.";

const DOMAIN_LABELS: Record<DomainId, string> = {
  vida: translations.es.nav_vida,
  danos: translations.es.nav_danos,
  salud: translations.es.nav_salud,
  pensiones: translations.es.nav_pensiones,
  reservas: translations.es.nav_reservas,
  reaseguro: translations.es.nav_reaseguro,
  regulatorio: translations.es.nav_regulatorio,
};

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

const scopeRef = { "@id": SCOPE_ID };
const personRef = { "@id": PERSON_ID };

/**
 * Declared once in the root layout, which wraps every route, so route-level
 * nodes can reference these ids inside the same document.
 */
export const siteGraph: JsonLdNode[] = [
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
    description: SITE_DESCRIPTION,
    inLanguage: LANGUAGE,
    author: personRef,
    publisher: personRef,
    license: MIT_LICENSE,
    creativeWorkStatus: "Experimental",
    usageInfo: scopeRef,
    // No `potentialAction: SearchAction`: the site has no search.
  },
  {
    "@type": "SoftwareSourceCode",
    "@id": SOFTWARE_ID,
    name: SITE_NAME,
    description:
      "Paquete de Python, servicio FastAPI y tablero para construir, probar y explicar modelos actuariales.",
    codeRepository: REPO_URL,
    programmingLanguage: ["Python", "TypeScript"],
    runtimePlatform: "Python 3.11+",
    license: MIT_LICENSE,
    version: pkg.version,
    author: personRef,
    isAccessibleForFree: true,
    inLanguage: LANGUAGE,
    creativeWorkStatus: "Experimental",
    usageInfo: scopeRef,
    // No `downloadUrl` / `installUrl`: the package is not published to an index.
  },
  {
    "@type": "CreativeWork",
    "@id": SCOPE_ID,
    url: url("/evidencia/"),
    name: "Evidencia, validación y límites",
    description: SCOPE_TEXT,
    inLanguage: LANGUAGE,
    author: personRef,
  },
];

interface PageOptions {
  /** Path with a leading and trailing slash, e.g. "/vida/". */
  path: string;
  name: string;
  description: string;
  /** Defaults to WebPage. */
  type?: "WebPage" | "CollectionPage";
  mainEntityId?: string;
}

function webPage({ path, name, description, type = "WebPage", mainEntityId }: PageOptions): JsonLdNode {
  return {
    "@type": type,
    "@id": `${url(path)}#webpage`,
    url: url(path),
    name,
    description,
    isPartOf: { "@id": WEBSITE_ID },
    inLanguage: LANGUAGE,
    author: personRef,
    creativeWorkStatus: "Experimental",
    usageInfo: scopeRef,
    ...(mainEntityId ? { mainEntity: { "@id": mainEntityId } } : {}),
  };
}

/**
 * The workbench tab of a domain page. It is a real calculator, but it only
 * appears after hydration, so the node describes the tool and never presents its
 * output as page content.
 */
function workbench(domain: DomainId): JsonLdNode {
  return {
    "@type": "WebApplication",
    "@id": `${url(`/${domain}/`)}#workbench`,
    name: `Workbench · ${DOMAIN_LABELS[domain]}`,
    url: `${url(`/${domain}/`)}?view=workbench#workbench`,
    // Not FinanceApplication: that categorises the tool as finance software.
    applicationCategory: "EducationalApplication",
    operatingSystem: "Any",
    browserRequirements: "Requiere JavaScript; el cálculo consulta api-suite.gonor.me.",
    isAccessibleForFree: true,
    inLanguage: LANGUAGE,
    author: personRef,
    creativeWorkStatus: "Experimental",
    usageInfo: scopeRef,
  };
}

export function homeGraph(name: string, description: string): JsonLdNode[] {
  return [webPage({ path: "/", name, description, mainEntityId: SOFTWARE_ID })];
}

export function libraryGraph(name: string, description: string): JsonLdNode[] {
  const listId = `${url("/biblioteca/")}#modelos`;
  return [
    webPage({ path: "/biblioteca/", name, description, type: "CollectionPage", mainEntityId: listId }),
    {
      "@type": "ItemList",
      "@id": listId,
      name: "Dominios actuariales explicados",
      numberOfItems: DOMAIN_ORDER.length,
      itemListOrder: "https://schema.org/ItemListOrderAscending",
      itemListElement: DOMAIN_ORDER.map((domain, index) => ({
        "@type": "ListItem",
        position: index + 1,
        name: DOMAIN_LABELS[domain],
        url: url(`/${domain}/`),
      })),
    },
  ];
}

export function domainGraph(domain: DomainId, name: string, description: string): JsonLdNode[] {
  const guide = DOMAIN_GUIDES[domain];
  const path = `/${domain}/`;
  const articleId = `${url(path)}#caso`;

  return [
    webPage({ path, name, description, mainEntityId: articleId }),
    {
      "@type": "TechArticle",
      "@id": articleId,
      headline: guide.question.es,
      description: guide.decision.es,
      about: { "@type": "Thing", name: DOMAIN_LABELS[domain] },
      // The six section headings rendered by components/guides/DomainGuide.tsx.
      articleSection: [
        "Propósito",
        "Beneficios y flujos",
        "Supuestos",
        "Método",
        "Resultados e interpretación",
        "Validación y límites",
      ],
      mainEntityOfPage: { "@id": `${url(path)}#webpage` },
      hasPart: { "@id": `${url(path)}#workbench` },
      isAccessibleForFree: true,
      inLanguage: LANGUAGE,
      author: personRef,
      creativeWorkStatus: "Experimental",
      usageInfo: scopeRef,
    },
    workbench(domain),
  ];
}

export function labGraph(name: string, description: string): JsonLdNode[] {
  const path = "/lab/";
  const articleId = `${url(path)}#caso`;
  const appId = `${url(path)}#calculadora`;

  return [
    webPage({ path, name, description, mainEntityId: articleId }),
    {
      "@type": "TechArticle",
      // Not HowTo: the six stages are views over one continuous model, not steps
      // the reader performs.
      "@id": articleId,
      additionalType: "https://schema.org/LearningResource",
      learningResourceType: "Ejemplo guiado",
      headline: labCopy.es.title,
      description: labCopy.es.subtitle,
      about: { "@type": "Thing", name: DOMAIN_LABELS.vida },
      mainEntityOfPage: { "@id": `${url(path)}#webpage` },
      hasPart: { "@id": appId },
      isAccessibleForFree: true,
      inLanguage: LANGUAGE,
      author: personRef,
      creativeWorkStatus: "Experimental",
      usageInfo: scopeRef,
    },
    {
      "@type": "WebApplication",
      "@id": appId,
      name: labCopy.es.title,
      url: url(path),
      applicationCategory: "EducationalApplication",
      operatingSystem: "Any",
      browserRequirements: "Requiere JavaScript; el cálculo consulta api-suite.gonor.me.",
      isAccessibleForFree: true,
      inLanguage: LANGUAGE,
      author: personRef,
      creativeWorkStatus: "Experimental",
      usageInfo: scopeRef,
    },
  ];
}

export function evidenceGraph(name: string, description: string): JsonLdNode[] {
  const path = "/evidencia/";
  const articleId = `${url(path)}#articulo`;

  return [
    webPage({ path, name, description, mainEntityId: articleId }),
    {
      "@type": "TechArticle",
      "@id": articleId,
      // The route's own name, not a headline written for the markup. An earlier
      // version invented one that appeared nowhere on the page, which is the
      // thing this file's own rule forbids.
      headline: name,
      description,
      about: { "@type": "Thing", name: "Validación y límites de los modelos" },
      mainEntityOfPage: { "@id": `${url(path)}#webpage` },
      isAccessibleForFree: true,
      inLanguage: LANGUAGE,
      author: personRef,
      creativeWorkStatus: "Experimental",
      usageInfo: scopeRef,
    },
  ];
}

export function apiDocsGraph(name: string, description: string): JsonLdNode[] {
  const path = "/api-docs/";
  const articleId = `${url(path)}#referencia`;

  return [
    webPage({ path, name, description, mainEntityId: articleId }),
    {
      "@type": "APIReference",
      "@id": articleId,
      headline: name,
      description,
      targetPlatform: "REST/HTTP JSON",
      assemblyVersion: pkg.version,
      about: { "@type": "Thing", name: "API REST de suite_actuarial" },
      mainEntityOfPage: { "@id": `${url(path)}#webpage` },
      isAccessibleForFree: true,
      inLanguage: LANGUAGE,
      author: personRef,
      creativeWorkStatus: "Experimental",
      usageInfo: scopeRef,
    },
  ];
}
