import os
import sys
import time
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# Ensure the scripts directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.clear_db import reset_db
from scripts.preprocess_lokaty import preprocess
from scripts.load_data import main as load_data_main


def wait_for_db(db_url):
    engine = create_engine(db_url)
    max_retries = 30
    for i in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("Database is ready!")
            return
        except OperationalError:
            print(f"Waiting for database... ({i + 1}/{max_retries})")
            time.sleep(2)
    print("Could not connect to database.")
    sys.exit(1)


def main():
    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg2://app:app@localhost:5432/passive_investment",
    )
    os.environ["DATABASE_URL"] = db_url

    print("Waiting for database...")
    wait_for_db(db_url)

    print("1. Resetting database schema and clearing data...")
    reset_db()

    print("2. Checking data files...")
    raw_csv = Path("data/raw/technical-details-deposit.csv")
    preprocessed_csv = Path("data/preprocessed/preprocessed_lokaty_warianty.csv")

    if not raw_csv.exists():
        print(f"ERROR: Raw CSV not found at {raw_csv}. Cannot proceed.")
        sys.exit(1)
    else:
        print(f"Raw CSV found: {raw_csv}")

    # Always preprocess to ensure latest data
    print("Preprocessing raw CSV...")
    try:
        preprocess()
    except Exception as e:
        print(f"Warning: Preprocessing failed: {e}")

    if not preprocessed_csv.exists():
        print(
            f"ERROR: Preprocessed CSV not found at {preprocessed_csv}. Cannot load data."
        )
        sys.exit(1)

    print("3. Loading data into database...")
    try:
        load_data_main()
    except Exception as e:
        print(f"Warning: Data loading failed: {e}")

    print("Database initialization complete.")


if __name__ == "__main__":
    main()
