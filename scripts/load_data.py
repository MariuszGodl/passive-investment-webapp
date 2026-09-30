import pandas as pd
from sqlalchemy import create_engine, text
import numpy as np


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
    banks_df = df[["bank_code"]].drop_duplicates()
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
    products_df = df[
        ["bank_code", "product_code", "product_name", "product_type"]
    ].drop_duplicates()
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
    for _, row in df.iterrows():
        conn.execute(
            text("""
                INSERT INTO offer_variant (
                    product_id, variant_code, valid_from, valid_to,
                    interest_rate, rate_type, term_value, term_unit,
                    term_days, min_amount, max_amount, currency,
                    capitalization, additional_condition
                )
                SELECT p.id, :variant_code, :valid_from, :valid_to,
                    :interest_rate, :rate_type, :term_value, :term_unit,
                    :term_days, :min_amount, :max_amount, :currency,
                    :capitalization, :additional_condition
                FROM product p
                JOIN bank b ON b.id = p.bank_id
                WHERE p.code = :product_code AND b.code = :bank_code
            """),
            {
                "bank_code": row["bank_code"],
                "product_code": row["product_code"],
                "variant_code": row["variant_code"],
                "valid_from": row["valid_from"],
                "valid_to": row["valid_to"],
                "interest_rate": row["interest_rate"],
                "rate_type": row["rate_type"],
                "term_value": row["term_value"],
                "term_unit": row["term_unit"],
                "term_days": row["term_days"],
                "min_amount": row["min_amount"],
                "max_amount": row["max_amount"],
                "currency": row["currency"] if pd.notnull(row["currency"]) else "PLN",
                "capitalization": row["capitalization"],
                "additional_condition": row["additional_condition"],
            },
        )
    print(f"Inserted/Updated {len(df)} variants")


def main():
    db_url = "postgresql+psycopg2://app:app@localhost:5432/passive_investment"
    csv_path = "data/preprocessed/preprocessed_lokaty_warianty.csv"

    df = load_and_clean_csv(csv_path)
    engine = get_db_engine(db_url)

    with engine.connect() as conn:
        with conn.begin():
            insert_banks(conn, df)
            insert_products(conn, df)
            insert_variants(conn, df)


if __name__ == "__main__":
    main()
