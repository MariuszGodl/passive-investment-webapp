import os

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text


def get_db_engine(db_url: str):
    """Creates and returns a SQLAlchemy engine."""
    return create_engine(db_url)


def load_and_clean_csv(csv_path: str) -> pd.DataFrame:
    """Loads CSV into a DataFrame and replaces NaNs with None."""
    print(f"Loading data from {csv_path}...")
    df = pd.read_csv(csv_path)
    # Replace nan with None so psycopg2 inserts NULL instead of NaN
    return df.replace({np.nan: None})


def insert_banks(conn, df: pd.DataFrame):
    """Extracts unique banks and inserts them into the database."""
    initial_count = len(df)
    banks_df = df[["bank_code"]].drop_duplicates()
    dropped_count = initial_count - len(banks_df)
    print(f"Dropped {dropped_count} duplicate banks")
    for _, row in banks_df.iterrows():
        conn.execute(
            text("""
                INSERT INTO bank (code, name)
                VALUES (:code, :name)
            """),
            {"code": row["bank_code"], "name": f"Brak: {row['bank_code']}"},
        )
    print(f"Inserted {len(banks_df)} banks")


def insert_products(conn, df: pd.DataFrame):
    """Extracts unique products and inserts them into the database."""
    initial_count = len(df)
    products_df = df[
        ["bank_code", "product_code", "product_name", "product_type"]
    ].drop_duplicates(subset=["bank_code", "product_code"])
    dropped_count = initial_count - len(products_df)
    print(f"Dropped {dropped_count} duplicate products")
    for _, row in products_df.iterrows():
        conn.execute(
            text("""
                INSERT INTO product (bank_id, code, name, product_type)
                SELECT id, :code, :name, :product_type
                FROM bank WHERE code = :bank_code
            """),
            {
                "bank_code": row["bank_code"],
                "code": row["product_code"],
                "name": row["product_name"],
                "product_type": row["product_type"],
            },
        )
    print(f"Inserted {len(products_df)} products")


def insert_variants(conn, df: pd.DataFrame):
    """Inserts or updates offer variants into the database."""
    print("Inserting variants...")
    initial_count = len(df)
    variants_df = df.drop_duplicates(
        subset=["bank_code", "product_code", "variant_code"]
    )
    dropped_count = initial_count - len(variants_df)
    print(f"Dropped {dropped_count} duplicate variants")
    for _, row in variants_df.iterrows():
        conn.execute(
            text("""
                INSERT INTO offer_variant (
                    product_id, variant_code,
                    interest_rate, apy, rate_type, term_value, term_unit,
                    term_days, currency,
                    capitalization, interest_payout,
                    inflation_indexed, early_termination,
                    interest_details, additional_condition
                )
                SELECT p.id, :variant_code,
                    :interest_rate, :apy, :rate_type, :term_value, :term_unit,
                    :term_days, :currency,
                    :capitalization, :interest_payout,
                    :inflation_indexed, :early_termination,
                    :interest_details, :additional_condition
                FROM product p
                JOIN bank b ON b.id = p.bank_id
                WHERE p.code = :product_code AND b.code = :bank_code
            """),
            {
                "bank_code": row["bank_code"],
                "product_code": row["product_code"],
                "variant_code": row["variant_code"],
                "interest_rate": row["interest_rate"],
                "apy": row.get("apy"),
                "rate_type": row["rate_type"],
                "term_value": row.get("term_value"),
                "term_unit": row.get("term_unit"),
                "term_days": row.get("term_days"),
                "currency": row["currency"]
                if pd.notnull(row.get("currency"))
                else "PLN",
                "capitalization": row.get("capitalization"),
                "interest_payout": row.get("interest_payout"),
                "inflation_indexed": row.get("inflation_indexed"),
                "early_termination": row.get("early_termination"),
                "interest_details": row.get("interest_details"),
                "additional_condition": row.get("additional_condition"),
            },
        )
    print(f"Inserted/Updated {len(variants_df)} variants")


def main():
    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg2://app:app@localhost:5432/passive_investment",
    )
    csv_path = "data/preprocessed/preprocessed_lokaty_warianty.csv"

    df = load_and_clean_csv(csv_path)
    engine = get_db_engine(db_url)

    with engine.connect() as conn, conn.begin():
        insert_banks(conn, df)
        insert_products(conn, df)
        insert_variants(conn, df)


if __name__ == "__main__":
    main()
