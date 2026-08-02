"""Integration tests for the config API endpoints."""


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


class TestConfigFechaFueraDeCobertura:
    """Una fecha sin perfil publicado se rechaza nombrando la cobertura.

    Antes de esta pantalla, salir de la cobertura era un `ModuleNotFoundError`
    genérico. Ahora la fecha la pone el cliente, así que es un input rechazado
    (422), y el detalle tiene que decir hasta dónde llegan los perfiles para
    que quien la envió sepa qué pedir.
    """

    def test_ultimo_dia_cubierto_responde_200(self, api_client):
        response = api_client.get("/api/v1/config/fecha/2027-01-31")
        assert response.status_code == 200
        assert response.json()["anio"] == 2026

    def test_dia_siguiente_devuelve_422_con_el_rango(self, api_client):
        response = api_client.get("/api/v1/config/fecha/2027-02-01")

        assert response.status_code == 422
        detalle = response.json()["detail"]
        assert "2027-02-01" in detalle
        assert "2024-02-01 a 2027-01-31" in detalle

    def test_fecha_anterior_al_primer_perfil_devuelve_422(self, api_client):
        response = api_client.get("/api/v1/config/fecha/2024-01-31")

        assert response.status_code == 422
        assert "2024-02-01 a 2027-01-31" in response.json()["detail"]


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
