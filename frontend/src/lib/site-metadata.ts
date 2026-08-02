/**
 * Shared `Metadata` shape for the twelve exported routes.
 *
 * Next does not merge a child `openGraph` into the parent's — it replaces it —
 * so a route layout that declared only a title used to lose the site card and
 * inherit the homepage's `og:url`. Every route therefore builds the full object
 * from here, and the social image is declared in one place.
 */

import type { Metadata } from "next";

export const SITE_NAME = "suite_actuarial";
export const SITE_URL = "https://suite.gonor.me";

/**
 * Versioned PNG rather than a generated image: the export has no route handlers
 * and no image optimization. `scripts/og-image.py` regenerates it from the
 * design tokens.
 */
export const SOCIAL_IMAGE = {
  url: "/og.png",
  width: 1200,
  height: 630,
  alt: "suite_actuarial · Laboratorio actuarial abierto",
};

interface RouteMetadataOptions {
  /** Page name without the brand suffix. Also used for the social card. */
  name: string;
  description: string;
  /** Path with a trailing slash, matching `trailingSlash: true`. */
  path: string;
  /** Full <title>. Defaults to `${name} | suite_actuarial`. */
  title?: string;
}

export function routeMetadata({ name, description, path, title }: RouteMetadataOptions): Metadata {
  return {
    title: title ?? `${name} | ${SITE_NAME}`,
    description,
    alternates: { canonical: path },
    openGraph: {
      type: "website",
      // The exported document is Spanish; English is a client-side preference
      // with no URL of its own, so `alternateLocale` stays a hint, not hreflang.
      locale: "es_MX",
      alternateLocale: "en_US",
      siteName: SITE_NAME,
      title: name,
      description,
      url: path,
      images: [SOCIAL_IMAGE],
    },
    twitter: {
      card: "summary_large_image",
      title: name,
      description,
      images: [SOCIAL_IMAGE],
    },
  };
}
