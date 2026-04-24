"""
trade.gov Consolidated Screening List (CSL) — Sprint 2

Endpoint: https://api.trade.gov/gateway/v1/consolidated_screening_list/search
Free, no auth required.

Screens against 13 government watchlists:
- Treasury: SDN, FSE, ISA, SSI, NS-MBS, PLC, CAPTA, DTC, UVML
- State: DTC, ISN
- Commerce: DPL, EL, MEU, Unverified
- OFAC non-SDN: NS-ISA, NS-SSI, NS-PLC, NS-CAPTA

Query params: name=<legal_name>, fuzzy_name=true
Threshold: sources_used, source, programs, name, score
"""
from typing import Any

from .base import BasePipelineStep, StepResult


class ConsolidatedScreeningStep(BasePipelineStep):
    step_number = 2
    step_name = "Trade.gov Consolidated Screening List"

    async def run(self, intake: dict[str, Any], job_id: str) -> StepResult:
        return self._skipped(sprint=2)
