# Edge agent guidance

Guidance for coding agents working on the public API edge. Read the root `AGENTS.md`
first; this file adds edge-specific rules. `README.md` in this directory is the
Spanish narrative for contributors.

## What this is

A Cloudflare Worker serving `api-suite.gonor.me`. It fronts the FastAPI service on
Cloud Run and is the only address the public reaches.

## The rule that matters most

**No actuarial logic here, ever.** Every number in every response is computed by the
Python package. If a change tempts you to compute, round, convert, or default a value
in TypeScript, it belongs in `src/suite_actuarial/` instead. The edge may reject a
request, cache a response, or annotate it — it may not produce one.

This is the same guardrail as the root `AGENTS.md` rule that domain logic lives in the
package, applied to the one place where duplicating it would be easiest and least
visible.

## Conventions

- **Keep decisions in pure functions.** `routes.ts` (cacheability, analytics labels)
  and `telemetry.ts` (event payload) hold the choices that are easy to get quietly
  wrong. They take no bindings and no network, so they are directly testable. Put new
  decisions there rather than inline in the handler.

- **Fail closed on rate limiting.** A missing limiter binding returns 503. Serving
  without a limiter would silently restore the cost exposure this layer exists to
  close, and the API would still look healthy. Do not soften this into a warning.

- **Do not overstate what the limiter buys.** Measured against the real deployment:
  250 requests over one reused connection tripped at ~108, while 200 requests over 25
  parallel connections never tripped at all — same IP, same colo. The counter is local
  to each edge machine. It bounds a naive scraper and not a distributed one, and
  `--max-instances` on Cloud Run remains the only hard billing ceiling. If you write
  about this layer, say that.

- **Never cache a calculation.** Only `/api/info` and `/api/v1/config/*` are
  cacheable. Every other endpoint carries the caller's own assumptions in the body;
  caching one would return someone else's numbers. This is a correctness rule, not a
  performance tradeoff.

- **Keys never travel.** `Authorization` and `X-API-Key` are stripped before the
  origin request so keys stay out of Cloud Run logs. KV stores the SHA-256 digest,
  never the key. Analytics carries the key's label, never the key.

- **The analytics contract is in `docs/ANALYTICS.md`.** Adding a property to the edge
  event means updating that document in the same change. No request bodies, response
  values, actuarial inputs, IP addresses, or user agents. A test asserts the exact
  property set; if you change it deliberately, change the test with a reason.

- **Two limits, two places.** `ANON_RATE_LIMIT`/`KEYED_RATE_LIMIT` in `vars` mirror
  the `ratelimits` blocks because the binding does not expose its own configuration.
  Edit both or the 429 body will state a number the limiter does not enforce.

## Verification

```bash
npm run typecheck
npm test
```

Both run in CI. Tests execute inside workerd, the runtime that serves production.

## Deployment note

The Worker is attached by **route**, not Custom Domain: `api-suite.gonor.me` already
has a proxied CNAME to Cloud Run's domain mapping, and a Custom Domain cannot take
over a hostname that has one without deleting the record and dropping the API while
DNS settles. Removing the route restores the previous path immediately, which is the
rollback. See `docs/DEPLOYMENT.md`.
