from datetime import date
from decimal import Decimal

import pytest

from app.db_functions import (
    _map_offer,
    calculate_apy,
    calculate_cash_flow_schedule,
    calculate_estimated_profit,
)


def test_monthly_deposit_apy_matches_preprocessed_example():
    apy = calculate_apy(Decimal("0.045"), 91, "monthly")

    assert apy == pytest.approx(Decimal("0.0459398250405896"), abs=Decimal("1e-15"))


def test_deposit_at_maturity_uses_simple_interest_for_profit():
    profit = calculate_estimated_profit(
        Decimal("0.045"),
        Decimal("10000"),
        183,
        "at_maturity",
    )

    assert profit == "225.62"


def test_deposit_apy_is_annualized_from_simple_interest_growth():
    term_years = Decimal(183) / Decimal(365)
    growth_factor = Decimal(1) + Decimal("0.045") * term_years

    assert calculate_apy(Decimal("0.045"), 183, "at_maturity") == (
        growth_factor ** (Decimal(1) / term_years) - Decimal(1)
    )


@pytest.mark.parametrize(
    ("capitalization", "periods"),
    [("daily", 365), ("monthly", 12), ("quarterly", 4), ("annual", 1)],
)
def test_compound_deposit_apy_uses_diagram_frequency(capitalization, periods):
    rate = Decimal("0.06")
    expected = (Decimal(1) + rate / periods) ** periods - Decimal(1)

    assert calculate_apy(
        rate,
        365,
        capitalization,
        term_value=Decimal(12),
        term_unit="months",
    ) == expected


def test_three_month_deposit_uses_exact_term_units_for_return():
    rate = Decimal("0.045")
    expected_growth = (Decimal(1) + rate / 12) ** 3

    assert calculate_apy(
        rate,
        91,
        "monthly",
        term_value=Decimal(3),
        term_unit="months",
    ) == expected_growth ** 4 - Decimal(1)
    assert calculate_estimated_profit(
        rate,
        Decimal("10000"),
        91,
        "monthly",
        term_value=Decimal(3),
        term_unit="months",
    ) == "112.92"


@pytest.mark.parametrize(
    ("annual_rate", "capitalization", "expected_apy"),
    [
        ("0.123456", "monthly", "13.07"),
        ("0.123456", "at_maturity", "12.35"),
        ("0.07", "at_maturity", "7.00"),
    ],
)
def test_offer_apy_percentage_is_rounded_to_two_decimal_places(
    annual_rate,
    capitalization,
    expected_apy,
):
    offer = _map_offer(
        {
            "product_type": "term_deposit",
            "capitalization": capitalization,
            "currency": "PLN",
            "interest_rate": Decimal(annual_rate),
            "term_days": 365,
            "min_amount": Decimal("1000"),
            "max_amount": None,
            "product_id": 1,
            "variant_id": 2,
            "variant_code": "DEP-1",
            "institution_name": "Bank",
            "name": "Deposit",
            "term_value": Decimal(12),
            "term_unit": "months",
            "rate_type": "fixed",
            "additional_condition": None,
            "valid_from": None,
            "valid_to": None,
        }
    )

    assert offer["apy"] == expected_apy


def test_cash_flow_schedule_has_initial_outflow_and_single_maturity_payout():
    flows = calculate_cash_flow_schedule(
        Decimal("10000"),
        "112.92",
        91,
        "PLN",
        start_date=date(2026, 1, 1),
        term_value=Decimal(3),
        term_unit="months",
    )

    assert flows == [
        {
            "date": "2026-01-01",
            "operation": "Initial investment",
            "amount": "-10000.00",
            "currency": "PLN",
        },
        {
            "date": "2026-04-01",
            "operation": "Maturity payout (principal + interest)",
            "amount": "10112.92",
            "currency": "PLN",
        },
    ]


@pytest.mark.parametrize("capitalization", [None, "unknown"])
def test_unknown_deposit_capitalization_returns_no_estimate(capitalization):
    assert calculate_apy(Decimal("0.05"), 365, capitalization) is None
    assert calculate_estimated_profit(
        Decimal("0.05"), Decimal("10000"), 365, capitalization
    ) is None


def test_ots_bond_apy_uses_quarterly_annualization():
    expected = (Decimal(1) + Decimal("0.05") / 4) ** 4 - Decimal(1)

    assert calculate_apy(Decimal("0.05"), 180, None, bond_code="OTS") == expected


def test_tos_bond_apy_is_the_fixed_rate():
    assert calculate_apy(Decimal("0.05"), 730, None, bond_code="TOS") == Decimal("0.05")


@pytest.mark.parametrize("bond_code", ["EDO", "ROS", "ROD", "COI"])
def test_indexed_bond_apy_uses_first_year_rate_then_cpi_and_margin(bond_code):
    growth_factor = Decimal("1.06") * Decimal("1.03") ** 2
    expected = growth_factor ** (Decimal(1) / Decimal(3)) - Decimal(1)

    assert calculate_apy(
        Decimal("0.06"),
        1095,
        None,
        bond_code=bond_code,
        cpi_rate=Decimal("0.02"),
        bond_margin=Decimal("0.01"),
    ) == expected


@pytest.mark.parametrize("bond_code", ["ROR", "DOR"])
def test_monthly_payout_bond_uses_reference_rate_and_margin(bond_code):
    growth_factor = (Decimal(1) + Decimal("0.04") / 12) * (
        Decimal(1) + (Decimal("0.05") + Decimal("0.01")) / 12
    ) ** 11

    assert calculate_apy(
        Decimal("0.04"),
        365,
        None,
        bond_code=bond_code,
        bond_margin=Decimal("0.01"),
        nbp_reference_rate=Decimal("0.05"),
    ) == growth_factor - Decimal(1)


def test_bond_estimate_is_unavailable_without_required_index_inputs():
    assert calculate_apy(Decimal("0.06"), 1095, None, bond_code="EDO") is None