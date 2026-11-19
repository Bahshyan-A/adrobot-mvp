import httpx
import pytest

from backend.config import Settings
from backend.errors import ApplicationError
from backend.integrations.transport import HttpTransport


def config():
    return Settings(keitaro_url="https://tracker.example", keitaro_api_key="test-secret")


def test_http_transport_uses_server_side_header_and_expected_path():
    def handler(request):
        assert request.url.path == "/admin_api/v1/offers"
        assert request.headers["Api-Key"] == "test-secret"
        assert "test-secret" not in str(request.url)
        return httpx.Response(200, json=[{"id": 1, "name": "Offer"}])

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        assert HttpTransport(config(), client).request("GET", "/offers")[0]["id"] == 1


@pytest.mark.parametrize("status", [401, 402, 403, 404, 500])
def test_upstream_error_body_and_credentials_are_not_exposed(status):
    transport = httpx.MockTransport(
        lambda _: httpx.Response(status, text="private response test-secret")
    )
    with httpx.Client(transport=transport) as client, pytest.raises(ApplicationError) as raised:
        HttpTransport(config(), client).request("GET", "/campaigns")
    assert raised.value.status_code == 502
    assert "test-secret" not in str(raised.value)
    assert "private response" not in str(raised.value)


def test_timeout_has_clear_retryable_error():
    def handler(request):
        raise httpx.ReadTimeout("timeout", request=request)

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as client,
        pytest.raises(ApplicationError) as raised,
    ):
        HttpTransport(config(), client).request("GET", "/campaigns")
    assert raised.value.status_code == 504


def test_invalid_json_is_rejected():
    transport = httpx.MockTransport(lambda _: httpx.Response(200, text="<html>Proxy page</html>"))
    with httpx.Client(transport=transport) as client, pytest.raises(ApplicationError) as raised:
        HttpTransport(config(), client).request("GET", "/campaigns")
    assert raised.value.status_code == 502


def test_application_token_protects_api(client, monkeypatch):
    from backend.config import settings

    monkeypatch.setattr(settings(), "app_token", "workspace-token")
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/campaigns").status_code == 401
    response = client.get("/api/campaigns", headers={"Authorization": "Bearer workspace-token"})
    assert response.status_code == 200


def test_health_has_no_runtime_mode_switch(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "auth_required": False,
        "campaign_name_prefix": "test_bakhshyan_",
    }
