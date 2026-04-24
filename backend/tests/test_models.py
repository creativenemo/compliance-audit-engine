import pytest
from pydantic import ValidationError

from app.models.intake import IntakeForm


def test_valid_intake():
    form = IntakeForm(
        first_name="Jane",
        last_name="Smith",
        business_email="jane@embarkaviation.com",
        legal_name="Embark Aviation Corp",
        domicile_state="DE",
        entity_type="Corp",
        employee_states=["VA", "FL", "CO"],
        business_nature="Aviation consulting",
        ecommerce_marketplace=False,
        customer_types=["B2B"],
        product_service_location=["DE", "VA"],
        annual_revenue="1m_5m",
        annual_transactions="1k_10k",
        states_registered_sales_tax=[],
    )
    assert form.legal_name == "Embark Aviation Corp"
    assert form.domicile_state == "DE"
    assert len(form.employee_states) == 3


def test_invalid_state_code():
    with pytest.raises(ValidationError, match="Invalid US state code"):
        IntakeForm(
            first_name="Jane",
            last_name="Smith",
            business_email="jane@test.com",
            legal_name="Test Corp",
            domicile_state="XX",
            entity_type="Corp",
            employee_states=[],
            business_nature="Testing",
            ecommerce_marketplace=False,
            customer_types=["B2B"],
            product_service_location=[],
            annual_revenue="under_100k",
            annual_transactions="under_200",
            states_registered_sales_tax=[],
        )


def test_invalid_email():
    with pytest.raises(ValidationError):
        IntakeForm(
            first_name="Jane",
            last_name="Smith",
            business_email="not-an-email",
            legal_name="Test Corp",
            domicile_state="DE",
            entity_type="Corp",
            employee_states=[],
            business_nature="Testing",
            ecommerce_marketplace=False,
            customer_types=["B2B"],
            product_service_location=[],
            annual_revenue="under_100k",
            annual_transactions="under_200",
            states_registered_sales_tax=[],
        )
