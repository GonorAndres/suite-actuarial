"use client";

import { createContext, useCallback, useContext, useMemo, type ReactNode } from "react";
import { translations, type Lang, type TranslationKey } from "./translations";

/* ── The language is the route, not a stored preference ─────────────────────
 *
 * Each language tree has its own root layout: `app/(es)/` exports the Spanish
 * documents at the original URLs and `app/(en)/en/` exports the English ones
 * under `/en/`. The layout passes its language down as a prop, so the value is
 * known at prerender time and the exported HTML, `<html lang>`, and the first
 * client render always agree. The old localStorage/useSyncExternalStore
 * machinery existed only because one document had to serve both languages.
 */

const LanguageContext = createContext<Lang | null>(null);

export function LanguageProvider({ lang, children }: { lang: Lang; children: ReactNode }) {
  return <LanguageContext.Provider value={lang}>{children}</LanguageContext.Provider>;
}

/** Prefix an internal href so navigation stays inside the current language tree. */
export function localizeHref(lang: Lang, href: string): string {
  if (lang !== "en") return href;
  return href === "/" ? "/en/" : `/en${href}`;
}

/**
 * Hook to access the route's language and the translation function.
 *
 * `t(key)` returns the translated string for the current language.
 * `href(path)` keeps internal links inside the current language tree.
 */
export function useLanguage() {
  const lang = useContext(LanguageContext);
  if (lang === null) {
    throw new Error("useLanguage must be used inside <LanguageProvider>");
  }

  const t = useCallback(
    (key: TranslationKey): string => {
      return translations[lang][key] ?? key;
    },
    [lang],
  );

  const href = useCallback((path: string) => localizeHref(lang, path), [lang]);

  return useMemo(() => ({ lang, t, href }), [lang, t, href]);
}
