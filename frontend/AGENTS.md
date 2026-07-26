# Frontend agent guidance

Guidance for coding agents working on the `suite_actuarial` Next.js dashboard.
Read the root `AGENTS.md` first; this file adds frontend-specific rules. UI copy and
docs follow the "Communication and form" rule there: direct, honest, good faith, no
overhype or filler.

## What the frontend is for

The frontend presents the actuarial reasoning first — purpose, assumptions, method, and
result — with code as a reproducible second layer.

## Stack caveat

This is **Next.js 16.2.4** with React 19, TypeScript 5, and Tailwind CSS v4. It is
newer than the typical Next.js patterns in training data, so APIs and conventions may
differ. Before writing new Next.js-specific code, check the current app for the
pattern in use.

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
```

The build must pass.

## Common mistakes to avoid

- Adding `useEffect` + `fetch` directly in a page instead of using `src/lib/api.ts`.
- Hardcoding UI strings without adding them to the i18n files.
- Adding a new component without reusing `cn` and the existing tokens.
- Forgetting to update `src/lib/types.ts` when the API contract changes.
- Adding emojis to UI copy unless explicitly requested.
