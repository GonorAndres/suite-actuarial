/**
 * Bindings and shared shapes for the API edge.
 */

/**
 * The subset of Cloudflare's rate limit binding this Worker uses.
 *
 * Declared structurally rather than imported so tests can substitute a
 * deterministic limiter: the real binding counts per Cloudflare location and
 * cannot be driven to a known state from a test.
 */
export interface RateLimiter {
  limit(options: { key: string }): Promise<{ success: boolean }>;
}

export interface Env {
  /**
   * Cloud Run service that performs the actuarial computation. The Worker is a
   * door, not a brain: every number in a response comes from this origin.
   */
  ORIGIN_URL: string;
  POSTHOG_HOST: string;

  /** Seconds an edge-cached response stays fresh. See `isCacheable`. */
  CACHE_TTL_SECONDS: string;

  /**
   * Requests per minute per tier. These mirror the `ratelimits` blocks in
   * `wrangler.jsonc` and exist only so the values can be stated in responses
   * and error messages -- the binding does not expose its own configuration.
   * They are the one pair of values that must be edited in two places.
   */
  ANON_RATE_LIMIT: string;
  KEYED_RATE_LIMIT: string;

  RL_ANON: RateLimiter;
  RL_KEYED: RateLimiter;

  /** SHA-256 hex of an API key -> JSON `{"label": "..."}`. */
  API_KEYS: KVNamespace;

  /** Secrets. Absent in local development; both are optional by design. */
  POSTHOG_PROJECT_API_KEY?: string;
  PROXY_SHARED_SECRET?: string;
}

export type Tier = "anonymous" | "key";

export interface Caller {
  tier: Tier;
  /** Human-readable name of the key holder. Never the key itself. */
  label?: string;
  /** Value the rate limiter counts against: key hash, or client IP. */
  rateKey: string;
}

export type CacheState = "hit" | "miss" | "bypass";

export type Outcome = "success" | "client_error" | "server_error" | "rate_limited";
