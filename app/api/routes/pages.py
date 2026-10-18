from decimal import Decimal
from datetime import date
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from fastapi.templating import Jinja2Templates

from app.db_and_finance_functions import (
    calculate_cash_flow_schedule,
    calculate_estimated_profit,
    get_offer_by_variant_id,
    get_offers,
)
from app.schemas.investment_request import InvestmentRequest, ProductEstimateRequest
from app.schemas.user import User

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


app_user = User(full_name="Piotr Cherek", email="x@gmail.com", password="qweqwe")
LOGGED_IN: bool = True
investment_details: dict[str, dict] = {}


@router.get("/", name="invest_page")
def invest_page(request: Request):
    context = {
        "products": get_offers(),
        "user": app_user if LOGGED_IN else None,
    }

    return templates.TemplateResponse(
        request=request,
        name="pages/dashboard.html",
        context=context,
    )


@router.get("/favorites", name="favorites_page")
def favorites_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="pages/favorites.html",
        context={
            "products": get_offers(variant_ids=app_user.favorites, active_only=False),
            "user": app_user if LOGGED_IN else None,
        },
    )


@router.get("/my_investments", name="my_investments_page")
def my_investments_page(request: Request):
    offers = get_offers(
        variant_ids=list(dict.fromkeys(app_user.investments)),
        active_only=False,
    )
    offers_by_variant = {offer["variant_id"]: offer for offer in offers}
    products = []
    for variant_id in dict.fromkeys(app_user.investments):
        offer = offers_by_variant.get(variant_id)
        if offer is None:
            continue
        records = [
            record
            for record in investment_details.values()
            if record["variant_id"] == variant_id
        ]
        if not records:
            products.append(offer)
            continue
        for record in records:
            product = {**offer, "investment": record}
            if record["amount"] is not None:
                product["estimated_amount"] = str(record["amount"])
                product["estimated_profit"] = record["estimated_profit"]
            products.append(product)

    return templates.TemplateResponse(
        request=request,
        name="pages/my_investments.html",
        context={
            "products": products,
            "user": app_user if LOGGED_IN else None,
        },
    )


@router.get("/login", name="login")
async def login(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="pages/login.html",
        context={},
    )


@router.get("/create_account", name="create_account")
async def create_account(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="pages/create_account.html",
        context={},
    )


@router.get("/product/{variant_id}", name="product_detail")
def product_detail(request: Request, variant_id: int, investment_id: str | None = None):
    product = get_offer_by_variant_id(variant_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Offer not found")
    investment = investment_details.get(investment_id or "")
    if investment is not None and investment["variant_id"] != variant_id:
        investment = None
    if investment is not None:
        product = {
            **product,
            "investment": investment,
            "estimated_amount": str(investment["amount"])
            if investment["amount"] is not None
            else None,
            "estimated_profit": investment["estimated_profit"]
            or product["estimated_profit"],
        }
        product["cash_flows"] = calculate_cash_flow_schedule(
            investment["amount"],
            investment["estimated_profit"],
            product["term_days"],
            product["currency"],
            start_date=date.fromisoformat(investment["start_date"]),
            term_value=Decimal(product["term_value"])
            if product["term_value"] is not None
            else None,
            term_unit=product["term_unit"],
        )

    return templates.TemplateResponse(
        request=request,
        name="pages/product_detail.html",
        context={
            "product": product,
            "investment": investment,
            "user": app_user if LOGGED_IN else None,
        },
    )


@router.post("/api/favorites/{variant_id}", name="toggle_favorite")
async def toggle_favorite(variant_id: int):
    is_favorite = False

    if variant_id in app_user.favorites:
        app_user.favorites.remove(variant_id)
    else:
        app_user.favorites.append(variant_id)
        is_favorite = True

    return {
        "variant_id": variant_id,
        "is_favorite": is_favorite,
        "favorites": app_user.favorites,
    }


@router.post("/api/my_investments/{variant_id}", name="add_investment")
async def add_investment(variant_id: int, investment: InvestmentRequest | None = None):
    offer = get_offer_by_variant_id(variant_id)
    if offer is None:
        raise HTTPException(status_code=404, detail="Offer not found")

    record = {
        "investment_id": uuid4().hex,
        "variant_id": variant_id,
        "amount": None,
        "horizon_months": None,
        "estimated_profit": None,
        "apy": offer["apy"],
        "start_date": date.today().isoformat(),
    }
    if investment is not None:
        record.update(investment.model_dump())
        rate = offer["annual_rate_decimal"]
        record["estimated_profit"] = calculate_estimated_profit(
            Decimal(rate) if rate is not None else None,
            investment.amount,
            offer["term_days"],
            offer["capitalization"],
            term_value=Decimal(offer["term_value"])
            if offer["term_value"] is not None
            else None,
            term_unit=offer["term_unit"],
        )
    app_user.investments.append(variant_id)
    investment_details[record["investment_id"]] = record

    return {
        "variant_id": variant_id,
        "investments": app_user.investments,
        "investment": record,
    }


@router.post("/api/estimates", name="estimate_products")
async def estimate_products(estimate: ProductEstimateRequest):
    products = get_offers(variant_ids=estimate.variant_ids, active_only=False)
    estimates = {}
    cash_flows = {}
    for product in products:
        rate = product["annual_rate_decimal"]
        variant_id = str(product["variant_id"])
        estimated_profit = calculate_estimated_profit(
            Decimal(rate) if rate is not None else None,
            estimate.amount,
            product["term_days"],
            product["capitalization"],
            term_value=Decimal(product["term_value"])
            if product["term_value"] is not None
            else None,
            term_unit=product["term_unit"],
        )
        estimates[variant_id] = estimated_profit
        cash_flows[variant_id] = calculate_cash_flow_schedule(
            estimate.amount,
            estimated_profit,
            product["term_days"],
            product["currency"],
            term_value=Decimal(product["term_value"])
            if product["term_value"] is not None
            else None,
            term_unit=product["term_unit"],
        )
    return {"estimates": estimates, "cash_flows": cash_flows}


@router.post("/api/users")
async def create_user(user: User):
    print(user)

    return {
        "message": "User created",
        "email": user.email,
    }


# @router.post("/api/login")
# async def login(user: LoginRequest):
#     db_user =
#
#     if db_user is None:
#         raise HTTPException(
#             status_code=401,
#             detail="Invalid email or password"
#         )
#
#     if not verify_password(user.password, db_user.password_hash):
#         raise HTTPException(
#             status_code=401,
#             detail="Invalid email or password"
#         )
#
#     return {
#         "message": "Login successful",
#         "email": db_user.email,
#     }
