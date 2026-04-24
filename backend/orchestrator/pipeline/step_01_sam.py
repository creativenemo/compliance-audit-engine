"""
SAM.gov Entity Management API v3 — Sprint 2

Endpoint: https://api.sam.gov/entity-information/v3/entities
Auth: free-tier API key obtained at sam.gov (env: SAM_GOV_API_KEY)

Query strategy:
  1. legalBusinessName=<legal_name>&samRegistered=Yes  (registered entities only)
  2. legalBusinessName=<legal_name>                    (fallback — includes non-registered)

Extracted fields:
  - legalBusinessName, ueiSAM, cageCode
  - registrationStatus (Active / Inactive)
  - exclusionStatusFlag (Y = debarred / excluded)
  - registrationExpirationDate
  - physicalAddress.stateOrProvinceCode
  - naicsCode (first entry from goodsAndServices)

Debarment rule:
  exclusionStatusFlag == 'Y'  →  finding = EXCLUDED
"""

import logging
import os
from typing import Any

import httpx

from .base import BasePipelineStep, StepResult

logger = logging.getLogger(__name__)

_SAM_ENDPOINT = "https://api.sam.gov/entity-information/v3/entities"

# Timeout budget: connect 10 s, total read 30 s (SAM.gov can be slow)
_TIMEOUT = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=5.0)

# SAM.gov returns paginated JSON; we only need the first entity match.
_DEFAULT_PARAMS: dict[str, str | int] = {
    "includeSections": "entityRegistration,coreData,assertions",
    "page": 0,
    "size": 1,
}


def _extract_entity(entity: dict[str, Any]) -> dict[str, Any]:
    """Pull the fields we care about from a single entityData entry."""
    reg = entity.get("entityRegistration") or {}
    core = entity.get("coreData") or {}
    assertions = entity.get("assertions") or {}

    # Physical address is nested under coreData
    phys_addr = (core.get("physicalAddress") or {})

    # NAICS codes live inside assertions → goodsAndServices → naicsCode (list of dicts)
    goods = assertions.get("goodsAndServices") or {}
    naics_list = goods.get("naicsCode") or []
    # Each entry is a dict with a "naicsCode" key; grab the first
    first_naics: str | None = None
    if naics_list and isinstance(naics_list[0], dict):
        first_naics = naics_list[0].get("naicsCode")
    elif naics_list and isinstance(naics_list[0], str):
        first_naics = naics_list[0]

    return {
        "legal_business_name": reg.get("legalBusinessName"),
        "uei_sam": reg.get("ueiSAM"),
        "cage_code": reg.get("cageCode"),
        "registration_status": reg.get("registrationStatus"),
        "exclusion_status_flag": reg.get("exclusionStatusFlag"),
        "registration_expiration_date": reg.get("registrationExpirationDate"),
        "state_or_province_code": phys_addr.get("stateOrProvinceCode"),
        "naics_code": first_naics,
    }


class SamGovStep(BasePipelineStep):
    step_number = 1
    step_name = "SAM.gov Entity Lookup"

    async def run(self, intake: dict[str, Any], job_id: str) -> StepResult:
        api_key: str = os.environ.get("SAM_GOV_API_KEY", "").strip()

        if not api_key:
            logger.warning(
                "[job=%s] SAM_GOV_API_KEY is not set — skipping SAM.gov lookup",
                job_id,
            )
            return StepResult(
                status="skipped",
                data={"sam_registered": False, "skip_reason": "SAM_GOV_API_KEY not configured"},
                message="SAM_GOV_API_KEY environment variable is not set; step skipped.",
            )

        legal_name: str = intake.get("legal_name", "").strip()
        if not legal_name:
            return StepResult(
                status="failed",
                error="intake missing required field: legal_name",
            )

        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                result_data, source_url = await self._query(client, api_key, legal_name, job_id)
        except httpx.TimeoutException as exc:
            logger.error("[job=%s] SAM.gov request timed out: %s", job_id, exc)
            return StepResult(status="failed", error=f"SAM.gov request timed out: {exc}")
        except httpx.HTTPStatusError as exc:
            logger.error(
                "[job=%s] SAM.gov HTTP error %s: %s",
                job_id,
                exc.response.status_code,
                exc.response.text[:500],
            )
            return StepResult(
                status="failed",
                error=f"SAM.gov returned HTTP {exc.response.status_code}: {exc.response.text[:200]}",
            )
        except httpx.RequestError as exc:
            logger.error("[job=%s] SAM.gov network error: %s", job_id, exc)
            return StepResult(status="failed", error=f"SAM.gov network error: {exc}")
        except Exception as exc:  # noqa: BLE001
            logger.exception("[job=%s] Unexpected error in SAM.gov step", job_id)
            return StepResult(status="failed", error=str(exc))

        result_data["source_url"] = source_url

        # Debarment / exclusion finding
        exclusion_flag = result_data.get("exclusion_status_flag")
        if exclusion_flag == "Y":
            result_data["finding"] = "EXCLUDED"
            message = (
                f"Entity '{legal_name}' is flagged as EXCLUDED on SAM.gov "
                f"(exclusionStatusFlag=Y). Debarment review required."
            )
            logger.warning("[job=%s] SAM.gov EXCLUDED flag for '%s'", job_id, legal_name)
        else:
            result_data["finding"] = None
            message = f"SAM.gov lookup complete for '{legal_name}'."

        return StepResult(status="complete", data=result_data, message=message)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _query(
        self,
        client: httpx.AsyncClient,
        api_key: str,
        legal_name: str,
        job_id: str,
    ) -> tuple[dict[str, Any], str]:
        """
        Two-pass query:
          Pass 1: samRegistered=Yes  (prefer actively registered entities)
          Pass 2: no samRegistered filter (catch entities not currently registered)

        Returns (extracted_data_dict, source_url_used).
        """
        base_params: dict[str, Any] = {
            **_DEFAULT_PARAMS,
            "api_key": api_key,
            "legalBusinessName": legal_name,
        }

        # Pass 1 — registered entities only
        params_registered = {**base_params, "samRegistered": "Yes"}
        url_registered = _build_url_for_logging(params_registered)
        logger.info("[job=%s] SAM.gov pass-1 query: %s", job_id, url_registered)

        response = await client.get(_SAM_ENDPOINT, params=params_registered)
        response.raise_for_status()
        payload = response.json()

        entity_data: list[dict[str, Any]] = (payload.get("entityData") or [])

        if entity_data:
            logger.info(
                "[job=%s] SAM.gov pass-1 found %d entity(ies)",
                job_id,
                len(entity_data),
            )
            extracted = _extract_entity(entity_data[0])
            extracted["sam_registered"] = True
            extracted["search_pass"] = 1
            return extracted, url_registered

        # Pass 2 — broader search (no samRegistered filter)
        logger.info(
            "[job=%s] SAM.gov pass-1 returned 0 results; falling back to pass-2",
            job_id,
        )
        url_broad = _build_url_for_logging(base_params)
        logger.info("[job=%s] SAM.gov pass-2 query: %s", job_id, url_broad)

        response2 = await client.get(_SAM_ENDPOINT, params=base_params)
        response2.raise_for_status()
        payload2 = response2.json()
        entity_data2: list[dict[str, Any]] = (payload2.get("entityData") or [])

        if entity_data2:
            logger.info(
                "[job=%s] SAM.gov pass-2 found %d entity(ies)",
                job_id,
                len(entity_data2),
            )
            extracted2 = _extract_entity(entity_data2[0])
            extracted2["sam_registered"] = False
            extracted2["search_pass"] = 2
            return extracted2, url_broad

        # Not found in either pass
        logger.info("[job=%s] SAM.gov: entity '%s' not found", job_id, legal_name)
        return {
            "sam_registered": False,
            "search_pass": 2,
            "legal_business_name": None,
            "uei_sam": None,
            "cage_code": None,
            "registration_status": "Not Found",
            "exclusion_status_flag": None,
            "registration_expiration_date": None,
            "state_or_province_code": None,
            "naics_code": None,
        }, url_broad


def _build_url_for_logging(params: dict[str, Any]) -> str:
    """Return a redacted URL string suitable for logs (API key masked)."""
    safe_params = {
        k: ("***" if k == "api_key" else v)
        for k, v in params.items()
    }
    request = httpx.Request("GET", _SAM_ENDPOINT, params=safe_params)
    return str(request.url)
