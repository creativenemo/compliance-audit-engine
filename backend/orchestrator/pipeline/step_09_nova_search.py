"""
Amazon Nova Web Search — Industry-Specific License Research — Sprint 5

Only step that uses Nova with live web_search tool enabled.
Model: Nova Lite (faster) with web_search tool

Query template:
  "What general business licenses and professional licenses are required for a
   {entity_type} in {domicile_state} that provides {business_nature}?
   Include state, county, and municipal requirements. List specific license names,
   issuing agencies, renewal periods, and approximate fees."

Also queries for each employee state if different license requirements apply.

Returns: structured list of {license_name, issuing_agency, state, renewal_period, fee_range, source_url}
"""
from typing import Any

from .base import BasePipelineStep, StepResult


class NovaWebSearchStep(BasePipelineStep):
    step_number = 9
    step_name = "Industry-Specific License Research"

    async def run(self, intake: dict[str, Any], job_id: str) -> StepResult:
        return self._skipped(sprint=5)
