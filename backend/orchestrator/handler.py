"""
Orchestrator Lambda — dequeues SQS FIFO messages and runs the full pipeline.
Triggered by: SQS event source mapping on audit-jobs.fifo
Timeout: 5 minutes
Memory: 1024 MB
"""
import asyncio
import json
import logging
from typing import Any

from app.models.job import JobStatus, StepStatus
from app.services import dynamo
from orchestrator.pipeline import ALL_STEPS

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    for record in event.get("Records", []):
        body = json.loads(record["body"])
        job_id = body["job_id"]
        intake = body["intake_data"]
        try:
            asyncio.run(_run_pipeline(job_id, intake))
        except Exception as exc:
            logger.exception("Pipeline failed for job %s: %s", job_id, exc)
            dynamo.update_job_status(job_id, JobStatus.FAILED)
    return {"statusCode": 200}


async def _run_pipeline(job_id: str, intake: dict[str, Any]) -> None:
    dynamo.update_job_status(job_id, JobStatus.RUNNING, current_step=1)

    # Steps 1–9 run in parallel; step 10 (Nova) runs after all data is gathered
    data_steps = ALL_STEPS[:9]
    report_step = ALL_STEPS[9]

    step_results: list[Any] = await asyncio.gather(
        *[_run_step(step, intake, job_id) for step in data_steps],
        return_exceptions=True,
    )

    # Collect results keyed by step number
    pipeline_data: dict[str, Any] = {}
    for step, result in zip(data_steps, step_results, strict=False):
        if isinstance(result, Exception):
            logger.error("Step %d failed: %s", step.step_number, result)
            dynamo.update_step_status(job_id, step.step_number - 1, StepStatus.FAILED, str(result))
        else:
            pipeline_data[f"step_{step.step_number:02d}"] = result.data

    # Step 10: Nova report synthesis
    dynamo.update_job_status(job_id, JobStatus.RUNNING, current_step=10)
    report_result = await _run_step(report_step, {**intake, "pipeline_data": pipeline_data}, job_id)
    dynamo.save_report(job_id, report_result.data)
    logger.info("Pipeline complete for job %s", job_id)

    # Email notification
    try:
        from app.services.email import send_report_ready_email
        intake_item = dynamo.get_job(job_id)
        if intake_item:
            intake_data = json.loads(intake_item.get("intake_data", "{}"))
            score_data = report_result.data.get("score_breakdown", {})
            overall = report_result.data.get("overall_risk_score", "MEDIUM")
            weights = {
                "entity_status": 0.25,
                "federal_compliance": 0.25,
                "sanctions_watchlists": 0.20,
                "tax_exposure": 0.20,
                "license_status": 0.10,
            }
            numeric_score = int(sum(score_data.get(k, 75) * w for k, w in weights.items()))
            send_report_ready_email(
                to_email=intake_data.get("business_email", ""),
                first_name=intake_data.get("first_name", ""),
                legal_name=intake_data.get("legal_name", ""),
                job_id=job_id,
                overall_score=numeric_score,
                risk_level=overall,
                report_url=f"/audit/{job_id}/report",
            )
    except Exception as e:
        logger.warning("Email notification failed for job %s: %s", job_id, e)


async def _run_step(step: Any, intake: dict[str, Any], job_id: str) -> Any:
    idx = step.step_number - 1
    dynamo.update_step_status(job_id, idx, StepStatus.RUNNING)
    result = await step.run(intake, job_id)
    final_status = StepStatus.COMPLETE if result.status == "complete" else StepStatus.SKIPPED
    dynamo.update_step_status(job_id, idx, final_status)
    return result
