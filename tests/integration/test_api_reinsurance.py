"""Integration tests for the reinsurance API endpoints."""

import pytest

SINIESTROS = [
    {
        "id_siniestro": "S001",
        "fecha_ocurrencia": "2024-03-15",
        "monto_bruto": 500_000,
        "tipo": "individual",
    },
    {
        "id_siniestro": "S002",
        "fecha_ocurrencia": "2024-06-20",
        "monto_bruto": 1_200_000,
        "tipo": "individual",
    },
]


class TestQuotaShare:
    def test_success(self, api_client):
        payload = {
            "porcentaje_cesion": 40,
            "comision_reaseguro": 25,
            "comision_override": 2.0,
            "vigencia_inicio": "2024-01-01",
            "vigencia_fin": "2024-12-31",
            "moneda": "MXN",
            "prima_bruta": 10_000_000,
            "siniestros": SINIESTROS,
        }
        response = api_client.post("/api/v1/reinsurance/quota-share", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["tipo_contrato"] == "quota_share"
        assert "monto_cedido" in data
        assert "monto_retenido" in data
        assert "recuperacion_reaseguro" in data
        assert isinstance(data["monto_cedido"], (int, float))

    def test_validation_error_cesion_over_100(self, api_client):
        payload = {
            "porcentaje_cesion": 150,
            "comision_reaseguro": 25,
            "vigencia_inicio": "2024-01-01",
            "vigencia_fin": "2024-12-31",
            "prima_bruta": 10_000_000,
            "siniestros": [],
        }
        response = api_client.post("/api/v1/reinsurance/quota-share", json=payload)
        assert response.status_code == 422

    def test_validation_error_missing_prima(self, api_client):
        payload = {
            "porcentaje_cesion": 40,
            "comision_reaseguro": 25,
            "vigencia_inicio": "2024-01-01",
            "vigencia_fin": "2024-12-31",
            "siniestros": [],
        }
        response = api_client.post("/api/v1/reinsurance/quota-share", json=payload)
        assert response.status_code == 422


class TestExcessOfLoss:
    def test_success(self, api_client):
        payload = {
            "retencion": 500_000,
            "limite": 5_000_000,
            "modalidad": "por_riesgo",
            "numero_reinstatements": 1,
            "tasa_prima": 5.0,
            "vigencia_inicio": "2024-01-01",
            "vigencia_fin": "2024-12-31",
            "moneda": "MXN",
            "prima_reaseguro_cobrada": 250_000,
            "siniestros": SINIESTROS,
        }
        response = api_client.post("/api/v1/reinsurance/excess-of-loss", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["tipo_contrato"] == "excess_of_loss"
        assert "recuperacion_reaseguro" in data
        assert "resultado_neto_cedente" in data

    def test_validation_error_zero_retencion(self, api_client):
        payload = {
            "retencion": 0,
            "limite": 5_000_000,
            "tasa_prima": 5.0,
            "vigencia_inicio": "2024-01-01",
            "vigencia_fin": "2024-12-31",
            "prima_reaseguro_cobrada": 250_000,
            "siniestros": [],
        }
        response = api_client.post("/api/v1/reinsurance/excess-of-loss", json=payload)
        assert response.status_code == 422


class TestStopLoss:
    def test_success(self, api_client):
        payload = {
            "attachment_point": 80,
            "limite_cobertura": 20,
            "primas_sujetas": 10_000_000,
            "vigencia_inicio": "2024-01-01",
            "vigencia_fin": "2024-12-31",
            "moneda": "MXN",
            "primas_totales": 10_000_000,
            "prima_reaseguro_cobrada": 500_000,
            "siniestros": SINIESTROS,
        }
        response = api_client.post("/api/v1/reinsurance/stop-loss", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["tipo_contrato"] == "stop_loss"
        assert "monto_cedido" in data
        assert "resultado_neto_cedente" in data

    def test_validation_error_attachment_over_200(self, api_client):
        payload = {
            "attachment_point": 250,
            "limite_cobertura": 20,
            "primas_sujetas": 10_000_000,
            "vigencia_inicio": "2024-01-01",
            "vigencia_fin": "2024-12-31",
            "primas_totales": 10_000_000,
            "siniestros": [],
        }
        response = api_client.post("/api/v1/reinsurance/stop-loss", json=payload)
        assert response.status_code == 422
