"""
SAM.gov Entity Management API — Sprint 2

Endpoint: https://api.sam.gov/entity-information/v3/entities
Auth: API key (free registration at sam.gov)

Query by legal_name + domicile_state. Returns:
- CAGE code, UEI (DUNS replacement)
- Entity status (Active / Inactive / Not Found)
- Debarment / exclusion status
- Federal award history

Fuzzy name match if exact match returns 0 results.
Write result to DynamoDB step#01.
"""
from typing import Any

from .base import BasePipelineStep, StepResult


class SamGovStep(BasePipelineStep):
    step_number = 1
    step_name = "SAM.gov Entity Lookup"

    async def run(self, intake: dict[str, Any], job_id: str) -> StepResult:
        return self._skipped(sprint=2)
