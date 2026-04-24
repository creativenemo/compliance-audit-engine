"""
Index Refresher Lambda — Sprint 2

Triggered by EventBridge:
- Nightly (00:00 UTC): download OFAC SDN JSON → s3://compliance-indexes/ofac/sdn_latest.json
- Monthly (1st, 00:00 UTC): download HHS OIG LEIE CSV → convert to JSON →
  s3://compliance-indexes/leie/leie_latest.json

OFAC source: https://www.treasury.gov/ofac/downloads/sdn.json
LEIE source: https://oig.hhs.gov/exclusions/downloadables/UPDATED.csv
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    source = event.get("source", "")
    detail_type = event.get("detail-type", "")

    logger.info("Index refresher triggered: source=%s detail-type=%s", source, detail_type)

    # Sprint 2: implement OFAC + LEIE download logic
    raise NotImplementedError("Index refresher — implement in Sprint 2")
