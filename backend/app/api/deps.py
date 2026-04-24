from fastapi import Header, HTTPException, status

from app.config import settings


async def require_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> str:
    # Sprint 1: accept dev key from env. Sprint 5: replace with DynamoDB api_keys lookup.
    if x_api_key != settings.dev_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return x_api_key
