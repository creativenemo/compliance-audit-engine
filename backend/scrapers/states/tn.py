"""
Tennessee Secretary of State (TNBEAR) — Sprint 4

SOS URL: https://tnbear.tn.gov/Ecommerce/FilingSearch.aspx
Search by name → extract status, registered agent, formation date, annual report due.

Annual report due: April 1.
Foreign qualification filing costs: ~$300 (Corp and LLC).
"""
from __future__ import annotations

import re
from typing import Any

from playwright.async_api import async_playwright

from scrapers.base import BaseSosScraper, EntityRegistration, ForeignQualification

_BROWSER_ARGS = ["--no-sandbox", "--disable-setuid-sandbox"]


def _parse_status(text: str) -> str:
    text_lower = text.lower()
    if "active" in text_lower or "good standing" in text_lower:
        return "Active"
    if "dissolv" in text_lower or "cancel" in text_lower or "revok" in text_lower:
        return "Dissolved"
    if "delinquent" in text_lower or "forfeited" in text_lower:
        return "Delinquent"
    return text.strip() or "Unknown"


class TennesseeScraper(BaseSosScraper):
    state_code = "TN"
    state_name = "Tennessee"
    sos_url = "https://tnbear.tn.gov/Ecommerce/FilingSearch.aspx"

    async def _search_and_extract(
        self, legal_name: str, foreign: bool = False
    ) -> dict[str, Any]:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(args=_BROWSER_ARGS)
            try:
                page = await browser.new_page()
                await page.goto(self.sos_url)
                await page.wait_for_load_state("networkidle")

                # Fill entity name field
                name_input = page.locator(
                    "input[name*='EntityName'], input[id*='EntityName'], "
                    "input[name*='name'], input[type='text']"
                ).first
                await name_input.fill(legal_name)

                submit = page.locator(
                    "input[type='submit'], button[type='submit'], input[value='Search']"
                ).first
                await submit.click()
                await page.wait_for_load_state("networkidle")

                links = page.locator("table td a, .results a, a[href*='Filing']")
                count = await links.count()
                if count == 0:
                    return {"found": False}

                target_index = 0
                if foreign:
                    for i in range(count):
                        txt = await links.nth(i).inner_text()
                        if "foreign" in txt.lower():
                            target_index = i
                            break
                    else:
                        return {"found": False, "foreign_not_found": True}

                await links.nth(target_index).click()
                await page.wait_for_load_state("networkidle")

                raw: dict[str, Any] = {"found": True, "url": page.url}
                body_text = await page.inner_text("body")
                raw["body_text"] = body_text

                # Entity name
                for sel in ["h1", "h2", ".entityName", "strong", "#lblEntityName"]:
                    el = page.locator(sel).first
                    if await el.count() > 0:
                        raw["entity_name"] = (await el.inner_text()).strip()
                        break

                # Status
                m = re.search(r"(?:Status)[:\s]+([A-Za-z ]+)", body_text)
                if m:
                    raw["status_raw"] = m.group(1).strip()

                # Formation date
                m = re.search(
                    r"(?:Formation Date|Filing Date|Date Filed|Incorporated)[:\s]+([\d/]+)",
                    body_text,
                )
                if m:
                    raw["formation_date"] = m.group(1).strip()

                # Annual report
                m = re.search(
                    r"(?:Annual Report Due|Report Due)[:\s]+([^\n]+)", body_text
                )
                if m:
                    raw["annual_report_due"] = m.group(1).strip()

                # Registered agent
                m = re.search(
                    r"Registered Agent[:\s\n]+([A-Za-z &,.'()-]+)", body_text
                )
                if m:
                    raw["registered_agent_name"] = m.group(1).strip()

                m = re.search(
                    r"(?:Registered Agent Address|Agent Address)[:\s\n]+([^\n]+)",
                    body_text,
                )
                if m:
                    raw["registered_agent_address"] = m.group(1).strip()

                return raw

            finally:
                await browser.close()

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

        return EntityRegistration(
            legal_name=raw.get("entity_name", legal_name),
            status=_parse_status(raw.get("status_raw", "")),
            formation_date=raw.get("formation_date"),
            registered_agent_name=raw.get("registered_agent_name"),
            registered_agent_address=raw.get("registered_agent_address"),
            annual_report_due=raw.get("annual_report_due", "April 1"),
            raw_data=raw,
        )

    async def scrape_foreign_quals(self, legal_name: str) -> ForeignQualification:
        try:
            raw = await self._search_and_extract(legal_name, foreign=True)
        except Exception as exc:
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
        date_m = re.search(
            r"(?:Qualification Date|Registration Date|File Date)[:\s]+([\d/]+)",
            body_text,
        )

        return ForeignQualification(
            state=self.state_code,
            qualified=True,
            registration_date=date_m.group(1) if date_m else raw.get("formation_date"),
            status=_parse_status(raw.get("status_raw", "")),
            estimated_filing_cost="~$300",
        )
