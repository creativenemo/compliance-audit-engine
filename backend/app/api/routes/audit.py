from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import require_api_key
from app.models.intake import IntakeForm
from app.models.job import AuditSubmitResponse, JobStatus, JobStatusResponse, StepProgress, StepStatus
from app.services import dynamo, s3, sqs
from app.services.share import create_share_token

router = APIRouter(prefix="/audit")


@router.post("", response_model=AuditSubmitResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_audit(form: IntakeForm, api_key: str = Depends(require_api_key)) -> AuditSubmitResponse:
    intake_dict = form.model_dump(mode="json")
    job_id = dynamo.create_job(intake_dict, api_key)

    if sqs_available():
        sqs.enqueue_audit_job(job_id, intake_dict)

    return AuditSubmitResponse(
        job_id=job_id,
        status_url=f"/api/v1/audit/{job_id}/status",
    )


@router.get("/{job_id}/status", response_model=JobStatusResponse)
async def get_audit_status(job_id: str, api_key: str = Depends(require_api_key)) -> JobStatusResponse:
    item = dynamo.get_job(job_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    steps = [
        StepProgress(
            id=s["id"],
            name=s["name"],
            status=StepStatus(s["status"]),
            started_at=_parse_dt(s.get("started_at")),
            completed_at=_parse_dt(s.get("completed_at")),
            error=s.get("error"),
        )
        for s in item.get("steps", [])
    ]

    current_step = int(item.get("current_step", 0))
    completed = sum(1 for s in steps if s.status in (StepStatus.COMPLETE, StepStatus.SKIPPED))
    progress_pct = round(completed / 10 * 100, 1)

    return JobStatusResponse(
        job_id=job_id,
        status=JobStatus(item["status"]),
        created_at=datetime.fromisoformat(item["created_at"]),
        updated_at=datetime.fromisoformat(item["updated_at"]),
        current_step=current_step,
        total_steps=10,
        progress_pct=progress_pct,
        steps=steps,
        eta_seconds=_estimate_eta(current_step, item["status"]),
    )


@router.get("/{job_id}/report")
async def get_audit_report(job_id: str, api_key: str = Depends(require_api_key)) -> dict:
    item = dynamo.get_job(job_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if item["status"] != JobStatus.COMPLETE.value:
        raise HTTPException(
            status_code=status.HTTP_425_TOO_EARLY,
            detail=f"Report not ready. Job status: {item['status']}",
        )

    report = dynamo.get_report(job_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return report


@router.get("/{job_id}/pdf")
async def get_audit_pdf(job_id: str, api_key: str = Depends(require_api_key)) -> dict:
    item = dynamo.get_job(job_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    url = s3.get_pdf_signed_url(job_id)
    if not url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF not yet generated")
    return {"pdf_url": url, "expires_in_seconds": 3600}


@router.get("/{job_id}/share")
async def get_share_link(job_id: str, api_key: str = Depends(require_api_key)) -> dict:
    item = dynamo.get_job(job_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    token, expiry = create_share_token(job_id)
    return {
        "share_url": f"/share/{token}",
        "expires_at": expiry.isoformat(),
        "expires_in_seconds": 7 * 24 * 3600,
    }


def sqs_available() -> bool:
    from app.config import settings
    return bool(settings.audit_queue_url)


def _parse_dt(value: str | None) -> datetime | None:
    if value:
        return datetime.fromisoformat(value)
    return None


def _estimate_eta(current_step: int, status: str) -> int | None:
    if status in (JobStatus.COMPLETE.value, JobStatus.FAILED.value):
        return None
    remaining = 10 - current_step
    return remaining * 5
