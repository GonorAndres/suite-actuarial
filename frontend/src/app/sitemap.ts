import type { MetadataRoute } from "next";

export const dynamic = "force-static";

const routes = ["", "/biblioteca", "/evidencia", "/lab", "/vida", "/danos", "/salud", "/pensiones", "/reservas", "/reaseguro", "/regulatorio", "/api-docs"];

const SITE = "https://suite.gonor.me";

// `trailingSlash: true` in next.config.ts, and every canonical tag carries the
// slash. Without it here the sitemap lists URLs that redirect.
//
// Every route exists in both trees — Spanish at the original URL, English under
// /en/ — with the same priority: the English pages are not a translation
// appendix. `alternates.languages` mirrors the hreflang tags on the pages;
// x-default points at Spanish, the site's original language.
export default function sitemap(): MetadataRoute.Sitemap {
  return routes.flatMap((route) => {
    const es = `${SITE}${route}/`;
    const en = `${SITE}/en${route}/`;
    const changeFrequency = route === "" ? ("weekly" as const) : ("monthly" as const);
    const priority = route === "" ? 1 : route === "/biblioteca" ? 0.9 : 0.7;
    const alternates = { languages: { "es-MX": es, "en-US": en, "x-default": es } };
    return [
      { url: es, changeFrequency, priority, alternates },
      { url: en, changeFrequency, priority, alternates },
    ];
  });
}
