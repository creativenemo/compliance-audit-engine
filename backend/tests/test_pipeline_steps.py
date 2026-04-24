"""Unit tests for pipeline steps — offline (no network, no AWS)."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

EMBARK_INTAKE = {
    "legal_name": "Embark Aviation Corp",
    "domicile_state": "DE",
    "entity_type": "Corp",
    "employee_states": ["VA", "FL", "CO"],
    "business_nature": "Aviation consulting",
    "ecommerce_marketplace": False,
    "customer_types": ["B2B", "Government"],
    "annual_revenue": "1m_5m",
}


# ─────────────────────────────────────────────────────────────────────────────
# Step 1 — SAM.gov (skip when no API key)
# ─────────────────────────────────────────────────────────────────────────────

def test_sam_skips_without_api_key(monkeypatch):
    monkeypatch.delenv("SAM_GOV_API_KEY", raising=False)
    import asyncio

    from orchestrator.pipeline.step_01_sam import SamGovStep
    step = SamGovStep()
    result = asyncio.run(step.run(EMBARK_INTAKE, "job-001"))
    assert result.status == "skipped"


@pytest.mark.asyncio
async def test_sam_returns_complete_on_match(monkeypatch):
    monkeypatch.setenv("SAM_GOV_API_KEY", "fake-key")

    fake_entity = {
        "entityRegistration": {
            "legalBusinessName": "Embark Aviation Corp",
            "ueiSAM": "ABC123",
            "cageCode": "XY001",
            "registrationStatus": "Active",
            "exclusionStatusFlag": "N",
            "registrationExpirationDate": "2027-01-01",
        },
        "coreData": {"physicalAddress": {"stateOrProvinceCode": "DE"}},
        "assertions": {"goodsAndServices": {"naicsCode": [{"naicsCode": "488190"}]}},
    }

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"entityData": [fake_entity]}
    mock_resp.raise_for_status = MagicMock()

    from orchestrator.pipeline.step_01_sam import SamGovStep
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        step = SamGovStep()
        result = await step.run(EMBARK_INTAKE, "job-001")

    assert result.status == "complete"
    assert result.data["sam_registered"] is True
    assert result.data["uei_sam"] == "ABC123"
    assert result.data["finding"] is None  # not excluded


@pytest.mark.asyncio
async def test_sam_flags_excluded_entity(monkeypatch):
    monkeypatch.setenv("SAM_GOV_API_KEY", "fake-key")

    fake_entity = {
        "entityRegistration": {
            "legalBusinessName": "Bad Actor LLC",
            "ueiSAM": "ZZZ999",
            "cageCode": None,
            "registrationStatus": "Active",
            "exclusionStatusFlag": "Y",
            "registrationExpirationDate": None,
        },
        "coreData": {},
        "assertions": {},
    }

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"entityData": [fake_entity]}
    mock_resp.raise_for_status = MagicMock()

    from orchestrator.pipeline.step_01_sam import SamGovStep
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        step = SamGovStep()
        result = await step.run({"legal_name": "Bad Actor LLC"}, "job-002")

    assert result.status == "complete"
    assert result.data["finding"] == "EXCLUDED"


# ─────────────────────────────────────────────────────────────────────────────
# Step 2 — CSL
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_csl_clear_when_no_matches():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"results": []}
    mock_resp.raise_for_status = MagicMock()

    from orchestrator.pipeline.step_02_csl import ConsolidatedScreeningStep
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        step = ConsolidatedScreeningStep()
        result = await step.run(EMBARK_INTAKE, "job-001")

    assert result.status == "complete"
    assert result.data["screening_status"] == "CLEAR"
    assert result.data["sources_checked"] == 13


@pytest.mark.asyncio
async def test_csl_review_when_matches():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "results": [
            {
                "name": "Embark Aviation Corp",
                "source": "SDN",
                "programs": ["IRAN"],
                "score": 0.92,
                "addresses": [],
                "alt_names": [],
                "start_date": "2020-01-01",
                "end_date": None,
            }
        ]
    }
    mock_resp.raise_for_status = MagicMock()

    from orchestrator.pipeline.step_02_csl import ConsolidatedScreeningStep
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        step = ConsolidatedScreeningStep()
        result = await step.run(EMBARK_INTAKE, "job-001")

    assert result.status == "complete"
    assert result.data["screening_status"] == "REVIEW"
    assert len(result.data["matches"]) == 1


# ─────────────────────────────────────────────────────────────────────────────
# Step 3 — OFAC
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ofac_skips_when_no_index():
    from orchestrator.pipeline.step_03_ofac import OfacSdnStep
    with patch("orchestrator.pipeline.step_03_ofac.get_index_json", return_value=None):
        step = OfacSdnStep()
        result = await step.run(EMBARK_INTAKE, "job-001")
    assert result.status == "skipped"


@pytest.mark.asyncio
async def test_ofac_clear_for_clean_entity():
    sdn_payload = json.dumps({
        "sdnList": {
            "sdnEntry": [
                {
                    "lastName": "Totally Different Corp",
                    "akaList": {},
                }
            ]
        }
    }).encode()

    from orchestrator.pipeline.step_03_ofac import OfacSdnStep
    with patch("orchestrator.pipeline.step_03_ofac.get_index_json", return_value=sdn_payload):
        step = OfacSdnStep()
        result = await step.run(EMBARK_INTAKE, "job-001")

    assert result.status == "complete"
    assert result.data["ofac_status"] == "CLEAR"


@pytest.mark.asyncio
async def test_ofac_match_for_sanctioned_entity():
    sdn_payload = json.dumps({
        "sdnList": {
            "sdnEntry": [
                {
                    "lastName": "Embark Aviation Corp",
                    "akaList": {},
                }
            ]
        }
    }).encode()

    from orchestrator.pipeline.step_03_ofac import OfacSdnStep
    with patch("orchestrator.pipeline.step_03_ofac.get_index_json", return_value=sdn_payload):
        step = OfacSdnStep()
        result = await step.run(EMBARK_INTAKE, "job-001")

    assert result.status == "complete"
    assert result.data["ofac_status"] in ("MATCH", "REVIEW")


# ─────────────────────────────────────────────────────────────────────────────
# Step 4 — LEIE
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_leie_skips_when_no_index():
    from orchestrator.pipeline.step_04_leie import LeieStep
    with patch("orchestrator.pipeline.step_04_leie.get_index_json", return_value=None):
        step = LeieStep()
        result = await step.run(EMBARK_INTAKE, "job-001")
    assert result.status == "skipped"


@pytest.mark.asyncio
async def test_leie_clear_for_clean_entity():
    leie_payload = json.dumps([
        {"BUSNAME": "Totally Different Medical LLC", "NPI": "123", "EXCLTYPE": "1128b(4)", "REINDATE": ""}
    ]).encode()

    from orchestrator.pipeline.step_04_leie import LeieStep
    with patch("orchestrator.pipeline.step_04_leie.get_index_json", return_value=leie_payload):
        step = LeieStep()
        result = await step.run(EMBARK_INTAKE, "job-001")

    assert result.status == "complete"
    assert result.data["leie_status"] == "CLEAR"


# ─────────────────────────────────────────────────────────────────────────────
# Step 6 — IRS / ProPublica (not found = for-profit path)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_irs_not_found_for_forprofit():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"organizations": []}
    mock_resp.raise_for_status = MagicMock()

    from orchestrator.pipeline.step_06_irs import IrsTaxExemptStep
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        step = IrsTaxExemptStep()
        result = await step.run(EMBARK_INTAKE, "job-001")

    assert result.status == "complete"
    assert result.data["nonprofit_status"] == "Not Found"


# ─────────────────────────────────────────────────────────────────────────────
# OFAC / LEIE name normalisation helpers
# ─────────────────────────────────────────────────────────────────────────────

def test_ofac_normalize_strips_suffix():
    from orchestrator.pipeline.step_03_ofac import normalize_name
    assert normalize_name("Embark Aviation Corp") == "embark aviation"
    assert normalize_name("Acme, LLC") == "acme"


def test_leie_normalize_strips_suffix():
    from orchestrator.pipeline.step_04_leie import normalize_name
    assert normalize_name("Best Health LLC") == "best health"


# ─────────────────────────────────────────────────────────────────────────────
# IRS match score helper
# ─────────────────────────────────────────────────────────────────────────────

def test_irs_match_score_exact():
    from orchestrator.pipeline.step_06_irs import _match_score
    assert _match_score("Red Cross Foundation", "Red Cross Foundation") == 100


def test_irs_match_score_partial():
    from orchestrator.pipeline.step_06_irs import _match_score
    score = _match_score("Aviation Safety Fund", "Aviation Safety")
    assert 50 < score < 100


def test_irs_match_score_unrelated():
    from orchestrator.pipeline.step_06_irs import _match_score
    score = _match_score("Apple Inc", "Boeing Corp")
    assert score < 30
