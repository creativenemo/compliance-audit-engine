"""
trade.gov Consolidated Screening List (CSL) — Sprint 2

Endpoint: https://api.trade.gov/gateway/v1/consolidated_screening_list/search
Auth: none required (public API)

The CSL aggregates 13 US government watchlists into a single search endpoint:

  Treasury / OFAC:
    SDN   — Specially Designated Nationals
    FSE   — Foreign Sanctions Evaders
    ISA   — Iran Sanctions Act
    SSI   — Sectoral Sanctions Identifications
    NS-MBS — Non-SDN Menu-Based Sanctions
    PLC   — Palestinian Legislative Council
    CAPTA — Correspondent Account or Payable-Through Account Sanctions
    UVML  — Unverified Multilateral

  State Department:
    DTC   — Debarred parties (ITAR)
    ISN   — Nonproliferation Sanctions

  Commerce / BIS:
    DPL   — Denied Persons List
    EL    — Entity List
    MEU   — Military End User
    Unverified — Unverified List

Query: name=<normalized_name>&fuzzy_name=true&size=5
Result: REVIEW if any matches returned, else CLEAR.

Each match record returned to the caller contains:
  name, source, programs, score, addresses, alt_names, start_date, end_date
"""

import logging
import re
from typing import Any

import httpx

from .base import BasePipelineStep, StepResult

logger = logging.getLogger(__name__)

_CSL_ENDPOINT = "https://api.trade.gov/gateway/v1/consolidated_screening_list/search"

# Timeout: CSL is generally fast, but give generous budget for retries at origin
_TIMEOUT = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=5.0)

_RESULTS_LIMIT = 5

# Canonical count of lists aggregated by the CSL endpoint (for reporting transparency)
_SOURCES_CHECKED = 13

# Sources reflected in the count above (informational, not used in logic)
_SOURCE_NAMES: list[str] = [
    "SDN", "FSE", "ISA", "SSI", "DTC", "DPL", "EL", "MEU",
    "Unverified", "NS-MBS", "PLC", "CAPTA", "UVML",
]

# Regex used to collapse internal whitespace during name normalisation
_WHITESPACE_RE = re.compile(r"\s+")


def _normalize_name(name: str) -> str:
    """
    Prepare a business name for CSL querying:
      - Strip leading/trailing whitespace
      - Fold all internal whitespace sequences to a single space
      - Convert to lowercase

    The API performs its own fuzzy matching; we just ensure we don't send
    accidental double-spaces or mixed-case that could trip up exact-match logic.
    """
    return _WHITESPACE_RE.sub(" ", name.strip()).lower()


def _extract_match(result: dict[str, Any]) -> dict[str, Any]:
    """
    Normalise a single CSL result entry into a consistent shape.
    Unknown or missing fields are surfaced as None so callers don't need
    defensive key checks.
    """
    # addresses may be a list of dicts or an empty list
    addresses: list[dict[str, Any]] = result.get("addresses") or []

    # alt_names may be a list of strings
    alt_names: list[str] = result.get("alt_names") or []

    # programs may be a list of strings (e.g. ["UKRAINE-EO13685"])
    programs: list[str] = result.get("programs") or []

    return {
        "name": result.get("name"),
        "source": result.get("source"),
        "programs": programs,
        "score": result.get("score"),
        "addresses": addresses,
        "alt_names": alt_names,
        "start_date": result.get("start_date"),
        "end_date": result.get("end_date"),
    }


class ConsolidatedScreeningStep(BasePipelineStep):
    step_number = 2
    step_name = "Trade.gov Consolidated Screening List"

    async def run(self, intake: dict[str, Any], job_id: str) -> StepResult:
        legal_name: str = intake.get("legal_name", "").strip()
        if not legal_name:
            return StepResult(
                status="failed",
                error="intake missing required field: legal_name",
            )

        normalized_name = _normalize_name(legal_name)
        params: dict[str, Any] = {
            "name": normalized_name,
            "fuzzy_name": "true",
            "size": _RESULTS_LIMIT,
        }

        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                response = await client.get(_CSL_ENDPOINT, params=params)
                response.raise_for_status()
                payload: dict[str, Any] = response.json()
        except httpx.TimeoutException as exc:
            logger.error("[job=%s] CSL request timed out: %s", job_id, exc)
            return StepResult(status="failed", error=f"CSL request timed out: {exc}")
        except httpx.HTTPStatusError as exc:
            logger.error(
                "[job=%s] CSL HTTP error %s: %s",
                job_id,
                exc.response.status_code,
                exc.response.text[:500],
            )
            return StepResult(
                status="failed",
                error=f"CSL returned HTTP {exc.response.status_code}: {exc.response.text[:200]}",
            )
        except httpx.RequestError as exc:
            logger.error("[job=%s] CSL network error: %s", job_id, exc)
            return StepResult(status="failed", error=f"CSL network error: {exc}")
        except Exception as exc:  # noqa: BLE001
            logger.exception("[job=%s] Unexpected error in CSL step", job_id)
            return StepResult(status="failed", error=str(exc))

        raw_results: list[dict[str, Any]] = payload.get("results") or []
        total_returned: int = len(raw_results)

        matches = [_extract_match(r) for r in raw_results]

        if matches:
            screening_status = "REVIEW"
            message = (
                f"CSL screening flagged '{legal_name}' for REVIEW: "
                f"{total_returned} match(es) found across {_SOURCES_CHECKED} lists."
            )
            logger.warning(
                "[job=%s] CSL REVIEW — %d match(es) for '%s': sources=%s",
                job_id,
                total_returned,
                legal_name,
                [m["source"] for m in matches],
            )
        else:
            screening_status = "CLEAR"
            message = (
                f"CSL screening CLEAR for '{legal_name}': "
                f"no matches across {_SOURCES_CHECKED} lists."
            )
            logger.info("[job=%s] CSL CLEAR for '%s'", job_id, legal_name)

        return StepResult(
            status="complete",
            data={
                "screening_status": screening_status,
                "matches": matches,
                "sources_checked": _SOURCES_CHECKED,
                "source_names": _SOURCE_NAMES,
                "query_name": normalized_name,
                "total_matches_returned": total_returned,
            },
            message=message,
        )
