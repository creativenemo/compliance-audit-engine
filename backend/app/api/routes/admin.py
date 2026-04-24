"""
Admin API — API key provisioning.

Requires the X-Admin-Key header (env: ADMIN_API_KEY).
Keys are stored in DynamoDB compliance-api-keys table:
  PK = apikey#{sha256(raw_key)}
  SK = #metadata
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

import boto3
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel

from app.config import settings

router = APIRouter(prefix="/admin")


# ─── Auth dependency ──────────────────────────────────────────────────────────

def require_admin_key(x_admin_key: Annotated[str, Header(alias="X-Admin-Key")]) -> str:
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return x_admin_key


# ─── Models ───────────────────────────────────────────────────────────────────

class CreateKeyRequest(BaseModel):
    label: str
    ttl_days: int = 365


class CreateKeyResponse(BaseModel):
    api_key: str
    label: str
    created_at: str
    expires_at: str
    key_hash: str


class RevokeKeyRequest(BaseModel):
    key_hash: str


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get_api_keys_table() -> Any:
    dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
    return dynamodb.Table(settings.api_keys_table_name)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.post("/keys", response_model=CreateKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    body: CreateKeyRequest,
    _: str = Depends(require_admin_key),
) -> CreateKeyResponse:
    raw_key = f"cae_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    now = datetime.now(UTC)
    expires_at = now + timedelta(days=body.ttl_days)
    ttl_epoch = int(expires_at.timestamp())

    table = _get_api_keys_table()
    table.put_item(Item={
        "pk": f"apikey#{key_hash}",
        "sk": "#metadata",
        "label": body.label,
        "created_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "ttl": ttl_epoch,
    })

    return CreateKeyResponse(
        api_key=raw_key,
        label=body.label,
        created_at=now.isoformat(),
        expires_at=expires_at.isoformat(),
        key_hash=key_hash,
    )


@router.delete("/keys", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    body: RevokeKeyRequest,
    _: str = Depends(require_admin_key),
) -> None:
    table = _get_api_keys_table()
    table.delete_item(Key={"pk": f"apikey#{body.key_hash}", "sk": "#metadata"})


@router.get("/keys", response_model=list[dict])
async def list_api_keys(_: str = Depends(require_admin_key)) -> list[dict]:
    table = _get_api_keys_table()
    # Scan is acceptable — the keys table is tiny
    response = table.scan(
        FilterExpression="begins_with(pk, :prefix)",
        ExpressionAttributeValues={":prefix": "apikey#"},
    )
    items = response.get("Items", [])
    # Strip the pk prefix; never return the raw key (it was never stored)
    return [
        {
            "key_hash": item["pk"].removeprefix("apikey#"),
            "label": item.get("label", ""),
            "created_at": item.get("created_at"),
            "expires_at": item.get("expires_at"),
        }
        for item in items
    ]
