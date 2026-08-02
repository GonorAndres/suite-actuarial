/**
 * Production edge for the suite_actuarial API.
 *
 * Everything the public can reach passes through here first. The Worker does
 * four things the Cloud Run service cannot do for itself, because all four have
 * to happen *before* a request costs anything:
 *
 *   1. Rate limiting -- abuse is refused at Cloudflare, where it is free.
 *      Once a request reaches Cloud Run it has already started a container.
 *   2. CORS -- third-party browser callers are allowed here, without widening
 *      the origin's own allowlist.
 *   3. Caching -- the annual regulatory configuration is identical for every
 *      caller, so serving it from the edge never wakes a container.
 *   4. Analytics -- the edge sees what the origin cannot: rate-limited
 *      requests, cache hits, and an origin that failed to answer.
 *
 * No actuarial logic lives here, and none may. Every number in every response
 * is computed by the Python package behind `ORIGIN_URL`.
 */

import { preflight, withCors } from "./cors";
import { resolveCaller } from "./auth";
import { isCacheable, normalizeRoute } from "./routes";
import { buildEdgeEventPayload, captureEdgeEvent } from "./telemetry";
import type { CacheState, Caller, Env, RateLimiter } from "./types";

/** FastAPI reports errors as `{"detail": ...}`; matching it keeps clients uniform. */
function jsonError(status: number, detail: string, extra?: HeadersInit): Response {
  return withCors(
    new Response(JSON.stringify({ detail }), {
      status,
      headers: { "Content-Type": "application/json", ...Object.fromEntries(new Headers(extra)) },
    }),
  );
}

function limiterFor(env: Env, caller: Caller): RateLimiter {
  return caller.tier === "key" ? env.RL_KEYED : env.RL_ANON;
}

/**
 * Build the upstream request.
 *
 * The caller's API key is dropped here on purpose: it authenticates against the
 * edge and has no meaning to the origin, so forwarding it would only put keys
 * into Cloud Run's request logs. `Host` is dropped so `fetch` sets the one the
 * origin expects; an inbound `X-Proxy-Secret` is dropped so a client cannot
 * present its own.
 */
function upstreamRequest(request: Request, url: URL, env: Env): Request {
  const headers = new Headers(request.headers);
  headers.delete("Authorization");
  headers.delete("X-API-Key");
  headers.delete("Host");
  headers.delete("X-Proxy-Secret");
  if (env.PROXY_SHARED_SECRET) {
    headers.set("X-Proxy-Secret", env.PROXY_SHARED_SECRET);
  }

  const target = new URL(url.pathname + url.search, env.ORIGIN_URL);
  return new Request(target, {
    method: request.method,
    headers,
    body: request.method === "GET" || request.method === "HEAD" ? undefined : request.body,
    redirect: "manual",
  });
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const startedAt = Date.now();
    const url = new URL(request.url);

    if (request.method === "OPTIONS") return preflight();

    // Fail closed. Rate limiting is the reason this layer exists; serving
    // without it would silently restore the cost exposure it was built to
    // close, and a green-looking API is exactly how that goes unnoticed.
    if (!env.RL_ANON || !env.RL_KEYED) {
      console.error("Rate limit bindings missing; refusing to serve unprotected.");
      return jsonError(503, "Edge misconfigured: rate limiting unavailable.");
    }

    const route = normalizeRoute(url.pathname);
    let cache: CacheState = "bypass";

    const resolved = await resolveCaller(request, env);
    if (!resolved.ok) {
      const response = jsonError(resolved.status, resolved.detail);
      report(ctx, env, { route, request, response, startedAt, cache, caller: anonymous(request) });
      return response;
    }
    const caller = resolved.caller;

    const { success } = await limiterFor(env, caller).limit({ key: caller.rateKey });
    if (!success) {
      const limit = caller.tier === "key" ? env.KEYED_RATE_LIMIT : env.ANON_RATE_LIMIT;
      const detail =
        caller.tier === "key"
          ? `Rate limit exceeded (${limit} requests per minute).`
          : `Rate limit exceeded (${limit} requests per minute). An API key raises this limit.`;
      const response = jsonError(429, detail, { "Retry-After": "60" });
      report(ctx, env, { route, request, response, startedAt, cache, caller });
      return response;
    }

    const cacheable = isCacheable(request.method, url.pathname);
    const cacheKey = new Request(url.toString(), { method: "GET" });
    const store = caches.default;

    if (cacheable) {
      const hit = await store.match(cacheKey);
      if (hit) {
        cache = "hit";
        const response = withCors(new Response(hit.body, hit));
        response.headers.set("X-Edge-Cache", "hit");
        report(ctx, env, { route, request, response, startedAt, cache, caller });
        return response;
      }
      cache = "miss";
    }

    let response: Response;
    try {
      const originResponse = await fetch(upstreamRequest(request, url, env));
      response = new Response(originResponse.body, originResponse);
    } catch (error) {
      console.error("Origin unreachable", error);
      const failure = jsonError(502, "The calculation service did not respond.");
      report(ctx, env, { route, request, response: failure, startedAt, cache, caller });
      return failure;
    }

    if (cacheable && response.status === 200) {
      const ttl = Number(env.CACHE_TTL_SECONDS) || 300;
      response.headers.set("Cache-Control", `public, max-age=${ttl}`);
      ctx.waitUntil(store.put(cacheKey, response.clone()));
    }

    const finalResponse = withCors(response);
    finalResponse.headers.set("X-Edge-Cache", cacheable ? "miss" : "bypass");
    report(ctx, env, { route, request, response: finalResponse, startedAt, cache, caller });
    return finalResponse;
  },
} satisfies ExportedHandler<Env>;

function anonymous(request: Request): Caller {
  return { tier: "anonymous", rateKey: `ip:${request.headers.get("CF-Connecting-IP") ?? "unknown"}` };
}

interface ReportInput {
  route: string;
  request: Request;
  response: Response;
  startedAt: number;
  cache: CacheState;
  caller: Caller;
}

/** Queue the analytics event. Without a PostHog key the edge sends nothing. */
function report(ctx: ExecutionContext, env: Env, input: ReportInput): void {
  const apiKey = env.POSTHOG_PROJECT_API_KEY?.trim();
  if (!apiKey) return;

  const cf = input.request.cf as { country?: string; colo?: string } | undefined;
  const payload = buildEdgeEventPayload({
    route: input.route,
    method: input.request.method,
    status: input.response.status,
    durationMs: Date.now() - input.startedAt,
    cache: input.cache,
    caller: input.caller,
    country: cf?.country,
    colo: cf?.colo,
    apiKey,
  });
  ctx.waitUntil(captureEdgeEvent(env.POSTHOG_HOST, payload));
}
