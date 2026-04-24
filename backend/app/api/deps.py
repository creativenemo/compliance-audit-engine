import hashlib

import boto3
from fastapi import Header, HTTPException, status

from app.config import settings


def _get_api_keys_table():
    dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
    return dynamodb.Table(settings.api_keys_table_name)


async def require_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> str:
    # Dev key always works (local dev / CI)
    if x_api_key == settings.dev_api_key:
        return x_api_key

    # DynamoDB lookup for production keys
    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    try:
        table = _get_api_keys_table()
        response = table.get_item(Key={"pk": f"apikey#{key_hash}", "sk": "#metadata"})
        if not response.get("Item"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API key",
                headers={"WWW-Authenticate": "ApiKey"},
            )
    except HTTPException:
        raise
    except Exception:
        # DynamoDB unavailable in local dev — fall through if dev env
        if settings.environment == "development":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API key",
                headers={"WWW-Authenticate": "ApiKey"},
            )
        raise

    return x_api_key
