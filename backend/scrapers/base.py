"""
Base class for Secretary of State scrapers — Sprint 4

Each state gets its own class in scrapers/states/{state_code}.py.
Tier 1 (Sprint 4): DE, WY, FL, CO, IL, VA, TN, WA, DC
Tier 2 (Month 2): CA, TX, NY, NV, OR, GA, NC, OH, PA
Tier 3 (Month 3-4): remaining states
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class EntityRegistration:
    legal_name: str
    status: str  # Active | Dissolved | Delinquent | Not Found
    formation_date: str | None
    registered_agent_name: str | None
    registered_agent_address: str | None
    annual_report_due: str | None
    raw_data: dict[str, Any]


@dataclass
class ForeignQualification:
    state: str
    qualified: bool
    registration_date: str | None
    status: str | None
    estimated_filing_cost: str | None


class BaseSosScraper(ABC):
    state_code: str
    state_name: str
    sos_url: str

    @abstractmethod
    async def scrape_entity(self, legal_name: str) -> EntityRegistration:
        """Scrape entity registration details from domicile SOS."""
        ...

    @abstractmethod
    async def scrape_foreign_quals(self, legal_name: str) -> ForeignQualification:
        """Check foreign qualification status for this state."""
        ...
