"""
IRS EO BMF + ProPublica Nonprofit Explorer — Sprint 3

IRS EO BMF: https://apps.irs.gov/app/eos/
ProPublica API: https://projects.propublica.org/nonprofits/api/v2/search.json?q=<name>
Both free, no auth.

Returns:
- 501(c) status and type
- EIN (if nonprofit)
- Most recent Form 990 year
- Total revenue (from 990)
- Executive compensation (top 5 from 990)
- If not nonprofit: consistent with entity type
"""
from typing import Any

from .base import BasePipelineStep, StepResult


class IrsTaxExemptStep(BasePipelineStep):
    step_number = 6
    step_name = "IRS Nonprofit & Tax-Exempt Status"

    async def run(self, intake: dict[str, Any], job_id: str) -> StepResult:
        return self._skipped(sprint=3)
