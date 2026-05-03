"""Integration tests for the regulatory API endpoints."""



VALID_RCS_PAYLOAD = {
    "config_vida": {
        "suma_asegurada_total": 50_000_000,
        "reserva_matematica": 15_000_000,
        "edad_promedio_asegurados": 40,
        "duracion_promedio_polizas": 10,
        "numero_asegurados": 1000,
    },
    "config_danos": {
        "primas_retenidas_12m": 20_000_000,
        "reserva_siniestros": 8_000_000,
        "coeficiente_variacion": 0.15,
        "numero_ramos": 3,
    },
    "config_inversion": {
        "valor_acciones": 10_000_000,
        "valor_bonos_gubernamentales": 30_000_000,
        "valor_bonos_corporativos": 15_000_000,
        "valor_inmuebles": 5_000_000,
        "duracion_promedio_bonos": 5.0,
        "calificacion_promedio_bonos": "AA",
    },
    "capital_minimo_pagado": 100_000_000,
}


class TestRCS:
    def test_success(self, api_client):
        response = api_client.post("/api/v1/regulatory/rcs", json=VALID_RCS_PAYLOAD)
        assert response.status_code == 200
        data = response.json()
        assert "rcs_total" in data
        assert "cumple_regulacion" in data
        assert "ratio_solvencia" in data
        assert isinstance(data["rcs_total"], (int, float))
        assert isinstance(data["cumple_regulacion"], bool)
        assert "desglose_por_riesgo" in data

    def test_success_vida_only(self, api_client):
        payload = {
            "config_vida": VALID_RCS_PAYLOAD["config_vida"],
            "capital_minimo_pagado": 50_000_000,
        }
        response = api_client.post("/api/v1/regulatory/rcs", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["rcs_suscripcion_vida"] >= 0
        assert data["rcs_suscripcion_danos"] == 0

    def test_validation_error_missing_capital(self, api_client):
        payload = {"config_vida": VALID_RCS_PAYLOAD["config_vida"]}
        response = api_client.post("/api/v1/regulatory/rcs", json=payload)
        assert response.status_code == 422

    def test_validation_error_negative_capital(self, api_client):
        payload = {**VALID_RCS_PAYLOAD, "capital_minimo_pagado": -1}
        response = api_client.post("/api/v1/regulatory/rcs", json=payload)
        assert response.status_code == 422


class TestSATDeductibility:
    def test_success(self, api_client):
        payload = {
            "tipo_seguro": "vida",
            "monto_prima": 50_000,
            "es_persona_fisica": True,
            "uma_anual": 39960.60,
        }
        response = api_client.post("/api/v1/regulatory/sat/deductibility", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "es_deducible" in data
        assert "monto_deducible" in data
        assert "fundamento_legal" in data
        assert isinstance(data["es_deducible"], bool)

    def test_validation_error_zero_prima(self, api_client):
        payload = {
            "tipo_seguro": "vida",
            "monto_prima": 0,
        }
        response = api_client.post("/api/v1/regulatory/sat/deductibility", json=payload)
        assert response.status_code == 422


class TestSATWithholding:
    def test_success(self, api_client):
        payload = {
            "tipo_seguro": "vida",
            "monto_pago": 100_000,
            "monto_gravable": 50_000,
            "es_renta_vitalicia": False,
            "es_retiro_ahorro": False,
        }
        response = api_client.post("/api/v1/regulatory/sat/withholding", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "requiere_retencion" in data
        assert "monto_retencion" in data
        assert "monto_neto_pagar" in data
        assert isinstance(data["requiere_retencion"], bool)

    def test_validation_error_missing_tipo(self, api_client):
        payload = {
            "monto_pago": 100_000,
            "monto_gravable": 50_000,
        }
        response = api_client.post("/api/v1/regulatory/sat/withholding", json=payload)
        assert response.status_code == 422
