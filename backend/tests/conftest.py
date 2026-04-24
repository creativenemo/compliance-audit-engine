import os

import pytest
from fastapi.testclient import TestClient

# Use dev key for tests
os.environ.setdefault("DEV_API_KEY", "test-key-001")
os.environ.setdefault("AUDIT_QUEUE_URL", "")  # disable SQS in tests


@pytest.fixture
def client(monkeypatch):
    # Patch DynamoDB calls so tests don't need AWS
    import uuid
    from unittest.mock import MagicMock, patch

    mock_job_id = str(uuid.uuid4())

    with (
        patch("app.services.dynamo.create_job", return_value=mock_job_id) as mock_create,
        patch("app.services.dynamo.get_job") as mock_get,
        patch("app.services.dynamo.get_report") as mock_report,
    ):
        from app.main import app
        mock_get.return_value = {
            "job_id": mock_job_id,
            "status": "queued",
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
            "current_step": 0,
            "steps": [
                {
                    "id": i + 1,
                    "name": f"Step {i + 1}",
                    "status": "pending",
                    "started_at": None,
                    "completed_at": None,
                    "error": None,
                }
                for i in range(10)
            ],
        }
        mock_report.return_value = None
        yield TestClient(app), mock_job_id
