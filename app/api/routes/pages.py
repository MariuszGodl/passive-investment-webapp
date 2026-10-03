from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

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


@router.get("/", name="invest_page")
async def invest_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="pages/dashboard.html",
        context={
            "products": PRODUCTS,
        },
    )


@router.get("/product/{product_id}", name="product_detail")
async def product_detail(request: Request, product_id: int):
    product = next((
        product
        for product in PRODUCTS
        if product["id"] == product_id
        ),
        None,
    )

    if product is None:
        return {"error": "Product not found"}

    return templates.TemplateResponse(
        request=request,
        name="pages/product_detail.html",
        context={
            "product": product,
        },
    )