"""
IRS Nonprofit Status + ProPublica Nonprofit Explorer — Sprint 3

Primary data source:
  ProPublica Nonprofit Explorer API (no auth required)
    Search:  https://projects.propublica.org/nonprofits/api/v2/search.json
    Detail:  https://projects.propublica.org/nonprofits/api/v2/organizations/{ein}.json

IRS EO BMF (https://apps.irs.gov/app/eos/) is skipped — the endpoint is
unreliable for programmatic access; ProPublica is preferred.

Name matching uses a simple normalised-token overlap ratio (no third-party
fuzzy-matching library required) with a threshold of 80 / 100.

Returns nonprofit_status="Not Found" (status="complete") when the organisation
is not in the IRS tax-exempt registry — the expected result for for-profit
entities.
"""

from __future__ import annotations

import logging
import re
import urllib.parse
from typing import Any

import httpx

from .base import BasePipelineStep, StepResult

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(10.0)
_MATCH_THRESHOLD = 80  # out of 100

# IRS subsection_code → human-readable label
_SUBSECTION_LABELS: dict[int, str] = {
    2: "501(c)(2) Title-Holding Corporation",
    3: "501(c)(3) Public Charity / Private Foundation",
    4: "501(c)(4) Social Welfare Organization",
    5: "501(c)(5) Labor / Agricultural Organization",
    6: "501(c)(6) Business League / Trade Association",
    7: "501(c)(7) Social / Recreational Club",
    8: "501(c)(8) Fraternal Beneficiary Society",
    10: "501(c)(10) Domestic Fraternal Society",
    12: "501(c)(12) Benevolent Life Insurance Association",
    13: "501(c)(13) Cemetery Company",
    14: "501(c)(14) Credit Union",
    19: "501(c)(19) Veterans Organization",
    25: "501(c)(25) Title-Holding Corporation (Multiple Parents)",
    27: "501(c)(27) State-Sponsored Workers' Compensation Reinsurance",
    92: "501(c)(92) ABLE Account Program",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True)


def _normalise(text: str) -> set[str]:
    """Lower-case, strip punctuation, return non-trivial tokens."""
    stopwords = {"the", "a", "an", "of", "and", "or", "for", "inc", "llc",
                 "ltd", "corp", "co", "company", "corporation", "foundation"}
    tokens = re.split(r"[\W_]+", text.lower())
    return {t for t in tokens if t and t not in stopwords}


def _match_score(query: str, candidate: str) -> int:
    """
    Simple token-overlap similarity, 0–100.
    Uses Jaccard-style intersection / union across normalised token sets.
    """
    q_tokens = _normalise(query)
    c_tokens = _normalise(candidate)
    if not q_tokens or not c_tokens:
        return 0
    intersection = q_tokens & c_tokens
    union = q_tokens | c_tokens
    return int(100 * len(intersection) / len(union))


def _subsection_label(code: int | None) -> str | None:
    if code is None:
        return None
    return _SUBSECTION_LABELS.get(code, f"501(c)({code})")


# ---------------------------------------------------------------------------
# API calls
# ---------------------------------------------------------------------------

async def _propublica_search(
    client: httpx.AsyncClient,
    legal_name: str,
    domicile_state: str | None,
) -> list[dict[str, Any]]:
    """Search ProPublica for organisations matching legal_name."""
    params: dict[str, str] = {"q": legal_name}
    if domicile_state:
        params["state[id]"] = domicile_state.upper()
    # ntee[id] left blank — we don't want to filter by NTEE code
    url = (
        "https://projects.propublica.org/nonprofits/api/v2/search.json?"
        + urllib.parse.urlencode(params)
    )
    try:
        resp = await client.get(url)
        resp.raise_for_status()
        payload = resp.json()
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "ProPublica search HTTP %s for %r", exc.response.status_code, legal_name
        )
        return []
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "ProPublica search error (%s): %s", type(exc).__name__, exc
        )
        return []

    orgs = payload.get("organizations", [])
    return orgs if isinstance(orgs, list) else []


async def _propublica_detail(
    client: httpx.AsyncClient, ein: str
) -> dict[str, Any] | None:
    """Fetch the detailed organisation record including 990 filings."""
    url = f"https://projects.propublica.org/nonprofits/api/v2/organizations/{ein}.json"
    try:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "ProPublica detail HTTP %s for EIN %s", exc.response.status_code, ein
        )
        return None
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "ProPublica detail error for EIN %s (%s): %s",
            ein, type(exc).__name__, exc,
        )
        return None


# ---------------------------------------------------------------------------
# Result builders
# ---------------------------------------------------------------------------

def _not_found_result(reason: str = "Consistent with for-profit entity type") -> StepResult:
    return StepResult(
        status="complete",
        data={
            "nonprofit_status": "Not Found",
            "ein": None,
            "subsection_code": None,
            "subsection_label": None,
            "most_recent_990_year": None,
            "total_revenue": None,
            "total_assets": None,
            "note": reason,
        },
        message="Organisation not found in IRS tax-exempt registry — " + reason,
    )


def _parse_numeric(value: Any) -> float | None:
    """Safely cast ProPublica financial fields (may be int, float, str, or None)."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _build_found_result(
    org_summary: dict[str, Any],
    detail: dict[str, Any] | None,
) -> StepResult:
    """Construct the StepResult when we have a confirmed match."""
    ein: str | None = str(org_summary.get("ein", "")) or None

    # Prefer detail-level fields when available
    detail_org: dict[str, Any] = (detail or {}).get("organization", {})
    subsection_raw = (
        detail_org.get("subsection_code")
        or org_summary.get("subsection_code")
    )
    try:
        subsection_code: int | None = int(subsection_raw) if subsection_raw is not None else None
    except (TypeError, ValueError):
        subsection_code = None

    name: str | None = (
        detail_org.get("name")
        or org_summary.get("name")
    )

    # Most recent 990 from detail filings_with_data
    filings: list[dict[str, Any]] = (detail or {}).get("filings_with_data", [])
    most_recent_filing: dict[str, Any] = filings[0] if filings else {}

    # ProPublica 990 field names
    total_revenue = _parse_numeric(
        most_recent_filing.get("totrevenue")
        or org_summary.get("revenue_amount")
    )
    total_assets = _parse_numeric(
        most_recent_filing.get("totassetsend")
        or org_summary.get("asset_amount")
    )
    filing_year_raw = (
        most_recent_filing.get("tax_prd_yr")
        or most_recent_filing.get("tax_prd")
        or org_summary.get("filing_year")
    )
    try:
        most_recent_990_year: int | None = int(str(filing_year_raw)[:4]) if filing_year_raw else None
    except (TypeError, ValueError):
        most_recent_990_year = None

    label = _subsection_label(subsection_code)
    note = (
        f"{label} — EIN {ein}" if label and ein
        else f"EIN {ein}" if ein
        else "Nonprofit record found"
    )

    data: dict[str, Any] = {
        "nonprofit_status": "Found",
        "ein": ein,
        "subsection_code": subsection_code,
        "subsection_label": label,
        "most_recent_990_year": most_recent_990_year,
        "total_revenue": total_revenue,
        "total_assets": total_assets,
        "note": note,
    }

    return StepResult(
        status="complete",
        data=data,
        message=f"IRS tax-exempt record found: {name} ({label or 'subsection unknown'})",
    )


# ---------------------------------------------------------------------------
# Step class
# ---------------------------------------------------------------------------

class IrsTaxExemptStep(BasePipelineStep):
    step_number = 6
    step_name = "IRS Nonprofit & Tax-Exempt Status"

    async def run(self, intake: dict[str, Any], job_id: str) -> StepResult:
        legal_name: str = intake.get("legal_name", "").strip()
        if not legal_name:
            return StepResult(
                status="failed",
                data={},
                message="Missing required intake field: legal_name",
                error="legal_name is empty",
            )

        domicile_state: str | None = intake.get("domicile_state") or None
        logger.info(
            "[%s] IRS/ProPublica lookup for %r (state=%s)",
            job_id, legal_name, domicile_state,
        )

        async with _build_client() as client:
            # ---------------------------------------------------------------- #
            # 1. Search ProPublica
            # ---------------------------------------------------------------- #
            orgs = await _propublica_search(client, legal_name, domicile_state)

            # ---------------------------------------------------------------- #
            # 2. Find best fuzzy match (score >= threshold)
            # ---------------------------------------------------------------- #
            best_org: dict[str, Any] | None = None
            best_score = 0
            for org in orgs:
                candidate_name: str = org.get("name", "")
                score = _match_score(legal_name, candidate_name)
                logger.debug(
                    "[%s] Candidate %r score=%d", job_id, candidate_name, score
                )
                if score > best_score:
                    best_score = score
                    best_org = org

            if best_org is None or best_score < _MATCH_THRESHOLD:
                logger.info(
                    "[%s] No ProPublica match above threshold (best=%d)",
                    job_id, best_score,
                )
                return _not_found_result()

            logger.info(
                "[%s] ProPublica match: %r (score=%d)",
                job_id, best_org.get("name"), best_score,
            )

            # ---------------------------------------------------------------- #
            # 3. Fetch detailed 990 data
            # ---------------------------------------------------------------- #
            ein_raw = best_org.get("ein")
            detail: dict[str, Any] | None = None
            if ein_raw:
                # ProPublica EINs may be stored as int or str; normalise to str
                ein_str = str(int(ein_raw)) if isinstance(ein_raw, (int, float)) else str(ein_raw)
                detail = await _propublica_detail(client, ein_str)

        return _build_found_result(best_org, detail)
