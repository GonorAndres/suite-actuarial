import { expect, test, type Page } from "@playwright/test";

/**
 * Gates on the discovery layer: the social card, the canonical/sitemap
 * agreement, the JSON-LD graph, and the language attribute. None of it is
 * visible in the UI, so without these assertions a regression is silent.
 */

const ROUTES = [
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

async function jsonLd(page: Page): Promise<Record<string, unknown>[]> {
  const blocks = await page.locator('script[type="application/ld+json"]').allTextContents();
  return blocks.flatMap((block) => {
    const parsed = JSON.parse(block) as { "@graph": Record<string, unknown>[] };
    return parsed["@graph"];
  });
}

const typesOf = (nodes: Record<string, unknown>[]) => nodes.map((node) => node["@type"]);

const SCOPE_ID = "https://suite.gonor.me/evidencia/#alcance";

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
  for (const route of ROUTES) {
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

test("the social image is a real 1200x630 asset", async ({ request }) => {
  const response = await request.get("/og.png");
  expect(response.status()).toBe(200);
  const body = await response.body();
  // PNG signature, then the IHDR width and height as big-endian uint32.
  expect(body.subarray(0, 8).toString("hex")).toBe("89504e470d0a1a0a");
  expect(body.readUInt32BE(16)).toBe(1200);
  expect(body.readUInt32BE(20)).toBe(630);
});

test("the sitemap lists the exported routes with their canonical trailing slash", async ({ request }) => {
  const xml = await (await request.get("/sitemap.xml")).text();
  const locations = [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map((match) => match[1]);
  expect(locations).toEqual(ROUTES.map((route) => `https://suite.gonor.me${route}`));
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

  for (const route of ROUTES) {
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
    const disclosing = nodes.filter(
      (node) =>
        CREATIVE_WORK_TYPES.includes(node["@type"] as string) && node["@id"] !== SCOPE_ID,
    );
    expect(disclosing.length).toBeGreaterThan(0);
    for (const node of disclosing) {
      expect(node.creativeWorkStatus, `${route} ${String(node["@type"])}`).toBe("Experimental");
      expect(node.usageInfo, `${route} ${String(node["@type"])}`).toEqual({ "@id": SCOPE_ID });
    }
  }
});

test("a domain page describes its case and its workbench", async ({ page }) => {
  await page.goto("/vida/");
  const nodes = await jsonLd(page);

  const article = nodes.find((node) => node["@type"] === "TechArticle");
  expect(article?.headline).toBe(
    "¿Qué prima financia un beneficio por fallecimiento durante un plazo definido?",
  );

  const app = nodes.find((node) => node["@type"] === "WebApplication");
  expect(app?.applicationCategory).toBe("EducationalApplication");
});

test("the library graph lists the same seven domains as the page", async ({ page }) => {
  await page.goto("/biblioteca/");
  const nodes = await jsonLd(page);
  const list = nodes.find((node) => node["@type"] === "ItemList") as
    | { numberOfItems: number; itemListElement: { url: string }[] }
    | undefined;

  expect(list?.numberOfItems).toBe(7);
  expect(list?.itemListElement).toHaveLength(await page.locator("main article").count());
  for (const item of list?.itemListElement ?? []) {
    expect(item.url).toMatch(/^https:\/\/suite\.gonor\.me\/[a-z]+\/$/);
  }
});

test("html lang follows the selected language, including after a reload", async ({ page }) => {
  await page.goto("/biblioteca/");
  await expect(page.locator("html")).toHaveAttribute("lang", "es");

  await page.getByRole("button", { name: "English" }).click();
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Models organized");
  await expect(page.locator("html")).toHaveAttribute("lang", "en");

  // The exported HTML is Spanish, so on reload the attribute has to be restored
  // from the stored preference before hydration rather than after it.
  await page.reload({ waitUntil: "commit" });
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Models organized");
  await expect(page.locator("html")).toHaveAttribute("lang", "en");

  await page.getByRole("button", { name: "Espanol" }).click();
  await expect(page.locator("html")).toHaveAttribute("lang", "es");
});

test("the stored language reaches html lang before hydration", async ({ page }) => {
  await page.goto("/biblioteca/");
  await page.getByRole("button", { name: "English" }).click();
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Models organized");

  // With the application chunks blocked, React never hydrates and the effect in
  // DocumentLanguage never runs, so only the inline snippet in the root layout
  // can set the attribute.
  await page.route("**/_next/static/chunks/**", (route) => route.abort());
  await page.goto("/biblioteca/");

  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  // The prerendered copy stays Spanish. That is the limit of this fix: without
  // locale routes there is one exported document per URL and it is Spanish.
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Modelos organizados");
});
