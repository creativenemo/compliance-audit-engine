"""
Secretary of State — Employee States Foreign Qualification Check — Sprint 4

For each state in intake.employee_states (excluding domicile_state):
- Check if entity has registered as a foreign qualifier via Playwright.
- Run all supported state lookups in parallel via asyncio.gather.
- States not yet in TIER1_SCRAPERS are returned with qualified=None and a note.

Returns:
- states_checked: list of per-state results
- missing_qualifications: state codes where qualified is False
- unsupported_states: state codes with no scraper yet
"""
from __future__ import annotations

import asyncio
from dataclasses import asdict
from typing import Any

from scrapers.base import ForeignQualification
from scrapers.states import TIER1_SCRAPERS

from .base import BasePipelineStep, StepResult


async def _safe_scrape_foreign(
    state_code: str,
    legal_name: str,
) -> dict[str, Any]:
    """
    Call scrape_foreign_quals for a supported state and return a serialisable dict.
    Any exception is caught and returns qualified=False with an error note.
    """
    scraper = TIER1_SCRAPERS[state_code]
    try:
        result: ForeignQualification = await scraper.scrape_foreign_quals(legal_name)
        return asdict(result)
    except Exception as exc:
        return {
            "state": state_code,
            "qualified": False,
            "registration_date": None,
            "status": None,
            "estimated_filing_cost": None,
            "error": str(exc),
        }


class SosEmployeeStatesStep(BasePipelineStep):
    step_number = 8
    step_name = "Employee States Foreign Qualification Check"

    async def run(self, intake: dict[str, Any], job_id: str) -> StepResult:
        legal_name: str = intake.get("legal_name", "")
        domicile_state: str = intake.get("domicile_state", "")
        employee_states: list[str] = intake.get("employee_states", [])

        if not legal_name:
            return StepResult(
                status="failed",
                data={},
                message="Missing required intake field: legal_name",
                error="intake_validation_error",
            )

        # Exclude the domicile state — that's already handled by step 07
        target_states = [s for s in employee_states if s != domicile_state]

        supported = [s for s in target_states if s in TIER1_SCRAPERS]
        unsupported = [s for s in target_states if s not in TIER1_SCRAPERS]

        # Run all supported-state scrapers in parallel
        tasks = [_safe_scrape_foreign(state, legal_name) for state in supported]
        scraped_results: list[dict[str, Any]] = await asyncio.gather(*tasks)

        # Build unsupported-state placeholders
        unsupported_results: list[dict[str, Any]] = [
            {
                "state": s,
                "qualified": None,
                "registration_date": None,
                "status": None,
                "estimated_filing_cost": None,
                "note": "Scraper not yet available",
            }
            for s in unsupported
        ]

        states_checked = scraped_results + unsupported_results

        missing_qualifications = [
            r["state"]
            for r in scraped_results
            if r.get("qualified") is False
        ]

        return StepResult(
            status="complete",
            data={
                "states_checked": states_checked,
                "missing_qualifications": missing_qualifications,
                "unsupported_states": unsupported,
            },
            message=(
                f"Checked {len(target_states)} employee state(s). "
                f"{len(missing_qualifications)} missing foreign qualification(s). "
                f"{len(unsupported)} state(s) without a scraper."
            ),
        )
