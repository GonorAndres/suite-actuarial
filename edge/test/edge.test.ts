import { createExecutionContext, waitOnExecutionContext } from "cloudflare:test";
import { afterEach, describe, expect, it } from "vitest";

import worker from "../src/index";
import { hashKey } from "../src/auth";
import { type FetchStub, issueKey, limiter, makeEnv, request, stubFetch } from "./helpers";

let stub: FetchStub | null = null;

function ok(body = '{"status":"ok"}'): Response {
  return new Response(body, { status: 200, headers: { "Content-Type": "application/json" } });
}

async function call(req: Request, env = makeEnv()) {
  const ctx = createExecutionContext();
  const response = await worker.fetch(req, env, ctx);
  await waitOnExecutionContext(ctx);
  return response;
}

afterEach(() => {
  stub?.restore();
  stub = null;
});

describe("CORS", () => {
  it("answers a preflight without touching the origin", async () => {
    stub = stubFetch(ok);
    const response = await call(request("/api/v1/pricing/temporal", { method: "OPTIONS" }));

    expect(response.status).toBe(204);
    expect(response.headers.get("Access-Control-Allow-Origin")).toBe("*");
    expect(stub.origin).toHaveLength(0);
  });

  it("adds the public policy to a proxied response", async () => {
    stub = stubFetch(ok);
    const response = await call(request("/api/v1/pricing/temporal", { method: "POST", body: "{}" }));

    expect(response.status).toBe(200);
    expect(response.headers.get("Access-Control-Allow-Origin")).toBe("*");
    // No cookies, no session: credentials must stay off.
    expect(response.headers.get("Access-Control-Allow-Credentials")).toBeNull();
  });
});

describe("rate limiting", () => {
  it("refuses to serve when the limiter binding is absent", async () => {
    // Rate limiting is the reason this layer exists. Serving without it would
    // silently restore the cost exposure the edge was built to close.
    stub = stubFetch(ok);
    const env = makeEnv({ RL_ANON: undefined as never });
    const response = await call(request("/api/info"), env);

    expect(response.status).toBe(503);
    expect(stub.origin).toHaveLength(0);
  });

  it("returns 429 with Retry-After and never reaches the origin", async () => {
    stub = stubFetch(ok);
    const response = await call(request("/api/info"), makeEnv({ RL_ANON: limiter(false) }));

    expect(response.status).toBe(429);
    expect(response.headers.get("Retry-After")).toBe("60");
    expect(stub.origin).toHaveLength(0);
    expect(await response.json()).toEqual({
      detail: "Rate limit exceeded (120 requests per minute). An API key raises this limit.",
    });
  });

  it("counts an anonymous caller against their IP", async () => {
    stub = stubFetch(ok);
    const seen: string[] = [];
    const env = makeEnv({
      RL_ANON: {
        limit: async ({ key }) => {
          seen.push(key);
          return { success: true };
        },
      },
    });
    await call(request("/api/info", { headers: { "CF-Connecting-IP": "203.0.113.7" } }), env);

    expect(seen).toEqual(["ip:203.0.113.7"]);
  });

  it("counts a key holder against the key digest, on the higher tier", async () => {
    stub = stubFetch(ok);
    await issueKey("secret-key", "acme");
    const anon: string[] = [];
    const keyed: string[] = [];
    const env = makeEnv({
      RL_ANON: {
        limit: async ({ key }) => {
          anon.push(key);
          return { success: true };
        },
      },
      RL_KEYED: {
        limit: async ({ key }) => {
          keyed.push(key);
          return { success: true };
        },
      },
    });
    await call(request("/api/info", { headers: { Authorization: "Bearer secret-key" } }), env);

    expect(anon).toHaveLength(0);
    expect(keyed).toEqual([`key:${await hashKey("secret-key")}`]);
  });
});

describe("API keys", () => {
  it("serves an anonymous caller", async () => {
    stub = stubFetch(ok);
    expect((await call(request("/api/info"))).status).toBe(200);
  });

  it("rejects an unrecognised key instead of silently downgrading it", async () => {
    // A typo in a key must fail loudly here, not surface later as mysterious
    // 429s once the anonymous limit is hit.
    stub = stubFetch(ok);
    const response = await call(request("/api/info", { headers: { "X-API-Key": "wrong" } }));

    expect(response.status).toBe(401);
    expect(stub.origin).toHaveLength(0);
  });

  it("accepts a key from either header", async () => {
    stub = stubFetch(ok);
    await issueKey("k1", "acme");
    expect((await call(request("/api/info", { headers: { "X-API-Key": "k1" } }))).status).toBe(200);
    expect(
      (await call(request("/api/info", { headers: { Authorization: "Bearer k1" } }))).status,
    ).toBe(200);
  });

  it("never forwards the caller's key to the origin", async () => {
    // `/health` rather than `/api/info`: the latter is cacheable, so a hit
    // would satisfy the request without ever producing an origin call to
    // inspect.
    stub = stubFetch(ok);
    await issueKey("k2", "acme");
    await call(request("/health", { headers: { Authorization: "Bearer k2", "X-API-Key": "k2" } }));

    expect(stub.origin[0]!.headers.get("Authorization")).toBeNull();
    expect(stub.origin[0]!.headers.get("X-API-Key")).toBeNull();
  });
});

describe("origin", () => {
  it("adds the shared secret and drops one the client tried to supply", async () => {
    stub = stubFetch(ok);
    await call(
      request("/health", { headers: { "X-Proxy-Secret": "forged" } }),
      makeEnv({ PROXY_SHARED_SECRET: "real-secret" }),
    );

    expect(stub.origin[0]!.headers.get("X-Proxy-Secret")).toBe("real-secret");
  });

  it("strips a forged secret when none is configured", async () => {
    stub = stubFetch(ok);
    await call(request("/health", { headers: { "X-Proxy-Secret": "forged" } }));

    expect(stub.origin[0]!.headers.get("X-Proxy-Secret")).toBeNull();
  });

  it("preserves path and query", async () => {
    stub = stubFetch(ok);
    await call(request("/api/v1/pricing/temporal?x=1"));

    expect(stub.origin[0]!.url).toBe("https://origin.test/api/v1/pricing/temporal?x=1");
  });

  it("reports 502 when the origin does not answer", async () => {
    stub = stubFetch(() => {
      throw new Error("connection refused");
    });
    const response = await call(request("/api/v1/pricing/temporal", { method: "POST", body: "{}" }));

    expect(response.status).toBe(502);
    expect(await response.json()).toEqual({ detail: "The calculation service did not respond." });
  });

  it("passes an origin error through unchanged", async () => {
    stub = stubFetch(() => new Response('{"detail":"invalid"}', { status: 422 }));
    const response = await call(request("/api/v1/pricing/temporal", { method: "POST", body: "{}" }));

    expect(response.status).toBe(422);
    expect(await response.json()).toEqual({ detail: "invalid" });
  });
});

describe("caching", () => {
  it("serves the annual configuration from the edge on the second call", async () => {
    stub = stubFetch(() => ok('{"uma":42794.64}'));
    const path = `/api/v1/config/2026/uma?case=${crypto.randomUUID()}`;

    const first = await call(request(path));
    expect(first.headers.get("X-Edge-Cache")).toBe("miss");
    expect(first.headers.get("Cache-Control")).toBe("public, max-age=300");

    const second = await call(request(path));
    expect(second.headers.get("X-Edge-Cache")).toBe("hit");
    expect(await second.json()).toEqual({ uma: 42794.64 });

    // The point of the cache: the second call never woke the origin.
    expect(stub.origin).toHaveLength(1);
  });

  it("sends every calculation to the origin", async () => {
    stub = stubFetch(ok);
    const path = "/api/v1/pricing/temporal";
    await call(request(path, { method: "POST", body: "{}" }));
    const second = await call(request(path, { method: "POST", body: "{}" }));

    expect(second.headers.get("X-Edge-Cache")).toBe("bypass");
    expect(stub.origin).toHaveLength(2);
  });

  it("does not cache a failed response", async () => {
    stub = stubFetch(() => new Response('{"detail":"boom"}', { status: 500 }));
    const path = `/api/v1/config/2026/uma?case=${crypto.randomUUID()}`;
    await call(request(path));
    await call(request(path));

    expect(stub.origin).toHaveLength(2);
  });
});

describe("analytics", () => {
  it("sends nothing when PostHog is not configured", async () => {
    stub = stubFetch(ok);
    await call(request("/api/info"));

    expect(stub.posthog).toHaveLength(0);
  });

  it("reports a served request without any caller data", async () => {
    stub = stubFetch(ok);
    await call(
      request(`/api/v1/config/2026/uma?case=${crypto.randomUUID()}`, {
        headers: { "CF-Connecting-IP": "203.0.113.7", "User-Agent": "curl/8" },
      }),
      makeEnv({ POSTHOG_PROJECT_API_KEY: "phc_test" }),
    );

    expect(stub.posthog).toHaveLength(1);
    const sent = JSON.parse(stub.posthog[0]!.body!) as {
      api_key: string;
      event: string;
      properties: Record<string, unknown>;
    };
    expect(sent.api_key).toBe("phc_test");
    expect(sent.event).toBe("api_edge_request");
    expect(sent.properties.api_route).toBe("/api/v1/config/:num/uma");
    expect(sent.properties.status_code).toBe(200);
    expect(sent.properties.outcome).toBe("success");
    expect(sent.properties.auth_tier).toBe("anonymous");
    expect(sent.properties.$process_person_profile).toBe(false);

    // The standing analytics contract: no IP, no user agent, no bodies.
    const serialized = stub.posthog[0]!.body!;
    expect(serialized).not.toContain("203.0.113.7");
    expect(serialized).not.toContain("curl/8");
  });

  it("reports a rate-limited request, which the origin never sees", async () => {
    stub = stubFetch(ok);
    await call(
      request("/api/info"),
      makeEnv({ RL_ANON: limiter(false), POSTHOG_PROJECT_API_KEY: "phc_test" }),
    );

    const sent = JSON.parse(stub.posthog[0]!.body!) as { properties: Record<string, unknown> };
    expect(sent.properties.status_code).toBe(429);
    expect(sent.properties.outcome).toBe("rate_limited");
  });

  it("attributes a key holder by label, never by key", async () => {
    stub = stubFetch(ok);
    await issueKey("k3", "acme");
    await call(
      request("/api/info", { headers: { Authorization: "Bearer k3" } }),
      makeEnv({ POSTHOG_PROJECT_API_KEY: "phc_test" }),
    );

    const serialized = stub.posthog[0]!.body!;
    const sent = JSON.parse(serialized) as { properties: Record<string, unknown> };
    expect(sent.properties.auth_tier).toBe("key");
    expect(sent.properties.api_key_label).toBe("acme");
    expect(sent.properties.distinct_id).toBe("key:acme");
    expect(serialized).not.toContain("k3");
  });

  it("does not delay the response on a telemetry outage", async () => {
    stub = stubFetch(ok);
    const response = await call(
      request("/api/info"),
      makeEnv({ POSTHOG_HOST: "https://posthog.test", POSTHOG_PROJECT_API_KEY: "phc_test" }),
    );

    expect(response.status).toBe(200);
  });
});
