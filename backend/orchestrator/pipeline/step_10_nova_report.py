"""
Amazon Nova Report Synthesis — Sprint 3

Model: Nova Lite (standard) or Nova Pro (Government/high-stakes customers)
Two-step call:
  1. Fast Nova Micro/Lite call → risk_score + overall_risk_level (shown on frontend quickly)
  2. Full Nova Lite/Pro call → complete ReportSchema JSON

System prompt (verbatim from PRD):
  "You are a US business compliance analyst. Your role is to generate a structured
   compliance audit report for a US business entity based on data collected from
   government APIs and databases. Generate a structured compliance audit report
   strictly following these rules:
   (1) Use ONLY facts present in the provided JSON data.
   (2) For every finding, cite the exact source field path (e.g. sam_gov.entity_status).
   (3) If data for a section is absent or incomplete, state 'Not found in available data sources'.
   (4) Risk scores must be derived from the provided data, not assumptions.
   (5) Output must be valid JSON matching the ReportSchema exactly.
   (6) Write in plain English accessible to a non-lawyer business owner."
"""
from datetime import datetime, timezone
from typing import Any

from .base import BasePipelineStep, StepResult

SYSTEM_PROMPT = (
    "You are a US business compliance analyst. Your role is to generate a structured "
    "compliance audit report for a US business entity based on data collected from "
    "government APIs and databases. Generate a structured compliance audit report "
    "strictly following these rules:\n"
    "(1) Use ONLY facts present in the provided JSON data.\n"
    "(2) For every finding, cite the exact source field path (e.g. sam_gov.entity_status).\n"
    "(3) If data for a section is absent or incomplete, state 'Not found in available data sources'.\n"
    "(4) Risk scores must be derived from the provided data, not assumptions.\n"
    "(5) Output must be valid JSON matching the ReportSchema exactly.\n"
    "(6) Write in plain English accessible to a non-lawyer business owner."
)

MOCK_REPORT = {
    "overall_risk_score": "MEDIUM",
    "score_breakdown": {
        "entity_status": 75.0,
        "federal_compliance": 80.0,
        "sanctions_watchlists": 100.0,
        "tax_exposure": 60.0,
        "license_status": 70.0,
    },
    "executive_summary": (
        "This is a Sprint 1 stub report. Full AI-generated narrative implemented in Sprint 3. "
        "All data pipeline steps are currently returning skipped status."
    ),
    "sections": [],
    "top_action_items": [
        {
            "priority": 1,
            "action": "Implement Sprint 2 federal data layer to populate real findings",
            "urgency": "high",
            "estimated_cost": "Development time",
        }
    ],
    "data_sources_checked": [],
    "generated_at": datetime.now(timezone.utc).isoformat(),
}


class NovaReportStep(BasePipelineStep):
    step_number = 10
    step_name = "Generating Compliance Report with AI"

    async def run(self, intake: dict[str, Any], job_id: str) -> StepResult:
        # Sprint 1: return mock report so end-to-end flow works
        # Sprint 3: call Amazon Nova via Bedrock with real pipeline data
        return StepResult(
            status="complete",
            data=MOCK_REPORT,
            message="Sprint 1 mock report. Real Nova synthesis in Sprint 3.",
        )
