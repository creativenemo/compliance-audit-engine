from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SectionStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    NOT_CHECKED = "NOT_CHECKED"


class ScoreBreakdown(BaseModel):
    entity_status: float = Field(ge=0, le=100)
    federal_compliance: float = Field(ge=0, le=100)
    sanctions_watchlists: float = Field(ge=0, le=100)
    tax_exposure: float = Field(ge=0, le=100)
    license_status: float = Field(ge=0, le=100)

    @property
    def overall(self) -> float:
        return (
            self.entity_status * 0.25
            + self.federal_compliance * 0.25
            + self.sanctions_watchlists * 0.20
            + self.tax_exposure * 0.20
            + self.license_status * 0.10
        )


class ReportSource(BaseModel):
    source_name: str
    source_url: str | None = None
    queried_at: datetime
    result_status: str


class ReportFinding(BaseModel):
    finding: str
    source_field: str
    source_name: str


class ActionItem(BaseModel):
    priority: int = Field(ge=1, le=5)
    action: str
    urgency: str
    estimated_cost: str | None = None


class ReportSection(BaseModel):
    section_id: str
    title: str
    status: SectionStatus
    findings: list[ReportFinding] = []
    recommendations: list[str] = []
    sources: list[str] = []


class ReportSchema(BaseModel):
    overall_risk_score: RiskLevel
    score_breakdown: ScoreBreakdown
    executive_summary: str
    sections: list[ReportSection]
    top_action_items: list[ActionItem]
    data_sources_checked: list[ReportSource]
    generated_at: datetime
    disclaimer: str = (
        "This report is generated from publicly available data sources for informational "
        "purposes only. It does not constitute legal advice. Consult qualified legal counsel "
        "for compliance decisions."
    )


