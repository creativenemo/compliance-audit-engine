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
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from scrapers.states import TIER1_SCRAPERS

from .base import BasePipelineStep, StepResult


class SosHomeStateStep(BasePipelineStep):
    step_number = 7
    step_name = "Home State Registration Check"

    async def run(self, intake: dict[str, Any], job_id: str) -> StepResult:
        legal_name: str = intake.get("legal_name", "")
        domicile_state: str = intake.get("domicile_state", "")

        if not legal_name or not domicile_state:
            return StepResult(
                status="failed",
                data={},
                message="Missing required intake fields: legal_name or domicile_state",
                error="intake_validation_error",
            )

        if domicile_state not in TIER1_SCRAPERS:
            return StepResult(
                status="skipped",
                data={"domicile_state": domicile_state},
                message=f"SOS scraper not yet implemented for {domicile_state}",
            )

        scraper = TIER1_SCRAPERS[domicile_state]

        try:
            registration = await scraper.scrape_entity(legal_name)
        except Exception as exc:
            return StepResult(
                status="failed",
                data={"domicile_state": domicile_state, "legal_name": legal_name},
                message=f"SOS scraper raised an unexpected error for {domicile_state}",
                error=str(exc),
            )

        return StepResult(
            status="complete",
            data={
                "domicile_state": domicile_state,
                **asdict(registration),
            },
            message=(
                f"Entity '{registration.legal_name}' found in {domicile_state} "
                f"with status '{registration.status}'"
            ),
        )
