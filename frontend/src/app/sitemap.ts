import type { MetadataRoute } from "next";

export const dynamic = "force-static";

const routes = ["", "/biblioteca", "/evidencia", "/lab", "/vida", "/danos", "/salud", "/pensiones", "/reservas", "/reaseguro", "/regulatorio", "/api-docs"];

export default function sitemap(): MetadataRoute.Sitemap {
  return routes.map((route) => ({ url: `https://suite.gonor.me${route}`, changeFrequency: route === "" ? "weekly" : "monthly", priority: route === "" ? 1 : route === "/biblioteca" ? 0.9 : 0.7 }));
}
