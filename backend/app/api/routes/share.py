from fastapi import APIRouter, HTTPException

from app.services import dynamo
from app.services.share import validate_share_token

router = APIRouter()


@router.get("/share/{token}")
async def get_shared_report(token: str) -> dict:
    job_id = validate_share_token(token)
    if not job_id:
        raise HTTPException(status_code=404, detail="Share link not found or expired")
    report = dynamo.get_report(job_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not available")
    return report
