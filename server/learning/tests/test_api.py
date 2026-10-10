import json

import pytest

from learning.models import Node


@pytest.fixture
def token(client):
    body = client.post("/api/v1/auth/device", content_type="application/json").json()
    return body["token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def post(client, token, url, data):
    return client.post(
        url, data=json.dumps(data), content_type="application/json", headers=auth(token)
    )


def patch(client, token, url, data):
    return client.patch(
        url, data=json.dumps(data), content_type="application/json", headers=auth(token)
    )


def make_root(client, token, question="Why is the sky blue?"):
    return post(
        client, token, "/api/v1/threads", {"question": question}
    ).json()


def add_dive(client, token, thread_id, parent_id, text="Rayleigh scattering"):
    return post(
        client,
        token,
        f"/api/v1/threads/{thread_id}/nodes",
        {"parent_node_id": parent_id, "kind": "dive", "span": {"text": text}},
    )


@pytest.mark.django_db
def test_create_thread_without_question(client, token):
    response = post(client, token, "/api/v1/threads", {})
    assert response.status_code == 201
    assert response.json()["thread"]["title"] == ""


@pytest.mark.django_db
def test_create_thread_with_question_starts_generation(client, token):
    response = post(
        client,
        token,
        "/api/v1/threads",
        {"question": "Why is the sky blue?", "lens": {"depth": "deep"}},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["thread"]["title"] == "Why is the sky blue?"
    assert body["cache_hit"] is False
    assert body["cost"] == 24
    assert body["node_id"]


@pytest.mark.django_db
def test_thread_snapshot_round_trip(client, token):
    created = make_root(client, token)
    thread_id = created["thread"]["id"]

    snapshot = client.get(
        f"/api/v1/threads/{thread_id}", headers=auth(token)
    ).json()
    assert snapshot["thread"]["id"] == thread_id
    assert len(snapshot["nodes"]) == 1
    node = snapshot["nodes"][0]
    assert node["id"] == created["node_id"]
    assert node["kind"] == "root"
    assert node["parent_id"] is None
    assert node["root_id"] == node["id"]
    assert node["status"] == "queued"
    assert node["body"] is None


@pytest.mark.django_db
def test_create_node_from_span_returns_202(client, token):
    created = make_root(client, token)
    thread_id = created["thread"]["id"]
    response = add_dive(client, token, thread_id, created["node_id"])
    assert response.status_code == 202
    assert response.json()["cache_hit"] is False

    snapshot = client.get(
        f"/api/v1/threads/{thread_id}", headers=auth(token)
    ).json()
    assert len(snapshot["nodes"]) == 2
    assert len(snapshot["spans"]) == 1
    assert snapshot["spans"][0]["text"] == "Rayleigh scattering"


@pytest.mark.django_db
def test_create_dive_without_span_is_rejected(client, token):
    created = make_root(client, token)
    response = post(
        client,
        token,
        f"/api/v1/threads/{created['thread']['id']}/nodes",
        {"parent_node_id": created["node_id"], "kind": "dive"},
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_patch_node_collapsed(client, token):
    created = make_root(client, token)
    response = patch(
        client,
        token,
        f"/api/v1/nodes/{created['node_id']}",
        {"collapsed": True},
    )
    assert response.status_code == 200
    assert response.json()["collapsed"] is True


@pytest.mark.django_db
def test_delete_node_removes_subtree(client, token):
    created = make_root(client, token)
    thread_id = created["thread"]["id"]
    dive = add_dive(client, token, thread_id, created["node_id"]).json()
    grandchild = add_dive(
        client, token, thread_id, dive["node_id"], text="Wavelength"
    ).json()

    response = client.delete(
        f"/api/v1/nodes/{dive['node_id']}", headers=auth(token)
    )
    assert response.status_code == 204
    assert not Node.objects.filter(id=dive["node_id"]).exists()
    assert not Node.objects.filter(id=grandchild["node_id"]).exists()
    assert Node.objects.filter(id=created["node_id"]).exists()


@pytest.mark.django_db
def test_notes_crud(client, token):
    created = make_root(client, token)
    thread_id = created["thread"]["id"]
    add_dive(client, token, thread_id, created["node_id"])
    snapshot = client.get(
        f"/api/v1/threads/{thread_id}", headers=auth(token)
    ).json()
    span_id = snapshot["spans"][0]["id"]

    created_note = post(
        client,
        token,
        f"/api/v1/threads/{thread_id}/notes",
        {"span_id": span_id, "tags": ["light"]},
    )
    assert created_note.status_code == 201
    note = created_note.json()
    assert note["text"] == "Rayleigh scattering"
    assert note["tags"] == ["light"]

    listing = client.get(
        f"/api/v1/threads/{thread_id}/notes", headers=auth(token)
    ).json()
    assert [n["id"] for n in listing["results"]] == [note["id"]]

    updated = patch(
        client, token, f"/api/v1/notes/{note['id']}", {"text": "on scattering"}
    ).json()
    assert updated["text"] == "on scattering"

    assert (
        client.delete(f"/api/v1/notes/{note['id']}", headers=auth(token)).status_code
        == 204
    )


@pytest.mark.django_db
def test_note_from_node_and_text_creates_and_reuses_span(client, token):
    created = make_root(client, token)
    thread_id = created["thread"]["id"]
    url = f"/api/v1/threads/{thread_id}/notes"

    first = post(
        client,
        token,
        url,
        {"source_node_id": created["node_id"], "text": "scattered blue light"},
    )
    assert first.status_code == 201
    assert first.json()["text"] == "scattered blue light"

    second = post(
        client,
        token,
        url,
        {"source_node_id": created["node_id"], "text": "scattered blue light"},
    )
    assert second.status_code == 201

    snapshot = client.get(
        f"/api/v1/threads/{thread_id}", headers=auth(token)
    ).json()
    assert len(snapshot["spans"]) == 1
    assert len(snapshot["notes"]) == 2


@pytest.mark.django_db
def test_free_form_note_needs_no_span(client, token):
    created = make_root(client, token)
    thread_id = created["thread"]["id"]
    response = post(
        client,
        token,
        f"/api/v1/threads/{thread_id}/notes",
        {"text": "remember: only below the horizon"},
    )
    assert response.status_code == 201
    note = response.json()
    assert note["text"] == "remember: only below the horizon"
    assert note["span_id"] is None
    assert note["context"] == "Why is the sky blue?"


@pytest.mark.django_db
def test_note_requires_span_or_node_and_text(client, token):
    created = make_root(client, token)
    thread_id = created["thread"]["id"]
    response = post(
        client,
        token,
        f"/api/v1/threads/{thread_id}/notes",
        {"context": "missing anchor"},
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_outline_includes_headings_and_notes(client, token):
    created = make_root(client, token)
    thread_id = created["thread"]["id"]
    add_dive(client, token, thread_id, created["node_id"])
    snapshot = client.get(
        f"/api/v1/threads/{thread_id}", headers=auth(token)
    ).json()
    span_id = snapshot["spans"][0]["id"]
    post(
        client,
        token,
        f"/api/v1/threads/{thread_id}/notes",
        {"span_id": span_id, "text": "remember this"},
    )

    response = client.get(
        f"/api/v1/threads/{thread_id}/outline", headers=auth(token)
    )
    assert response.status_code == 200
    markdown = response.content.decode()
    assert "# Why is the sky blue?" in markdown
    assert "- remember this" in markdown


@pytest.mark.django_db
def test_list_threads_returns_own_newest_first(client, token):
    make_root(client, token, "Why is the sky blue?")
    make_root(client, token, "How do black holes bend time?")

    other = client.post(
        "/api/v1/auth/device", content_type="application/json"
    ).json()["token"]
    make_root(client, other, "Someone else's question")

    listing = client.get("/api/v1/threads", headers=auth(token)).json()
    titles = [row["title"] for row in listing["results"]]
    assert titles == ["How do black holes bend time?", "Why is the sky blue?"]
    assert listing["next"] is None


@pytest.mark.django_db
def test_threads_require_auth(client):
    assert client.post("/api/v1/threads").status_code == 401
    assert client.get("/api/v1/threads").status_code == 401
