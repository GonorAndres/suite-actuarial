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
            "tipo_triangulo": "acumulado",
            "metodo_promedio": "simple",
            "calcular_tail_factor": False,
        }
        response = api_client.post("/api/v1/reserves/chain-ladder", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["metodo"] == "chain_ladder"
        assert data["unidad_monetaria"] == "millones_mxn"
        assert "reserva_total" in data
        assert "ultimate_total" in data
        assert "factores_desarrollo" in data
        assert isinstance(data["reserva_total"], (int, float))
        assert data["reserva_total"] >= 0

    def test_success_weighted(self, api_client):
        payload = {
            "triangle": VALID_TRIANGLE,
            "origin_years": ORIGIN_YEARS,
            "tipo_triangulo": "acumulado",
            "metodo_promedio": "weighted",
        }
        response = api_client.post("/api/v1/reserves/chain-ladder", json=payload)
        assert response.status_code == 200

    def test_validation_error_mismatched_rows(self, api_client):
        payload = {
            "triangle": VALID_TRIANGLE,
            "origin_years": [2019, 2020],
            "tipo_triangulo": "acumulado",
        }
        response = api_client.post("/api/v1/reserves/chain-ladder", json=payload)
        assert response.status_code == 400


class TestBornhuetterFerguson:
    def test_success(self, api_client):
        payload = {
            "triangle": VALID_TRIANGLE,
            "origin_years": ORIGIN_YEARS,
            "tipo_triangulo": "acumulado",
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
        assert data["unidad_monetaria"] == "millones_mxn"
        assert "reserva_total" in data
        assert isinstance(data["reserva_total"], (int, float))

    def test_validation_error_zero_loss_ratio(self, api_client):
        payload = {
            "triangle": VALID_TRIANGLE,
            "origin_years": ORIGIN_YEARS,
            "tipo_triangulo": "acumulado",
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
            "tipo_triangulo": "acumulado",
            "num_simulaciones": 500,
            "seed": 42,
            "percentiles": [50, 75, 90, 95, 99],
        }
        response = api_client.post("/api/v1/reserves/bootstrap", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["metodo"] == "bootstrap"
        assert data["unidad_monetaria"] == "millones_mxn"
        assert "reserva_total" in data
        assert "percentiles" in data
        assert isinstance(data["percentiles"], dict)
        assert data["reserva_total"] >= 0

    def test_deterministic_with_same_seed(self, api_client):
        payload = {
            "triangle": VALID_TRIANGLE,
            "origin_years": ORIGIN_YEARS,
            "tipo_triangulo": "acumulado",
            "num_simulaciones": 500,
            "seed": 42,
        }
        r1 = api_client.post("/api/v1/reserves/bootstrap", json=payload)
        r2 = api_client.post("/api/v1/reserves/bootstrap", json=payload)
        assert r1.json()["reserva_total"] == r2.json()["reserva_total"]


class TestTipoTrianguloObligatorio:
    """El tipo de triángulo se declara en cada petición; no tiene valor por defecto.

    Un valor por defecto dejaría el camino silencioso abierto: quien envíe un
    triángulo incremental sin declararlo recibiría una reserva menor a la
    correcta, sin error ni advertencia. Se prefiere el rechazo.
    """

    ENDPOINTS = [
        ("/api/v1/reserves/chain-ladder", {}),
        (
            "/api/v1/reserves/bornhuetter-ferguson",
            {
                "primas_por_anio": {2019: 100, 2020: 100, 2021: 100, 2022: 100, 2023: 100},
                "loss_ratio_apriori": 0.65,
            },
        ),
        ("/api/v1/reserves/bootstrap", {"num_simulaciones": 100, "seed": 1}),
    ]

    @pytest.mark.parametrize(("ruta", "extra"), ENDPOINTS)
    def test_omitirlo_es_422(self, api_client, ruta, extra):
        payload = {"triangle": VALID_TRIANGLE, "origin_years": ORIGIN_YEARS, **extra}
        respuesta = api_client.post(ruta, json=payload)
        assert respuesta.status_code == 422, respuesta.text
        assert any(
            "tipo_triangulo" in [str(p) for p in err["loc"]] for err in respuesta.json()["detail"]
        )

    def test_un_valor_invalido_es_422(self, api_client):
        payload = {
            "triangle": VALID_TRIANGLE,
            "origin_years": ORIGIN_YEARS,
            "tipo_triangulo": "lo_que_sea",
        }
        respuesta = api_client.post("/api/v1/reserves/chain-ladder", json=payload)
        assert respuesta.status_code == 422

    def test_declarar_incremental_cambia_la_reserva(self, api_client):
        """El mismo triángulo declarado de las dos formas no da lo mismo.

        Es la diferencia que la heurística borraba.
        """
        base = {"triangle": VALID_TRIANGLE, "origin_years": ORIGIN_YEARS}
        acumulado = api_client.post(
            "/api/v1/reserves/chain-ladder", json={**base, "tipo_triangulo": "acumulado"}
        )
        incremental = api_client.post(
            "/api/v1/reserves/chain-ladder", json={**base, "tipo_triangulo": "incremental"}
        )
        assert acumulado.status_code == 200, acumulado.text
        assert incremental.status_code == 200, incremental.text
        assert acumulado.json()["reserva_total"] != incremental.json()["reserva_total"]


class TestLimiteDeTamano:
    """El tamaño del triángulo se acota en la aplicación, no en la infraestructura.

    Antes solo lo limitaban los valores por omisión de Cloud Run (cuerpo de
    ~32 MB, timeout de 60 s). Eso es una red de seguridad accidental: un
    triángulo enorme agotaba el tiempo de una de las 2 instancias en vez de
    recibir un rechazo inmediato.
    """

    def test_demasiados_anios_de_origen_se_rechaza(self, api_client):
        filas = [[100.0] * 3 for _ in range(80)]
        payload = {
            "triangle": filas,
            "origin_years": list(range(1950, 2030)),
            "tipo_triangulo": "acumulado",
        }
        respuesta = api_client.post("/api/v1/reserves/chain-ladder", json=payload)
        assert respuesta.status_code == 422, respuesta.text

    def test_demasiados_periodos_de_desarrollo_se_rechaza(self, api_client):
        payload = {
            "triangle": [[100.0] * 80, [100.0] * 79],
            "origin_years": [2020, 2021],
            "tipo_triangulo": "acumulado",
        }
        respuesta = api_client.post("/api/v1/reserves/chain-ladder", json=payload)
        assert respuesta.status_code == 400, respuesta.text
        assert "periodos de desarrollo" in respuesta.json()["detail"]

    def test_un_triangulo_de_tamano_normal_pasa(self, api_client):
        payload = {
            "triangle": VALID_TRIANGLE,
            "origin_years": ORIGIN_YEARS,
            "tipo_triangulo": "acumulado",
        }
        assert api_client.post("/api/v1/reserves/chain-ladder", json=payload).status_code == 200
