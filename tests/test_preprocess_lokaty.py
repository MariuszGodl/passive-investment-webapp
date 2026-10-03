import pandas as pd
import pytest

from scripts.preprocess_lokaty import (
    compute_term_days,
    merge_currency,
    drop_columns,
    add_term_days,
    add_currency,
    drop_invalid_rows,
    validate_enums,
    map_enums,
    rename_columns,
    reorder_columns,
    AVG_DAYS_PER_MONTH,
    DEFAULT_CURRENCY,
    CURRENCY_COLUMNS,
    OUTPUT_COLUMN_ORDER,
)


@pytest.mark.parametrize(
    "okres, okres_typ, expected",
    [
        (15, "dni", 15),
        (3, "mies.", round(3 * AVG_DAYS_PER_MONTH)),
        (None, "dni", None),
        (15, None, None),
        (None, None, None),
    ],
)
def test_compute_term_days(okres, okres_typ, expected):
    assert (
        compute_term_days(pd.Series({"okres": okres, "okres_typ": okres_typ}))
        == expected
    )


@pytest.mark.parametrize(
    "min_cur, max_cur, expected",
    [
        (None, None, DEFAULT_CURRENCY),
        ("", "", DEFAULT_CURRENCY),
        ("USD", None, "USD"),
        (None, "EUR", "EUR"),
        ("PLN", "PLN", "PLN"),
    ],
)
def test_merge_currency_valid(min_cur, max_cur, expected):
    assert (
        merge_currency(
            pd.Series({"min_kwota_waluta": min_cur, "max_kwota_waluta": max_cur})
        )
        == expected
    )


def test_merge_currency_mismatch():
    with pytest.raises(ValueError, match="Currency mismatch"):
        merge_currency(
            pd.Series(
                {
                    "min_kwota_waluta": "PLN",
                    "max_kwota_waluta": "EUR",
                    "kod_wariantu": "V1",
                }
            )
        )


def test_drop_columns():
    df = pd.DataFrame(
        {"keep": [1], "data_edycji": [2], "edytor": [3], "okres_mies_automat": [4]}
    )
    result = drop_columns(df)
    assert list(result.columns) == ["keep"]


def test_add_term_days():
    df = pd.DataFrame(
        [{"okres": 10, "okres_typ": "dni"}, {"okres": None, "okres_typ": None}]
    )
    result = add_term_days(df)
    assert "term_days" in result.columns
    assert result["term_days"].iloc[0] == 10
    assert pd.isna(result["term_days"].iloc[1])
    assert result["term_days"].dtype.name == "Int64"


def test_add_currency():
    df = pd.DataFrame(
        [
            {"min_kwota_waluta": "USD", "max_kwota_waluta": "USD"},
            {"min_kwota_waluta": None, "max_kwota_waluta": None},
        ]
    )
    result = add_currency(df)
    assert "currency" in result.columns
    assert result["currency"].iloc[0] == "USD"
    assert result["currency"].iloc[1] == DEFAULT_CURRENCY
    for col in CURRENCY_COLUMNS:
        assert col not in result.columns


def test_drop_invalid_rows():
    df = pd.DataFrame(
        [
            {"lokata/konto": "lok_ter", "rodzaj_oproc": "stałe", "kod_wariantu": "V1"},
            {"lokata/konto": None, "rodzaj_oproc": "stałe", "kod_wariantu": "V2"},
            {"lokata/konto": "lok_ter", "rodzaj_oproc": None, "kod_wariantu": "V3"},
        ]
    )
    result = drop_invalid_rows(df)
    assert len(result) == 1
    assert result["kod_wariantu"].iloc[0] == "V1"


def test_validate_enums_valid():
    df_valid = pd.DataFrame(
        {
            "lokata/konto": ["lok_ter"],
            "rodzaj_oproc": ["stałe"],
            "okres_typ": ["dni"],
            "kapitalizacja": ["miesięczna"],
        }
    )
    validate_enums(df_valid)


def test_validate_enums_valid_null():
    df_valid_null = pd.DataFrame(
        {
            "lokata/konto": ["lok_ter"],
            "rodzaj_oproc": ["stałe"],
            "okres_typ": [None],
            "kapitalizacja": [None],
        }
    )
    validate_enums(df_valid_null)


def test_validate_enums_invalid():
    df_invalid = pd.DataFrame(
        {
            "lokata/konto": ["unknown_type"],
            "rodzaj_oproc": ["stałe"],
            "okres_typ": ["dni"],
            "kapitalizacja": ["miesięczna"],
        }
    )
    with pytest.raises(ValueError, match="Unknown enum values found in CSV"):
        validate_enums(df_invalid)


@pytest.mark.parametrize(
    "col, expected",
    [
        ("lokata/konto", ["term_deposit", "savings_account"]),
        ("rodzaj_oproc", ["fixed", "variable"]),
        ("okres_typ", ["months", "days"]),
        ("kapitalizacja", ["monthly", "annual"]),
    ],
)
def test_map_enums(col, expected):
    df = pd.DataFrame(
        {
            "lokata/konto": ["lok_ter", "lok_kon"],
            "rodzaj_oproc": ["stałe", "zmienne"],
            "okres_typ": ["mies.", "dni"],
            "kapitalizacja": ["miesięczna", "roczna"],
        }
    )
    result = map_enums(df)
    assert list(result[col]) == expected


def test_rename_columns():
    df = pd.DataFrame({"kod_banku": ["B1"], "nazwa_lokaty": ["Lokata"]})
    result = rename_columns(df)
    assert "bank_code" in result.columns
    assert "product_name" in result.columns


def test_reorder_columns():
    # Create df with all output columns but in random order
    df = pd.DataFrame({col: [] for col in reversed(OUTPUT_COLUMN_ORDER)})
    result = reorder_columns(df)
    assert list(result.columns) == OUTPUT_COLUMN_ORDER
