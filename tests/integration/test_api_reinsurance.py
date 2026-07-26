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

    def test_success_layer_equal_to_retention(self, api_client):
        """A 5M xs 5M layer is a valid XL structure."""
        payload = {
            "retencion": 5_000_000,
            "limite": 5_000_000,
            "modalidad": "por_riesgo",
            "numero_reinstatements": 0,
            "tasa_prima": 5.0,
            "vigencia_inicio": "2024-01-01",
            "vigencia_fin": "2024-12-31",
            "prima_reaseguro_cobrada": 250_000,
            "siniestros": [],
        }
        response = api_client.post("/api/v1/reinsurance/excess-of-loss", json=payload)

        assert response.status_code == 200

    @pytest.mark.parametrize(
        ("retencion", "limite", "monto_bruto", "recuperacion_esperada"),
        [
            # 5M xs 5M: la capa canonica que el gate defectuoso rechazaba.
            (5_000_000, 5_000_000, 12_000_000, 5_000_000),  # capa agotada
            (5_000_000, 5_000_000, 7_000_000, 2_000_000),  # capa parcial
            (5_000_000, 5_000_000, 5_000_000, 0),  # frontera: siniestro = prioridad
            (5_000_000, 5_000_000, 3_000_000, 0),  # bajo la prioridad
            (10_000_000, 5_000_000, 20_000_000, 5_000_000),  # 5M xs 10M
            (10_000_000, 5_000_000, 12_500_000, 2_500_000),
            (20_000_000, 10_000_000, 35_000_000, 10_000_000),  # 10M xs 20M
        ],
    )
    def test_recuperacion_por_siniestro_en_capas_validas(
        self, api_client, retencion, limite, monto_bruto, recuperacion_esperada
    ):
        """Recuperacion = min(max(siniestro - prioridad, 0), ancho de capa).

        Las esperanzas estan calculadas a mano para capas de mercado donde el
        ancho es igual o menor que la prioridad ("5M xs 5M", "5M xs 10M",
        "10M xs 20M"). El gate `limite > retencion` (A3) rechazaba las tres con
        422; ademas de aceptarlas, la aritmetica de capado por siniestro debe
        seguir siendo la correcta.
        """
        payload = {
            "retencion": retencion,
            "limite": limite,
            "modalidad": "por_riesgo",
            "numero_reinstatements": 0,
            "tasa_prima": 5.0,
            "vigencia_inicio": "2024-01-01",
            "vigencia_fin": "2024-12-31",
            "prima_reaseguro_cobrada": 250_000,
            "siniestros": [
                {
                    "id_siniestro": "S100",
                    "fecha_ocurrencia": "2024-05-01",
                    "monto_bruto": monto_bruto,
                    "tipo": "individual",
                }
            ],
        }
        response = api_client.post("/api/v1/reinsurance/excess-of-loss", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["recuperacion_reaseguro"] == pytest.approx(recuperacion_esperada)

    @pytest.mark.parametrize(
        ("reinstalaciones", "recuperacion_esperada", "agregado_esperado"),
        [
            (0, 5_000_000, 5_000_000),  # una sola capa disponible
            (1, 10_000_000, 10_000_000),  # el escenario exacto del hallazgo A4
            (2, 15_000_000, 15_000_000),  # tres capas, pero solo dos perdidas
        ],
    )
    def test_las_reinstalaciones_amplian_el_agregado(
        self, api_client, reinstalaciones, recuperacion_esperada, agregado_esperado
    ):
        """Dos perdidas de 12M sobre 5M xs 5M, variando reinstalaciones (A4).

        Cada perdida excede la capa en 7M y se capa por ocurrencia en 5M. El
        agregado es `limite * (1 + reinstalaciones)`, asi que sin
        reinstalaciones solo se cede una capa y con una se ceden dos. Antes las
        tres filas devolvian 5M: las reinstalaciones nunca se aplicaban.

        Con dos reinstalaciones el agregado alcanza 15M pero solo hay dos
        perdidas, asi que la cesion se topa en 10M: es la comprobacion de que
        el tope por ocurrencia sigue vigente.
        """
        payload = {
            "retencion": 5_000_000,
            "limite": 5_000_000,
            "modalidad": "por_riesgo",
            "numero_reinstatements": reinstalaciones,
            "tasa_prima": 5.0,
            "vigencia_inicio": "2024-01-01",
            "vigencia_fin": "2024-12-31",
            "prima_reaseguro_cobrada": 250_000,
            "siniestros": [
                {
                    "id_siniestro": f"S{n}",
                    "fecha_ocurrencia": "2024-05-01",
                    "monto_bruto": 12_000_000,
                    "tipo": "individual",
                }
                for n in (1, 2)
            ],
        }
        response = api_client.post("/api/v1/reinsurance/excess-of-loss", json=payload)

        assert response.status_code == 200
        data = response.json()
        cedido = min(recuperacion_esperada, 10_000_000)
        assert data["recuperacion_reaseguro"] == pytest.approx(cedido)
        assert float(data["detalles"]["limite_agregado"]) == pytest.approx(agregado_esperado)


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
