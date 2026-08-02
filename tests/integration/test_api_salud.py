"""Integration tests for the salud (health) API endpoints."""

import pytest

from tests.integration.sexo_heredado import LETRAS_HEREDADAS, assert_rechaza_sexo_heredado


class TestGMMCalcular:
    def test_success(self, api_client):
        payload = {
            "edad": 35,
            "sexo": "masculino",
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
            "sexo": "femenino",
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
            "sexo": "masculino",
            "suma_asegurada": 5_000_000,
            "deducible": 20_000,
            "coaseguro_pct": 0.10,
        }
        response = api_client.post("/api/v1/salud/gmm/calcular", json=payload)
        assert response.status_code == 422

    def test_validation_error_coaseguro_over_1(self, api_client):
        payload = {
            "edad": 35,
            "sexo": "masculino",
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
            "sexo": "masculino",
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
            "sexo": "masculino",
            "suma_asegurada": 1_000_000,
        }
        response = api_client.post("/api/v1/salud/accidentes/calcular", json=payload)
        assert response.status_code == 422


class TestSexoHeredado:
    """Las iniciales de la convencion vieja fallan fuerte en /api/v1/salud/*.

    Este router hablaba "M"/"F" (masculino/femenino), la convencion opuesta a la
    de pricing y pensiones. Es el caso que hacia el dano: una "M" que aqui
    significaba hombre y alla mujer. Ahora ninguna de las tres letras pasa.
    """

    @pytest.mark.parametrize("letra", LETRAS_HEREDADAS)
    def test_gmm_rechaza_letra_heredada(self, api_client, letra):
        payload = {
            "edad": 35,
            "sexo": letra,
            "suma_asegurada": 5_000_000,
            "deducible": 20_000,
            "coaseguro_pct": 0.10,
        }
        assert_rechaza_sexo_heredado(
            api_client.post("/api/v1/salud/gmm/calcular", json=payload), letra
        )

    @pytest.mark.parametrize("letra", LETRAS_HEREDADAS)
    def test_accidentes_rechaza_letra_heredada(self, api_client, letra):
        payload = {
            "edad": 40,
            "sexo": letra,
            "suma_asegurada": 1_000_000,
            "ocupacion": "oficina",
        }
        assert_rechaza_sexo_heredado(
            api_client.post("/api/v1/salud/accidentes/calcular", json=payload), letra
        )


class TestSaludProcedencia:
    """Las cifras de salud deben viajar con su alcance y su nivel de respaldo.

    El aviso existia como constante `DISCLAIMER` del modulo y no lo importaba
    nadie: ni el dominio lo emitia ni la respuesta HTTP lo llevaba. Quien
    consumia el JSON recibia una prima con tasas ilustrativas sin señal alguna
    de que lo eran.
    """

    def test_gmm_incluye_aviso_y_nivel_de_respaldo(self, api_client):
        from suite_actuarial.salud.gmm import DISCLAIMER, VALIDATION_TIER

        payload = {
            "edad": 35,
            "sexo": "masculino",
            "suma_asegurada": 5_000_000,
            "deducible": 20_000,
            "coaseguro_pct": 0.10,
        }
        response = api_client.post("/api/v1/salud/gmm/calcular", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["disclaimer"] == DISCLAIMER
        assert data["disclaimer"].strip()
        assert "ILUSTRATIVAS" in data["disclaimer"]
        assert data["validation_tier"] == VALIDATION_TIER == "experimental"

    def test_accidentes_incluye_aviso_y_nivel_de_respaldo(self, api_client):
        from suite_actuarial.salud.accidentes import DISCLAIMER, VALIDATION_TIER

        payload = {
            "edad": 40,
            "sexo": "masculino",
            "suma_asegurada": 1_000_000,
            "ocupacion": "oficina",
        }
        response = api_client.post("/api/v1/salud/accidentes/calcular", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["disclaimer"] == DISCLAIMER
        assert data["disclaimer"].strip()
        assert "ILUSTRATIVOS" in data["disclaimer"]
        assert data["validation_tier"] == VALIDATION_TIER == "experimental"
