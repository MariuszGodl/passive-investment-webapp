import hashlib
import hmac
import secrets
from decimal import Decimal
from datetime import date

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import IntegrityError

from app.db_and_finance_functions import (
    calculate_cash_flow_schedule,
    calculate_estimated_profit,
    create_user,
    create_user_investment,
    get_offer_by_variant_id,
    get_offers,
    get_user_by_email,
    get_user_investment,
    get_user_investments,
    get_user_state,
    toggle_user_favorite,
)
from app.schemas.investment_request import InvestmentRequest, ProductEstimateRequest
from app.schemas.login_request import CreateAccountRequest, LoginRequest

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


_PASSWORD_ITERATIONS = 600_000


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt,
        _PASSWORD_ITERATIONS,
    )
    return f"pbkdf2_sha256${_PASSWORD_ITERATIONS}${salt.hex()}${digest.hex()}"


def _verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = password_hash.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            bytes.fromhex(salt_hex),
            int(iterations),
        )
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def _current_user(request: Request) -> dict | None:
    user_id = request.session.get("user_id")
    return get_user_state(user_id) if user_id is not None else None


def _require_user(request: Request) -> dict:
    user = _current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


@router.get("/", name="invest_page")
def invest_page(request: Request):
    user = _current_user(request)
    context = {
        "products": get_offers(),
        "user": user,
    }

    return templates.TemplateResponse(
        request=request,
        name="pages/dashboard.html",
        context=context,
    )


@router.get("/favorites", name="favorites_page")
def favorites_page(request: Request):
    user = _current_user(request)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="pages/favorites.html",
        context={
            "products": get_offers(variant_ids=user["favorites"]),
            "user": user,
        },
    )


@router.get("/my_investments", name="my_investments_page")
def my_investments_page(request: Request):
    user = _current_user(request)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    records = get_user_investments(user["id"])
    offers = get_offers(
        variant_ids=list(dict.fromkeys(record["variant_id"] for record in records)),
    )
    offers_by_variant = {offer["variant_id"]: offer for offer in offers}
    products = []
    for record in records:
        offer = offers_by_variant.get(record["variant_id"])
        if offer is None:
            continue
        investment = {
            **record,
            "investment_id": str(record["id"]),
            "start_date": record["start_date"].isoformat(),
        }
        product = {**offer, "investment": investment}
        if record["amount"] is not None:
            product["estimated_amount"] = str(record["amount"])
            product["estimated_profit"] = record["estimated_profit"]
        products.append(product)

    return templates.TemplateResponse(
        request=request,
        name="pages/my_investments.html",
        context={
            "products": products,
            "user": user,
        },
    )


@router.get("/login", name="login")
async def login(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="pages/login.html",
        context={"user": _current_user(request)},
    )


@router.get("/create_account", name="create_account")
async def create_account(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="pages/create_account.html",
        context={"user": _current_user(request)},
    )


@router.get("/product/{variant_id}", name="product_detail")
def product_detail(request: Request, variant_id: int, investment_id: str | None = None):
    user = _current_user(request)
    product = get_offer_by_variant_id(variant_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Offer not found")
    investment = None
    if user is not None and investment_id is not None and investment_id.isdigit():
        investment = get_user_investment(user["id"], int(investment_id))
        if investment is not None and investment["variant_id"] != variant_id:
            investment = None
    if investment is not None:
        investment["investment_id"] = str(investment["id"])
        investment["start_date"] = investment["start_date"].isoformat()
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
            "user": user,
        },
    )


@router.post("/api/favorites/{variant_id}", name="toggle_favorite")
async def toggle_favorite(variant_id: int, request: Request):
    user = _require_user(request)
    is_favorite = toggle_user_favorite(user["id"], variant_id)
    updated_user = get_user_state(user["id"])

    return {
        "variant_id": variant_id,
        "is_favorite": is_favorite,
        "favorites": updated_user["favorites"],
    }


@router.post("/api/my_investments/{variant_id}", name="add_investment")
async def add_investment(
    variant_id: int,
    request: Request,
    investment: InvestmentRequest | None = None,
):
    user = _require_user(request)
    offer = get_offer_by_variant_id(variant_id)
    if offer is None:
        raise HTTPException(status_code=404, detail="Offer not found")

    amount = None
    horizon_months = None
    estimated_profit = None
    if investment is not None:
        amount = investment.amount
        horizon_months = investment.horizon_months
        rate = offer["annual_rate_decimal"]
        estimated_profit = calculate_estimated_profit(
            Decimal(rate) if rate is not None else None,
            investment.amount,
            offer["term_days"],
            offer["capitalization"],
            term_value=Decimal(offer["term_value"])
            if offer["term_value"] is not None
            else None,
            term_unit=offer["term_unit"],
        )
    apy = Decimal(offer["apy"]) / Decimal("100") if offer["apy"] else None
    saved_investment = create_user_investment(
        user["id"],
        variant_id,
        amount,
        horizon_months,
        estimated_profit,
        apy,
    )
    record = {
        **saved_investment,
        "investment_id": str(saved_investment["id"]),
        "start_date": saved_investment["start_date"].isoformat(),
    }

    return {
        "variant_id": variant_id,
        "investments": get_user_state(user["id"])["investments"],
        "investment": record,
    }


@router.post("/api/register", name="register")
async def register(account: CreateAccountRequest, request: Request):
    email = account.email.strip().lower()
    try:
        user_id = create_user(
            account.full_name.strip(),
            email,
            _hash_password(account.password),
        )
    except IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists",
        ) from error
    request.session["user_id"] = user_id
    return {"user": get_user_state(user_id)}


@router.post("/api/login", name="authenticate")
async def authenticate(credentials: LoginRequest, request: Request):
    user = get_user_by_email(credentials.email.strip().lower())
    if user is None or not _verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    request.session["user_id"] = user["id"]
    return {"user": get_user_state(user["id"])}


@router.post("/api/logout", name="logout")
async def logout(request: Request):
    request.session.clear()
    return {"logged_out": True}


@router.post("/api/estimates", name="estimate_products")
async def estimate_products(estimate: ProductEstimateRequest):
    products = get_offers(variant_ids=estimate.variant_ids)
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
