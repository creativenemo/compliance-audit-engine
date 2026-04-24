import secrets
from datetime import datetime, timedelta, timezone

import boto3

from app.config import settings


def _get_table():
    dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
    return dynamodb.Table(settings.jobs_table_name)


def create_share_token(job_id: str) -> tuple[str, datetime]:
    """Store a 7-day share token in DynamoDB. Returns (token, expiry_datetime)."""
    token = secrets.token_urlsafe(32)
    expiry = datetime.now(timezone.utc) + timedelta(days=7)
    ttl = int(expiry.timestamp())

    table = _get_table()
    table.put_item(Item={
        "job_id": f"share#{token}",
        "sk": "#share",
        "real_job_id": job_id,
        "expires_at": expiry.isoformat(),
        "ttl": ttl,
    })
    return token, expiry


def validate_share_token(token: str) -> str | None:
    """Returns job_id if token is valid and not expired, else None."""
    table = _get_table()
    response = table.get_item(Key={"job_id": f"share#{token}", "sk": "#share"})
    item = response.get("Item")
    if not item:
        return None

    expires_at = datetime.fromisoformat(item["expires_at"])
    if datetime.now(timezone.utc) > expires_at:
        return None

    return item["real_job_id"]
