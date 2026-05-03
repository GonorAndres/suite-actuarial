"""Integration tests for the salud (health) API endpoints."""



class TestGMMCalcular:
    def test_success(self, api_client):
        payload = {
            "edad": 35,
            "sexo": "M",
            "suma_asegurada": 5_000_000,
            "deducible": 20_000,
            "coaseguro_pct": 0.10,
            "tope_coaseguro": 200_000,
            "zona": "urbano",
            "nivel": "medio",
        }
        response = api_client.post("/api/v1/salud/gmm/calcular", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "asegurado" in data
        assert "producto" in data
        assert "tarificacion" in data
        assert "siniestralidad_esperada" in data
        assert isinstance(data["siniestralidad_esperada"], (int, float))

    def test_success_female_metro(self, api_client):
        payload = {
            "edad": 28,
            "sexo": "F",
            "suma_asegurada": 10_000_000,
            "deducible": 50_000,
            "coaseguro_pct": 0.10,
            "zona": "metro",
            "nivel": "alto",
        }
        response = api_client.post("/api/v1/salud/gmm/calcular", json=payload)
        assert response.status_code == 200

    def test_validation_error_edad_too_high(self, api_client):
        payload = {
            "edad": 111,
            "sexo": "M",
            "suma_asegurada": 5_000_000,
            "deducible": 20_000,
            "coaseguro_pct": 0.10,
        }
        response = api_client.post("/api/v1/salud/gmm/calcular", json=payload)
        assert response.status_code == 422

    def test_validation_error_coaseguro_over_1(self, api_client):
        payload = {
            "edad": 35,
            "sexo": "M",
            "suma_asegurada": 5_000_000,
            "deducible": 20_000,
            "coaseguro_pct": 1.5,
        }
        response = api_client.post("/api/v1/salud/gmm/calcular", json=payload)
        assert response.status_code == 422


class TestAccidentesCalcular:
    def test_success(self, api_client):
        payload = {
            "edad": 40,
            "sexo": "M",
            "suma_asegurada": 1_000_000,
            "ocupacion": "oficina",
        }
        response = api_client.post("/api/v1/salud/accidentes/calcular", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "suma_asegurada" in data
        assert "prima_anual" in data
        assert "perdidas_organicas" in data
        assert "indemnizacion_diaria" in data
        assert "gastos_funerarios" in data
        assert isinstance(data["prima_anual"], (int, float))

    def test_validation_error_edad_under_18(self, api_client):
        payload = {
            "edad": 10,
            "sexo": "M",
            "suma_asegurada": 1_000_000,
        }
        response = api_client.post("/api/v1/salud/accidentes/calcular", json=payload)
        assert response.status_code == 422
