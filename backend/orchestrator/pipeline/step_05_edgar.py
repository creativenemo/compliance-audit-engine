"""
SEC EDGAR Full-Text Search + Company Lookup — Sprint 3

Endpoints used:
  1. Full-text search (EFTS):
       https://efts.sec.gov/LATEST/search-index?q="<legal_name>"&dateRange=custom&startdt=2018-01-01
  2. Company / CIK search:
       https://efts.sec.gov/LATEST/search-index?q="<legal_name>"&category=form-type&forms=10-K,10-Q,8-K
       https://www.sec.gov/cgi-bin/browse-edgar?company=<legal_name>&...&output=atom  (Atom fallback)
  3. Submissions JSON (requires CIK):
       https://data.sec.gov/submissions/CIK{cik:010d}.json

All requests carry the User-Agent required by the SEC fair-use policy:
  "Compliance Audit Engine compliance@example.com"

Returns edgar_found=False (status="complete") when the company is not registered
with the SEC — that is the expected result for private companies.
"""

from __future__ import annotations

import logging
import re
import urllib.parse
from typing import Any

import httpx

from .base import BasePipelineStep, StepResult

logger = logging.getLogger(__name__)

_USER_AGENT = "Compliance Audit Engine compliance@example.com"
_TIMEOUT = httpx.Timeout(10.0)

# Form types that indicate SEC enforcement / administrative proceedings
_ENFORCEMENT_FORMS = frozenset({"AP", "AP-W", "33-", "34-", "AP-NS"})

# How many recent filings to surface for the enforcement-action scan
_FILING_SCAN_LIMIT = 50


def _build_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        headers={"User-Agent": _USER_AGENT},
        timeout=_TIMEOUT,
        follow_redirects=True,
    )


def _quote_name(legal_name: str) -> str:
    """Wrap the name in escaped double-quotes and percent-encode the whole thing."""
    return urllib.parse.quote(f'"{legal_name}"', safe="")


async def _fulltext_search(
    client: httpx.AsyncClient, legal_name: str
) -> list[dict[str, Any]]:
    """
    Step 1 — EFTS full-text search.
    Returns the raw list of hit _source dicts (may be empty).
    """
    url = (
        "https://efts.sec.gov/LATEST/search-index"
        f"?q={_quote_name(legal_name)}"
        "&dateRange=custom&startdt=2018-01-01"
        "&hits.hits._source=period_of_report,file_date,form_type,entity_name,file_num"
    )
    try:
        resp = await client.get(url)
        resp.raise_for_status()
        payload = resp.json()
    except httpx.HTTPStatusError as exc:
        logger.warning("EFTS full-text search HTTP %s: %s", exc.response.status_code, url)
        return []
    except Exception as exc:  # noqa: BLE001
        logger.warning("EFTS full-text search error (%s): %s", type(exc).__name__, exc)
        return []

    hits = (
        payload.get("hits", {})
        .get("hits", [])
    )
    return [h.get("_source", {}) for h in hits if isinstance(h, dict)]


async def _find_cik_via_efts(
    client: httpx.AsyncClient, legal_name: str
) -> str | None:
    """
    Step 2a — search EFTS with form filter to locate a CIK.
    Returns the CIK as a plain string (no leading zeros) or None.
    """
    url = (
        "https://efts.sec.gov/LATEST/search-index"
        f"?q={_quote_name(legal_name)}"
        "&category=form-type&forms=10-K,10-Q,8-K"
    )
    try:
        resp = await client.get(url)
        resp.raise_for_status()
        payload = resp.json()
    except Exception as exc:  # noqa: BLE001
        logger.warning("EFTS CIK search error (%s): %s", type(exc).__name__, exc)
        return None

    hits = payload.get("hits", {}).get("hits", [])
    for hit in hits:
        src = hit.get("_source", {})
        # entity_id / file_num fields sometimes carry the CIK
        entity_id = src.get("entity_id") or src.get("file_num") or ""
        cik_match = re.search(r"\d+", str(entity_id))
        if cik_match:
            return cik_match.group()
    return None


async def _find_cik_via_atom(
    client: httpx.AsyncClient, legal_name: str
) -> str | None:
    """
    Step 2b — EDGAR company search (Atom feed) to locate a CIK.
    """
    encoded_name = urllib.parse.quote(legal_name)
    url = (
        "https://www.sec.gov/cgi-bin/browse-edgar"
        f"?company={encoded_name}"
        "&CIK=&type=&dateb=&owner=include&count=10&search_text=&action=getcompany&output=atom"
    )
    try:
        resp = await client.get(url)
        resp.raise_for_status()
        text = resp.text
    except Exception as exc:  # noqa: BLE001
        logger.warning("EDGAR Atom feed error (%s): %s", type(exc).__name__, exc)
        return None

    # The Atom feed encodes the CIK inside <company-info> or <id> elements.
    # Pattern: /cgi-bin/browse-edgar?action=getcompany&CIK=0000123456&...
    cik_match = re.search(r"CIK=(\d+)", text)
    if cik_match:
        return cik_match.group(1).lstrip("0") or "0"
    return None


async def _get_submissions(
    client: httpx.AsyncClient, cik: str
) -> dict[str, Any] | None:
    """
    Step 3 — fetch the submissions JSON for a known CIK.
    Returns the parsed JSON dict or None on error.
    """
    try:
        cik_int = int(cik)
    except ValueError:
        logger.warning("Invalid CIK value: %r", cik)
        return None

    url = f"https://data.sec.gov/submissions/CIK{cik_int:010d}.json"
    try:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            logger.info("Submissions not found for CIK %s (404)", cik)
        else:
            logger.warning(
                "Submissions HTTP %s for CIK %s", exc.response.status_code, cik
            )
        return None
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Submissions fetch error for CIK %s (%s): %s",
            cik, type(exc).__name__, exc,
        )
        return None


def _extract_submissions_data(
    submissions: dict[str, Any],
) -> dict[str, Any]:
    """
    Parse the submissions JSON into the fields we care about.
    Returns a flat dict ready to be merged into step data.
    """
    name: str | None = submissions.get("name")
    sic: str | None = str(submissions.get("sic", "")) or None
    sic_description: str | None = submissions.get("sicDescription")
    state_of_incorporation: str | None = submissions.get("stateOfIncorporation")

    recent: dict[str, Any] = submissions.get("filings", {}).get("recent", {})
    forms: list[str] = recent.get("form", [])
    dates: list[str] = recent.get("filingDate", [])
    accessions: list[str] = recent.get("accessionNumber", [])

    recent_filings_count = len(forms)

    # Find the most recent 10-K
    latest_10k_date: str | None = None
    for form, date in zip(forms, dates, strict=False):
        if form in ("10-K", "10-K/A"):
            latest_10k_date = date
            break  # list is newest-first

    # Scan for enforcement actions
    enforcement_actions: list[dict[str, Any]] = []
    scan_limit = min(_FILING_SCAN_LIMIT, len(forms))
    for i in range(scan_limit):
        form = forms[i] if i < len(forms) else ""
        # Match exact tokens or prefix (e.g. "33-12345")
        if any(form == ef or form.startswith(ef) for ef in _ENFORCEMENT_FORMS):
            enforcement_actions.append(
                {
                    "form_type": form,
                    "date": dates[i] if i < len(dates) else None,
                    "accession_number": accessions[i] if i < len(accessions) else None,
                }
            )

    return {
        "company_name": name,
        "sic_code": sic,
        "sic_description": sic_description,
        "state_of_incorporation": state_of_incorporation,
        "latest_10k_date": latest_10k_date,
        "recent_filings_count": recent_filings_count,
        "enforcement_actions": enforcement_actions,
    }


class SecEdgarStep(BasePipelineStep):
    step_number = 5
    step_name = "SEC EDGAR Filing Check"

    async def run(self, intake: dict[str, Any], job_id: str) -> StepResult:
        legal_name: str = intake.get("legal_name", "").strip()
        if not legal_name:
            return StepResult(
                status="failed",
                data={},
                message="Missing required intake field: legal_name",
                error="legal_name is empty",
            )

        logger.info("[%s] SEC EDGAR lookup for %r", job_id, legal_name)

        async with _build_client() as client:
            # ------------------------------------------------------------------ #
            # Step 1: full-text search — collect recent filings for context
            # ------------------------------------------------------------------ #
            ft_hits = await _fulltext_search(client, legal_name)

            # ------------------------------------------------------------------ #
            # Step 2: resolve CIK — try EFTS first, then Atom feed fallback
            # ------------------------------------------------------------------ #
            cik: str | None = await _find_cik_via_efts(client, legal_name)
            if not cik:
                cik = await _find_cik_via_atom(client, legal_name)

            # ------------------------------------------------------------------ #
            # Step 3: fetch detailed submissions data when we have a CIK
            # ------------------------------------------------------------------ #
            submissions_data: dict[str, Any] = {}
            source_url = (
                f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json"
                if cik and cik.isdigit()
                else "https://efts.sec.gov/LATEST/search-index"
            )

            if cik:
                submissions = await _get_submissions(client, cik)
                if submissions:
                    submissions_data = _extract_submissions_data(submissions)

        edgar_found = bool(cik or ft_hits)

        if edgar_found:
            data: dict[str, Any] = {
                "edgar_found": True,
                "cik": cik,
                "company_name": submissions_data.get("company_name"),
                "sic_code": submissions_data.get("sic_code"),
                "sic_description": submissions_data.get("sic_description"),
                "state_of_incorporation": submissions_data.get("state_of_incorporation"),
                "latest_10k_date": submissions_data.get("latest_10k_date"),
                "recent_filings_count": submissions_data.get("recent_filings_count", len(ft_hits)),
                "enforcement_actions": submissions_data.get("enforcement_actions", []),
                "source_url": source_url,
            }
            message = f"EDGAR record found — CIK {cik}" if cik else "EDGAR filings found (no CIK resolved)"
        else:
            data = {
                "edgar_found": False,
                "cik": None,
                "company_name": None,
                "sic_code": None,
                "sic_description": None,
                "state_of_incorporation": None,
                "latest_10k_date": None,
                "recent_filings_count": 0,
                "enforcement_actions": [],
                "source_url": "https://efts.sec.gov/LATEST/search-index",
                "note": "Consistent with private company status",
            }
            message = "No EDGAR record found — consistent with private company status"

        return StepResult(status="complete", data=data, message=message)
