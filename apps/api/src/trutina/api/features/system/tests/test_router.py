import pytest


@pytest.mark.unit
class TestRoot:
    async def test_returns_200(self, api_client):
        response = await api_client.get("/")

        assert response.status_code == 200

    async def test_returns_service_identity_from_settings(self, api_client, api_app):
        response = await api_client.get("/")

        body = response.json()
        assert body["service"]["title"] == api_app.title
        assert body["service"]["description"] == api_app.description
        assert body["service"]["version"] == api_app.version

    async def test_service_transport_field_is_rest(self, api_client):
        response = await api_client.get("/")

        assert response.json()["service"]["transport"] == "rest"

    async def test_includes_docs_link(self, api_client):
        response = await api_client.get("/")

        assert response.json()["docs"] == "/docs"

    async def test_includes_openapi_link(self, api_client):
        response = await api_client.get("/")

        assert response.json()["openapi"] == "/openapi.json"


@pytest.mark.unit
class TestHealth:
    async def test_returns_200(self, api_client):
        response = await api_client.get("/health")

        assert response.status_code == 200

    async def test_returns_ok_status(self, api_client):
        response = await api_client.get("/health")

        assert response.json() == {"status": "ok"}

    async def test_does_not_touch_container(self, api_client, api_app):
        del api_app.state.container

        response = await api_client.get("/health")

        assert response.status_code == 200
