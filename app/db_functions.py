import os
from calendar import monthrange
from collections.abc import Mapping, Sequence
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from functools import lru_cache
from typing import Any

from sqlalchemy import bindparam, create_engine, text
from sqlalchemy.engine import Engine


_DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://app:app@localhost:5432/passive_investment",
)

_OFFER_SELECT = """
SELECT
    ov.id AS variant_id,
    p.id AS product_id,
    b.code AS institution_name,
    p.name,
    p.product_type::text AS product_type,
    ov.variant_code,
    ov.interest_rate,
    ov.rate_type::text AS rate_type,
    ov.term_value,
    ov.term_unit::text AS term_unit,
    ov.term_days,
    ov.min_amount,
    ov.max_amount,
    ov.currency,
    ov.capitalization::text AS capitalization,
    ov.additional_condition,
    ov.valid_from,
    ov.valid_to
FROM offer_variant AS ov
JOIN product AS p ON p.id = ov.product_id
JOIN bank AS b ON b.id = p.bank_id
"""

_PRODUCT_TYPE_LABELS = {
    "term_deposit": "Term deposit",
    "savings_account": "Savings account",
    "deposit_with_fund": "Deposit with fund",
}

_CAPITALIZATION_LABELS = {
    "at_maturity": "At maturity",
    "monthly": "Monthly",
    "quarterly": "Quarterly",
    "daily": "Daily",
    "annual": "Annual",
    "at_promo_end": "At promotion end",
}

_COMPOUNDING_PERIODS = {
    "daily": 365,
    "monthly": 12,
    "quarterly": 4,
    "annual": 1,
}
_DAYS_PER_YEAR = Decimal("365")
_MONEY_QUANTUM = Decimal("0.01")


@lru_cache(maxsize=1)
def _get_engine() -> Engine:
    return create_engine(_DATABASE_URL)


def _format_decimal(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return format(value.normalize(), "f")


def _format_duration(
    term_value: Decimal | None,
    term_unit: str | None,
    term_days: int | None,
    product_type: str,
) -> str:
    if term_value is not None:
        value = _format_decimal(term_value)
        return f"{value} {term_unit or 'days'}"
    if term_days is not None:
        return f"{term_days} days"
    if product_type == "savings_account":
        return "No fixed term"
    return "Not specified"


def _format_amount_range(
    min_amount: Decimal | None,
    max_amount: Decimal | None,
    currency: str,
) -> str:
    minimum = _format_decimal(min_amount)
    maximum = _format_decimal(max_amount)
    if minimum is not None and maximum is not None:
        return f"{minimum}–{maximum} {currency}"
    if minimum is not None:
        return f"From {minimum} {currency}"
    if maximum is not None:
        return f"Up to {maximum} {currency}"
    return "Not specified"


def _term_years(
    term_days: int | None,
    term_value: Decimal | None,
    term_unit: str | None,
) -> Decimal | None:
    if term_value is not None and term_unit == "months":
        return term_value / Decimal(12)
    if term_value is not None and term_unit == "days":
        return term_value / _DAYS_PER_YEAR
    if term_days is None:
        return None
    return Decimal(term_days) / _DAYS_PER_YEAR


def _add_months(start_date: date, months: int) -> date:
    month_index = start_date.year * 12 + start_date.month - 1 + months
    year, month_index = divmod(month_index, 12)
    month = month_index + 1
    day = min(start_date.day, monthrange(year, month)[1])
    return date(year, month, day)


def _investment_growth_factor(
    annual_rate: Decimal | None,
    term_days: int | None,
    capitalization: str | None,
    *,
    term_value: Decimal | None = None,
    term_unit: str | None = None,
    bond_code: str | None = None,
    cpi_rate: Decimal | None = None,
    bond_margin: Decimal | None = None,
    nbp_reference_rate: Decimal | None = None,
) -> Decimal | None:
    years = _term_years(term_days, term_value, term_unit)
    if annual_rate is None or years is None or years <= 0:
        return None

    if bond_code is not None:
        code = bond_code.upper()
        if code == "OTS":
            if years >= 1:
                return None
            return (Decimal(1) + annual_rate / 4) ** (4 * years)
        if code == "TOS":
            return (Decimal(1) + annual_rate) ** years
        if code in {"EDO", "ROS", "ROD", "COI"}:
            if years < 1 or cpi_rate is None or bond_margin is None:
                return None
            return (Decimal(1) + annual_rate) * (
                Decimal(1) + cpi_rate + bond_margin
            ) ** (years - 1)
        if code in {"ROR", "DOR"}:
            if bond_margin is None or nbp_reference_rate is None:
                return None
            return (Decimal(1) + annual_rate / 12) * (
                Decimal(1) + (nbp_reference_rate + bond_margin) / 12
            ) ** (12 * years - 1)
        return None

    if capitalization in {"at_maturity", "at_promo_end"}:
        return Decimal(1) + annual_rate * years

    periods = _COMPOUNDING_PERIODS.get(capitalization or "")
    if periods is None:
        return None
    return (Decimal(1) + annual_rate / periods) ** (periods * years)


def calculate_apy(
    annual_rate: Decimal | None,
    term_days: int | None,
    capitalization: str | None,
    *,
    term_value: Decimal | None = None,
    term_unit: str | None = None,
    bond_code: str | None = None,
    cpi_rate: Decimal | None = None,
    bond_margin: Decimal | None = None,
    nbp_reference_rate: Decimal | None = None,
) -> Decimal | None:
    """Calculate APY as a decimal fraction using the deposit or bond diagram."""
    years = _term_years(term_days, term_value, term_unit)
    if years is None or years <= 0:
        return None

    growth_factor = _investment_growth_factor(
        annual_rate,
        term_days,
        capitalization,
        term_value=term_value,
        term_unit=term_unit,
        bond_code=bond_code,
        cpi_rate=cpi_rate,
        bond_margin=bond_margin,
        nbp_reference_rate=nbp_reference_rate,
    )
    if growth_factor is None or growth_factor <= 0:
        return None

    if bond_code is not None and bond_code.upper() == "TOS":
        return annual_rate
    return growth_factor ** (Decimal(1) / years) - Decimal(1)


def calculate_estimated_profit(
    annual_rate: Decimal | None,
    investment_amount: Decimal | None,
    term_days: int | None,
    capitalization: str | None = "at_maturity",
    *,
    term_value: Decimal | None = None,
    term_unit: str | None = None,
    bond_code: str | None = None,
    cpi_rate: Decimal | None = None,
    bond_margin: Decimal | None = None,
    nbp_reference_rate: Decimal | None = None,
) -> str | None:
    """Return gross interest for the investment term, rounded to cents."""
    if investment_amount is None:
        return None

    growth_factor = _investment_growth_factor(
        annual_rate,
        term_days,
        capitalization,
        term_value=term_value,
        term_unit=term_unit,
        bond_code=bond_code,
        cpi_rate=cpi_rate,
        bond_margin=bond_margin,
        nbp_reference_rate=nbp_reference_rate,
    )
    if growth_factor is None:
        return None

    profit = (investment_amount * (growth_factor - Decimal(1))).quantize(
        _MONEY_QUANTUM,
        rounding=ROUND_HALF_UP,
    )
    return format(profit, "f")


def calculate_cash_flow_schedule(
    investment_amount: Decimal | None,
    estimated_profit: str | None,
    term_days: int | None,
    currency: str,
    *,
    start_date: date | None = None,
    term_value: Decimal | None = None,
    term_unit: str | None = None,
) -> list[dict[str, str]]:
    """Return the initial investment and maturity cash flows for an offer."""
    if investment_amount is None or estimated_profit is None or term_days is None or term_days <= 0:
        return []

    start_date = start_date or date.today()
    if term_value is not None and term_unit == "months" and term_value == term_value.to_integral_value():
        maturity_date = _add_months(start_date, int(term_value))
    else:
        maturity_date = start_date + timedelta(days=term_days)
    principal = investment_amount.quantize(_MONEY_QUANTUM, rounding=ROUND_HALF_UP)
    return_amount = principal + Decimal(estimated_profit)
    return [
        {
            "date": start_date.isoformat(),
            "operation": "Initial investment",
            "amount": format(-principal, "f"),
            "currency": currency,
        },
        {
            "date": maturity_date.isoformat(),
            "operation": "Maturity payout (principal + interest)",
            "amount": format(return_amount, "f"),
            "currency": currency,
        },
    ]


def _map_offer(row: Mapping[Any, Any]) -> dict[str, Any]:
    product_type = row["product_type"]
    capitalization = row["capitalization"]
    currency = row["currency"] or "PLN"
    interest_rate = row["interest_rate"]
    interest_rate_percent = (
        _format_decimal(interest_rate * Decimal("100"))
        if interest_rate is not None
        else None
    )
    term_days = row["term_days"]
    min_amount = row["min_amount"]
    max_amount = row["max_amount"]
    apy = calculate_apy(
        interest_rate,
        term_days,
        capitalization,
        term_value=row["term_value"],
        term_unit=row["term_unit"],
    )
    apy_percent = (
        format(
            (apy * Decimal("100")).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            ),
            ".2f",
        )
        if apy is not None
        else None
    )
    estimated_profit = calculate_estimated_profit(
        interest_rate,
        min_amount,
        term_days,
        capitalization,
        term_value=row["term_value"],
        term_unit=row["term_unit"],
    )
    cash_flows = calculate_cash_flow_schedule(
        min_amount,
        estimated_profit,
        term_days,
        currency,
        term_value=row["term_value"],
        term_unit=row["term_unit"],
    )

    return {
        "id": row["product_id"],
        "variant_id": row["variant_id"],
        "variant_code": row["variant_code"],
        "product_type": product_type,
        "term_days": term_days,
        "term_value": _format_decimal(row["term_value"]),
        "term_unit": row["term_unit"],
        "min_amount": _format_decimal(min_amount),
        "max_amount": _format_decimal(max_amount),
        "annual_rate": _format_decimal(interest_rate * Decimal("100"))
        if interest_rate is not None
        else None,
        "annual_rate_decimal": _format_decimal(interest_rate),
        "apy": apy_percent,
        "estimated_amount": _format_decimal(min_amount),
        "institution_name": row["institution_name"],
        "name": row["name"],
        "badge": _PRODUCT_TYPE_LABELS.get(
            product_type,
            product_type.replace("_", " ").title(),
        ),
        "duration": _format_duration(
            row["term_value"],
            row["term_unit"],
            term_days,
            product_type,
        ),
        "requirement": row["additional_condition"] or "No additional conditions listed",
        "interest_rate": interest_rate_percent,
        "rate_type": row["rate_type"],
        "rate_type_label": row["rate_type"].capitalize(),
        "currency": currency,
        "amount_range": _format_amount_range(min_amount, max_amount, currency),
        "capitalization": capitalization,
        "capitalization_label": _CAPITALIZATION_LABELS.get(
            capitalization,
            "Not recorded",
        ),
        "payout_description": _CAPITALIZATION_LABELS.get(
            capitalization,
            "Capitalization not recorded",
        ),
        "estimated_profit": estimated_profit,
        "cash_flows": cash_flows,
        "valid_from": row["valid_from"],
        "valid_to": row["valid_to"],
        "interest_payout": None,
        "inflation_indexed": None,
        "early_termination": None,
        "interest_details": None,
    }


def get_offers(
    variant_ids: Sequence[int] | None = None,
    *,
    active_only: bool = True,
) -> list[dict[str, Any]]:
    """Return offer variants joined with their product and bank data."""
    if variant_ids is not None and not variant_ids:
        return []

    query = (
        _OFFER_SELECT
        + """
        WHERE (
            NOT :active_only
            OR (
                (ov.valid_from IS NULL OR ov.valid_from <= CURRENT_DATE)
                AND (ov.valid_to IS NULL OR ov.valid_to >= CURRENT_DATE)
            )
        )
    """
    )
    parameters: dict[str, Any] = {"active_only": active_only}
    if variant_ids is not None:
        query += " AND ov.id IN :variant_ids"
        parameters["variant_ids"] = list(variant_ids)

    query += " ORDER BY b.name, p.name, ov.term_days NULLS LAST, ov.interest_rate DESC, ov.id"
    statement = text(query)
    if variant_ids is not None:
        statement = statement.bindparams(bindparam("variant_ids", expanding=True))

    with _get_engine().connect() as connection:
        rows = connection.execute(statement, parameters).mappings().all()
    return [_map_offer(row) for row in rows]


def get_offer_by_variant_id(variant_id: int) -> dict[str, Any] | None:
    """Return one offer variant, including expired variants, for its detail page."""
    query = _OFFER_SELECT + " WHERE ov.id = :variant_id"
    with _get_engine().connect() as connection:
        row = (
            connection.execute(
                text(query),
                {"variant_id": variant_id},
            )
            .mappings()
            .first()
        )
    return _map_offer(row) if row is not None else None
