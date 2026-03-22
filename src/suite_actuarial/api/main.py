"""
Main FastAPI application for the Mexican Insurance Analytics Suite.

Provides REST endpoints for pricing, reinsurance, reserves, and regulatory
calculations used in the Mexican insurance market.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from suite_actuarial.api.routers import pricing, regulatory, reinsurance, reserves

app = FastAPI(
    title="Mexican Insurance Analytics Suite API",
    version="1.0.0",
    description=(
        "REST API for actuarial calculations in the Mexican insurance market. "
        "Includes life product pricing (temporal, ordinario, dotal), "
        "reinsurance analysis (quota share, excess of loss, stop loss), "
        "reserve estimation (Chain Ladder, Bornhuetter-Ferguson, Bootstrap), "
        "and regulatory compliance (RCS, SAT deductibility, ISR withholding)."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pricing.router, prefix="/api/v1")
app.include_router(reinsurance.router, prefix="/api/v1")
app.include_router(reserves.router, prefix="/api/v1")
app.include_router(regulatory.router, prefix="/api/v1")


@app.get("/", tags=["root"])
def root():
    """Return basic API information."""
    return {
        "name": "Mexican Insurance Analytics Suite API",
        "version": "1.0.0",
        "modules": [
            "pricing",
            "reinsurance",
            "reserves",
            "regulatory",
        ],
        "docs_url": "/docs",
    }


@app.get("/health", tags=["root"])
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
