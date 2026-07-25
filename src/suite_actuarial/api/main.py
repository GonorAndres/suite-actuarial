"""Application server for the suite_actuarial open laboratory."""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

app = FastAPI(
    title="suite_actuarial developer interface",
    version="2.1.0",
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        "version": "2.1.0",
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
def health_check():
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
