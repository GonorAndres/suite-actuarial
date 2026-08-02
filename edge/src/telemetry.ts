/**
 * PostHog capture from the edge.
 *
 * This mirrors the contract in `src/suite_actuarial/api/telemetry.py` and
 * deliberately keeps the same shape, but it is a separate event
 * (`api_edge_request`) rather than a second source for `api_request`. Two
 * reasons: the origin never sees a request that was rate limited or served
 * from cache, so the counts would not agree; and keeping them distinct means a
 * discrepancy between the two is readable as "the edge absorbed it" instead of
 * looking like data loss.
 *
 * What is not sent, matching the project's standing analytics contract: request
 * bodies, query strings, response bodies, actuarial inputs or results, user
 * agents, IP addresses, and API keys. Country and Cloudflare location are new
 * to the edge event and are documented in `docs/ANALYTICS.md`.
 */

import type { CacheState, Caller, Outcome } from "./types";

export const EDGE_EVENT = "api_edge_request";
export const ANONYMOUS_DISTINCT_ID = "suite-actuarial-api-edge";
const LIB_VERSION = "2.2.0";

export function outcomeFor(status: number): Outcome {
  if (status === 429) return "rate_limited";
  if (status < 400) return "success";
  if (status < 500) return "client_error";
  return "server_error";
}

export interface EdgeEventInput {
  route: string;
  method: string;
  status: number;
  durationMs: number;
  cache: CacheState;
  caller: Caller;
  country?: string;
  colo?: string;
  apiKey: string;
}

export function buildEdgeEventPayload(input: EdgeEventInput): Record<string, unknown> {
  const properties: Record<string, unknown> = {
    // A fixed id for anonymous traffic, the key label for identified traffic.
    // Person profiles stay off in both cases: the point is to see which
    // surfaces are used and by which integration, not to build a profile.
    distinct_id: input.caller.tier === "key" ? `key:${input.caller.label}` : ANONYMOUS_DISTINCT_ID,
    $process_person_profile: false,
    $lib: "suite_actuarial_edge",
    $lib_version: LIB_VERSION,
    api_route: input.route,
    http_method: input.method,
    status_code: input.status,
    duration_ms: Math.max(0, Math.round(input.durationMs)),
    outcome: outcomeFor(input.status),
    cache: input.cache,
    auth_tier: input.caller.tier,
  };
  if (input.caller.tier === "key") properties.api_key_label = input.caller.label;
  if (input.country) properties.country = input.country;
  if (input.colo) properties.colo = input.colo;

  return { api_key: input.apiKey, event: EDGE_EVENT, properties };
}

/**
 * Send the event. Never throws: a telemetry outage must not become an API
 * outage, and the caller has already received their response by the time this
 * runs inside `waitUntil`.
 */
export async function captureEdgeEvent(
  host: string,
  payload: Record<string, unknown>,
): Promise<void> {
  try {
    await fetch(`${host.replace(/\/+$/, "")}/capture/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch (error) {
    console.error("PostHog capture failed", error);
  }
}
