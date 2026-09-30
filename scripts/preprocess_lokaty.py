"""Preprocess lokaty_warianty.csv into DB-ready format.

Reads data/raw/lokaty_warianty.csv and outputs
data/preprocessed/preprocessed_lokaty_warianty.csv with:
- Internal columns dropped (data_edycji, edytor, okres_mies_automat)
- Enum values mapped to English DB values
- term_days computed from okres + okres_typ
- Currency columns merged into single column
- Columns renamed to match DB schema
"""

from pathlib import Path

import pandas as pd

# -- Paths ---------------------------------------------------------------------

RAW_PATH = Path("data/raw/lokaty_warianty.csv")
OUT_PATH = Path("data/preprocessed/preprocessed_lokaty_warianty.csv")

# -- Columns to drop (internal / redundant) ------------------------------------

DROP_COLUMNS = ["data_edycji", "edytor", "okres_mies_automat"]
CURRENCY_COLUMNS = ["min_kwota_waluta", "max_kwota_waluta"]

# -- Constants -----------------------------------------------------------------

AVG_DAYS_PER_MONTH = 30.44
DEFAULT_CURRENCY = "PLN"

# -- Enum column classification ------------------------------------------------

REQUIRED_ENUM_COLUMNS = ["lokata/konto", "rodzaj_oproc"]
NULLABLE_ENUM_COLUMNS = {"okres_typ", "kapitalizacja"}

# -- Enum mappings (Polish CSV values to English DB enum values) ----------------

PRODUCT_TYPE_MAP = {
    "lok_ter": "term_deposit",
    "lok_kon": "savings_account",
    "lok_fun": "deposit_with_fund",
}

RATE_TYPE_MAP = {
    "stałe": "fixed",
    "zmienne": "variable",
}

TERM_UNIT_MAP = {
    "mies.": "months",
    "dni": "days",
}

CAPITALIZATION_MAP = {
    "na zakończenie lokaty": "at_maturity",
    "miesięczna": "monthly",
    "kwartalna": "quarterly",
    "dzienna": "daily",
    "roczna": "annual",
    "na zakończenie promocji": "at_promo_end",
}

COLUMN_RENAME_MAP = {
    "kod_banku": "bank_code",
    "nazwa_lokaty": "product_name",
    "kod_lokaty": "product_code",
    "lokata/konto": "product_type",
    "kod_wariantu": "variant_code",
    "data_od": "valid_from",
    "data_do": "valid_to",
    "min_kwota": "min_amount",
    "max_kwota": "max_amount",
    "okres": "term_value",
    "okres_typ": "term_unit",
    "oproc": "interest_rate",
    "rodzaj_oproc": "rate_type",
    "dodatkowy_warunek": "additional_condition",
    "kapitalizacja": "capitalization",
}

ENUM_CHECKS = {
    "lokata/konto": PRODUCT_TYPE_MAP,
    "rodzaj_oproc": RATE_TYPE_MAP,
    "okres_typ": TERM_UNIT_MAP,
    "kapitalizacja": CAPITALIZATION_MAP,
}

OUTPUT_COLUMN_ORDER = [
    # bank
    "bank_code",
    # product
    "product_code",
    "product_name",
    "product_type",
    # offer_variant
    "variant_code",
    "valid_from",
    "valid_to",
    "interest_rate",
    "rate_type",
    "term_value",
    "term_unit",
    "term_days",
    "min_amount",
    "max_amount",
    "currency",
    "capitalization",
    "additional_condition",
]


def compute_term_days(row: pd.Series) -> float | None:
    """Convert okres + okres_typ to a uniform number of days."""
    if pd.isna(row["okres"]) or pd.isna(row["okres_typ"]):
        return None
    value = float(row["okres"])
    unit = row["okres_typ"]
    if unit == "dni":
        return round(value)
    if unit == "mies.":
        return round(value * AVG_DAYS_PER_MONTH)
    return None


def merge_currency(row: pd.Series) -> str:
    """Merge min_kwota_waluta and max_kwota_waluta into single currency."""
    min_cur = row.get("min_kwota_waluta")
    max_cur = row.get("max_kwota_waluta")
    min_cur = min_cur if pd.notna(min_cur) and min_cur != "" else None
    max_cur = max_cur if pd.notna(max_cur) and max_cur != "" else None

    if min_cur and max_cur and min_cur != max_cur:
        raise ValueError(
            f"Currency mismatch: min={min_cur}, max={max_cur} "
            f"in variant {row.get('kod_wariantu', '?')}"
        )
    return min_cur or max_cur or DEFAULT_CURRENCY


# -- Pipeline steps ------------------------------------------------------------


def drop_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Remove internal and redundant columns."""
    return df.drop(columns=DROP_COLUMNS)


def add_term_days(df: pd.DataFrame) -> pd.DataFrame:
    """Compute normalized term_days from okres + okres_typ."""
    df["term_days"] = df.apply(compute_term_days, axis=1)
    df["term_days"] = df["term_days"].astype("Int64")  # nullable int
    return df


def add_currency(df: pd.DataFrame) -> pd.DataFrame:
    """Merge two currency columns into one, then drop the originals."""
    df["currency"] = df.apply(merge_currency, axis=1)
    df = df.drop(columns=CURRENCY_COLUMNS)
    return df


def drop_invalid_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows where required enum columns are empty."""
    for col in REQUIRED_ENUM_COLUMNS:
        bad = df[df[col].isna()]
        if not bad.empty:
            codes = bad["kod_wariantu"].tolist()
            print(f"  WARNING: dropping {len(bad)} rows with empty {col}: {codes}")
            df = df[df[col].notna()]
    return df


def validate_enums(df: pd.DataFrame) -> None:
    """Raise ValueError if any enum column contains unexpected values."""
    errors: list[str] = []
    for col, mapping in ENUM_CHECKS.items():
        values = (
            df[col].dropna().unique()
            if col in NULLABLE_ENUM_COLUMNS
            else df[col].unique()
        )
        unknown = set(values) - set(mapping.keys())
        if unknown:
            errors.append(f"  {col}: unexpected values {unknown}")

    if errors:
        raise ValueError("Unknown enum values found in CSV:\n" + "\n".join(errors))


def map_enums(df: pd.DataFrame) -> pd.DataFrame:
    """Replace Polish enum values with English DB enum values."""
    for col, mapping in ENUM_CHECKS.items():
        df[col] = df[col].map(mapping)
    return df


def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename CSV columns to match DB schema."""
    return df.rename(columns=COLUMN_RENAME_MAP)


def reorder_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Reorder columns to logical grouping (bank → product → offer)."""
    return df[OUTPUT_COLUMN_ORDER]


def print_summary(df: pd.DataFrame) -> None:
    """Print stats about the processed data."""
    print(f"\n  Banks:    {df['bank_code'].nunique()}")
    print(f"  Products: {df['product_code'].nunique()}")
    print(f"  Variants: {df['variant_code'].nunique()}")
    print(f"  Active:   {df['valid_to'].isna().sum()} (valid_to is empty)")


# -- Main ----------------------------------------------------------------------


def preprocess() -> None:
    """Run the full preprocessing pipeline."""
    print(f"Reading {RAW_PATH} ...")
    df = pd.read_csv(RAW_PATH, encoding="utf-8-sig")
    print(f"  {len(df)} rows, {len(df.columns)} columns")

    df = drop_columns(df)
    df = add_term_days(df)
    df = add_currency(df)
    df = drop_invalid_rows(df)
    validate_enums(df)
    df = map_enums(df)
    df = rename_columns(df)
    df = reorder_columns(df)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False)
    print(f"  Written {len(df)} rows → {OUT_PATH}")

    print_summary(df)


if __name__ == "__main__":
    preprocess()
