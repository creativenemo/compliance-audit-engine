import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import boto3
from boto3.dynamodb.conditions import Key

from app.config import settings
from app.models.job import STEP_NAMES, JobStatus, StepStatus


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ttl_24h() -> int:
    from datetime import timedelta
    return int((datetime.now(timezone.utc) + timedelta(hours=24)).timestamp())


def get_table() -> Any:
    dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
    return dynamodb.Table(settings.jobs_table_name)


def create_job(intake_data: dict[str, Any], api_key: str) -> str:
    job_id = str(uuid4())
    table = get_table()
    now = _now_iso()

    steps = [
        {
            "id": i + 1,
            "name": STEP_NAMES[i],
            "status": StepStatus.PENDING.value,
            "started_at": None,
            "completed_at": None,
            "error": None,
        }
        for i in range(10)
    ]

    table.put_item(Item={
        "job_id": job_id,
        "sk": "#metadata",
        "status": JobStatus.QUEUED.value,
        "created_at": now,
        "updated_at": now,
        "api_key_hash": hashlib.sha256(api_key.encode()).hexdigest(),
        "intake_data": json.dumps(intake_data),
        "current_step": 0,
        "total_steps": 10,
        "steps": steps,
        "ttl": _ttl_24h(),
    })
    return job_id


def get_job(job_id: str) -> dict[str, Any] | None:
    table = get_table()
    response = table.get_item(Key={"job_id": job_id, "sk": "#metadata"})
    return response.get("Item")


def update_job_status(job_id: str, status: JobStatus, current_step: int = 0) -> None:
    table = get_table()
    table.update_item(
        Key={"job_id": job_id, "sk": "#metadata"},
        UpdateExpression="SET #s = :s, updated_at = :u, current_step = :cs",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":s": status.value,
            ":u": _now_iso(),
            ":cs": current_step,
        },
    )


def update_step_status(job_id: str, step_index: int, status: StepStatus, error: str | None = None) -> None:
    table = get_table()
    now = _now_iso()
    update_expr = (
        f"SET steps[{step_index}].#s = :s, steps[{step_index}].completed_at = :ca, updated_at = :u"
    )
    expr_values: dict[str, Any] = {":s": status.value, ":ca": now, ":u": now}
    if error:
        update_expr += f", steps[{step_index}].#e = :e"
        expr_values[":e"] = error

    table.update_item(
        Key={"job_id": job_id, "sk": "#metadata"},
        UpdateExpression=update_expr,
        ExpressionAttributeNames={"#s": "status", "#e": "error"},
        ExpressionAttributeValues=expr_values,
    )


def save_report(job_id: str, report_json: dict[str, Any]) -> None:
    table = get_table()
    from datetime import timedelta
    ttl_1yr = int((datetime.now(timezone.utc) + timedelta(days=365)).timestamp())
    table.put_item(Item={
        "job_id": job_id,
        "sk": "#report",
        "report": json.dumps(report_json),
        "created_at": _now_iso(),
        "ttl": ttl_1yr,
    })
    update_job_status(job_id, JobStatus.COMPLETE, current_step=10)


def get_report(job_id: str) -> dict[str, Any] | None:
    table = get_table()
    response = table.get_item(Key={"job_id": job_id, "sk": "#report"})
    item = response.get("Item")
    if item:
        return json.loads(item["report"])
    return None
