from calendar import monthrange
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient

from app import main
from app.api.routes import pages
from app.db_and_finance_functions import _map_offer


def test_registration_and_login_store_a_password_hash(monkeypatch):
    stored = {}
    user = {
        "id": 9,
        "full_name": "Test User",
        "email": "test@example.com",
        "favorites": [],
        "investments": [],
    }

    def create_user(full_name, email, password_hash):
        stored["password_hash"] = password_hash
        return user["id"]

    monkeypatch.setattr(pages, "create_user", create_user)
    monkeypatch.setattr(pages, "get_user_state", lambda user_id: user)
    monkeypatch.setattr(
        pages,
        "get_user_by_email",
        lambda email: {**user, "password_hash": stored["password_hash"]},
    )

    with TestClient(main.app) as client:
        registered = client.post(
            "/api/register",
            json={
                "full_name": "Test User",
                "email": "TEST@example.com",
                "password": "test-password-123",
            },
        )
        assert registered.status_code == 200
        assert stored["password_hash"] != "test-password-123"
        assert pages._verify_password("test-password-123", stored["password_hash"])

        client.post("/api/logout")
        logged_in = client.post(
            "/api/login",
            json={"email": "test@example.com", "password": "test-password-123"},
        )
        assert logged_in.status_code == 200
        assert logged_in.json()["user"]["id"] == user["id"]


def test_repeated_investments_keep_distinct_amounts_and_detail_links(monkeypatch):
    offer = _map_offer(
        {
            "product_type": "term_deposit",
            "capitalization": "monthly",
            "currency": "PLN",
            "interest_rate": Decimal("0.045"),
            "term_days": 91,
            "product_id": 1,
            "variant_id": 7001,
            "variant_code": "DEP-1",
            "institution_name": "Bank",
            "name": "Deposit",
            "term_value": Decimal(3),
            "term_unit": "months",
            "rate_type": "fixed",
            "additional_condition": None,
            "apy": None,
            "interest_payout": None,
            "inflation_indexed": None,
            "early_termination": None,
            "interest_details": None,
        }
    )
    user = {"id": 1, "full_name": "Test User", "email": "test@example.com"}
    records = []

    def create_investment(user_id, variant_id, amount, horizon_months, profit, apy):
        record = {
            "id": len(records) + 1,
            "variant_id": variant_id,
            "amount": amount,
            "horizon_months": horizon_months,
            "estimated_profit": profit,
            "apy": apy,
            "start_date": date.today(),
        }
        records.append(record)
        return record

    monkeypatch.setattr(pages, "get_offer_by_variant_id", lambda variant_id: offer)
    monkeypatch.setattr(pages, "get_offers", lambda **kwargs: [offer])
    monkeypatch.setattr(pages, "_current_user", lambda request: user)
    monkeypatch.setattr(pages, "get_user_investments", lambda user_id: records)
    monkeypatch.setattr(pages, "create_user_investment", create_investment)
    monkeypatch.setattr(
        pages,
        "get_user_investment",
        lambda user_id, investment_id: next(
            (record for record in records if record["id"] == investment_id),
            None,
        ),
    )
    monkeypatch.setattr(
        pages,
        "get_user_state",
        lambda user_id: {
            **user,
            "favorites": [],
            "investments": [record["variant_id"] for record in records],
        },
    )

    try:
        with TestClient(main.app) as client:
            first = client.post(
                "/api/my_investments/7001",
                json={
                    "amount": 10000,
                    "horizon_months": 3,
                    "product_types": ["bank_deposits"],
                    "payout_methods": ["at_end"],
                },
            ).json()["investment"]
            second = client.post(
                "/api/my_investments/7001",
                json={
                    "amount": 20000,
                    "horizon_months": 3,
                    "product_types": ["bank_deposits"],
                    "payout_methods": ["at_end"],
                },
            ).json()["investment"]

            assert first["investment_id"] != second["investment_id"]
            assert first["estimated_profit"] == "112.92"
            assert second["estimated_profit"] == "225.84"

            investments_page = client.get("/my_investments")
            assert investments_page.text.count("Invested ") == 2
            assert "112.92 PLN" in investments_page.text
            assert "225.84 PLN" in investments_page.text
            assert f"investment_id={first['investment_id']}" in investments_page.text
            assert f"investment_id={second['investment_id']}" in investments_page.text

            first_detail = client.get(
                f"/product/7001?investment_id={first['investment_id']}"
            )
            assert "112.92 PLN" in first_detail.text
            assert "10112.92 PLN" in first_detail.text
            assert "Cash flow schedule" in first_detail.text

            estimates = client.post(
                "/api/estimates",
                json={"amount": 10000, "variant_ids": [7001]},
            ).json()
            assert estimates["estimates"]["7001"] == "112.92"
            start_date = date.fromisoformat(first["start_date"])
            month_index = start_date.year * 12 + start_date.month - 1 + 3
            maturity_year, maturity_month_index = divmod(month_index, 12)
            maturity_month = maturity_month_index + 1
            maturity_day = min(
                start_date.day,
                monthrange(maturity_year, maturity_month)[1],
            )
            expected_maturity_date = date(
                maturity_year,
                maturity_month,
                maturity_day,
            ).isoformat()
            assert estimates["cash_flows"]["7001"][-1]["date"] == expected_maturity_date
            assert estimates["cash_flows"]["7001"][-1]["amount"] == "10112.92"
    finally:
        records.clear()
