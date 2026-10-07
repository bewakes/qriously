import pytest

from accounts.models import DeviceSession, User
from accounts.tokens import hash_token


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

    user = User.objects.get(id=body["user"]["id"])
    assert user.is_anonymous_device is True
    session = DeviceSession.objects.get(user=user)
    assert session.label == "pytest"
    assert session.token_hash != body["token"]
    assert session.token_hash == hash_token(body["token"])


@pytest.mark.django_db
def test_me_requires_token(client):
    response = client.get("/api/v1/me")
    assert response.status_code == 401


@pytest.mark.django_db
def test_me_with_valid_token(client):
    created = client.post("/api/v1/auth/device", content_type="application/json").json()

    response = client.get(
        "/api/v1/me", HTTP_AUTHORIZATION=f"Bearer {created['token']}"
    )

    assert response.status_code == 200
    assert response.json()["user"]["id"] == created["user"]["id"]


@pytest.mark.django_db
def test_me_with_invalid_token(client):
    response = client.get("/api/v1/me", HTTP_AUTHORIZATION="Bearer not-a-real-token")
    assert response.status_code == 401


@pytest.mark.django_db
def test_revoked_token_rejected(client):
    created = client.post("/api/v1/auth/device", content_type="application/json").json()
    session = DeviceSession.objects.get(token_hash=hash_token(created["token"]))
    session.revoke()

    response = client.get(
        "/api/v1/me", HTTP_AUTHORIZATION=f"Bearer {created['token']}"
    )
    assert response.status_code == 401
