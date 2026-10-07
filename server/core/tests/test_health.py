import pytest


@pytest.mark.django_db
def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
def test_readiness(client):
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
