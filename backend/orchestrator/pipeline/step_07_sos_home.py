"""
Secretary of State — Domicile State Scraper — Sprint 4

Uses Playwright (Docker Lambda container) to scrape domicile SOS website.
Scraper class: scrapers/states/{state_code}.py (e.g., scrapers/states/de.py)

Tier 1 states (Sprint 4): DE, WY, FL, CO, IL, VA, TN, WA, DC
Tier 2 (Month 2): CA, TX, NY, NV, OR, GA, NC, OH, PA
Tier 3 (Month 3-4): remaining states

Returns:
- Entity name (as registered)
- Entity status: Active / Dissolved / Delinquent / Not Found
- Formation date
- Registered agent name + address
- Annual report due date
- State-specific filing fee estimates
"""
from typing import Any

from .base import BasePipelineStep, StepResult


class SosHomeStateStep(BasePipelineStep):
    step_number = 7
    step_name = "Home State Registration Check"

    async def run(self, intake: dict[str, Any], job_id: str) -> StepResult:
        return self._skipped(sprint=4)
