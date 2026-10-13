from fastapi import APIRouter, HTTPException, Request
from fastapi.templating import Jinja2Templates

from app.db_functions import get_offer_by_variant_id, get_offers
from app.schemas.user import User

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


app_user = User(full_name="Piotr Cherek", email="x@gmail.com", password="qweqwe")
LOGGED_IN: bool = True


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
    return templates.TemplateResponse(
        request=request,
        name="pages/my_investments.html",
        context={
            "products": get_offers(variant_ids=app_user.investments, active_only=False),
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
def product_detail(request: Request, variant_id: int):
    product = get_offer_by_variant_id(variant_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Offer not found")

    return templates.TemplateResponse(
        request=request,
        name="pages/product_detail.html",
        context={
            "product": product,
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
async def add_investment(variant_id: int):
    if variant_id not in app_user.investments:
        app_user.investments.append(variant_id)

    return {
        "variant_id": variant_id,
        "investments": app_user.investments,
    }


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
