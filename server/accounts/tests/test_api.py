import pytest

from accounts.models import DeviceSession
from accounts.policies import hash_token


def device_token(client):
    return client.post(
        "/api/v1/auth/device", content_type="application/json"
    ).json()["token"]


@pytest.mark.django_db
def test_device_auth_creates_anonymous_user(client):
    response = client.post(
        "/api/v1/auth/device", {"label": "pytest"}, content_type="application/json"
    )

    assert response.status_code == 201
    body = response.json()
    assert body["user"]["is_anonymous_device"] is True
    assert body["user"]["email"] is None
    assert body["token"]


@pytest.mark.django_db
def test_me_requires_token(client):
    assert client.get("/api/v1/me").status_code == 401


@pytest.mark.django_db
def test_me_with_valid_token(client):
    created = client.post("/api/v1/auth/device", content_type="application/json").json()

    response = client.get(
        "/api/v1/me", headers={"Authorization": f"Bearer {created['token']}"}
    )

    assert response.status_code == 200
    assert response.json()["user"]["id"] == created["user"]["id"]


@pytest.mark.django_db
def test_me_with_invalid_token(client):
    response = client.get(
        "/api/v1/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_revoked_token_rejected(client):
    token = device_token(client)
    DeviceSession.objects.get(token_hash=hash_token(token)).revoke()

    response = client.get(
        "/api/v1/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
