"""Integration tests for the reserves API endpoints."""

import pytest

VALID_TRIANGLE = [
    [3000, 5000, 5600, 5800, 5900],
    [3200, 5200, 5800, 6000, None],
    [3500, 5500, 6100, None, None],
    [3800, 5900, None, None, None],
    [4000, None, None, None, None],
]
ORIGIN_YEARS = [2019, 2020, 2021, 2022, 2023]


class TestChainLadder:
    def test_success(self, api_client):
        payload = {
            "triangle": VALID_TRIANGLE,
            "origin_years": ORIGIN_YEARS,
            "metodo_promedio": "simple",
            "calcular_tail_factor": False,
        }
        response = api_client.post("/api/v1/reserves/chain-ladder", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["metodo"] == "chain_ladder"
        assert "reserva_total" in data
        assert "ultimate_total" in data
        assert "factores_desarrollo" in data
        assert isinstance(data["reserva_total"], (int, float))
        assert data["reserva_total"] >= 0

    def test_success_weighted(self, api_client):
        payload = {
            "triangle": VALID_TRIANGLE,
            "origin_years": ORIGIN_YEARS,
            "metodo_promedio": "weighted",
        }
        response = api_client.post("/api/v1/reserves/chain-ladder", json=payload)
        assert response.status_code == 200

    def test_validation_error_mismatched_rows(self, api_client):
        payload = {
            "triangle": VALID_TRIANGLE,
            "origin_years": [2019, 2020],
        }
        response = api_client.post("/api/v1/reserves/chain-ladder", json=payload)
        assert response.status_code == 400


class TestBornhuetterFerguson:
    def test_success(self, api_client):
        payload = {
            "triangle": VALID_TRIANGLE,
            "origin_years": ORIGIN_YEARS,
            "primas_por_anio": {
                "2019": 8000,
                "2020": 8500,
                "2021": 9000,
                "2022": 9500,
                "2023": 10000,
            },
            "loss_ratio_apriori": 0.65,
            "metodo_promedio": "simple",
        }
        response = api_client.post("/api/v1/reserves/bornhuetter-ferguson", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["metodo"] == "bornhuetter_ferguson"
        assert "reserva_total" in data
        assert isinstance(data["reserva_total"], (int, float))

    def test_validation_error_zero_loss_ratio(self, api_client):
        payload = {
            "triangle": VALID_TRIANGLE,
            "origin_years": ORIGIN_YEARS,
            "primas_por_anio": {"2019": 8000},
            "loss_ratio_apriori": 0,
        }
        response = api_client.post("/api/v1/reserves/bornhuetter-ferguson", json=payload)
        assert response.status_code == 422


class TestBootstrap:
    def test_success_with_seed(self, api_client):
        payload = {
            "triangle": VALID_TRIANGLE,
            "origin_years": ORIGIN_YEARS,
            "num_simulaciones": 500,
            "seed": 42,
            "percentiles": [50, 75, 90, 95, 99],
        }
        response = api_client.post("/api/v1/reserves/bootstrap", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["metodo"] == "bootstrap"
        assert "reserva_total" in data
        assert "percentiles" in data
        assert isinstance(data["percentiles"], dict)
        assert data["reserva_total"] >= 0

    def test_deterministic_with_same_seed(self, api_client):
        payload = {
            "triangle": VALID_TRIANGLE,
            "origin_years": ORIGIN_YEARS,
            "num_simulaciones": 500,
            "seed": 42,
        }
        r1 = api_client.post("/api/v1/reserves/bootstrap", json=payload)
        r2 = api_client.post("/api/v1/reserves/bootstrap", json=payload)
        assert r1.json()["reserva_total"] == r2.json()["reserva_total"]
