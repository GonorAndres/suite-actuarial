import { describe, expect, it } from "vitest";

import { UNMATCHED_ROUTE, isCacheable, normalizeRoute } from "../src/routes";

describe("normalizeRoute", () => {
  it("keeps a known route intact", () => {
    expect(normalizeRoute("/api/v1/pricing/temporal")).toBe("/api/v1/pricing/temporal");
    expect(normalizeRoute("/api/info")).toBe("/api/info");
  });

  it("collapses the year so one route is one label", () => {
    expect(normalizeRoute("/api/v1/config/2026/uma")).toBe("/api/v1/config/:num/uma");
    expect(normalizeRoute("/api/v1/config/2025/uma")).toBe("/api/v1/config/:num/uma");
  });

  it("collapses ISO dates", () => {
    expect(normalizeRoute("/api/v1/config/fecha/2026-08-02")).toBe("/api/v1/config/fecha/:date");
  });

  it("reports undefined paths under one label so scanning cannot inflate cardinality", () => {
    expect(normalizeRoute("/wp-admin.php")).toBe(UNMATCHED_ROUTE);
    expect(normalizeRoute("/api/v1/nope")).toBe(UNMATCHED_ROUTE);
    expect(normalizeRoute("/api/v1/pricingX")).toBe(UNMATCHED_ROUTE);
  });
});

describe("isCacheable", () => {
  it("caches the annual configuration and the metadata endpoint", () => {
    expect(isCacheable("GET", "/api/v1/config/2026/uma")).toBe(true);
    expect(isCacheable("GET", "/api/info")).toBe(true);
  });

  it("never caches a calculation", () => {
    // Every pricing/reserve endpoint is a POST carrying the caller's own
    // assumptions. Caching one would return another caller's numbers.
    expect(isCacheable("POST", "/api/v1/pricing/temporal")).toBe(false);
    expect(isCacheable("GET", "/api/v1/pricing/temporal")).toBe(false);
    expect(isCacheable("POST", "/api/v1/config/2026/uma")).toBe(false);
  });

  it("does not cache health, which exists to report the current state", () => {
    expect(isCacheable("GET", "/health")).toBe(false);
  });
});
