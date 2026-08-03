/**
 * Shared `Metadata` shape for the exported routes, in both language trees.
 *
 * Next does not merge a child `openGraph` into the parent's — it replaces it —
 * so a route layout that declared only a title used to lose the site card and
 * inherit the homepage's `og:url`. Every route therefore builds the full object
 * from here, and the social image is declared in one place.
 *
 * Every route exists twice: the Spanish document at its original URL and the
 * English one under `/en/`. `routeMetadata` derives both variants from the
 * localized path it receives and emits reciprocal hreflang alternates with
 * `x-default` pointing at Spanish, the site's original language.
 */

import type { Metadata } from "next";
import type { Lang } from "@/lib/i18n/translations";

export const SITE_NAME = "suite_actuarial";
export const SITE_URL = "https://suite.gonor.me";

/**
 * Versioned PNG rather than a generated image: the export has no route handlers
 * and no image optimization. `scripts/og-image.py` regenerates it from the
 * design tokens.
 */
export function socialImage(lang: Lang = "es") {
  return {
    url: "/og.png",
    width: 1200,
    height: 630,
    alt:
      lang === "es"
        ? "suite_actuarial · Laboratorio actuarial abierto"
        : "suite_actuarial · Open actuarial laboratory",
  };
}

/** Both language variants of a localized path, trailing slash preserved. */
export function twinPaths(path: string): { es: string; en: string } {
  const es = path === "/en/" ? "/" : path.startsWith("/en/") ? path.slice(3) : path;
  const en = es === "/" ? "/en/" : `/en${es}`;
  return { es, en };
}

/** Reciprocal hreflang map shared by both variants of a route (gate: a
 *  non-reciprocal hreflang is worse than none). */
export function languageAlternates(path: string): Record<string, string> {
  const { es, en } = twinPaths(path);
  return { "es-MX": es, "en-US": en, "x-default": es };
}

interface RouteMetadataOptions {
  /** Page name without the brand suffix. Also used for the social card. */
  name: string;
  description: string;
  /** Localized path with a trailing slash, matching `trailingSlash: true`;
   *  English routes pass their own `/en/...` path. */
  path: string;
  /** Full <title>. Defaults to `${name} | suite_actuarial`. */
  title?: string;
  /** Language of this route's document. Defaults to Spanish. */
  lang?: Lang;
}

export function routeMetadata({
  name,
  description,
  path,
  title,
  lang = "es",
}: RouteMetadataOptions): Metadata {
  return {
    title: title ?? `${name} | ${SITE_NAME}`,
    description,
    alternates: { canonical: path, languages: languageAlternates(path) },
    openGraph: {
      type: "website",
      locale: lang === "es" ? "es_MX" : "en_US",
      alternateLocale: lang === "es" ? "en_US" : "es_MX",
      siteName: SITE_NAME,
      title: name,
      description,
      url: path,
      images: [socialImage(lang)],
    },
    twitter: {
      card: "summary_large_image",
      title: name,
      description,
      images: [socialImage(lang)],
    },
  };
}
