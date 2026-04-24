VALID_INTAKE = {
    "first_name": "Jane",
    "last_name": "Smith",
    "business_email": "jane@embarkaviation.com",
    "legal_name": "Embark Aviation Corp",
    "domicile_state": "DE",
    "entity_type": "Corp",
    "employee_states": ["VA", "FL", "CO", "IL", "TN", "WA", "DC"],
    "business_nature": "Professional aviation services and consulting",
    "ecommerce_marketplace": False,
    "customer_types": ["B2B", "Government"],
    "product_service_location": ["DE", "VA", "FL", "CO", "IL", "TN", "WA", "DC"],
    "annual_revenue": "1m_5m",
    "annual_transactions": "1k_10k",
    "states_registered_sales_tax": [],
}

HEADERS = {"X-API-Key": "test-key-001"}


def test_health(client):
    test_client, _ = client
    r = test_client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_submit_audit_returns_job_id(client):
    test_client, mock_job_id = client
    r = test_client.post("/api/v1/audit", json=VALID_INTAKE, headers=HEADERS)
    assert r.status_code == 202
    data = r.json()
    assert "job_id" in data
    assert "status_url" in data
    assert data["status"] == "queued"


def test_submit_audit_requires_api_key(client):
    test_client, _ = client
    r = test_client.post("/api/v1/audit", json=VALID_INTAKE)
    assert r.status_code == 422  # missing header


def test_submit_audit_invalid_api_key(client):
    test_client, _ = client
    r = test_client.post("/api/v1/audit", json=VALID_INTAKE, headers={"X-API-Key": "wrong"})
    assert r.status_code == 401


def test_get_status(client):
    test_client, mock_job_id = client
    r = test_client.get(f"/api/v1/audit/{mock_job_id}/status", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert data["job_id"] == mock_job_id
    assert data["total_steps"] == 10
    assert len(data["steps"]) == 10


def test_get_report_not_ready(client):
    test_client, mock_job_id = client
    r = test_client.get(f"/api/v1/audit/{mock_job_id}/report", headers=HEADERS)
    # queued job → 425 Too Early
    assert r.status_code == 425


def test_submit_invalid_state(client):
    test_client, _ = client
    bad_intake = {**VALID_INTAKE, "domicile_state": "XX"}
    r = test_client.post("/api/v1/audit", json=bad_intake, headers=HEADERS)
    assert r.status_code == 422
