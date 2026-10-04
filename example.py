import os
from sqlalchemy import create_engine, text


def get_bond_technical_details():
    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg2://app:app@localhost:5432/passive_investment",
    )
    engine = create_engine(db_url)

    with engine.connect() as conn:
        # Pull a sample record from offer_variant joining with product
        query = text("""
            SELECT
                ov.term_value,
                ov.term_unit,
                ov.rate_type,
                ov.apy,
                ov.interest_rate,
                ov.capitalization,
                ov.interest_payout,
                ov.inflation_indexed,
                ov.early_termination
            FROM offer_variant ov
            LIMIT 1
        """)

        result = conn.execute(query).fetchone()

        if result:
            term = (
                f"{result.term_value} {result.term_unit}"
                if result.term_value
                else "Unknown"
            )
            rate = result.apy if result.apy is not None else result.interest_rate

            return {
                "Bond duration": term,
                "Interest rate type": result.rate_type.capitalize()
                if result.rate_type
                else "Unknown",
                "Annual interest rate": f"{rate}% APY" if rate else "Unknown",
                "Investment value": "10 000 PLN",  # Hardcoded mock, can be dynamic
                "Estimated profit": "Needs to be computed i will add this as column to db in future",
                "Interest capitalization": result.capitalization.capitalize()
                if result.capitalization
                else "Unknown",
                "Interest payout during investment": "Yes"
                if result.interest_payout
                else "No",
                "Interest payout frequency": result.interest_payout
                if result.interest_payout
                else "Unknown",
                "Inflation-indexed interest": "Yes"
                if result.inflation_indexed
                else "No",
                "Early redemption option": "Yes" if result.early_termination else "No",
            }
        else:
            return {"Error": "No data found in the database."}


if __name__ == "__main__":
    try:
        bond_data = get_bond_technical_details()
        for key, value in bond_data.items():
            print(f"{key}: {value}")
    except Exception as e:
        print(f"Error connecting to DB or executing query: {e}")
