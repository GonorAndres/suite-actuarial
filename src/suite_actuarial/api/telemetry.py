"""Privacy-safe, opt-in server-side telemetry for API request health."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from collections.abc import Mapping
from urllib.request import Request, urlopen

LOGGER = logging.getLogger(__name__)
POSTHOG_EVENT = "api_request"
POSTHOG_DISTINCT_ID = "suite-actuarial-api"


def _posthog_api_key() -> str:
    return os.environ.get("POSTHOG_PROJECT_API_KEY", os.environ.get("POSTHOG_API_KEY", "")).strip()


def posthog_enabled() -> bool:
    """Return whether the deployment has opted into PostHog capture."""
    return bool(_posthog_api_key())


def build_api_event_payload(
    *,
    route: str,
    method: str,
    status_code: int,
    duration_ms: int,
    outcome: str,
    api_key: str,
) -> dict[str, object]:
    """Build the narrow event contract sent to PostHog.

    Request bodies, query strings, response bodies, user agents, IP addresses,
    and actuarial inputs/results are intentionally excluded.
    """
    properties: dict[str, object] = {
        "distinct_id": POSTHOG_DISTINCT_ID,
        "$process_person_profile": False,
        "$lib": "suite_actuarial_api",
        "$lib_version": "2.2.0",
        "api_route": route,
        "http_method": method,
        "status_code": int(status_code),
        "duration_ms": max(0, int(duration_ms)),
        "outcome": outcome,
    }
    return {"api_key": api_key, "event": POSTHOG_EVENT, "properties": properties}


def _send_payload(payload: Mapping[str, object]) -> None:
    host = os.environ.get("POSTHOG_HOST", "https://us.i.posthog.com").rstrip("/")
    request = Request(
        f"{host}/capture/",
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=1.5) as response:  # noqa: S310 - host is deployment configuration
        response.read()


def _log_task_failure(task: asyncio.Task[object]) -> None:
    try:
        task.result()
    except Exception:  # pragma: no cover - network failures depend on deployment
        LOGGER.debug("PostHog capture failed", exc_info=True)


def schedule_api_event(
    *,
    route: str,
    method: str,
    status_code: int,
    started_at: float,
) -> None:
    """Queue a capture without delaying or failing the API response."""
    api_key = _posthog_api_key()
    if not api_key:
        return
    duration_ms = round((time.perf_counter() - started_at) * 1000)
    outcome = (
        "success" if status_code < 400 else "client_error" if status_code < 500 else "server_error"
    )
    payload = build_api_event_payload(
        route=route,
        method=method,
        status_code=status_code,
        duration_ms=duration_ms,
        outcome=outcome,
        api_key=api_key,
    )
    try:
        task = asyncio.create_task(asyncio.to_thread(_send_payload, payload))
    except RuntimeError:  # pragma: no cover - only possible without an active event loop
        return
    task.add_done_callback(_log_task_failure)
