import { describe, expect, it } from "vitest";

import { presentedKey } from "../src/auth";
import { EDGE_EVENT, buildEdgeEventPayload, outcomeFor } from "../src/telemetry";
import type { Caller } from "../src/types";

const anonymous: Caller = { tier: "anonymous", rateKey: "ip:198.51.100.1" };
const keyed: Caller = { tier: "key", label: "acme", rateKey: "key:abc123" };

function payload(caller: Caller, status = 200) {
  return buildEdgeEventPayload({
    route: "/api/v1/pricing/temporal",
    method: "POST",
    status,
    durationMs: 12.6,
    cache: "bypass",
    caller,
    country: "MX",
    colo: "QRO",
    apiKey: "phc_test",
  });
}

describe("outcomeFor", () => {
  it("separates a rate-limited request from an ordinary client error", () => {
    // 429 is the edge doing its job, not a caller mistake. Folding it into
    // client_error would hide the signal this layer exists to produce.
    expect(outcomeFor(429)).toBe("rate_limited");
    expect(outcomeFor(422)).toBe("client_error");
    expect(outcomeFor(200)).toBe("success");
    expect(outcomeFor(502)).toBe("server_error");
  });
});

describe("buildEdgeEventPayload", () => {
  it("carries the documented contract and nothing else", () => {
    const properties = payload(anonymous).properties as Record<string, unknown>;

    expect(Object.keys(properties).sort()).toEqual(
      [
        "$lib",
        "$lib_version",
        "$process_person_profile",
        "api_route",
        "auth_tier",
        "cache",
        "colo",
        "country",
        "distinct_id",
        "duration_ms",
        "http_method",
        "outcome",
        "status_code",
      ].sort(),
    );
  });

  it("names the edge event distinctly from the origin's", () => {
    // The origin emits `api_request` and never sees a rate-limited or cached
    // request. Sharing one name would make the gap look like data loss.
    expect(payload(anonymous).event).toBe(EDGE_EVENT);
    expect(payload(anonymous).event).toBe("api_edge_request");
  });

  it("keeps anonymous traffic under one id and creates no person profile", () => {
    const properties = payload(anonymous).properties as Record<string, unknown>;
    expect(properties.distinct_id).toBe("suite-actuarial-api-edge");
    expect(properties.$process_person_profile).toBe(false);
    expect(properties.api_key_label).toBeUndefined();
  });

  it("attributes a key holder by label", () => {
    const properties = payload(keyed).properties as Record<string, unknown>;
    expect(properties.distinct_id).toBe("key:acme");
    expect(properties.api_key_label).toBe("acme");
    expect(properties.$process_person_profile).toBe(false);
  });

  it("rounds duration and never reports a negative one", () => {
    expect((payload(anonymous).properties as Record<string, unknown>).duration_ms).toBe(13);
  });
});

describe("presentedKey", () => {
  const at = (headers: HeadersInit) => new Request("https://api-suite.gonor.me/", { headers });

  it("reads a bearer token case-insensitively", () => {
    expect(presentedKey(at({ Authorization: "Bearer abc" }))).toBe("abc");
    expect(presentedKey(at({ Authorization: "bearer abc" }))).toBe("abc");
  });

  it("reads the dedicated header", () => {
    expect(presentedKey(at({ "X-API-Key": "abc" }))).toBe("abc");
  });

  it("treats absent or empty credentials as anonymous", () => {
    expect(presentedKey(at({}))).toBeNull();
    expect(presentedKey(at({ "X-API-Key": "   " }))).toBeNull();
    expect(presentedKey(at({ Authorization: "Basic abc" }))).toBeNull();
  });
});
