import { cloudflareTest } from "@cloudflare/vitest-pool-workers";
import { defineConfig } from "vitest/config";

/**
 * Tests run inside workerd, the same runtime that serves production.
 *
 * Bindings are declared here rather than read from `wrangler.jsonc` so the
 * suite does not depend on deployment-time resource ids, and so the rate
 * limiters can be replaced per test: the real binding counts per Cloudflare
 * location and cannot be driven to a known state.
 */
export default defineConfig({
  plugins: [
    cloudflareTest({
      main: "./src/index.ts",
      miniflare: {
        compatibilityDate: "2026-08-01",
        kvNamespaces: ["API_KEYS"],
        bindings: {
          ORIGIN_URL: "https://origin.test",
          POSTHOG_HOST: "https://posthog.test",
          CACHE_TTL_SECONDS: "300",
          ANON_RATE_LIMIT: "120",
          KEYED_RATE_LIMIT: "1200",
        },
      },
    }),
  ],
});
