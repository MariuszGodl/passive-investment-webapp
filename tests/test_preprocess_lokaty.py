import pytest

from scripts.preprocess_lokaty import (
    clean_placeholder,
    parse_numeric,
    parse_yes_no,
    normalize_capitalization,
    merge_requirements,
    compute_term_days,
    infer_product_type,
    AVG_DAYS_PER_MONTH,
)


# -- clean_placeholder ---------------------------------------------------------


@pytest.mark.parametrize(
    "val, expected",
    [
        (None, None),
        ("", None),
        ("typed by the user", None),
        ("typed by user", None),
        ("calculated", None),
        ("  Typed By The User  ", None),
        ("Some real value", "Some real value"),
        (42, "42"),
    ],
)
def test_clean_placeholder(val, expected):
    assert clean_placeholder(val) == expected


# -- parse_numeric -------------------------------------------------------------


@pytest.mark.parametrize(
    "val, expected",
    [
        ("0.045", 0.045),
        (0.03, 0.03),
        ("typed by the user", None),
        (None, None),
        ("", None),
        ("not_a_number", None),
    ],
)
def test_parse_numeric(val, expected):
    assert parse_numeric(val) == expected


# -- parse_yes_no --------------------------------------------------------------


@pytest.mark.parametrize(
    "val, expected",
    [
        ("Yes", True),
        ("No", False),
        ("yes", True),
        ("no", False),
        (None, None),
        ("typed by the user", None),
    ],
)
def test_parse_yes_no(val, expected):
    assert parse_yes_no(val) == expected


# -- normalize_capitalization --------------------------------------------------


@pytest.mark.parametrize(
    "val, expected",
    [
        ("monthly", "monthly"),
        ("at maturity", "at_maturity"),
        ("quarterly", "quarterly"),
        ("daily", "daily"),
        ("annual", "annual"),
        ("at promo end", "at_promo_end"),
        ("Monthly", "monthly"),
        (None, None),
        ("typed by the user", None),
    ],
)
def test_normalize_capitalization(val, expected):
    assert normalize_capitalization(val) == expected


# -- merge_requirements --------------------------------------------------------


def test_merge_requirements_all_present():
    result = merge_requirements("Req 1", "Req 2", "Req 3")
    assert result == "Req 1 | Req 2 | Req 3"


def test_merge_requirements_some_empty():
    result = merge_requirements("Req 1", None, "Req 3")
    assert result == "Req 1 | Req 3"


def test_merge_requirements_all_empty():
    result = merge_requirements(None, None, None)
    assert result is None


def test_merge_requirements_placeholders():
    result = merge_requirements("typed by the user", "Req 2", "calculated")
    assert result == "Req 2"


# -- compute_term_days ---------------------------------------------------------


@pytest.mark.parametrize(
    "term_value, term_unit, expected",
    [
        (15, "days", 15),
        (3, "months", round(3 * AVG_DAYS_PER_MONTH)),
        (None, "days", None),
        (15, None, None),
        (None, None, None),
        (365, "days", 365),
        (12, "months", round(12 * AVG_DAYS_PER_MONTH)),
    ],
)
def test_compute_term_days(term_value, term_unit, expected):
    assert compute_term_days(term_value, term_unit) == expected


# -- infer_product_type --------------------------------------------------------


@pytest.mark.parametrize(
    "name, expected",
    [
        ("Lokata terminowa", "term_deposit"),
        ("Konto oszczędnościowe w ramach Członkostwa", "savings_account"),
        ("Konto Mega Oszczędnościowe", "savings_account"),
        ("Lokata z funduszem XIX", "deposit_with_fund"),
        ("Rachunek Oszczędzam", "savings_account"),
        (None, "term_deposit"),
        ("", "term_deposit"),
    ],
)
def test_infer_product_type(name, expected):
    assert infer_product_type(name) == expected
