"""Integration tests for the danos (P&C) API endpoints."""

import pytest


class TestAutoCalcuar:
    def test_success(self, api_client):
        payload = {
            "valor_vehiculo": 350_000,
            "tipo_vehiculo": "sedan_compacto",
            "antiguedad_anos": 3,
            "zona": "guadalajara",
            "edad_conductor": 35,
            "deducible_pct": 0.05,
        }
        response = api_client.post("/api/v1/danos/auto/calcular", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "vehiculo" in data
        assert "conductor" in data
        assert "coberturas" in data
        assert "prima_total" in data
        assert isinstance(data["prima_total"], (int, float))
        assert data["prima_total"] > 0

    def test_success_with_historial(self, api_client):
        payload = {
            "valor_vehiculo": 350_000,
            "tipo_vehiculo": "sedan_compacto",
            "antiguedad_anos": 3,
            "zona": "guadalajara",
            "edad_conductor": 35,
            "historial_siniestros": [0, 0, 1],
        }
        response = api_client.post("/api/v1/danos/auto/calcular", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "bonus_malus" in data

    def test_validation_error_negative_valor(self, api_client):
        payload = {
            "valor_vehiculo": -1,
            "tipo_vehiculo": "sedan_compacto",
            "antiguedad_anos": 3,
            "zona": "guadalajara",
            "edad_conductor": 35,
        }
        response = api_client.post("/api/v1/danos/auto/calcular", json=payload)
        assert response.status_code == 422

    def test_validation_error_edad_conductor_under_18(self, api_client):
        payload = {
            "valor_vehiculo": 350_000,
            "tipo_vehiculo": "sedan_compacto",
            "antiguedad_anos": 3,
            "zona": "guadalajara",
            "edad_conductor": 16,
        }
        response = api_client.post("/api/v1/danos/auto/calcular", json=payload)
        assert response.status_code == 422


class TestIncendioCalcular:
    def test_success(self, api_client):
        payload = {
            "valor_inmueble": 5_000_000,
            "tipo_construccion": "concreto",
            "zona": "urbana_media",
            "uso": "habitacional",
        }
        response = api_client.post("/api/v1/danos/incendio/calcular", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "valor_inmueble" in data
        assert "prima_anual" in data
        assert "tasa_base" in data
        assert isinstance(data["prima_anual"], (int, float))
        assert data["prima_anual"] > 0

    def test_validation_error_zero_valor(self, api_client):
        payload = {
            "valor_inmueble": 0,
            "tipo_construccion": "concreto",
            "zona": "urbana_media",
            "uso": "habitacional",
        }
        response = api_client.post("/api/v1/danos/incendio/calcular", json=payload)
        assert response.status_code == 422


class TestRCCalcular:
    def test_success(self, api_client):
        payload = {
            "limite_responsabilidad": 10_000_000,
            "deducible": 100_000,
            "clase_actividad": "oficinas",
        }
        response = api_client.post("/api/v1/danos/rc/calcular", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "limite_responsabilidad" in data
        assert "prima_anual" in data
        assert "tasa_base" in data
        assert isinstance(data["prima_anual"], (int, float))


class TestBonusMalus:
    def test_success_no_claims(self, api_client):
        payload = {
            "nivel_actual": 0,
            "numero_siniestros": 0,
        }
        response = api_client.post("/api/v1/danos/bonus-malus", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "nivel_previo" in data
        assert "nivel_nuevo" in data
        assert "factor" in data
        assert data["nivel_previo"] == 0
        # No claims should decrease the level
        assert data["nivel_nuevo"] < data["nivel_previo"]

    def test_success_with_claims(self, api_client):
        payload = {
            "nivel_actual": 0,
            "numero_siniestros": 2,
        }
        response = api_client.post("/api/v1/danos/bonus-malus", json=payload)
        assert response.status_code == 200
        data = response.json()
        # Claims should increase the level
        assert data["nivel_nuevo"] > data["nivel_previo"]


class TestFrecuenciaSeveridad:
    def test_success_with_seed(self, api_client):
        payload = {
            "dist_frecuencia": "poisson",
            "params_frecuencia": {"lambda_": 5.0},
            "dist_severidad": "lognormal",
            "params_severidad": {"mu": 10.0, "sigma": 1.5},
            "n_simulaciones": 10_000,
            "seed": 42,
        }
        response = api_client.post("/api/v1/danos/frecuencia-severidad", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "prima_pura" in data
        assert "var_95" in data
        assert "tvar_95" in data
        assert "var_99" in data
        assert "tvar_99" in data
        assert "simulaciones" in data
        assert isinstance(data["prima_pura"], (int, float))
        assert data["prima_pura"] > 0

    def test_deterministic_with_same_seed(self, api_client):
        payload = {
            "dist_frecuencia": "poisson",
            "params_frecuencia": {"lambda_": 5.0},
            "dist_severidad": "lognormal",
            "params_severidad": {"mu": 10.0, "sigma": 1.5},
            "n_simulaciones": 10_000,
            "seed": 123,
        }
        r1 = api_client.post("/api/v1/danos/frecuencia-severidad", json=payload)
        r2 = api_client.post("/api/v1/danos/frecuencia-severidad", json=payload)
        assert r1.json()["prima_pura"] == r2.json()["prima_pura"]
