import os
import sys
import time
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# Ensure the scripts directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.clear_db import reset_db
from scripts.convert_excel_to_csv import convert_excel_to_csv
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
    raw_csv = Path("data/raw/lokaty_warianty.csv")
    excel_path = Path("data/raw/lokaty.xlsx")

    # Check if raw csv exists or needs generating
    if not raw_csv.exists() and excel_path.exists():
        print(f"Raw CSV not found. Converting from {excel_path}...")
        convert_excel_to_csv(str(excel_path))
    elif raw_csv.exists():
        print("Raw CSV already exists.")
    else:
        print(f"Neither {raw_csv} nor {excel_path} found. Skipping conversion.")

    preprocessed_csv = Path("data/preprocessed/preprocessed_lokaty_warianty.csv")

    # Always try to preprocess if preprocessed file is missing or if we want to ensure latest.
    if not preprocessed_csv.exists():
        print("Preprocessed CSV not found. Preprocessing...")
        try:
            preprocess()
        except Exception as e:
            print(f"Warning: Preprocessing failed: {e}")
    else:
        print("Preprocessed CSV already exists.")

    print("3. Loading data into database...")
    try:
        load_data_main()
    except Exception as e:
        print(f"Warning: Data loading failed: {e}")

    print("Database initialization complete.")


if __name__ == "__main__":
    main()
