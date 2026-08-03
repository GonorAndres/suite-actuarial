import { expect, test } from "@playwright/test";

const domains = [
  ["vida", "Seguros de Vida"],
  ["danos", "Seguros de Daños"],
  ["salud", "Seguros de Salud"],
  ["pensiones", "Pensiones"],
  ["reservas", "Reservas"],
  ["reaseguro", "Reaseguro"],
  ["regulatorio", "Regulatorio"],
] as const;

test("home exposes finished paths without public placeholders", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("modelos actuariales");
  await expect(page.getByRole("link", { name: "Biblioteca" }).first()).toHaveAttribute("href", "/biblioteca/");
  await expect(page.getByRole("link", { name: "Evidencia" }).first()).toHaveAttribute("href", "/evidencia/");
  await expect(page.getByText("Grabación pendiente")).toHaveCount(0);
});

test("library exposes seven explained domains and calculator paths", async ({ page }) => {
  await page.goto("/biblioteca/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Modelos organizados");
  await expect(page.locator("main article")).toHaveCount(7);
  await expect(page.getByRole("link", { name: "Abrir Workbench" })).toHaveCount(7);
});

for (const [route, title] of domains) {
  test(`${route} separates its continuous case from its workbench`, async ({ page }) => {
    await page.goto(`/${route}/`);
    await expect(page.getByRole("heading", { level: 1 })).toContainText(title);
    const guide = page.locator("main article").first();
    await expect(page.getByRole("tab", { name: "Caso explicado" })).toHaveAttribute("aria-selected", "true");
    await expect(guide.getByRole("heading", { name: "Propósito" })).toBeVisible();
    await expect(guide.getByRole("heading", { name: "Validación y límites" })).toBeVisible();
    await expect(guide.getByRole("link", { name: /^01/ })).toHaveCount(0);
    await page.getByRole("tab", { name: "Workbench" }).click();
    await expect(page.locator("#workbench")).toBeVisible();
    await expect(page.getByRole("heading", { name: "Qué calcula" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Para qué sirve" })).toBeVisible();
  });
}

test("a workbench model can be linked directly", async ({ page }) => {
  await page.goto("/reaseguro/?model=xl#workbench");
  await expect(page).toHaveURL(/model=xl#workbench/);
  await expect(page.getByRole("tab", { name: "Workbench" })).toHaveAttribute("aria-selected", "true");
  await expect(page.getByRole("tab", { name: "Exceso de Pérdida" })).toHaveAttribute("aria-selected", "true");
});

test("bonus-malus explains its experience-rating purpose and boundary", async ({ page }) => {
  await page.goto("/danos/?model=bonus_malus&view=workbench#workbench");
  await expect(page.getByRole("heading", { name: "Bonus–malus: transición por experiencia" })).toBeVisible();
  await expect(page.getByText("El nuevo nivel determina un factor de prima.")).toBeVisible();
  await expect(page.getByText(/no representa una tarifa mexicana única/)).toBeVisible();
});

test("domain tabs hide on downward scroll and return on upward scroll", async ({ page }) => {
  await page.goto("/vida/");
  const header = page.locator("header").first();
  const workspace = page.locator('[data-domain="vida"]');
  const switcher = workspace.locator(":scope > div").first();
  await expect(header).toHaveClass(/translate-y-0/);
  await expect(switcher).toHaveClass(/translate-y-0/);
  await page.evaluate(() => window.scrollTo(0, 900));
  await expect(header).toHaveClass(/-translate-y-full/);
  await expect(switcher).toHaveClass(/-translate-y/);
  await page.evaluate(() => window.scrollTo(0, 0));
  await expect(header).toHaveClass(/translate-y-0/);
  await expect(switcher).toHaveClass(/translate-y-0/);
});

test("domain tabs do not tuck away before the switcher is pinned", async ({ page }) => {
  await page.goto("/vida/");
  const workspace = page.locator('[data-domain="vida"]');
  const switcher = workspace.locator(":scope > div").first();
  // Stop short of the sticky offset: the switcher is still in normal flow, so
  // hiding it here would drag it up over the text above instead of tucking it
  // under the masthead, leaving a gap where the bar used to sit.
  const stillInFlow = await switcher.evaluate((el) => {
    let top = 0;
    let node: HTMLElement | null = el as HTMLElement;
    while (node) {
      top += node.offsetTop;
      node = node.offsetParent as HTMLElement | null;
    }
    return Math.round(top / 2);
  });
  await page.evaluate((y) => window.scrollTo(0, y), stillInFlow);
  await expect(switcher).toHaveClass(/translate-y-0/);
  const box = await switcher.boundingBox();
  expect(box!.y).toBeGreaterThan(64);
});

test("evidence states its ceiling and shows the domain status without interaction", async ({ page }) => {
  await page.goto("/evidencia/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("explorar modelos");
  // The central claim is explicit text, not an inference left to the reader.
  await expect(page.getByText("como máximo, en el nivel 02")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Profesionalmente válido" })).toBeVisible();
  // The domain table is the centerpiece: no <details>, no click, scroll only.
  await expect(page.locator("tbody tr")).toHaveCount(7);
  // No dead ends: every domain row leads to its case and its workbench.
  await expect(page.getByRole("link", { name: "Caso →", exact: true })).toHaveCount(7);
  await expect(page.getByRole("link", { name: "Workbench →", exact: true })).toHaveCount(7);
});

test("evidence turns each declared limit into an ask with a first step", async ({ page }) => {
  await page.goto("/evidencia/");
  const asks = page.locator("#ayuda article");
  await expect(asks).toHaveCount(6);
  for (const ask of await asks.all()) {
    await expect(ask.getByRole("link")).toHaveCount(1);
  }
  await expect(page.getByRole("link", { name: "Proponer una contribución" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Leer auditoría" })).toBeVisible();
});

test("evidence domain status stacks into cards on mobile", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/evidencia/");
  // The table relies on horizontal space; narrow screens get cards instead.
  await expect(page.locator("#estado table")).toBeHidden();
  await expect(page.getByRole("link", { name: "Workbench →", exact: true })).toHaveCount(7);
});

test("language switch navigates to the English document", async ({ page }) => {
  await page.goto("/biblioteca/");
  await page.getByRole("link", { name: "English" }).click();
  await expect(page).toHaveURL("/en/biblioteca/");
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Models organized");

  await page.getByRole("link", { name: "Espanol" }).click();
  await expect(page).toHaveURL("/biblioteca/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Modelos organizados");
});

test("language switch carries the path, query and hash across trees", async ({ page }) => {
  // Crossing root layouts is a full document load; without carrying the query
  // and hash the workbench state would silently reset to the case tab.
  await page.goto("/reaseguro/?model=xl&view=workbench#workbench");
  await page.getByRole("link", { name: "English" }).click();
  await expect(page).toHaveURL("/en/reaseguro/?model=xl&view=workbench#workbench");
  await expect(page.getByRole("tab", { name: "Workbench" })).toHaveAttribute("aria-selected", "true");
  await expect(page.getByRole("tab", { name: "Excess of Loss" })).toHaveAttribute("aria-selected", "true");
});

test("the header marks the active section under /en/", async ({ page }) => {
  // `pathname.startsWith(item.href)` was false for every item under the /en
  // prefix, which failed silently: the nav rendered with no active state.
  await page.goto("/en/lab/");
  const active = page.locator("header nav").first().getByRole("link", { name: "Guided example" });
  await expect(active).toHaveClass(/text-terracotta/);
  await expect(
    page.locator("header nav").first().getByRole("link", { name: "Library" }),
  ).not.toHaveClass(/text-terracotta/);
});

test("English navigation stays inside the English tree", async ({ page }) => {
  await page.goto("/en/");
  await expect(page.getByRole("link", { name: "Library" }).first()).toHaveAttribute("href", "/en/biblioteca/");
  await expect(page.getByRole("link", { name: "Evidence" }).first()).toHaveAttribute("href", "/en/evidencia/");
  await page.goto("/en/biblioteca/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Models organized");
  await expect(page.locator("main article")).toHaveCount(7);
  await expect(page.getByRole("link", { name: "Open Workbench" })).toHaveCount(7);
});

test("an English domain page serves its case in English", async ({ page }) => {
  await page.goto("/en/vida/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Life Insurance");
  await expect(page.getByRole("tab", { name: "Explained case" })).toHaveAttribute("aria-selected", "true");
  const guide = page.locator("main article").first();
  await expect(guide.getByRole("heading", { name: "Purpose" })).toBeVisible();
  await expect(guide.getByRole("heading", { name: "Validation and limits" })).toBeVisible();
});

test("mobile navigation reaches the new destinations", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page.getByRole("button", { name: "Toggle menu" }).click();
  await expect(page.getByRole("navigation").last().getByRole("link", { name: "Biblioteca" })).toBeVisible();
  await expect(page.getByRole("navigation").last().getByRole("link", { name: "Evidencia" })).toBeVisible();
});
