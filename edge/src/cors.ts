/**
 * CORS for a public, credential-free API.
 *
 * The origin's own allowlist names only the dashboard. Opening the policy here
 * rather than there keeps the two decisions separate: the Cloud Run service
 * stays reachable by exactly one named site, while the edge -- which is the
 * only thing the public can reach -- is what decides who may call from a
 * browser.
 *
 * `Access-Control-Allow-Credentials` stays off. The API has no cookies and no
 * session, and a wildcard origin combined with credentials is rejected by
 * browsers anyway.
 */

const HEADERS: Record<string, string> = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, X-API-Key",
  "Access-Control-Max-Age": "86400",
};

export function withCors(response: Response): Response {
  const merged = new Response(response.body, response);
  for (const [name, value] of Object.entries(HEADERS)) {
    merged.headers.set(name, value);
  }
  return merged;
}

/**
 * Answer a preflight at the edge without touching the origin.
 *
 * A preflight carries no caller intent worth counting, so it is not rate
 * limited and not reported: doing either would inflate every metric by roughly
 * the number of cross-origin POSTs.
 */
export function preflight(): Response {
  return withCors(new Response(null, { status: 204 }));
}
