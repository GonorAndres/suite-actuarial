"""Integration tests for the pensiones API endpoints."""

import pytest

from tests.integration.sexo_heredado import LETRAS_HEREDADAS, assert_rechaza_sexo_heredado


class TestLey73Calcular:
    def test_success(self, api_client):
        payload = {
            "semanas_cotizadas": 1500,
            "salario_promedio_diario": 800.0,
            "edad_retiro": 65,
        }
        response = api_client.post("/api/v1/pensiones/ley73/calcular", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["regimen"] is not None
        assert "pension_mensual" in data
        assert "aguinaldo_anual" in data
        assert "pension_anual_total" in data
        assert isinstance(data["pension_mensual"], (int, float))
        assert data["pension_mensual"] > 0

    def test_success_age_60(self, api_client):
        payload = {
            "semanas_cotizadas": 800,
            "salario_promedio_diario": 500.0,
            "edad_retiro": 60,
        }
        response = api_client.post("/api/v1/pensiones/ley73/calcular", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["edad_retiro"] == 60
        assert data["factor_edad"] < 1.0  # Reduced for early retirement

    def test_validation_error_semanas_under_500(self, api_client):
        payload = {
            "semanas_cotizadas": 200,
            "salario_promedio_diario": 800.0,
            "edad_retiro": 65,
        }
        response = api_client.post("/api/v1/pensiones/ley73/calcular", json=payload)
        assert response.status_code == 422

    def test_validation_error_edad_under_60(self, api_client):
        payload = {
            "semanas_cotizadas": 1500,
            "salario_promedio_diario": 800.0,
            "edad_retiro": 55,
        }
        response = api_client.post("/api/v1/pensiones/ley73/calcular", json=payload)
        assert response.status_code == 422


class TestSinPerfilVigente:
    """Ley 73 y Ley 97 leen el perfil regulatorio vigente (UMA, pension
    garantizada) a la fecha del servidor. Agotada la cobertura de perfiles,
    devolvian 500 con traceback mientras el router regulatorio ya respondia
    503: mismo fallo, dos respuestas. Ahora ambos realms responden 503 con el
    rango cubierto en el detalle.
    """

    @pytest.fixture
    def hoy_sin_cobertura(self, monkeypatch):
        from datetime import date

        from suite_actuarial.config import loader

        monkeypatch.setattr(loader, "_hoy", lambda: date(2030, 6, 15))

    def test_ley73_devuelve_503(self, api_client, hoy_sin_cobertura):
        payload = {
            "semanas_cotizadas": 1500,
            "salario_promedio_diario": 800.0,
            "edad_retiro": 65,
        }
        response = api_client.post("/api/v1/pensiones/ley73/calcular", json=payload)
        assert response.status_code == 503
        detalle = response.json()["detail"]
        assert "2024-02-01 a 2027-01-31" in detalle

    def test_ley97_devuelve_503(self, api_client, hoy_sin_cobertura):
        payload = {
            "saldo_afore": 2_000_000,
            "edad": 65,
            "sexo": "masculino",
            "semanas_cotizadas": 1500,
            "tasa_interes": 0.035,
        }
        response = api_client.post("/api/v1/pensiones/ley97/calcular", json=payload)
        assert response.status_code == 503
        detalle = response.json()["detail"]
        assert "2024-02-01 a 2027-01-31" in detalle


class TestLey97Calcular:
    def test_success(self, api_client):
        payload = {
            "saldo_afore": 2_000_000,
            "edad": 65,
            "sexo": "masculino",
            "semanas_cotizadas": 1500,
            "tasa_interes": 0.035,
        }
        response = api_client.post("/api/v1/pensiones/ley97/calcular", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "renta_vitalicia" in data
        assert "retiro_programado" in data
        assert "recomendacion" in data
        assert "pension_garantizada" in data
        assert isinstance(data["renta_vitalicia"]["pension_mensual"], (int, float))

    def test_validation_error_zero_saldo(self, api_client):
        payload = {
            "saldo_afore": 0,
            "edad": 65,
            "sexo": "masculino",
            "semanas_cotizadas": 1500,
        }
        response = api_client.post("/api/v1/pensiones/ley97/calcular", json=payload)
        assert response.status_code == 422


class TestRentaVitaliciaCalcular:
    def test_success(self, api_client):
        payload = {
            "edad": 65,
            "sexo": "masculino",
            "monto_mensual": 15_000,
            "tasa_interes": 0.035,
            "periodo_diferimiento": 0,
            "periodo_garantizado": 0,
        }
        response = api_client.post("/api/v1/pensiones/renta-vitalicia/calcular", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "factor_renta" in data
        assert "prima_unica" in data
        assert isinstance(data["factor_renta"], (int, float))
        assert isinstance(data["prima_unica"], (int, float))
        assert data["factor_renta"] > 0
        assert data["prima_unica"] > 0

    def test_validation_error_invalid_sexo(self, api_client):
        payload = {
            "edad": 65,
            "sexo": "X",
            "monto_mensual": 15_000,
            "tasa_interes": 0.035,
        }
        response = api_client.post("/api/v1/pensiones/renta-vitalicia/calcular", json=payload)
        assert response.status_code == 422


class TestConmutacionTabla:
    def test_success(self, api_client):
        response = api_client.get(
            "/api/v1/pensiones/conmutacion/tabla",
            params={"sexo": "masculino", "tasa_interes": 0.055, "edad_min": 30, "edad_max": 35},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["sexo"] == "masculino"
        assert data["tasa_interes"] == 0.055
        assert "filas" in data
        assert isinstance(data["filas"], list)
        assert len(data["filas"]) == 6  # 30,31,32,33,34,35
        row = data["filas"][0]
        assert "Dx" in row
        assert "Nx" in row
        assert "Mx" in row
        assert "ax" in row
        assert "Ax" in row


class TestSexoHeredado:
    """Las iniciales de la convencion vieja fallan fuerte en /api/v1/pensiones/*.

    Este router hablaba "H"/"M" (hombre/mujer), incluido el parametro de query
    de la tabla de conmutacion. Las tres letras se rechazan por igual.
    """

    @pytest.mark.parametrize("letra", LETRAS_HEREDADAS)
    def test_ley97_rechaza_letra_heredada(self, api_client, letra):
        payload = {
            "saldo_afore": 2_000_000,
            "edad": 65,
            "sexo": letra,
            "semanas_cotizadas": 1500,
        }
        assert_rechaza_sexo_heredado(
            api_client.post("/api/v1/pensiones/ley97/calcular", json=payload), letra
        )

    @pytest.mark.parametrize("letra", LETRAS_HEREDADAS)
    def test_renta_vitalicia_rechaza_letra_heredada(self, api_client, letra):
        payload = {
            "edad": 65,
            "sexo": letra,
            "monto_mensual": 15_000,
            "tasa_interes": 0.035,
        }
        assert_rechaza_sexo_heredado(
            api_client.post("/api/v1/pensiones/renta-vitalicia/calcular", json=payload), letra
        )

    @pytest.mark.parametrize("letra", LETRAS_HEREDADAS)
    def test_conmutacion_rechaza_letra_heredada(self, api_client, letra):
        response = api_client.get(
            "/api/v1/pensiones/conmutacion/tabla",
            params={"sexo": letra, "tasa_interes": 0.055},
        )
        assert_rechaza_sexo_heredado(response, letra)
