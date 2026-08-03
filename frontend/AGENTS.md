# Frontend agent guidance

Guidance for coding agents working on the `suite_actuarial` Next.js dashboard.
Read the root `AGENTS.md` first; this file adds frontend-specific rules. UI copy and
docs follow the "Communication and form" rule there: direct, honest, good faith, no
overhype or filler.

## What the frontend is for

The frontend presents the actuarial reasoning first — purpose, assumptions, method, and
result — with code as a reproducible second layer.

## Stack caveat

This is **Next.js 16.2.12** with React 19, TypeScript 5, and Tailwind CSS v4. It is
newer than the typical Next.js patterns in training data, so APIs and conventions may
differ. Before writing new Next.js-specific code, check the current app for the
pattern in use.

Production is a static export: `next.config.ts` sets `output: "export"` with
`trailingSlash: true` into `frontend/out/`, deployed on Cloudflare Pages. No route
handlers, middleware, ISR, or image optimization; `sitemap.ts` and `robots.ts` need
`dynamic = "force-static"`. In dev, `/api/*` is rewritten to `API_PROXY_URL`
(default `http://127.0.0.1:8000`); in production `NEXT_PUBLIC_API_URL` points at
`api-suite.gonor.me`, which is now the Worker in `edge/` rather than Cloud Run
directly — the address is unchanged, so no frontend code changes, but the dashboard's
calls are counted against the same rate limit as everyone else's. The preview branch
adds `cloudflare/_worker.js` as a same-origin proxy. See `docs/DEPLOYMENT.md`.

## Conventions

- **App Router.** Server Components are the default. Add `"use client"` only when a
  component needs interactivity, browser APIs, or React hooks.

- **Do not issue ad hoc API requests.** Route all backend calls through the typed
  client in `src/lib/api.ts`. Keep `src/lib/types.ts` aligned with Pydantic request/response
  models in the Python package.

- **Use existing hooks for calculations.** `useCalculation` and `useLiveCalculation` handle
  loading, error, and result states consistently. Do not recreate this logic in page
  components.

- **Reuse the design system.** Import UI primitives from `src/components/ui/index.ts` and
  use `cn` from `@/lib/design-system` for class composition. Use the existing tokens
  (`bg-navy`, `text-cream`, `font-heading`, etc.) instead of hard-coded values.

- **Bilingual copy is mandatory.** All user-visible text must go through the i18n system
  in `src/lib/i18n/`. Do not hardcode Spanish or English strings directly in components.

- **Preserve UX states.** Every calculation page should handle loading, error, empty,
  and result states consistently.

- **Responsive by default.** Keep layouts usable across screen sizes.

## Discovery layer: metadata, structured data, social card

- **Route metadata comes from `src/lib/site-metadata.ts`.** `routeMetadata({ name,
  description, path })` builds the title, description, canonical, OpenGraph and
  Twitter blocks in one place. Do not hand-write `openGraph` in a route layout: Next
  replaces a child `openGraph` instead of merging it, so a partial override silently
  drops the social image and inherits the homepage's `og:url`.

- **JSON-LD lives in the route's `layout.tsx`.** Every `page.tsx` is `"use client"`
  and cannot carry structured data as a Server Component, so the sibling layout that
  already holds the metadata renders `<StructuredData graph={...} />`. Graphs are
  built in `src/lib/structured-data.ts`. The root layout declares `#website`,
  `#person`, `#software` and the scope node once; route graphs reference those ids.

- **Structured data must not overstate.** This is an educational laboratory, so no
  type whose semantics are "something is sold, quoted, or professionally certified"
  (`FinancialProduct`, `Service`, `Offer`, `AggregateRating`), no `Dataset` (nothing
  is distributed and the mortality basis is synthetic), no `FAQPage` (there are no
  Q&A blocks), no `EducationalOccupationalProgram` (no provider, no credential), and
  `Person` rather than `Organization`. Every emitted `CreativeWork` subtype carries
  `creativeWorkStatus: "Experimental"` and `usageInfo` pointing at the scope node —
  with one exception: the scope node (`/evidencia/#alcance`) *is* that disclosure, so
  it does not link to itself. Values must come from real page content —
  `DOMAIN_GUIDES`, `labCopy`, `translations`, or the route's own description.

  `tests/seo-metadata.spec.ts` gates the disclosure and the forbidden types, and the
  shape of that gate matters. It derives the nodes to check from `CREATIVE_WORK_TYPES`
  rather than from whichever nodes already carry the field: an earlier version
  selected `nodes.filter(n => "creativeWorkStatus" in n)` and then asserted those
  nodes carried it, so a creative work that omitted the disclosure was excluded from
  its own check and the suite stayed green. If you emit a new `CreativeWork` subtype,
  add it to that list or it is not gated. The forbidden-`@type` walk is recursive for
  the same reason: a nested `Organization` or `Offer` under `publisher` or `about` is
  still a claim.

- **The social card is a versioned PNG.** `frontend/public/og.png`, regenerated by
  `frontend/scripts/og-image.py` from the design tokens. The export has no route
  handlers and no image optimization, and an extensionless `opengraph-image` artifact
  would depend on Cloudflare Pages guessing a Content-Type. The repository `.gitignore`
  ignores `*.png`, with an explicit exception for this file.

- **The language is the route, not a stored preference.** Two root layouts:
  `app/(es)/` exports the Spanish documents at the original URLs and `app/(en)/en/`
  exports the English ones under `/en/`, each with its real `<html lang>`. The root
  layout passes the language into `LanguageProvider`; `useLanguage()` returns
  `{ lang, t, href }`, where `href()` keeps internal links inside the current tree.
  There is no localStorage, no bootstrap snippet, and no client-side `lang`
  correction. A new route must be added in **both** trees: the Spanish
  `layout.tsx` + `page.tsx` under `(es)/`, and under `(en)/en/` a layout with the
  English `name`/`description` (passing `lang: "en"` to `routeMetadata` and the
  graph builder) plus a `page.tsx` that re-exports the Spanish page component.
  Both variants emit reciprocal hreflang (`es-MX`, `en-US`, `x-default` → Spanish)
  via `routeMetadata`; `tests/seo-metadata.spec.ts` gates the pairing and
  `sitemap.ts` lists both trees. The language switcher in the Header is a real
  link to the twin document that carries path, query and hash across the full
  document load — crossing root layouts is never a client transition.

## Design system guardrails

- When adding a new color or token, update both `theme.ts` and `tokens.css`, and register
  it in the `@theme inline` block of `globals.css` so Tailwind generates utility classes.
- Chart series use the fixed categorical order defined in `theme.chart`. Do not cycle colors
  or invent new ones for the same data.

## Verification

Run these from `frontend/` before considering a change complete:

```bash
npm run lint
npm run build
npm run test:e2e
```

All three must pass; all three run in CI. `test:e2e` runs the Playwright specs in
`tests/` against the static export, so it needs the `npm run build` output.

## Common mistakes to avoid

- Adding `useEffect` + `fetch` directly in a page instead of using `src/lib/api.ts`.
- Hardcoding UI strings without adding them to the i18n files.
- Adding a new component without reusing `cn` and the existing tokens.
- Forgetting to update `src/lib/types.ts` when the API contract changes.
- Adding emojis to UI copy unless explicitly requested.
