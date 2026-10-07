import pytest


@pytest.fixture
def token(client):
    body = client.post("/api/v1/auth/device", content_type="application/json").json()
    return body["token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.django_db
def test_device_auth_includes_wallet(client):
    body = client.post("/api/v1/auth/device", content_type="application/json").json()
    assert body["wallet"]["balance"] == 5000
    assert body["wallet"]["currency"] == "micro_credits"
    assert body["granted"] == 5000


@pytest.mark.django_db
def test_balance_endpoint(client, token):
    response = client.get("/api/v1/credits/balance", headers=auth(token))
    assert response.status_code == 200
    assert response.json()["balance"] == 5000


@pytest.mark.django_db
def test_ledger_endpoint(client, token):
    response = client.get("/api/v1/credits/ledger", headers=auth(token))
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["reason"] == "signup_grant"


@pytest.mark.django_db
def test_credits_require_auth(client):
    assert client.get("/api/v1/credits/balance").status_code == 401
    assert client.get("/api/v1/credits/ledger").status_code == 401
