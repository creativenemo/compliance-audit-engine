"""
OFAC SDN Local Index Lookup — Sprint 2

Loads the Treasury SDN list from S3 and performs fuzzy name matching
against entity names and all registered aliases (akaList).

Thresholds (rapidfuzz token_sort_ratio):
  >= 95  → MATCH  (likely sanctions hit, block / escalate)
  80–94  → REVIEW (possible hit, manual review required)
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


class OfacSdnStep(BasePipelineStep):
    step_number = 3
    step_name = "OFAC SDN Sanctions Check"

    async def run(self, intake: dict[str, Any], job_id: str) -> StepResult:
        raw = get_index_json("ofac/sdn_latest.json")
        if raw is None:
            return StepResult(
                status="skipped",
                data={},
                message="OFAC index not yet downloaded",
            )

        try:
            sdn_data = json.loads(raw)
            entries: list[dict] = (
                sdn_data.get("sdnList", {}).get("sdnEntry", [])
            )
        except (json.JSONDecodeError, AttributeError) as exc:
            return StepResult(
                status="failed",
                data={},
                message="Failed to parse OFAC SDN index",
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
        best_entry: dict | None = None
        aliases_checked: int = 0

        for entry in entries:
            # Primary name is stored in lastName for entity-type entries
            primary_name: str = entry.get("lastName", "") or ""
            candidates: list[str] = [primary_name] if primary_name else []

            # Collect all alternate names from akaList
            aka_list = entry.get("akaList") or {}
            aka_entries = aka_list.get("aka", [])
            if isinstance(aka_entries, dict):
                # Single aka comes back as a plain dict, not a list
                aka_entries = [aka_entries]
            for aka in aka_entries:
                alt_name: str = aka.get("name", "") or ""
                if alt_name:
                    candidates.append(alt_name)

            for candidate in candidates:
                aliases_checked += 1
                score: float = fuzz.token_sort_ratio(
                    query, normalize_name(candidate)
                )
                if score > best_score:
                    best_score = score
                    best_entry = entry

        if best_score >= 95:
            ofac_status = "MATCH"
        elif best_score >= 80:
            ofac_status = "REVIEW"
        else:
            ofac_status = "CLEAR"
            best_entry = None  # suppress weak near-miss details

        return StepResult(
            status="complete",
            data={
                "ofac_status": ofac_status,
                "confidence_pct": round(best_score, 2),
                "matched_entry": best_entry,
                "aliases_checked": aliases_checked,
            },
        )
