import pytest

from accounts.models import Session
from accounts.policies import hash_token
from accounts.services import get_auth_provider


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
    Session.objects.get(token_hash=hash_token(token)).revoke()

    response = client.get(
        "/api/v1/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_login_start_sends_code(client):
    response = client.post(
        "/api/v1/auth/login/start",
        {"email": "me@example.com"},
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json()["sent"] is True


@pytest.mark.django_db
def test_login_claims_anonymous_session(client):
    created = client.post(
        "/api/v1/auth/device", {"label": "pytest"}, content_type="application/json"
    ).json()

    code = get_auth_provider().start("me@example.com")
    response = client.post(
        "/api/v1/auth/login",
        {"email": "me@example.com", "code": code},
        headers={"Authorization": f"Bearer {created['token']}"},
        content_type="application/json",
    )

    assert response.status_code == 200
    body = response.json()
    assert body["user"]["id"] == created["user"]["id"]
    assert body["user"]["email"] == "me@example.com"
    assert body["user"]["is_anonymous_device"] is False
    assert body["token"] != created["token"]


@pytest.mark.django_db
def test_login_creates_registered_user(client):
    code = get_auth_provider().start("new@example.com")
    response = client.post(
        "/api/v1/auth/login",
        {"email": "new@example.com", "code": code},
        content_type="application/json",
    )

    assert response.status_code == 200
    body = response.json()
    assert body["user"]["is_anonymous_device"] is False
    assert body["wallet"]["lifetime_granted"] > 0


@pytest.mark.django_db
def test_login_rejects_bad_code(client):
    get_auth_provider().start("me@example.com")
    response = client.post(
        "/api/v1/auth/login",
        {"email": "me@example.com", "code": "000000"},
        content_type="application/json",
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_generation_gated_behind_login(client):
    token = device_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    blocked = client.post(
        "/api/v1/threads", {}, headers=headers, content_type="application/json"
    )
    assert blocked.status_code == 403

    code = get_auth_provider().start("me@example.com")
    claimed = client.post(
        "/api/v1/auth/login",
        {"email": "me@example.com", "code": code},
        headers=headers,
        content_type="application/json",
    ).json()

    allowed = client.post(
        "/api/v1/threads",
        {"title": "A thread"},
        headers={"Authorization": f"Bearer {claimed['token']}"},
        content_type="application/json",
    )
    assert allowed.status_code == 201


@pytest.mark.django_db
def test_logout_revokes_session(client):
    created = client.post(
        "/api/v1/auth/device", content_type="application/json"
    ).json()
    code = get_auth_provider().start("me@example.com")
    logged = client.post(
        "/api/v1/auth/login",
        {"email": "me@example.com", "code": code},
        headers={"Authorization": f"Bearer {created['token']}"},
        content_type="application/json",
    ).json()
    headers = {"Authorization": f"Bearer {logged['token']}"}

    assert client.get("/api/v1/me", headers=headers).status_code == 200
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/v1/me", headers=headers).status_code == 401
