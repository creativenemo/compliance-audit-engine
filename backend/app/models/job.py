from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


class StepStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    SKIPPED = "skipped"


STEP_NAMES = [
    "Looking up your entity on federal databases",
    "Screening against 13 government watchlists",
    "Checking OFAC sanctions lists",
    "Checking federal healthcare exclusions",
    "Searching SEC EDGAR public filings",
    "Verifying nonprofit / tax-exempt status",
    "Checking home state registration",
    "Checking employee states for foreign qualifications",
    "Researching industry-specific requirements",
    "Generating your compliance report with AI",
]


class StepProgress(BaseModel):
    id: int
    name: str
    status: StepStatus = StepStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    current_step: int = 0
    total_steps: int = 10
    progress_pct: float = 0.0
    steps: list[StepProgress] = Field(default_factory=list)
    eta_seconds: int | None = None


class AuditSubmitResponse(BaseModel):
    job_id: str
    status: JobStatus = JobStatus.QUEUED
    status_url: str
    message: str = "Audit job queued. Poll status_url for progress."
