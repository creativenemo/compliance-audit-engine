"""
OFAC SDN Local Index — Sprint 2

Source: https://www.treasury.gov/ofac/downloads/sdn.json (nightly download)
Stored in S3: s3://compliance-indexes/ofac/sdn_latest.json

Local fuzzy name matching via rapidfuzz:
- Normalize: lowercase → strip punctuation → remove entity suffixes (LLC, Inc, Corp, Ltd)
- Score ≥ 95%: MATCH (block)
- Score 80–94%: REVIEW (flag for human review)
- Score < 80%: CLEAR

No external API call at query time — reads from S3 warm copy.
Returns: match_status, confidence_pct, matched_entry (if match/review)
"""
from typing import Any

from .base import BasePipelineStep, StepResult


class OfacSdnStep(BasePipelineStep):
    step_number = 3
    step_name = "OFAC SDN Sanctions Check"

    async def run(self, intake: dict[str, Any], job_id: str) -> StepResult:
        return self._skipped(sprint=2)
