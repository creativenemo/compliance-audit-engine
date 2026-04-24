"""
HHS OIG LEIE Exclusion Check — Sprint 2

Loads the HHS OIG List of Excluded Individuals/Entities from S3 and
performs fuzzy name matching against the BUSNAME field (entity matches).

Thresholds (rapidfuzz token_sort_ratio):
  >= 95  → MATCH  (excluded entity — block / escalate)
  80–94  → REVIEW (possible exclusion hit, manual review required)
  < 80   → CLEAR
"""
import json
import re
from typing import Any

from rapidfuzz import fuzz

from app.services.s3 import get_index_json

from .base import BasePipelineStep, StepResult


def normalize_name(name: str) -> str:
    name = name.lower()
    name = re.sub(r"[^\w\s]", "", name)
    for suffix in [" llc", " inc", " corp", " ltd", " lp", " llp", " co", " company"]:
        name = name.replace(suffix, "")
    return name.strip()


class LeieStep(BasePipelineStep):
    step_number = 4
    step_name = "HHS OIG LEIE Exclusion Check"

    async def run(self, intake: dict[str, Any], job_id: str) -> StepResult:
        raw = get_index_json("leie/leie_latest.json")
        if raw is None:
            return StepResult(
                status="skipped",
                data={},
                message="LEIE index not yet downloaded",
            )

        try:
            records: list[dict] = json.loads(raw)
        except json.JSONDecodeError as exc:
            return StepResult(
                status="failed",
                data={},
                message="Failed to parse LEIE index",
                error=str(exc),
            )

        entity_name: str = intake.get("legal_name", "")
        if not entity_name:
            return StepResult(
                status="failed",
                data={},
                message="No legal_name provided in intake",
                error="missing_field:legal_name",
            )

        query = normalize_name(entity_name)

        best_score: float = 0.0
        best_record: dict | None = None

        for record in records:
            busname: str = record.get("BUSNAME", "") or ""
            if not busname:
                continue
            score: float = fuzz.token_sort_ratio(
                query, normalize_name(busname)
            )
            if score > best_score:
                best_score = score
                best_record = record

        if best_score >= 95:
            leie_status = "MATCH"
        elif best_score >= 80:
            leie_status = "REVIEW"
        else:
            leie_status = "CLEAR"
            best_record = None  # suppress weak near-miss details

        npi: str | None = None
        exclusion_type: str | None = None
        reinstatement_date: str | None = None

        if best_record is not None:
            npi = best_record.get("NPI") or None
            exclusion_type = best_record.get("EXCLTYPE") or None
            reinstatement_date = best_record.get("REINDATE") or None

        return StepResult(
            status="complete",
            data={
                "leie_status": leie_status,
                "confidence_pct": round(best_score, 2),
                "matched_entry": best_record,
                "npi": npi,
                "exclusion_type": exclusion_type,
                "reinstatement_date": reinstatement_date,
            },
        )
