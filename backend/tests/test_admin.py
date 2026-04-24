"""Tests for admin API key management endpoints."""

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DEV_API_KEY", "test-key-001")
os.environ.setdefault("ADMIN_API_KEY", "admin-test-key")
os.environ.setdefault("AUDIT_QUEUE_URL", "")

ADMIN_HEADERS = {"X-Admin-Key": "admin-test-key"}


@pytest.fixture
def client():
    with (
        patch("app.api.routes.admin._get_api_keys_table") as mock_table_fn,
    ):
        mock_table = MagicMock()
        mock_table_fn.return_value = mock_table
        mock_table.put_item.return_value = {}
        mock_table.delete_item.return_value = {}
        mock_table.scan.return_value = {"Items": []}

        from app.main import app
        yield TestClient(app), mock_table


def test_create_key_success(client):
    test_client, mock_table = client
    r = test_client.post(
        "/api/v1/admin/keys",
        json={"label": "test-customer", "ttl_days": 365},
        headers=ADMIN_HEADERS,
    )
    assert r.status_code == 201
    data = r.json()
    assert data["api_key"].startswith("cae_")
    assert data["label"] == "test-customer"
    assert "expires_at" in data
    assert "key_hash" in data
    mock_table.put_item.assert_called_once()


def test_create_key_requires_admin_auth(client):
    test_client, _ = client
    r = test_client.post(
        "/api/v1/admin/keys",
        json={"label": "test"},
        headers={"X-Admin-Key": "wrong"},
    )
    assert r.status_code == 401


def test_create_key_missing_admin_header(client):
    test_client, _ = client
    r = test_client.post("/api/v1/admin/keys", json={"label": "test"})
    assert r.status_code == 422


def test_revoke_key(client):
    test_client, mock_table = client
    r = test_client.request(
        "DELETE",
        "/api/v1/admin/keys",
        json={"key_hash": "abc123"},
        headers=ADMIN_HEADERS,
    )
    assert r.status_code == 204
    mock_table.delete_item.assert_called_once_with(
        Key={"pk": "apikey#abc123", "sk": "#metadata"}
    )


def test_list_keys_empty(client):
    test_client, _ = client
    r = test_client.get("/api/v1/admin/keys", headers=ADMIN_HEADERS)
    assert r.status_code == 200
    assert r.json() == []


def test_list_keys_returns_records(client):
    test_client, mock_table = client
    mock_table.scan.return_value = {
        "Items": [
            {
                "pk": "apikey#deadbeef",
                "sk": "#metadata",
                "label": "acme-corp",
                "created_at": "2026-01-01T00:00:00+00:00",
                "expires_at": "2027-01-01T00:00:00+00:00",
            }
        ]
    }
    r = test_client.get("/api/v1/admin/keys", headers=ADMIN_HEADERS)
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["key_hash"] == "deadbeef"
    assert items[0]["label"] == "acme-corp"
