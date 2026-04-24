"""
HHS OIG LEIE (List of Excluded Individuals/Entities) — Sprint 2

Source: https://oig.hhs.gov/exclusions/downloadables/UPDATED.csv (monthly download)
Stored in S3: s3://compliance-indexes/leie/leie_latest.json

Excludes entities from Medicare/Medicaid participation.
Applies primarily to healthcare entities but relevant for gov contractors.

Same fuzzy matching strategy as OFAC (rapidfuzz, same thresholds).
Returns: exclusion_status, npi (if found), exclusion_type, reinstatement_date
"""
from typing import Any

from .base import BasePipelineStep, StepResult


class LeieStep(BasePipelineStep):
    step_number = 4
    step_name = "HHS OIG LEIE Exclusion Check"

    async def run(self, intake: dict[str, Any], job_id: str) -> StepResult:
        return self._skipped(sprint=2)
