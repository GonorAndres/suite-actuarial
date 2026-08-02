/**
 * Optional API keys.
 *
 * The API is open: a caller with no key is served, at the lower rate limit. A
 * key only raises that limit and attaches a label to the analytics, so keys are
 * an accounting mechanism rather than a gate.
 *
 * A key that is presented but not recognised is rejected with 401 rather than
 * quietly downgraded to anonymous. Downgrading would turn a typo in a key into
 * mysterious 429s much later, which is the kind of failure that costs an
 * afternoon to diagnose.
 */

import type { Caller, Env } from "./types";

export type CallerResult =
  | { ok: true; caller: Caller }
  | { ok: false; status: 401; detail: string };

/** Keys are stored and looked up by digest, so KV never holds a usable key. */
export async function hashKey(key: string): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(key));
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

/** Accepts `Authorization: Bearer <key>` or `X-API-Key: <key>`. */
export function presentedKey(request: Request): string | null {
  const authorization = request.headers.get("Authorization") ?? "";
  const bearer = /^Bearer\s+(.+)$/i.exec(authorization.trim());
  if (bearer) return bearer[1]?.trim() || null;
  const header = request.headers.get("X-API-Key");
  return header?.trim() || null;
}

export async function resolveCaller(request: Request, env: Env): Promise<CallerResult> {
  const key = presentedKey(request);

  if (!key) {
    // `CF-Connecting-IP` is set by Cloudflare and cannot be spoofed by the
    // client. The IP is used only as a rate limit counter and is never sent to
    // PostHog or forwarded to the origin.
    const ip = request.headers.get("CF-Connecting-IP") ?? "unknown";
    return { ok: true, caller: { tier: "anonymous", rateKey: `ip:${ip}` } };
  }

  const digest = await hashKey(key);
  const record = await env.API_KEYS.get(digest);
  if (record === null) {
    return { ok: false, status: 401, detail: "Unknown API key." };
  }

  let label = "unnamed";
  try {
    const parsed: unknown = JSON.parse(record);
    if (parsed && typeof parsed === "object" && typeof (parsed as { label?: unknown }).label === "string") {
      label = (parsed as { label: string }).label;
    }
  } catch {
    // A malformed record is a provisioning slip, not a reason to refuse a key
    // that is genuinely present in KV. Serve it under the fallback label.
  }

  return { ok: true, caller: { tier: "key", label, rateKey: `key:${digest}` } };
}
