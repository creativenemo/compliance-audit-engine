"""
Index Refresher Lambda — Sprint 2

Triggered by EventBridge:
- Nightly (00:00 UTC): download OFAC SDN JSON → s3://compliance-indexes/ofac/sdn_latest.json
- Monthly (1st, 00:00 UTC): download HHS OIG LEIE CSV → convert to JSON →
  s3://compliance-indexes/leie/leie_latest.json

OFAC source: https://www.treasury.gov/ofac/downloads/sdn.json
LEIE source: https://oig.hhs.gov/exclusions/downloadables/UPDATED.csv
"""
import csv
import io
import json
import logging
import urllib.request
from typing import Any

from app.services.s3 import put_index_json

logger = logging.getLogger(__name__)

OFAC_SDN_URL = "https://www.treasury.gov/ofac/downloads/sdn.json"
LEIE_CSV_URL = "https://oig.hhs.gov/exclusions/downloadables/UPDATED.csv"


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    detail_type = event.get("detail-type", "")
    logger.info(
        "Index refresher triggered: source=%s detail-type=%s",
        event.get("source", ""),
        detail_type,
    )

    if "leie" in detail_type.lower():
        _refresh_leie()

    _refresh_ofac()  # always refresh OFAC

    return {"statusCode": 200}


def _refresh_ofac() -> None:
    """Download the OFAC SDN JSON from Treasury and store it in S3."""
    logger.info("Downloading OFAC SDN list from %s", OFAC_SDN_URL)
    try:
        with urllib.request.urlopen(OFAC_SDN_URL, timeout=120) as response:
            data: bytes = response.read()
    except Exception as exc:
        logger.error("Failed to download OFAC SDN list: %s", exc)
        raise

    # Validate that it parses before storing so we never overwrite with garbage
    try:
        parsed = json.loads(data)
        entries = parsed.get("sdnList", {}).get("sdnEntry", [])
        entry_count = len(entries) if isinstance(entries, list) else 0
    except (json.JSONDecodeError, AttributeError) as exc:
        logger.error("OFAC SDN response is not valid JSON: %s", exc)
        raise

    put_index_json("ofac/sdn_latest.json", data)
    logger.info("OFAC SDN index updated — %d entries stored", entry_count)


def _refresh_leie() -> None:
    """Download the HHS OIG LEIE CSV, convert to JSON, and store in S3."""
    logger.info("Downloading LEIE CSV from %s", LEIE_CSV_URL)
    try:
        with urllib.request.urlopen(LEIE_CSV_URL, timeout=120) as response:
            raw_bytes: bytes = response.read()
    except Exception as exc:
        logger.error("Failed to download LEIE CSV: %s", exc)
        raise

    try:
        # The CSV is UTF-8; fall back to latin-1 for any stray Windows-1252 chars
        try:
            text = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = raw_bytes.decode("latin-1")

        reader = csv.DictReader(io.StringIO(text))
        records: list[dict[str, str]] = [row for row in reader]
    except Exception as exc:
        logger.error("Failed to parse LEIE CSV: %s", exc)
        raise

    payload: bytes = json.dumps(records).encode("utf-8")
    put_index_json("leie/leie_latest.json", payload)
    logger.info("LEIE index updated — %d records stored", len(records))
