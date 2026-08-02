"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useSyncExternalStore,
  type ReactNode,
} from "react";
import { DEFAULT_LANG as EXPORTED_LANG, LANG_STORAGE_KEY } from "./langBootstrap";
import { translations, type Lang, type TranslationKey } from "./translations";

interface LanguageContextValue {
  lang: Lang;
  setLang: (lang: Lang) => void;
}

const LanguageContext = createContext<LanguageContextValue | null>(null);

const STORAGE_KEY = LANG_STORAGE_KEY;

/** Language of the statically exported HTML. The first client render must
 *  agree with it or React discards the whole tree as a hydration mismatch. */
const DEFAULT_LANG: Lang = EXPORTED_LANG;

/* ── The stored preference as an external store ──────────────────────────────
 *
 * The chosen language lives in `localStorage`, which is not React state and
 * is unreadable while the page is being prerendered. Seeding `useState` from
 * it made the first client render disagree with the exported HTML on every
 * text node, so React threw the whole tree away and rebuilt it on each load.
 *
 * `useSyncExternalStore` is the supported way out: it hands React a server
 * snapshot to hydrate against and the real one immediately after, which is a
 * brief flash of Spanish instead of a discarded tree.
 */

const listeners = new Set<() => void>();

let cachedLang: Lang | null = null;

function readStoredLang(): Lang {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === "en" || stored === "es") return stored;
  } catch {
    // storage unavailable
  }
  return DEFAULT_LANG;
}

function subscribe(onStoreChange: () => void): () => void {
  listeners.add(onStoreChange);
  return () => {
    listeners.delete(onStoreChange);
  };
}

/** Cached so React sees a stable value between store changes. */
function getSnapshot(): Lang {
  if (cachedLang === null) cachedLang = readStoredLang();
  return cachedLang;
}

/** What the prerendered HTML was built with. */
function getServerSnapshot(): Lang {
  return DEFAULT_LANG;
}

function writeLang(next: Lang): void {
  cachedLang = next;
  try {
    localStorage.setItem(STORAGE_KEY, next);
  } catch {
    // storage unavailable
  }
  for (const listener of listeners) listener();
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const lang = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  const setLang = useCallback((next: Lang) => {
    writeLang(next);
  }, []);

  const value = useMemo(() => ({ lang, setLang }), [lang, setLang]);

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
}

/**
 * Hook to access language state and translation function.
 *
 * `t(key)` returns the translated string for the current language.
 */
export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) {
    throw new Error("useLanguage must be used inside <LanguageProvider>");
  }

  const { lang, setLang } = ctx;

  const t = useCallback(
    (key: TranslationKey): string => {
      return translations[lang][key] ?? key;
    },
    [lang],
  );

  return { lang, setLang, t };
}
