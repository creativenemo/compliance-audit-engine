"""
Step 10 — Nova Report Synthesis: Full Compliance Audit Report

Two-step architecture
---------------------
Step A (fast):  Nova Lite — small prompt that returns ONLY the five risk scores
                and the overall_risk_score label.  This result is written to
                DynamoDB immediately so the frontend can show a score while the
                full report is still generating.

Step B (full):  Nova Lite (default) or Nova Pro (high-stakes customers) —
                full prompt with the entire pipeline_data payload.  Returns the
                complete ReportSchema JSON.

Score methodology (weights baked into the scoring prompt)
---------------------------------------------------------
    Entity Status       25 %  — SAM.gov registration + SOS status
    Federal Compliance  25 %  — SAM.gov exclusion flag + CSL screening
    Sanctions/Watchlists 20 % — OFAC SDN + LEIE status
    Tax Exposure        20 %  — sales-tax nexus gaps
    License Status      10 %  — Nova web-search license coverage

Error handling
--------------
    On Bedrock exception the step returns status="failed" together with a
    FALLBACK_REPORT that clearly states AI synthesis failed but includes all
    raw pipeline data so the frontend is never completely empty.
"""
from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from botocore.exceptions import BotoCoreError, ClientError

from app.config import settings
from app.services.bedrock import invoke_nova, parse_json_response

from .base import BasePipelineStep, StepResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt (verbatim from PRD)
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "You are a US business compliance analyst. Your role is to generate a structured "
    "compliance audit report for a US business entity based on data collected from "
    "government APIs and databases. Generate a structured compliance audit report "
    "strictly following these rules:\n"
    "(1) Use ONLY facts present in the provided JSON data.\n"
    "(2) For every finding, cite the exact source field path "
    "(e.g. sam_gov.entity_status).\n"
    "(3) If data for a section is absent or incomplete, state "
    "'Not found in available data sources'.\n"
    "(4) Risk scores must be derived from the provided data, not assumptions.\n"
    "(5) Output must be valid JSON matching the ReportSchema exactly.\n"
    "(6) Write in plain English accessible to a non-lawyer business owner."
)

# ---------------------------------------------------------------------------
# Scoring sub-prompt (Step A)
# ---------------------------------------------------------------------------

_SCORE_SYSTEM_PROMPT = (
    "You are a compliance risk analyst. Given pipeline data from government APIs, "
    "compute five numeric risk scores (0–100, where 100 = fully compliant / no risk) "
    "and an overall risk label. "
    "Return ONLY a valid JSON object with no prose. "
    "Score weights: "
    "entity_status=25%, federal_compliance=25%, sanctions_watchlists=20%, "
    "tax_exposure=20%, license_status=10%."
)

_SCORE_USER_TEMPLATE = """\
Compute compliance risk scores for this entity based on the pipeline data below.

Score methodology:
- entity_status (weight 25%): Based on SAM.gov registration status and Secretary
  of State (SOS) active/inactive status.  100 = active in all checked databases.
- federal_compliance (weight 25%): Based on SAM.gov exclusion/debarment flag and
  Consolidated Screening List (CSL) hits.  100 = no exclusions found.
- sanctions_watchlists (weight 20%): Based on OFAC SDN list and LEIE exclusion
  status.  100 = not found on any watchlist.
- tax_exposure (weight 20%): Based on gaps between employee_states and
  states_registered_sales_tax.  100 = all nexus states have sales-tax registration.
- license_status (weight 10%): Based on Nova license research.  100 = all required
  licenses confirmed present.

overall_risk_score mapping (use the weighted average of the five scores):
  90–100 → "LOW"
  70–89  → "MEDIUM"
  50–69  → "HIGH"
  0–49   → "CRITICAL"

Pipeline data:
{pipeline_data_json}

Return exactly this JSON and nothing else:
{{
  "overall_risk_score": "LOW|MEDIUM|HIGH|CRITICAL",
  "score_breakdown": {{
    "entity_status": <0-100>,
    "federal_compliance": <0-100>,
    "sanctions_watchlists": <0-100>,
    "tax_exposure": <0-100>,
    "license_status": <0-100>
  }}
}}
"""

# ---------------------------------------------------------------------------
# Full report user prompt (Step B)
# ---------------------------------------------------------------------------

_REPORT_USER_TEMPLATE = """\
Generate a complete compliance audit report for the entity described in the
pipeline data below.  Use the pre-computed risk scores provided.

Pre-computed risk scores:
{scores_json}

Full pipeline data (from government APIs and databases):
{pipeline_data_json}

Return exactly this JSON schema and nothing else — no markdown, no prose:
{{
  "overall_risk_score": "LOW|MEDIUM|HIGH|CRITICAL",
  "score_breakdown": {{
    "entity_status": <0-100>,
    "federal_compliance": <0-100>,
    "sanctions_watchlists": <0-100>,
    "tax_exposure": <0-100>,
    "license_status": <0-100>
  }},
  "executive_summary": "<3-5 sentences summarising the key findings and overall risk>",
  "sections": [
    {{
      "section_id": "entity_overview",
      "title": "Entity Overview",
      "status": "PASS|FAIL|WARNING|NOT_CHECKED",
      "findings": [
        {{"finding": "<str>", "source_field": "<e.g. step_01.entity_status>", "source_name": "<e.g. SAM.gov>"}}
      ],
      "recommendations": ["<actionable recommendation>"],
      "sources": ["<source name or URL>"]
    }},
    {{
      "section_id": "sanctions",
      "title": "Sanctions & Watchlist Screening",
      "status": "PASS|FAIL|WARNING|NOT_CHECKED",
      "findings": [],
      "recommendations": [],
      "sources": []
    }},
    {{
      "section_id": "federal_exclusions",
      "title": "Federal Exclusions & Debarment",
      "status": "PASS|FAIL|WARNING|NOT_CHECKED",
      "findings": [],
      "recommendations": [],
      "sources": []
    }},
    {{
      "section_id": "state_registration",
      "title": "State Registration & Good Standing",
      "status": "PASS|FAIL|WARNING|NOT_CHECKED",
      "findings": [],
      "recommendations": [],
      "sources": []
    }},
    {{
      "section_id": "edgar",
      "title": "SEC EDGAR Filing Status",
      "status": "PASS|FAIL|WARNING|NOT_CHECKED",
      "findings": [],
      "recommendations": [],
      "sources": []
    }},
    {{
      "section_id": "nonprofit",
      "title": "IRS Tax-Exempt Status",
      "status": "PASS|FAIL|WARNING|NOT_CHECKED",
      "findings": [],
      "recommendations": [],
      "sources": []
    }},
    {{
      "section_id": "industry_licenses",
      "title": "Industry Licenses & Permits",
      "status": "PASS|FAIL|WARNING|NOT_CHECKED",
      "findings": [],
      "recommendations": [],
      "sources": []
    }},
    {{
      "section_id": "sales_tax",
      "title": "Sales Tax Nexus & Registration",
      "status": "PASS|FAIL|WARNING|NOT_CHECKED",
      "findings": [],
      "recommendations": [],
      "sources": []
    }},
    {{
      "section_id": "ai_risk_summary",
      "title": "AI Risk Assessment Summary",
      "status": "PASS|FAIL|WARNING|NOT_CHECKED",
      "findings": [],
      "recommendations": [],
      "sources": []
    }}
  ],
  "top_action_items": [
    {{
      "priority": <1-5>,
      "action": "<specific action the business owner should take>",
      "urgency": "critical|high|medium|low",
      "estimated_cost": "<dollar range or 'Varies'>"
    }}
  ],
  "data_sources_checked": [
    {{
      "source_name": "<e.g. SAM.gov>",
      "queried_at": "<ISO datetime string>",
      "result_status": "success|failed|skipped"
    }}
  ],
  "generated_at": "<ISO datetime string>"
}}

Rules:
1. Every findings entry MUST have a non-empty source_field referencing the exact
   key path in the pipeline data (e.g. "step_01.sam_status").
2. If a step's data is absent or its status was "skipped", set the section
   status to "NOT_CHECKED" and note 'Not found in available data sources'.
3. top_action_items must be ordered by urgency (critical first) and capped at 10.
4. data_sources_checked must include one entry per pipeline step (01–09).
5. generated_at must be a valid ISO 8601 datetime with UTC offset.
"""

# ---------------------------------------------------------------------------
# Fallback report — returned when Bedrock is completely unavailable
# ---------------------------------------------------------------------------

def _build_fallback_report(pipeline_data: dict[str, Any]) -> dict[str, Any]:
    """Minimal valid report structure used when Nova synthesis fails."""
    now = datetime.now(UTC).isoformat()
    return {
        "overall_risk_score": "HIGH",
        "score_breakdown": {
            "entity_status": 50.0,
            "federal_compliance": 50.0,
            "sanctions_watchlists": 50.0,
            "tax_exposure": 50.0,
            "license_status": 50.0,
        },
        "executive_summary": (
            "AI-powered report synthesis was unavailable at the time of this audit. "
            "Raw compliance data was successfully collected from government sources and "
            "is included below. "
            "Please review the collected data manually or re-run the audit to obtain a "
            "full AI-generated analysis. "
            "A risk level of HIGH has been assigned conservatively pending full synthesis."
        ),
        "sections": [
            {
                "section_id": "ai_risk_summary",
                "title": "AI Risk Assessment Summary",
                "status": "NOT_CHECKED",
                "findings": [
                    {
                        "finding": (
                            "AI report synthesis failed. Raw pipeline data was collected "
                            "but could not be analyzed automatically."
                        ),
                        "source_field": "system.nova_synthesis_error",
                        "source_name": "Audit Engine",
                    }
                ],
                "recommendations": [
                    "Re-run the audit to attempt AI synthesis again.",
                    "Review raw pipeline data in the job record for manual assessment.",
                ],
                "sources": ["Amazon Bedrock"],
            }
        ],
        "top_action_items": [
            {
                "priority": 1,
                "action": "Re-run the compliance audit — AI synthesis was unavailable.",
                "urgency": "high",
                "estimated_cost": "No charge for re-run",
            }
        ],
        "data_sources_checked": [
            {
                "source_name": f"Step {k}",
                "queried_at": now,
                "result_status": "success" if v else "skipped",
            }
            for k, v in pipeline_data.items()
        ],
        "generated_at": now,
        "_raw_pipeline_data": pipeline_data,
        "_synthesis_failed": True,
    }


# ---------------------------------------------------------------------------
# Helper — condense pipeline_data to stay within context limits
# ---------------------------------------------------------------------------

_MAX_PIPELINE_JSON_CHARS = 28_000  # ~7 k tokens, leaves room for prompts


def _serialize_pipeline_data(pipeline_data: dict[str, Any]) -> str:
    """JSON-serialize pipeline_data, truncating gracefully if too large."""
    full = json.dumps(pipeline_data, default=str, indent=2)
    if len(full) <= _MAX_PIPELINE_JSON_CHARS:
        return full

    # Truncate each step's data individually to keep proportional coverage.
    # For steps whose serialized form exceeds the per-step budget, replace the
    # value with a plain-string snippet so the outer JSON stays valid.
    condensed: dict[str, Any] = {}
    budget_per_step = _MAX_PIPELINE_JSON_CHARS // max(len(pipeline_data), 1)
    for key, value in pipeline_data.items():
        step_json = json.dumps(value, default=str)
        if len(step_json) > budget_per_step:
            # Store the truncated raw text as a string annotation so Nova can
            # still read partial data without a JSON parse error.
            condensed[key] = {
                "_truncated": True,
                "_preview": step_json[:budget_per_step],
            }
        else:
            condensed[key] = value

    result = json.dumps(condensed, default=str, indent=2)
    logger.warning(
        "pipeline_data serialized to %d chars (original %d) — truncated to fit context window",
        len(result),
        len(full),
    )
    return result


# ---------------------------------------------------------------------------
# Step implementation
# ---------------------------------------------------------------------------

class NovaReportStep(BasePipelineStep):
    """Pipeline step 10 — two-step Nova report synthesis."""

    step_number = 10
    step_name = "Generating Compliance Report with AI"

    async def run(self, intake: dict[str, Any], job_id: str) -> StepResult:
        """Run two-step Nova report synthesis.

        Parameters
        ----------
        intake:
            Combined dict of intake form fields **plus** ``pipeline_data`` key
            (set by the orchestrator handler after steps 1–9 complete).
        job_id:
            Job identifier for log correlation.

        Returns
        -------
        StepResult
            status="complete" with the full ReportSchema-compatible dict in
            ``data``, or status="failed" with a fallback report on Bedrock error.
        """
        pipeline_data: dict[str, Any] = intake.get("pipeline_data", {})
        pipeline_json = _serialize_pipeline_data(pipeline_data)

        # ------------------------------------------------------------------ #
        # Step A — fast risk scoring (Nova Lite)                              #
        # ------------------------------------------------------------------ #
        logger.info("[job=%s] Step 10A: fast risk scoring via Nova Lite", job_id)

        scores: dict[str, Any] = {}
        try:
            score_raw = await invoke_nova(
                system_prompt=_SCORE_SYSTEM_PROMPT,
                user_message=_SCORE_USER_TEMPLATE.format(
                    pipeline_data_json=pipeline_json
                ),
                model_id=settings.nova_model_id,  # Nova Lite — fast
                max_tokens=512,
                temperature=0.0,
            )
            scores = parse_json_response(score_raw)
            if scores:
                logger.info(
                    "[job=%s] Step 10A: scores computed — overall=%s",
                    job_id,
                    scores.get("overall_risk_score"),
                )
            else:
                logger.warning(
                    "[job=%s] Step 10A: score response unparseable; "
                    "continuing to full report without pre-computed scores",
                    job_id,
                )
        except (ClientError, BotoCoreError) as exc:
            logger.warning(
                "[job=%s] Step 10A: Bedrock unavailable for scoring (%s); "
                "continuing to full report step",
                job_id,
                exc,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "[job=%s] Step 10A: unexpected scoring error (%s); continuing",
                job_id,
                exc,
            )

        # ------------------------------------------------------------------ #
        # Step B — full report (Nova Lite default, Pro if configured)         #
        # ------------------------------------------------------------------ #
        logger.info("[job=%s] Step 10B: full report synthesis via Nova", job_id)

        scores_json = json.dumps(scores, indent=2) if scores else '{"note": "Not pre-computed"}'

        try:
            report_raw = await invoke_nova(
                system_prompt=_SYSTEM_PROMPT,
                user_message=_REPORT_USER_TEMPLATE.format(
                    scores_json=scores_json,
                    pipeline_data_json=pipeline_json,
                ),
                model_id=settings.nova_pro_model_id,  # Nova Pro for full report quality
                max_tokens=8192,
                temperature=0.1,
            )
        except (ClientError, BotoCoreError) as exc:
            logger.error(
                "[job=%s] Step 10B: Bedrock unavailable — returning fallback report: %s",
                job_id,
                exc,
            )
            return StepResult(
                status="failed",
                error=str(exc),
                data=_build_fallback_report(pipeline_data),
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "[job=%s] Step 10B: unexpected error — returning fallback report: %s",
                job_id,
                exc,
            )
            return StepResult(
                status="failed",
                error=str(exc),
                data=_build_fallback_report(pipeline_data),
            )

        report = parse_json_response(report_raw)

        if not report:
            logger.error(
                "[job=%s] Step 10B: Nova returned unparseable report — returning fallback",
                job_id,
            )
            return StepResult(
                status="failed",
                error="Nova response could not be parsed as JSON",
                data=_build_fallback_report(pipeline_data),
            )

        # Guarantee generated_at is present even if model omitted it
        if not report.get("generated_at"):
            report["generated_at"] = datetime.now(UTC).isoformat()

        # If Step A scores are available and the full report omitted them (rare),
        # back-fill score_breakdown from the fast call
        if scores and not report.get("score_breakdown"):
            report["score_breakdown"] = scores.get("score_breakdown", {})
        if scores and not report.get("overall_risk_score"):
            report["overall_risk_score"] = scores.get("overall_risk_score", "HIGH")

        logger.info(
            "[job=%s] Step 10: report synthesis complete — overall_risk=%s",
            job_id,
            report.get("overall_risk_score"),
        )

        return StepResult(
            status="complete",
            data=report,
        )
