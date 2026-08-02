"""Application server for the suite_actuarial open laboratory."""

import math
import os
import secrets
import time
from collections.abc import Awaitable, Callable
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from suite_actuarial.api.routers import (
    config,
    danos,
    pensiones,
    pricing,
    regulatory,
    reinsurance,
    reserves,
    salud,
)
from suite_actuarial.api.telemetry import schedule_api_event

app = FastAPI(
    title="suite_actuarial developer interface",
    version="2.2.0",
    description=(
        "Developer interface behind the open actuarial laboratory. "
        "Includes life product pricing (temporal, ordinario, dotal), "
        "reinsurance analysis (quota share, excess of loss, stop loss), "
        "reserve estimation (Chain Ladder, Bornhuetter-Ferguson, and an "
        "illustrative residual re-sampling band), "
        "and regulatory reference calculations. Simplified regulatory, fiscal, "
        "pension and market models are explicitly experimental."
    ),
)


def _allowed_origins() -> list[str]:
    """Origins allowed to call this API from a browser.

    The frontend is served from Cloudflare Pages, a different origin than the
    Cloud Run backend, so the allowlist has to name it explicitly. Set
    `SUITE_CORS_ORIGINS` to a comma-separated list per environment; the default
    covers local development only.

    `allow_credentials` stays off on purpose: this API uses no cookies and no
    session auth, and combining credentials with a wildcard origin is rejected
    by browsers anyway.
    """
    configured = os.environ.get("SUITE_CORS_ORIGINS", "").strip()
    if configured:
        return [origin.strip() for origin in configured.split(",") if origin.strip()]
    return ["http://localhost:3000", "http://127.0.0.1:3000"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.middleware("http")
async def capture_api_request_metrics(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Capture aggregate API health metrics when PostHog is configured.

    The event contains only route, method, status, outcome, and duration. No
    actuarial request data, response values, identity, IP, or query string is
    sent. The network call is queued after the response path and cannot change
    the API result.
    """
    tracked = request.url.path.startswith("/api/v1/") or request.url.path in {"/api/info"}
    if not tracked:
        return await call_next(request)
    started_at = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        schedule_api_event(
            route=request.url.path,
            method=request.method,
            status_code=500,
            started_at=started_at,
        )
        raise
    schedule_api_event(
        route=request.url.path,
        method=request.method,
        status_code=response.status_code,
        started_at=started_at,
    )
    return response


@app.middleware("http")
async def require_proxy_secret(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Reject traffic that did not arrive through the Cloudflare proxy.

    Only active when `SUITE_PROXY_SHARED_SECRET` is set, which is how the dev
    deployment is walled: the dev service is reachable on the open internet by
    URL, so an unlisted address is not a boundary. The Cloudflare worker adds
    the header server-side after Access has authenticated the visitor, so a
    direct request to the Cloud Run URL gets 404 instead of a working API.

    Production leaves the variable unset and stays open, as intended.

    `/health` stays exempt so the container health check keeps working.
    """
    expected = os.environ.get("SUITE_PROXY_SHARED_SECRET", "")
    if expected and request.url.path != "/health":
        if not secrets.compare_digest(request.headers.get("X-Proxy-Secret", ""), expected):
            # 404 rather than 403: a walled deployment should not confirm it exists.
            return JSONResponse({"detail": "Not Found"}, status_code=404)
    return await call_next(request)


def _json_seguro(valor: object) -> object:
    """Reemplaza los flotantes no finitos por su forma en texto.

    `json.dumps` rechaza `inf` y `nan`. FastAPI devuelve el valor recibido
    dentro del cuerpo del error de validacion, asi que una peticion con
    `Infinity` hacia fallar al *serializador del error*: el rechazo correcto
    (422) se convertia en un 500 sin cuerpo util.
    """
    if isinstance(valor, float) and not math.isfinite(valor):
        return str(valor)
    if isinstance(valor, dict):
        return {k: _json_seguro(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_json_seguro(v) for v in valor]
    return valor


@app.exception_handler(RequestValidationError)
async def validacion_no_finita(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Devuelve 422 con detalle utilizable aunque la entrada traiga inf o nan."""
    detalle = jsonable_encoder(exc.errors(), custom_encoder={float: _json_seguro})
    return JSONResponse({"detail": _json_seguro(detalle)}, status_code=422)


app.include_router(config.router, prefix="/api/v1")
app.include_router(danos.router, prefix="/api/v1")
app.include_router(pensiones.router, prefix="/api/v1")
app.include_router(pricing.router, prefix="/api/v1")
app.include_router(reinsurance.router, prefix="/api/v1")
app.include_router(reserves.router, prefix="/api/v1")
app.include_router(regulatory.router, prefix="/api/v1")
app.include_router(salud.router, prefix="/api/v1")


def api_information() -> dict[str, str | list[str]]:
    """Return machine-readable project and developer-interface metadata."""
    return {
        "name": "suite_actuarial open laboratory",
        "version": "2.2.0",
        "modules": [
            "config",
            "danos",
            "pensiones",
            "pricing",
            "reinsurance",
            "reserves",
            "regulatory",
            "salud",
        ],
        "docs_url": "/docs",
    }


@app.get("/api/info", tags=["root"])
def api_info() -> dict[str, str | list[str]]:
    """Expose metadata without making the API the product's front door."""
    return api_information()


@app.get("/health", tags=["root"])
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


frontend_directory = Path(os.environ.get("SUITE_ACTUARIAL_FRONTEND", "/app/frontend-static"))
if frontend_directory.is_dir():
    app.mount("/", StaticFiles(directory=frontend_directory, html=True), name="laboratory")
else:

    @app.get("/", tags=["root"])
    def development_root() -> dict[str, str | list[str]]:
        """Keep a useful root response when the static laboratory is not built."""
        return api_information()
