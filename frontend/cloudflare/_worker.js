/**
 * Cloudflare Pages worker for the dev deployment.
 *
 * Two jobs:
 *
 * 1. Serve the static export unchanged for every normal request.
 * 2. Proxy `/api/*` to the dev Cloud Run service so the dashboard and the API
 *    share one origin. Same origin means no CORS preflight and, more to the
 *    point, one Cloudflare Access policy covers both: a visitor who has not
 *    passed Access never reaches either.
 *
 * The shared secret is added here, on Cloudflare's side, and never ships to the
 * browser. The dev backend can therefore reject anything that did not come
 * through this proxy, which is what makes the wall real rather than an unlisted
 * URL. Set both values as environment variables on the Pages project:
 *
 *   API_ORIGIN           https://suite-actuarial-dev-<hash>-uc.a.run.app
 *   PROXY_SHARED_SECRET  (same value the Cloud Run service holds)
 */

const worker = {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (!url.pathname.startsWith("/api/")) {
      return env.ASSETS.fetch(request);
    }

    if (!env.API_ORIGIN) {
      return new Response("API_ORIGIN is not configured for this deployment", {
        status: 503,
      });
    }

    const upstream = new URL(url.pathname + url.search, env.API_ORIGIN);
    const headers = new Headers(request.headers);
    headers.set("Host", upstream.host);
    if (env.PROXY_SHARED_SECRET) {
      headers.set("X-Proxy-Secret", env.PROXY_SHARED_SECRET);
    }

    return fetch(
      new Request(upstream, {
        method: request.method,
        headers,
        body: request.method === "GET" || request.method === "HEAD" ? undefined : request.body,
        redirect: "manual",
      }),
    );
  },
};

export default worker;
