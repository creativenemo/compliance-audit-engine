"""
Step 09 — Nova Web Search: Industry-Specific License Research

Uses Amazon Nova Lite to research what business licenses and permits apply
to the entity based on its type, domicile state, business nature, and every
state where employees are located.

Model
-----
    amazon.nova-lite-v1:0 (fast, low cost — adequate for structured JSON output)

Output shape
------------
    {
        "licenses": [
            {
                "license_name": str,
                "issuing_agency": str,
                "state": str,          // "Federal" for federal-level licenses
                "description": str,
                "renewal_period": str,
                "fee_range": str,
                "applies_to_this_entity": bool,
                "notes": str
            }
        ],
        "summary": str
    }

Error handling
--------------
    On any Bedrock exception the step returns status="skipped" so the rest of
    the pipeline (and the final report) can continue without license data.
"""
from __future__ import annotations

import logging
from typing import Any

from botocore.exceptions import BotoCoreError, ClientError

from app.config import settings
from app.services.bedrock import invoke_nova, parse_json_response

from .base import BasePipelineStep, StepResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "You are a US business compliance expert specializing in licensing requirements. "
    "Research what licenses and permits are required for the described business. "
    "Return ONLY a valid JSON object matching the exact schema provided. "
    "Cite specific government agency names and URLs when known."
)

_USER_TEMPLATE = """\
Research business license and permit requirements for:
- Entity Type: {entity_type}
- State: {domicile_state}
- Business Nature: {business_nature}
- Also check these employee states: {employee_states}

Return JSON matching this schema exactly — no prose, no markdown, just JSON:
{{
  "licenses": [
    {{
      "license_name": "<string>",
      "issuing_agency": "<string>",
      "state": "<two-letter state code, or 'Federal' for federal licenses>",
      "description": "<string>",
      "renewal_period": "<string>",
      "fee_range": "<string>",
      "applies_to_this_entity": true,
      "notes": "<string>"
    }}
  ],
  "summary": "<1-3 sentence plain-English summary of key licensing obligations>"
}}

Rules:
1. Include both state-level and federal licenses that genuinely apply.
2. For each employee state listed, include any state-specific licenses required.
3. Set applies_to_this_entity to false (and include a brief note) for licenses
   that are commonly confused with this business type but do not apply.
4. Use "Unknown" for fields where authoritative data is unavailable.
5. Do not invent license requirements — only cite real, verifiable obligations.
"""


# ---------------------------------------------------------------------------
# Step implementation
# ---------------------------------------------------------------------------

class NovaWebSearchStep(BasePipelineStep):
    """Pipeline step 09 — Nova license research."""

    step_number = 9
    step_name = "Industry-Specific License Research"

    async def run(self, intake: dict[str, Any], job_id: str) -> StepResult:
        """Run Nova license research for the entity described in *intake*.

        Parameters
        ----------
        intake:
            The intake form data dict (fields from ``IntakeForm``).
        job_id:
            Job identifier for log correlation.

        Returns
        -------
        StepResult
            status="complete" with ``data`` containing the parsed license list,
            or status="skipped" if Bedrock is unavailable.
        """
        entity_type: str = intake.get("entity_type", "Unknown")
        domicile_state: str = intake.get("domicile_state", "Unknown")
        business_nature: str = intake.get("business_nature", "Not specified")
        employee_states: list[str] = intake.get("employee_states", [])

        employee_states_str = (
            ", ".join(sorted(set(employee_states))) if employee_states else "None"
        )

        user_message = _USER_TEMPLATE.format(
            entity_type=entity_type,
            domicile_state=domicile_state,
            business_nature=business_nature,
            employee_states=employee_states_str,
        )

        logger.info(
            "[job=%s] Step 09: invoking Nova for license research "
            "(entity_type=%s, domicile=%s, employee_states=%s)",
            job_id,
            entity_type,
            domicile_state,
            employee_states_str,
        )

        try:
            raw_text = await invoke_nova(
                system_prompt=_SYSTEM_PROMPT,
                user_message=user_message,
                model_id=settings.nova_model_id,
                max_tokens=4096,
                temperature=0.1,
            )
        except (ClientError, BotoCoreError) as exc:
            logger.warning(
                "[job=%s] Step 09: Bedrock unavailable — skipping license research: %s",
                job_id,
                exc,
            )
            return StepResult(
                status="skipped",
                message=str(exc),
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "[job=%s] Step 09: unexpected error during Nova call — skipping: %s",
                job_id,
                exc,
            )
            return StepResult(
                status="skipped",
                message=str(exc),
            )

        parsed = parse_json_response(raw_text)

        if not parsed:
            logger.warning(
                "[job=%s] Step 09: Nova returned unparseable response — skipping",
                job_id,
            )
            return StepResult(
                status="skipped",
                message="Nova response could not be parsed as JSON",
            )

        licenses: list[dict[str, Any]] = parsed.get("licenses", [])
        summary: str = parsed.get("summary", "")

        logger.info(
            "[job=%s] Step 09: license research complete — %d licenses found",
            job_id,
            len(licenses),
        )

        return StepResult(
            status="complete",
            data={
                "licenses": licenses,
                "summary": summary,
                "entity_type": entity_type,
                "domicile_state": domicile_state,
                "employee_states": employee_states,
            },
        )
