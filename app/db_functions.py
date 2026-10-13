import os
from collections.abc import Mapping, Sequence
from decimal import Decimal
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


def calculate_estimated_profit(
    annual_rate: Decimal | None,
    investment_amount: Decimal | None,
    term_days: int | None,
) -> str | None:
    """Placeholder for estimated-return calculation."""
    if annual_rate is None or investment_amount is None or term_days is None:
        return None
    return "12345"


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

    return {
        "id": row["product_id"],
        "variant_id": row["variant_id"],
        "variant_code": row["variant_code"],
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
        "estimated_profit": calculate_estimated_profit(
            interest_rate,
            min_amount,
            term_days,
        ),
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
