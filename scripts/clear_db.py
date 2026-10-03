import argparse
import os
import subprocess
import sys

from sqlalchemy import create_engine, text


def get_db_engine(db_url: str):
    return create_engine(db_url)


def clear_rows(engine):
    print("Removing all rows from the database...")
    with engine.connect() as conn, conn.begin():
        # Truncate tables and restart identity
        conn.execute(text("TRUNCATE TABLE bank, product, offer_variant CASCADE;"))
    print("Rows removed successfully.")


def reset_db():
    print("Fully resetting the database via alembic...")
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_dir = os.path.join(project_root, "db")

    # Run alembic downgrade base
    print("Downgrading database to base...")
    result = subprocess.run(["uv", "run", "alembic", "downgrade", "base"], cwd=db_dir, check=False)
    if result.returncode != 0:
        print("Error during alembic downgrade.", file=sys.stderr)
        sys.exit(1)

    # Run alembic upgrade head
    print("Upgrading database to head...")
    result = subprocess.run(["uv", "run", "alembic", "upgrade", "head"], cwd=db_dir, check=False)
    if result.returncode != 0:
        print("Error during alembic upgrade.", file=sys.stderr)
        sys.exit(1)

    print("Database reset successfully.")


def main():
    parser = argparse.ArgumentParser(description="Clear the postgres database.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Fully reset the database (drop and recreate tables).",
    )
    args = parser.parse_args()

    db_url = "postgresql+psycopg2://app:app@localhost:5432/passive_investment"
    engine = get_db_engine(db_url)

    if args.reset:
        reset_db()
    else:
        clear_rows(engine)


if __name__ == "__main__":
    main()
