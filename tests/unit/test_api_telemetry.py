"""Tests for the opt-in, payload-free API telemetry contract."""

from suite_actuarial.api.telemetry import build_api_event_payload


def test_payload_contains_only_api_health_fields() -> None:
    payload = build_api_event_payload(
        route="/api/v1/pricing/ordinario",
        method="POST",
        status_code=200,
        duration_ms=18,
        outcome="success",
        api_key="phc_test",
    )

    assert payload["api_key"] == "phc_test"
    assert payload["event"] == "api_request"
    assert payload["properties"] == {
        "distinct_id": "suite-actuarial-api",
        "$process_person_profile": False,
        "$lib": "suite_actuarial_api",
        "$lib_version": "2.1.0",
        "api_route": "/api/v1/pricing/ordinario",
        "http_method": "POST",
        "status_code": 200,
        "duration_ms": 18,
        "outcome": "success",
    }


def test_payload_does_not_accept_request_or_result_data() -> None:
    payload = build_api_event_payload(
        route="/api/v1/danos/bonus-malus",
        method="POST",
        status_code=422,
        duration_ms=-4,
        outcome="client_error",
        api_key="phc_test",
    )
    properties = payload["properties"]

    assert isinstance(properties, dict)
    assert properties["duration_ms"] == 0
    assert "request_body" not in properties
    assert "response_body" not in properties
    assert "suma_asegurada" not in properties
    assert "resultado" not in properties
