"""
Delaware Division of Corporations — Sprint 4

SOS URL: https://icis.corp.delaware.gov/ecorp/entitysearch/namesearch.aspx
Entity search by name → click result → extract status, agent, formation date.

Delaware is domicile for ~70% of US corporations.
Annual report due: March 1 (corporations), June 1 (LLCs).
Foreign qualification filing costs: Corp ~$50/yr, LLC ~$300/yr franchise tax.
"""
from __future__ import annotations

import re
from typing import Any

from playwright.async_api import async_playwright

from scrapers.base import BaseSosScraper, EntityRegistration, ForeignQualification

_BROWSER_ARGS = ["--no-sandbox", "--disable-setuid-sandbox"]


def _detect_annual_report_due(entity_text: str) -> str:
    """Return annual report due date based on entity type keywords in page text."""
    text_lower = entity_text.lower()
    if "llc" in text_lower or "limited liability" in text_lower:
        return "June 1"
    return "March 1"


def _parse_status(text: str) -> str:
    """Map raw status text to canonical status value."""
    text_lower = text.lower()
    if "good standing" in text_lower or "active" in text_lower:
        return "Active"
    if "cancel" in text_lower or "void" in text_lower or "revok" in text_lower:
        return "Dissolved"
    if "delinquent" in text_lower or "forfeited" in text_lower:
        return "Delinquent"
    return text.strip() or "Unknown"


class DelawareScraper(BaseSosScraper):
    state_code = "DE"
    state_name = "Delaware"
    sos_url = "https://icis.corp.delaware.gov/ecorp/entitysearch/namesearch.aspx"

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    async def _search_and_extract(
        self,
        legal_name: str,
        foreign: bool = False,
    ) -> dict[str, Any]:
        """
        Run a Delaware entity name search and return a raw data dict.

        When `foreign=True` we look for "Foreign" entries in the results
        instead of the primary domestic registration.
        """
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(args=_BROWSER_ARGS)
            try:
                page = await browser.new_page()
                await page.goto(self.sos_url)
                await page.wait_for_load_state("networkidle")

                # Fill search form
                await page.fill("#EntityName", legal_name)
                await page.click("input[type=submit]")
                await page.wait_for_load_state("networkidle")

                # Check whether any results table appeared
                results_table = page.locator("table.search-table, table#tblResults, table")
                row_count = await results_table.count()
                if row_count == 0:
                    return {"found": False}

                # Collect result rows — each row has an anchor for the entity detail
                rows = page.locator("td a")
                links_count = await rows.count()
                if links_count == 0:
                    return {"found": False}

                # When looking for foreign quals, prefer rows containing "Foreign"
                target_index = 0
                if foreign:
                    for i in range(links_count):
                        link_text = await rows.nth(i).inner_text()
                        if "foreign" in link_text.lower():
                            target_index = i
                            break
                    else:
                        # No foreign row found
                        return {"found": False, "foreign_not_found": True}

                await rows.nth(target_index).click()
                await page.wait_for_load_state("networkidle")

                # ---- Extract detail page --------------------------------
                raw: dict[str, Any] = {"found": True, "url": page.url}

                # Entity name
                for sel in ["h1", "strong", "span#lblEntityName", "#lblEntityName"]:
                    el = page.locator(sel).first
                    if await el.count() > 0:
                        raw["entity_name"] = (await el.inner_text()).strip()
                        break

                # Full page text for regex parsing
                body_text = await page.inner_text("body")
                raw["body_text"] = body_text

                # Status — look for table row with "Status" label
                status_match = re.search(
                    r"(?:Status|Entity Status)[:\s]+([A-Za-z ]+)", body_text
                )
                if status_match:
                    raw["status_raw"] = status_match.group(1).strip()

                # Formation / file date
                date_match = re.search(
                    r"(?:Incorporation Date|Formation Date|File Date)[:\s]+([\d/]+)",
                    body_text,
                )
                if date_match:
                    raw["formation_date"] = date_match.group(1).strip()

                # Registered agent name
                agent_match = re.search(
                    r"Registered Agent[:\s\n]+([A-Za-z &,.'()-]+)", body_text
                )
                if agent_match:
                    raw["registered_agent_name"] = agent_match.group(1).strip()

                # Registered agent address (next line after agent name)
                agent_addr_match = re.search(
                    r"Registered Agent Address[:\s\n]+([^\n]+)", body_text
                )
                if agent_addr_match:
                    raw["registered_agent_address"] = agent_addr_match.group(1).strip()

                return raw

            finally:
                await browser.close()

    # ------------------------------------------------------------------ #
    #  Public interface                                                    #
    # ------------------------------------------------------------------ #

    async def scrape_entity(self, legal_name: str) -> EntityRegistration:
        try:
            raw = await self._search_and_extract(legal_name, foreign=False)
        except Exception as exc:
            return EntityRegistration(
                legal_name=legal_name,
                status="Not Found",
                formation_date=None,
                registered_agent_name=None,
                registered_agent_address=None,
                annual_report_due=None,
                raw_data={"error": str(exc)},
            )

        if not raw.get("found"):
            return EntityRegistration(
                legal_name=legal_name,
                status="Not Found",
                formation_date=None,
                registered_agent_name=None,
                registered_agent_address=None,
                annual_report_due=None,
                raw_data=raw,
            )

        status_raw = raw.get("status_raw", "")
        entity_name = raw.get("entity_name", legal_name)
        annual_due = _detect_annual_report_due(
            raw.get("body_text", "") + entity_name
        )

        return EntityRegistration(
            legal_name=entity_name,
            status=_parse_status(status_raw),
            formation_date=raw.get("formation_date"),
            registered_agent_name=raw.get("registered_agent_name"),
            registered_agent_address=raw.get("registered_agent_address"),
            annual_report_due=annual_due,
            raw_data=raw,
        )

    async def scrape_foreign_quals(self, legal_name: str) -> ForeignQualification:
        try:
            raw = await self._search_and_extract(legal_name, foreign=True)
        except Exception:
            return ForeignQualification(
                state=self.state_code,
                qualified=False,
                registration_date=None,
                status=None,
                estimated_filing_cost=None,
            )

        if not raw.get("found"):
            return ForeignQualification(
                state=self.state_code,
                qualified=False,
                registration_date=None,
                status=None,
                estimated_filing_cost=None,
            )

        body_text = raw.get("body_text", "")
        # Determine LLC vs Corp for filing cost
        is_llc = "llc" in body_text.lower() or "limited liability" in body_text.lower()
        cost = "~$300/yr franchise tax" if is_llc else "~$50/yr"

        status_raw = raw.get("status_raw", "")
        date_match = re.search(
            r"(?:Qualification Date|Registration Date|File Date)[:\s]+([\d/]+)",
            body_text,
        )

        return ForeignQualification(
            state=self.state_code,
            qualified=True,
            registration_date=date_match.group(1) if date_match else raw.get("formation_date"),
            status=_parse_status(status_raw),
            estimated_filing_cost=cost,
        )
