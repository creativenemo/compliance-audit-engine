from enum import Enum
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, field_validator


class EntityType(str, Enum):
    LLC = "LLC"
    CORP = "Corp"
    LP = "LP"
    LLP = "LLP"
    SOLE_PROP = "SoleProp"
    NONPROFIT = "Nonprofit"
    OTHER = "Other"


class CustomerType(str, Enum):
    B2B = "B2B"
    B2C = "B2C"
    GOVERNMENT = "Government"


class RevenueRange(str, Enum):
    UNDER_100K = "under_100k"
    R_100K_500K = "100k_500k"
    R_500K_1M = "500k_1m"
    R_1M_5M = "1m_5m"
    R_5M_25M = "5m_25m"
    OVER_25M = "over_25m"


class TransactionRange(str, Enum):
    UNDER_200 = "under_200"
    R_200_1K = "200_1k"
    R_1K_10K = "1k_10k"
    R_10K_100K = "10k_100k"
    OVER_100K = "over_100k"


US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC",
}

USStateCode = Annotated[str, Field(pattern=r"^[A-Z]{2}$")]


class IntakeForm(BaseModel):
    # Contact
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    business_email: EmailStr

    # Entity Details
    legal_name: str = Field(min_length=1, max_length=500)
    domicile_state: USStateCode
    entity_type: EntityType
    employee_states: list[USStateCode] = Field(default_factory=list)
    business_nature: str = Field(min_length=1, max_length=1000)

    # Operating Profile
    ecommerce_marketplace: bool = False
    customer_types: list[CustomerType] = Field(min_length=1)
    product_service_location: list[USStateCode] = Field(default_factory=list)

    # Revenue & Tax
    annual_revenue: RevenueRange
    annual_transactions: TransactionRange
    states_registered_sales_tax: list[USStateCode] = Field(default_factory=list)

    @field_validator("domicile_state", "employee_states", "product_service_location", "states_registered_sales_tax", mode="before")
    @classmethod
    def validate_state_codes(cls, v: object) -> object:
        if isinstance(v, list):
            for state in v:
                if state not in US_STATES:
                    raise ValueError(f"Invalid US state code: {state}")
        elif isinstance(v, str) and v not in US_STATES:
            raise ValueError(f"Invalid US state code: {v}")
        return v
