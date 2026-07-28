"""FastAPI route tests using the in-process TestClient (offline)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_personas():
    resp = client.get("/api/demo/personas")
    assert resp.status_code == 200
    ids = {p["id"] for p in resp.json()}
    assert {"equity-research", "fi-pm", "compliance"} <= ids


def test_corpus_returns_titles_only():
    resp = client.get("/api/demo/corpus")
    assert resp.status_code == 200
    docs = resp.json()
    assert any(d["id"] == "DEAL-MEMO-007" for d in docs)
    assert all(d["snippet"] == "" for d in docs)  # no content leaked


def test_option_a_invoke():
    resp = client.post(
        "/api/demo/optionA/invoke",
        json={"persona_id": "equity-research", "query": "semiconductor outlook"},
    )
    assert resp.status_code == 200
    assert resp.json()["identity_basis"] == "app_only"


def test_option_b_invoke():
    resp = client.post(
        "/api/demo/optionB/invoke",
        json={"persona_id": "fi-pm", "query": "energy credit"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["identity_basis"] == "per_user_obo"
    assert "EQ-RES-001" not in body["visible_doc_ids"]


def test_compare_endpoint():
    resp = client.post(
        "/api/demo/compare",
        json={"persona_id": "equity-research", "query": "high yield energy credit"},
    )
    assert resp.status_code == 200
    assert resp.json()["difference_doc_ids"]


def test_unknown_persona_404():
    resp = client.post(
        "/api/demo/optionA/invoke",
        json={"persona_id": "nobody", "query": "hello"},
    )
    assert resp.status_code == 404


def test_unsafe_query_400():
    resp = client.post(
        "/api/demo/optionA/invoke",
        json={"persona_id": "equity-research", "query": "   "},
    )
    assert resp.status_code == 400
