/**
 * Bindings the test runtime provides.
 *
 * `vitest.config.ts` declares these rather than reading `wrangler.jsonc`, so
 * nothing generates the ambient type for them. Declaring the namespace here
 * keeps `env` from `cloudflare:test` typed without casting at every use.
 */
declare namespace Cloudflare {
  interface Env {
    API_KEYS: KVNamespace;
    ORIGIN_URL: string;
    POSTHOG_HOST: string;
    CACHE_TTL_SECONDS: string;
    ANON_RATE_LIMIT: string;
    KEYED_RATE_LIMIT: string;
  }
}
