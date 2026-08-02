/**
 * The stored language preference, and the snippet that applies it to
 * `<html lang>` before hydration.
 *
 * The export is prerendered in Spanish, so the served HTML always ships
 * `lang="es"`. Without this snippet a reader whose stored preference is English
 * gets a document that declares Spanish until React hydrates and
 * `DocumentLanguage` runs its effect — long enough for a screen reader to pick
 * the wrong voice on first paint.
 *
 * This module has no `"use client"` directive on purpose: the root layout is a
 * Server Component and needs the same constants.
 *
 * What it does not fix: a crawler that never runs JavaScript still sees
 * `lang="es"` on every page, because there is one exported document per route
 * and it is Spanish. Only locale routes change that.
 */

export const LANG_STORAGE_KEY = "suite_actuarial_lang";

/** Language of the statically exported HTML. */
export const DEFAULT_LANG = "es";

export const LANG_BOOTSTRAP_SCRIPT = [
  "try{",
  `var l=localStorage.getItem(${JSON.stringify(LANG_STORAGE_KEY)});`,
  'if(l==="en"||l==="es")document.documentElement.lang=l;',
  "}catch(e){}",
].join("");
