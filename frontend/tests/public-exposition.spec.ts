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

test("evidence distinguishes implementation from professional validity", async ({ page }) => {
  await page.goto("/evidencia/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("explorar modelos");
  await expect(page.getByRole("heading", { name: "Profesionalmente válido" })).toBeVisible();
  await page.getByText("Ver el estado por dominio").click();
  await expect(page.locator("tbody tr")).toHaveCount(7);
});

test("language switch changes public library copy", async ({ page }) => {
  await page.goto("/biblioteca/");
  await page.getByRole("button", { name: "English" }).click();
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Models organized");
});

test("mobile navigation reaches the new destinations", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page.getByRole("button", { name: "Toggle menu" }).click();
  await expect(page.getByRole("navigation").last().getByRole("link", { name: "Biblioteca" })).toBeVisible();
  await expect(page.getByRole("navigation").last().getByRole("link", { name: "Evidencia" })).toBeVisible();
});
