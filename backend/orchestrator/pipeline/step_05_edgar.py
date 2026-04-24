"""
SEC EDGAR Full-Text Search — Sprint 3

Endpoints:
- https://efts.sec.gov/LATEST/search-index?q="<legal_name>"&dateRange=custom&startdt=2020-01-01
- https://data.sec.gov/submissions/CIK{cik}.json

Returns:
- CIK number (if public company)
- Most recent 10-K filing date
- Subsidiaries count (from Exhibit 21)
- Any SEC enforcement actions (litigation releases)
- If not found: consistent with private company status

Query by exact legal name, then fuzzy if no match.
"""
from typing import Any

from .base import BasePipelineStep, StepResult


class SecEdgarStep(BasePipelineStep):
    step_number = 5
    step_name = "SEC EDGAR Filing Check"

    async def run(self, intake: dict[str, Any], job_id: str) -> StepResult:
        return self._skipped(sprint=3)
