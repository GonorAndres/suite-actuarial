import { env as bindings } from "cloudflare:test";

import { hashKey } from "../src/auth";
import type { Env, RateLimiter } from "../src/types";

/** A limiter with a decided answer, so tests do not depend on real counters. */
export function limiter(success: boolean): RateLimiter {
  return { limit: async () => ({ success }) };
}

export interface Recorded {
  url: string;
  method: string;
  headers: Headers;
  body?: string;
}

export interface FetchStub {
  origin: Recorded[];
  posthog: Recorded[];
  restore(): void;
}

/**
 * Replace `fetch` so the origin and PostHog can be observed.
 *
 * Requests are routed by host: `origin.test` is the Cloud Run stand-in and
 * `posthog.test` is the analytics endpoint, matching the bindings in
 * `vitest.config.ts`.
 */
export function stubFetch(originResponse: () => Response | Promise<Response>): FetchStub {
  const real = globalThis.fetch;
  const origin: Recorded[] = [];
  const posthog: Recorded[] = [];

  globalThis.fetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
    const request = input instanceof Request ? input : new Request(input, init);
    const url = new URL(request.url);
    const record: Recorded = {
      url: request.url,
      method: request.method,
      headers: new Headers(request.headers),
    };

    if (url.hostname === "posthog.test") {
      record.body = await request.text();
      posthog.push(record);
      return new Response("{}", { status: 200 });
    }

    origin.push(record);
    return await originResponse();
  }) as typeof fetch;

  return {
    origin,
    posthog,
    restore() {
      globalThis.fetch = real;
    },
  };
}

export function makeEnv(overrides: Partial<Env> = {}): Env {
  return {
    ORIGIN_URL: "https://origin.test",
    POSTHOG_HOST: "https://posthog.test",
    CACHE_TTL_SECONDS: "300",
    ANON_RATE_LIMIT: "120",
    KEYED_RATE_LIMIT: "1200",
    RL_ANON: limiter(true),
    RL_KEYED: limiter(true),
    API_KEYS: bindings.API_KEYS,
    ...overrides,
  } as Env;
}

/** Register an API key the way provisioning does: digest in, label attached. */
export async function issueKey(key: string, label: string): Promise<void> {
  await bindings.API_KEYS.put(await hashKey(key), JSON.stringify({ label }));
}

export function request(path: string, init: RequestInit = {}): Request {
  return new Request(`https://api-suite.gonor.me${path}`, init);
}
