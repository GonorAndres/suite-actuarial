"""El muro del despliegue de desarrollo.

El servicio de dev es alcanzable por URL en la internet abierta, asi que una
direccion no publicada no es una frontera. El muro real es la cabecera que el
proxy de Cloudflare anade del lado del servidor, despues de que Access
autentico a la persona.

Estas pruebas construyen su propia app: el middleware lee la variable de entorno
al atender cada peticion, pero el `api_client` compartido es de sesion y otras
pruebas dependen de que no este amurallado.
"""

import importlib
import os

import pytest


@pytest.fixture
def app_amurallada(monkeypatch):
    """App con el secreto configurado, como en el despliegue de dev."""
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    monkeypatch.setenv("SUITE_PROXY_SHARED_SECRET", "secreto-de-prueba")
    import suite_actuarial.api.main as main

    importlib.reload(main)
    yield TestClient(main.app)
    monkeypatch.delenv("SUITE_PROXY_SHARED_SECRET", raising=False)
    importlib.reload(main)


class TestMuroDelProxy:
    def test_sin_cabecera_no_revela_el_api(self, app_amurallada):
        """404 y no 403: un despliegue amurallado no confirma que existe."""
        response = app_amurallada.get("/api/v1/config/2026")

        assert response.status_code == 404

    def test_con_la_cabecera_correcta_responde(self, app_amurallada):
        response = app_amurallada.get(
            "/api/v1/config/2026",
            headers={"X-Proxy-Secret": "secreto-de-prueba"},
        )

        assert response.status_code == 200

    def test_con_la_cabecera_incorrecta_no_pasa(self, app_amurallada):
        response = app_amurallada.get(
            "/api/v1/config/2026",
            headers={"X-Proxy-Secret": "otro"},
        )

        assert response.status_code == 404

    def test_health_queda_exento(self, app_amurallada):
        """Cloud Run necesita el health check sin conocer el secreto."""
        response = app_amurallada.get("/health")

        assert response.status_code == 200


class TestSinSecretoElApiEsPublico:
    def test_produccion_no_exige_cabecera(self, api_client):
        """Sin la variable configurada no hay muro, que es lo que quiere prod."""
        assert os.environ.get("SUITE_PROXY_SHARED_SECRET", "") == ""

        assert api_client.get("/api/v1/config/2026").status_code == 200
