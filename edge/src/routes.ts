/**
 * Route classification: what gets cached, and how a path is reported.
 *
 * These are pure functions on purpose. They carry the decisions that are easy
 * to get quietly wrong -- caching something that varies, or emitting an
 * analytics label with unbounded cardinality -- so they are the part of the
 * edge that is directly testable without a network or a binding.
 */

/** Path prefixes this Worker recognises as belonging to the API. */
const KNOWN_PREFIXES = [
  "/api/v1/config",
  "/api/v1/danos",
  "/api/v1/pensiones",
  "/api/v1/pricing",
  "/api/v1/reinsurance",
  "/api/v1/reserves",
  "/api/v1/regulatory",
  "/api/v1/salud",
];

/** Exact paths that are part of the API surface but sit outside `/api/v1`. */
const KNOWN_EXACT = ["/api/info", "/health", "/docs", "/redoc", "/openapi.json"];

/**
 * Label used for any path the API does not define.
 *
 * Without it a scanner walking random URLs would create a new PostHog property
 * value per probe. The status code still records that the request 404'd, so
 * scanning stays visible without the cardinality.
 */
export const UNMATCHED_ROUTE = "<unmatched>";

const DIGITS = /^\d+$/;
const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

function isKnown(pathname: string): boolean {
  if (KNOWN_EXACT.includes(pathname)) return true;
  return KNOWN_PREFIXES.some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
  );
}

/**
 * Reduce a concrete path to a stable analytics label.
 *
 * `/api/v1/config/2026/uma` becomes `/api/v1/config/:num/uma`. The year is
 * dropped deliberately: one label per route keeps the event property bounded,
 * and which year was queried is not what this metric is for.
 */
export function normalizeRoute(pathname: string): string {
  if (!isKnown(pathname)) return UNMATCHED_ROUTE;
  return pathname
    .split("/")
    .map((segment) => {
      if (DIGITS.test(segment)) return ":num";
      if (ISO_DATE.test(segment)) return ":date";
      return segment;
    })
    .join("/");
}

/**
 * Whether a response may be served from the edge cache.
 *
 * Only the annual regulatory configuration and the metadata endpoint qualify:
 * both are the same for every caller and change only on deploy. Every
 * calculation endpoint is a POST carrying the caller's own assumptions, so
 * there is nothing shared to cache and caching one would be a correctness bug,
 * not just a stale read.
 */
export function isCacheable(method: string, pathname: string): boolean {
  if (method !== "GET") return false;
  return pathname === "/api/info" || pathname.startsWith("/api/v1/config/");
}
