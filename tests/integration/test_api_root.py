"""Integration tests for the root API endpoints."""


class TestRoot:
    def test_root_returns_200(self, api_client):
        response = api_client.get("/")
        assert response.status_code == 200

    def test_root_contains_modules(self, api_client):
        response = api_client.get("/")
        data = response.json()
        assert "modules" in data
        expected_modules = [
            "config",
            "danos",
            "pensiones",
            "pricing",
            "reinsurance",
            "reserves",
            "regulatory",
            "salud",
        ]
        for mod in expected_modules:
            assert mod in data["modules"]

    def test_root_contains_name_and_version(self, api_client):
        response = api_client.get("/")
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["version"] == "1.0.0"


class TestHealth:
    def test_health_returns_200(self, api_client):
        response = api_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data == {"status": "ok"}
