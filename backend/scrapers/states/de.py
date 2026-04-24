"""
Delaware Division of Corporations — Sprint 4

SOS URL: https://icis.corp.delaware.gov/ecorp/entitysearch/namesearch.aspx
Entity search by name → click result → extract status, agent, formation date.

Delaware is domicile for ~70% of US corporations.
Annual report due: March 1 (corporations), June 1 (LLCs).
"""
from scrapers.base import BaseSosScraper, EntityRegistration, ForeignQualification


class DelawareScraper(BaseSosScraper):
    state_code = "DE"
    state_name = "Delaware"
    sos_url = "https://icis.corp.delaware.gov/ecorp/entitysearch/namesearch.aspx"

    async def scrape_entity(self, legal_name: str) -> EntityRegistration:
        raise NotImplementedError("Delaware scraper — Sprint 4")

    async def scrape_foreign_quals(self, legal_name: str) -> ForeignQualification:
        raise NotImplementedError("Delaware foreign qual scraper — Sprint 4")
