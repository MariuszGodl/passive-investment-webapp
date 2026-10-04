from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from app.schemas.user import User

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


PRODUCTS = [
    {
        "id": 1,
        "institution_name": "PKO Bank Polski",
        "name": "Captain's Investment Deposit",
        "badge": "Guaranteed return",
        "duration": "12 months",
        "requirement": "Personal account required at PKO BP",
        "interest_rate": 7.5,
        "estimated_profit": 750,
        "payout_description": "Interest paid at investment maturity",
    },
    {
        "id": 2,
        "institution_name": "VeloBank",
        "name": "Captain's Investment Deposit",
        "badge": "Welcome deposit",
        "duration": "12 months",
        "requirement": "Personal account required at VeloBank",
        "interest_rate": 7.5,
        "estimated_profit": 750,
        "payout_description": "Interest paid at investment maturity",
    },
    {
        "id": 3,
        "institution_name": "Treasury Bonds",
        "name": "10-year Treasury Bond",
        "badge": "Treasury bond",
        "duration": "10 years",
        "requirement": "No bank account required",
        "interest_rate": 8.2,
        "estimated_profit": 820,
        "payout_description": "Interest according to bond terms",
    },
]

USERS = [User(full_name="Piotr Cherek", email="x@gmail.com", password="qweqwe")]

app_user: User | None = USERS[0]
LOGGED_IN: bool = True


@router.get("/", name="invest_page")
async def invest_page(request: Request):
    context = {
        "products": PRODUCTS,
        "user": app_user if LOGGED_IN else None,
    }

    return templates.TemplateResponse(
        request=request,
        name="pages/dashboard.html",
        context=context,
    )


@router.get("/favorites", name="favorites_page")
async def favorites_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="pages/favorites.html",
        context={
            "products": PRODUCTS,
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


@router.get("/product/{product_id}", name="product_detail")
async def product_detail(request: Request, product_id: int):
    product = next(
        (product for product in PRODUCTS if product["id"] == product_id),
        None,
    )

    if product is None:
        return {"error": "Product not found"}

    return templates.TemplateResponse(
        request=request,
        name="pages/product_detail.html",
        context={
            "product": product,
            "user": app_user if LOGGED_IN else None,
        },
    )


@router.post("/api/favorites/{product_id}", name="toggle_favorite")
async def toggle_favorite(product_id: int):
    is_favorite = False

    if product_id in app_user.favorites:
        app_user.favorites.remove(product_id)
    else:
        app_user.favorites.append(product_id)
        is_favorite = True

    return {
        "product_id": product_id,
        "is_favorite": is_favorite,
        "favorites": app_user.favorites,
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
