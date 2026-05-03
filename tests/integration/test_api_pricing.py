"""Integration tests for the pricing API endpoints."""

import pytest

VALID_PRICING_PAYLOAD = {
    "edad": 35,
    "sexo": "H",
    "suma_asegurada": 1_000_000,
    "plazo_years": 20,
    "tasa_interes": 0.055,
    "frecuencia_pago": "anual",
    "recargo_gastos_admin": 0.05,
    "recargo_gastos_adq": 0.10,
    "recargo_utilidad": 0.03,
}


def _assert_pricing_response(data):
    """Validate shared PricingResponse structure."""
    assert "producto" in data
    assert "prima_neta" in data
    assert "prima_total" in data
    assert "moneda" in data
    assert "desglose_recargos" in data
    assert "metadata" in data
    assert isinstance(data["prima_neta"], (int, float))
    assert isinstance(data["prima_total"], (int, float))
    assert data["prima_neta"] > 0
    assert data["prima_total"] > 0


class TestPricingTemporal:
    def test_success(self, api_client):
        response = api_client.post("/api/v1/pricing/temporal", json=VALID_PRICING_PAYLOAD)
        assert response.status_code == 200
        data = response.json()
        _assert_pricing_response(data)
        assert data["producto"] == "temporal"

    def test_invalid_edad_negative(self, api_client):
        payload = {**VALID_PRICING_PAYLOAD, "edad": -1}
        response = api_client.post("/api/v1/pricing/temporal", json=payload)
        assert response.status_code == 422

    def test_invalid_edad_too_high(self, api_client):
        payload = {**VALID_PRICING_PAYLOAD, "edad": 121}
        response = api_client.post("/api/v1/pricing/temporal", json=payload)
        assert response.status_code == 422

    def test_domain_error_edad_plus_plazo_exceeds_table(self, api_client):
        payload = {**VALID_PRICING_PAYLOAD, "edad": 100, "plazo_years": 30}
        response = api_client.post("/api/v1/pricing/temporal", json=payload)
        assert response.status_code == 400


class TestPricingOrdinario:
    def test_success(self, api_client):
        response = api_client.post("/api/v1/pricing/ordinario", json=VALID_PRICING_PAYLOAD)
        assert response.status_code == 200
        data = response.json()
        _assert_pricing_response(data)
        assert data["producto"] == "ordinario"

    def test_validation_error_missing_sexo(self, api_client):
        payload = {k: v for k, v in VALID_PRICING_PAYLOAD.items() if k != "sexo"}
        response = api_client.post("/api/v1/pricing/ordinario", json=payload)
        assert response.status_code == 422


class TestPricingDotal:
    def test_success(self, api_client):
        response = api_client.post("/api/v1/pricing/dotal", json=VALID_PRICING_PAYLOAD)
        assert response.status_code == 200
        data = response.json()
        _assert_pricing_response(data)
        assert data["producto"] == "dotal"

    def test_validation_error_zero_suma(self, api_client):
        payload = {**VALID_PRICING_PAYLOAD, "suma_asegurada": 0}
        response = api_client.post("/api/v1/pricing/dotal", json=payload)
        assert response.status_code == 422


class TestPricingCompare:
    def test_success(self, api_client):
        response = api_client.post("/api/v1/pricing/compare", json=VALID_PRICING_PAYLOAD)
        assert response.status_code == 200
        data = response.json()
        assert "temporal" in data
        assert "ordinario" in data
        assert "dotal" in data
        _assert_pricing_response(data["temporal"])
        _assert_pricing_response(data["ordinario"])
        _assert_pricing_response(data["dotal"])

    def test_compare_invalid_sexo(self, api_client):
        payload = {**VALID_PRICING_PAYLOAD, "sexo": "X"}
        response = api_client.post("/api/v1/pricing/compare", json=payload)
        assert response.status_code == 422
