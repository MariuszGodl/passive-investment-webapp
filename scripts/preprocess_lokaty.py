"""Preprocess technical-details-deposit.csv into DB-ready format.

Reads data/raw/technical-details-deposit.csv and outputs
data/preprocessed/preprocessed_lokaty_warianty.csv with:
- Dual-header rows handled (row 1 = Polish, row 2 = English → skipped)
- Placeholder values cleaned (e.g. "typed by the user", "calculated")
- term_days computed from okres + okres_typ
- Capitalization values normalized to DB enum values
- Multiple "Dodatkowe wymagania" columns merged into single text
- Columns renamed/selected to match DB schema
"""

from pathlib import Path

import pandas as pd

# -- Paths ---------------------------------------------------------------------

RAW_PATH = Path("data/raw/technical-details-deposit.csv")
OUT_PATH = Path("data/preprocessed/preprocessed_lokaty_warianty.csv")

# -- Constants -----------------------------------------------------------------

AVG_DAYS_PER_MONTH = 30.44

# -- Column indices (0-based) in the raw CSV -----------------------------------
# Row 1 (Polish headers):
#  0: kod banku
#  1: kod_lokaty
#  2: kod_wariantu
#  3: (unnamed – product name)
#  4: okres trwania
#  5: okres
#  6: okres typ
#  7: typ oprocentowania
#  8: roczne oprocentowanie
#  9: APY (calculated)
# 10: APY (second column, same label)
# 11: wartość oprocentowania
# 12: szacowany zysk
# 13: kapitalizacja odsetek
# 14: wypłata odsetek w trakcie trwania inwestycji
# 15: oprocentowanie zależne od inflacji
# 16: Możliwośc wcześniejszego zakończenia inwestycji
# 17: szczegóły odsetek
# 18: Dodatkowe wymagania  (1)
# 19: Dodatkowe wymagania  (2)
# 20: Dodatkowe wymagania  (3)

COL_BANK_CODE = 0
COL_PRODUCT_CODE = 1
COL_VARIANT_CODE = 2
COL_PRODUCT_NAME = 3
# COL_DEPOSIT_DURATION = 4  # user-typed, skip
COL_TERM_VALUE = 5
COL_TERM_UNIT = 6
COL_RATE_TYPE = 7
COL_INTEREST_RATE = 8
COL_APY = 9
# COL_APY2 = 10  # "calculated" label, skip
# COL_INVESTMENT_VALUE = 11  # user-typed, skip
# COL_ESTIMATED_VALUE = 12  # calculated, skip
COL_CAPITALIZATION = 13
COL_INTEREST_PAYOUT = 14
COL_INFLATION_INDEXED = 15
COL_EARLY_TERMINATION = 16
COL_INTEREST_DETAILS = 17
COL_REQ_1 = 18
COL_REQ_2 = 19
COL_REQ_3 = 20


# -- Capitalization normalization ----------------------------------------------

CAPITALIZATION_MAP = {
    "at maturity": "at_maturity",
    "monthly": "monthly",
    "quarterly": "quarterly",
    "daily": "daily",
    "annual": "annual",
    "at promo end": "at_promo_end",
    "at_maturity": "at_maturity",
    "at_promo_end": "at_promo_end",
}

# -- Product type inference ----------------------------------------------------
# The new CSV doesn't have an explicit product_type column.
# We infer from the product name.

SAVINGS_ACCOUNT_KEYWORDS = [
    "konto oszczędnościowe",
    "konto mega oszczędnościowe",
    "rachunek oszczędnościowy",
    "konto zasobne",
    "konto lokacyjne",
    "ekokonto oszczędnościowe",
    "konto pełne marzeń",
    "konto superoszczędnościowe",
    "konto oszczędzam",
    "rachunek oszczędzam",
]

FUND_KEYWORDS = [
    "z funduszem",
    "lokata z funduszem",
]


# COME BACK TO IT -------------------------
def infer_product_type(name: str) -> str:
    """Infer product type from the product name."""
    if pd.isna(name) or not name:
        return "term_deposit"
    lower = name.lower().strip()
    for kw in FUND_KEYWORDS:
        if kw in lower:
            return "deposit_with_fund"
    for kw in SAVINGS_ACCOUNT_KEYWORDS:
        if kw in lower:
            return "savings_account"
    return "term_deposit"


# -- Helpers -------------------------------------------------------------------


def clean_placeholder(val) -> None | str:
    """Return None for placeholder / empty values."""
    if pd.isna(val):
        return None
    s = str(val).strip().lower()
    if s in ("typed by the user", "typed by user", "calculated", ""):
        return None
    return str(val).strip()


def parse_numeric(val) -> float | None:
    """Parse a numeric value, returning None for placeholders."""
    cleaned = clean_placeholder(val)
    if cleaned is None:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_yes_no(val) -> bool | None:
    """Parse Yes/No values."""
    cleaned = clean_placeholder(val)
    if cleaned is None:
        return None
    return cleaned.lower() == "yes"


def normalize_capitalization(val) -> str | None:
    """Normalize capitalization value to DB enum."""
    cleaned = clean_placeholder(val)
    if cleaned is None:
        return None
    lower = cleaned.lower().strip()
    mapped = CAPITALIZATION_MAP.get(lower)
    if mapped:
        return mapped
    # Try without spaces
    normalized = lower.replace(" ", "_")
    if normalized in CAPITALIZATION_MAP.values():
        return normalized
    print(f"  WARNING: unknown capitalization value: '{cleaned}'")
    return None


def merge_requirements(*args) -> str | None:
    """Merge multiple requirement columns into a single string."""
    parts = []
    for val in args:
        cleaned = clean_placeholder(val)
        if cleaned:
            parts.append(cleaned)
    return " | ".join(parts) if parts else None


def compute_term_days(term_value, term_unit) -> int | None:
    """Convert term_value + term_unit to uniform number of days."""
    if term_value is None or term_unit is None:
        return None
    try:
        value = float(term_value)
    except (ValueError, TypeError):
        return None
    unit = str(term_unit).lower().strip()
    if unit == "days":
        return round(value)
    if unit == "months":
        return round(value * AVG_DAYS_PER_MONTH)
    return None


# -- Main pipeline -------------------------------------------------------------


def read_raw_csv() -> pd.DataFrame:
    """Read the raw CSV and drop the English header row."""
    print(f"Reading {RAW_PATH} ...")
    # Row 0 = Polish headers
    # Row 1 = English headers
    # Row 2+ = data
    df = pd.read_csv(RAW_PATH, encoding="utf-8", header=0, skiprows=[1])
    cols = df.columns.tolist()
    print(f"  {len(df)} rows, {len(cols)} columns")
    return df


def process_row(raw) -> dict | None:
    """Process a single row from the raw CSV into a valid DB record. Returns None if invalid."""
    bank_code = (
        str(raw[COL_BANK_CODE]).strip() if pd.notna(raw[COL_BANK_CODE]) else None
    )
    product_code = (
        str(raw[COL_PRODUCT_CODE]).strip() if pd.notna(raw[COL_PRODUCT_CODE]) else None
    )
    variant_code = (
        str(raw[COL_VARIANT_CODE]).strip() if pd.notna(raw[COL_VARIANT_CODE]) else None
    )
    product_name = (
        str(raw[COL_PRODUCT_NAME]).strip() if pd.notna(raw[COL_PRODUCT_NAME]) else None
    )

    term_value = parse_numeric(raw[COL_TERM_VALUE])
    term_unit_raw = clean_placeholder(raw[COL_TERM_UNIT])
    rate_type_raw = clean_placeholder(raw[COL_RATE_TYPE])
    interest_rate = parse_numeric(raw[COL_INTEREST_RATE])
    apy = parse_numeric(raw[COL_APY])

    capitalization = normalize_capitalization(raw[COL_CAPITALIZATION])
    interest_payout = clean_placeholder(raw[COL_INTEREST_PAYOUT])
    inflation_indexed = parse_yes_no(raw[COL_INFLATION_INDEXED])
    early_termination = parse_yes_no(raw[COL_EARLY_TERMINATION])
    interest_details = clean_placeholder(raw[COL_INTEREST_DETAILS])

    # Merge additional requirements
    req1 = raw[COL_REQ_1] if COL_REQ_1 < len(raw) else None
    req2 = raw[COL_REQ_2] if COL_REQ_2 < len(raw) else None
    req3 = raw[COL_REQ_3] if COL_REQ_3 < len(raw) else None
    additional_condition = merge_requirements(req1, req2, req3)

    # Normalize term_unit
    term_unit = None
    if term_unit_raw:
        lower = term_unit_raw.lower()
        if lower in ("months", "month"):
            term_unit = "months"
        elif lower in ("days", "day"):
            term_unit = "days"
        else:
            print(f"  WARNING: unknown term_unit '{term_unit_raw}' for {variant_code}")

    # Normalize rate_type
    rate_type = None
    if rate_type_raw:
        lower = rate_type_raw.lower()
        if lower == "fixed":
            rate_type = "fixed"
        elif lower == "variable":
            rate_type = "variable"
        else:
            print(f"  WARNING: unknown rate_type '{rate_type_raw}' for {variant_code}")

    # Compute term_days
    term_days = compute_term_days(term_value, term_unit)

    # Infer product_type
    product_type = infer_product_type(product_name)

    # Validate required fields
    if not bank_code or not product_code or not variant_code:
        raise ValueError(
            "Missing critical identifiers (bank_code, product_code, or variant_code) in row"
        )
    if rate_type is None:
        raise ValueError(f"Missing rate_type for variant: {variant_code}")
    if interest_rate is None:
        raise ValueError(f"Missing interest_rate for variant: {variant_code}")

    # COME BACK TO IT --------------------------- (Maby add validation logic for apy)
    return {
        "bank_code": bank_code,
        "product_code": product_code,
        "product_name": product_name,
        "product_type": product_type,
        "variant_code": variant_code,
        "interest_rate": interest_rate,
        "apy": apy,
        "rate_type": rate_type,
        "term_value": term_value,
        "term_unit": term_unit,
        "term_days": term_days,
        "capitalization": capitalization,
        "interest_payout": interest_payout,
        "inflation_indexed": inflation_indexed,
        "early_termination": early_termination,
        "interest_details": interest_details,
        "additional_condition": additional_condition,
        "currency": "PLN",
    }


def format_and_save_output(records: list[dict]) -> pd.DataFrame:
    """Format the list of records into a DataFrame and save to CSV."""
    out_df = pd.DataFrame(records)

    # Convert term_days to nullable int
    if "term_days" in out_df.columns:
        out_df["term_days"] = out_df["term_days"].astype("Int64")

    # Reorder columns
    output_columns = [
        "bank_code",
        "product_code",
        "product_name",
        "product_type",
        "variant_code",
        "interest_rate",
        "apy",
        "rate_type",
        "term_value",
        "term_unit",
        "term_days",
        "currency",
        "capitalization",
        "interest_payout",
        "inflation_indexed",
        "early_termination",
        "interest_details",
        "additional_condition",
    ]
    out_df = out_df[output_columns]

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUT_PATH, index=False)
    print(f"  Written {len(out_df)} rows → {OUT_PATH}")
    return out_df


def print_summary(out_df: pd.DataFrame) -> None:
    """Print summary statistics."""
    print(f"\n  Banks:    {out_df['bank_code'].nunique()}")
    print(f"  Products: {out_df['product_code'].nunique()}")
    print(f"  Variants: {out_df['variant_code'].nunique()}")
    print(f"  Rate types: {out_df['rate_type'].value_counts().to_dict()}")
    print(f"  Product types: {out_df['product_type'].value_counts().to_dict()}")


def preprocess() -> None:
    """Run the full preprocessing pipeline."""
    df = read_raw_csv()

    records = []
    for _, row in df.iterrows():
        record = process_row(row.values)
        if record:
            records.append(record)

    out_df = format_and_save_output(records)
    print_summary(out_df)


if __name__ == "__main__":
    preprocess()
