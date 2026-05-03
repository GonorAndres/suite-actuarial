"""Integration tests for the config API endpoints."""

import pytest


class TestConfigFull:
    def test_success(self, api_client):
        response = api_client.get("/api/v1/config/2026")
        assert response.status_code == 200
        data = response.json()
        assert data["anio"] == 2026
        assert "uma" in data
        assert "tasas_sat" in data
        assert "factores_cnsf" in data
        assert "factores_tecnicos" in data

    def test_missing_year_returns_404(self, api_client):
        response = api_client.get("/api/v1/config/1999")
        assert response.status_code == 404


class TestConfigUMA:
    def test_success(self, api_client):
        response = api_client.get("/api/v1/config/2026/uma")
        assert response.status_code == 200
        data = response.json()
        assert "uma_diaria" in data
        assert "uma_mensual" in data
        assert "uma_anual" in data
        assert isinstance(data["uma_diaria"], (int, float))
        assert data["uma_diaria"] > 0


class TestConfigTasasSAT:
    def test_success(self, api_client):
        response = api_client.get("/api/v1/config/2026/tasas-sat")
        assert response.status_code == 200
        data = response.json()
        assert "tasa_retencion_rentas_vitalicias" in data
        assert "tasa_isr_personas_morales" in data
        assert "tasa_iva" in data
        assert "limite_deducciones_pf_umas" in data


class TestConfigFactoresCNSF:
    def test_success(self, api_client):
        response = api_client.get("/api/v1/config/2026/factores-cnsf")
        assert response.status_code == 200
        data = response.json()
        assert "shock_acciones" in data
        assert "shock_inmuebles" in data
        assert "shocks_credito" in data
        assert "correlacion_vida_danos" in data
        assert isinstance(data["shocks_credito"], dict)
