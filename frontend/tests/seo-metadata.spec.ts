import { expect, test, type Page } from "@playwright/test";
import { DOMAIN_GUIDES } from "../src/lib/domain-guides";

/**
 * Gates on the discovery layer: the social card, the canonical/sitemap
 * agreement, the hreflang pairing, the JSON-LD graph, and the language
 * attribute. None of it is visible in the UI, so without these assertions a
 * regression is silent.
 *
 * Every route exists twice: the Spanish document at its original URL and the
 * English one under `/en/`. Both trees are gated with the same checks.
 */

const ES_ROUTES = [
  "/",
  "/biblioteca/",
  "/evidencia/",
  "/lab/",
  "/vida/",
  "/danos/",
  "/salud/",
  "/pensiones/",
  "/reservas/",
  "/reaseguro/",
  "/regulatorio/",
  "/api-docs/",
];

const enTwin = (route: string) => (route === "/" ? "/en/" : `/en${route}`);
const EN_ROUTES = ES_ROUTES.map(enTwin);
const ALL_ROUTES = [...ES_ROUTES, ...EN_ROUTES];

async function jsonLd(page: Page): Promise<Record<string, unknown>[]> {
  const blocks = await page.locator('script[type="application/ld+json"]').allTextContents();
  return blocks.flatMap((block) => {
    const parsed = JSON.parse(block) as { "@graph": Record<string, unknown>[] };
    return parsed["@graph"];
  });
}

const typesOf = (nodes: Record<string, unknown>[]) => nodes.map((node) => node["@type"]);

/** The disclosure node of the tree a route belongs to. */
const scopeIdFor = (route: string) =>
  route.startsWith("/en/")
    ? "https://suite.gonor.me/en/evidencia/#alcance"
    : "https://suite.gonor.me/evidencia/#alcance";

/**
 * The CreativeWork subtypes this site emits. The disclosure gate is driven from
 * this list rather than from whichever nodes happen to carry the field, so
 * adding a new creative work without disclosing it fails instead of passing
 * unnoticed. Extend it when a new subtype is emitted.
 */
const CREATIVE_WORK_TYPES = [
  "CreativeWork",
  "WebSite",
  "WebPage",
  "CollectionPage",
  "TechArticle",
  "WebApplication",
  "SoftwareSourceCode",
  "APIReference",
];

/** Every `@type` anywhere in the graph, including nested objects and arrays. */
function everyType(value: unknown, found: string[] = []): string[] {
  if (Array.isArray(value)) {
    for (const item of value) everyType(item, found);
  } else if (value && typeof value === "object") {
    const node = value as Record<string, unknown>;
    const type = node["@type"];
    if (typeof type === "string") found.push(type);
    if (Array.isArray(type)) for (const t of type) if (typeof t === "string") found.push(t);
    for (const child of Object.values(node)) everyType(child, found);
  }
  return found;
}

test("every route carries the social card and its own OpenGraph url", async ({ page }) => {
  for (const route of ALL_ROUTES) {
    await page.goto(route);
    const expected = `https://suite.gonor.me${route}`;
    await expect(page.locator('link[rel="canonical"]')).toHaveAttribute("href", expected);
    await expect(page.locator('meta[property="og:url"]')).toHaveAttribute("content", expected);
    await expect(page.locator('meta[property="og:image"]')).toHaveAttribute(
      "content",
      "https://suite.gonor.me/og.png",
    );
    await expect(page.locator('meta[name="twitter:card"]')).toHaveAttribute(
      "content",
      "summary_large_image",
    );
  }
});

test("every route pairs with its twin through reciprocal hreflang", async ({ page }) => {
  // A non-reciprocal hreflang is worse than none: both variants must emit the
  // same three alternates, and x-default must point at Spanish.
  for (const route of ES_ROUTES) {
    const es = `https://suite.gonor.me${route}`;
    const en = `https://suite.gonor.me${enTwin(route)}`;
    for (const variant of [route, enTwin(route)]) {
      await page.goto(variant);
      await expect(page.locator('link[rel="alternate"][hreflang="es-MX"]')).toHaveAttribute("href", es);
      await expect(page.locator('link[rel="alternate"][hreflang="en-US"]')).toHaveAttribute("href", en);
      await expect(page.locator('link[rel="alternate"][hreflang="x-default"]')).toHaveAttribute("href", es);
    }
  }
});

test("each tree serves its language in the exported HTML", async ({ page }) => {
  // No JavaScript involved: the attribute and the copy are in the static
  // document, which is the whole point of the locale routes.
  await page.goto("/biblioteca/");
  await expect(page.locator("html")).toHaveAttribute("lang", "es");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Modelos organizados");

  await page.goto("/en/biblioteca/");
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Models organized");
});

test("the English document needs no JavaScript to be English", async ({ page }) => {
  // What a crawler that runs nothing sees. Before the locale routes, this
  // exact scenario served Spanish under an English preference.
  await page.route("**/_next/static/chunks/**", (route) => route.abort());
  await page.goto("/en/biblioteca/");
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Models organized");
});

test("the social image is a real 1200x630 asset", async ({ request }) => {
  const response = await request.get("/og.png");
  expect(response.status()).toBe(200);
  const body = await response.body();
  // PNG signature, then the IHDR width and height as big-endian uint32.
  expect(body.subarray(0, 8).toString("hex")).toBe("89504e470d0a1a0a");
  expect(body.readUInt32BE(16)).toBe(1200);
  expect(body.readUInt32BE(20)).toBe(630);
});

test("the sitemap lists both trees with their canonical trailing slash", async ({ request }) => {
  const xml = await (await request.get("/sitemap.xml")).text();
  const locations = [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map((match) => match[1]);
  expect(locations).toEqual(
    ES_ROUTES.flatMap((route) => [
      `https://suite.gonor.me${route}`,
      `https://suite.gonor.me${enTwin(route)}`,
    ]),
  );
  // Every entry carries the same reciprocal alternates as the pages.
  expect((xml.match(/<xhtml:link/g) ?? []).length).toBe(locations.length * 3);
});

test("the site graph declares the project, its author and its scope", async ({ page }) => {
  await page.goto("/");
  const nodes = await jsonLd(page);
  expect(typesOf(nodes)).toEqual(
    expect.arrayContaining(["WebSite", "Person", "SoftwareSourceCode", "WebPage"]),
  );

  const scope = nodes.find((node) => node["@id"] === "https://suite.gonor.me/evidencia/#alcance");
  expect(scope?.description).toContain("Este repositorio no afirma tenerlos");

  const software = nodes.find((node) => node["@type"] === "SoftwareSourceCode");
  expect(software?.codeRepository).toBe("https://github.com/GonorAndres/suite-actuarial");
  // A published release would need an index entry; there is none.
  expect(software).not.toHaveProperty("downloadUrl");

  // The English tree carries the same site-level ids with its own disclosure.
  await page.goto("/en/");
  const enNodes = await jsonLd(page);
  const enScope = enNodes.find(
    (node) => node["@id"] === "https://suite.gonor.me/en/evidencia/#alcance",
  );
  expect(enScope?.description).toContain("This repository does not claim to have them");
  const enSite = enNodes.find((node) => node["@type"] === "WebSite");
  expect(enSite?.["@id"]).toBe("https://suite.gonor.me/#website");
});

test("structured data claims no commercial or professional standing", async ({ page }) => {
  const forbidden = [
    "FinancialProduct",
    "InsuranceAgency",
    "Service",
    "Offer",
    "AggregateRating",
    "Review",
    "Dataset",
    "EducationalOccupationalProgram",
    "Organization",
  ];

  for (const route of ALL_ROUTES) {
    await page.goto(route);
    const nodes = await jsonLd(page);
    expect(nodes.length).toBeGreaterThan(0);
    // Recursive: a forbidden type nested under publisher, provider or about is
    // still a claim the project makes. Reading only the top-level `@type`
    // would let it through.
    for (const type of everyType(nodes)) {
      expect(forbidden).not.toContain(type);
    }

    // Positive assertion, and deliberately so. The earlier form of this check
    // selected the nodes that already carried `creativeWorkStatus` and then
    // asserted they carried it, so a node that omitted the disclosure was
    // excluded from its own gate and the suite stayed green. Here the set is
    // derived from the emitted types, so an undisclosed creative work fails.
    const scopeId = scopeIdFor(route);
    const disclosing = nodes.filter(
      (node) =>
        CREATIVE_WORK_TYPES.includes(node["@type"] as string) && node["@id"] !== scopeId,
    );
    expect(disclosing.length).toBeGreaterThan(0);
    for (const node of disclosing) {
      expect(node.creativeWorkStatus, `${route} ${String(node["@type"])}`).toBe("Experimental");
      expect(node.usageInfo, `${route} ${String(node["@type"])}`).toEqual({ "@id": scopeId });
    }
  }
});

test("a domain page describes its case and its workbench, in each language", async ({ page }) => {
  await page.goto("/vida/");
  const nodes = await jsonLd(page);

  const article = nodes.find((node) => node["@type"] === "TechArticle");
  expect(article?.headline).toBe(DOMAIN_GUIDES.vida.question.es);

  const app = nodes.find((node) => node["@type"] === "WebApplication");
  expect(app?.applicationCategory).toBe("EducationalApplication");

  // The English twin localizes the same graph from the same page content.
  await page.goto("/en/vida/");
  const enNodes = await jsonLd(page);
  const enArticle = enNodes.find((node) => node["@type"] === "TechArticle");
  expect(enArticle?.headline).toBe(DOMAIN_GUIDES.vida.question.en);
  expect(enArticle?.inLanguage).toBe("en-US");
});

test("the library graph lists the same seven domains as the page", async ({ page }) => {
  for (const [route, pattern] of [
    ["/biblioteca/", /^https:\/\/suite\.gonor\.me\/[a-z]+\/$/],
    ["/en/biblioteca/", /^https:\/\/suite\.gonor\.me\/en\/[a-z]+\/$/],
  ] as const) {
    await page.goto(route);
    const nodes = await jsonLd(page);
    const list = nodes.find((node) => node["@type"] === "ItemList") as
      | { numberOfItems: number; itemListElement: { url: string }[] }
      | undefined;

    expect(list?.numberOfItems).toBe(7);
    expect(list?.itemListElement).toHaveLength(await page.locator("main article").count());
    for (const item of list?.itemListElement ?? []) {
      expect(item.url).toMatch(pattern);
    }
  }
});
