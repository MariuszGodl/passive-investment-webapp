from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


@router.get("/")
async def invest_page(request: Request):

    products = [
        {
            "id": 1,
            "name": "Example Treasury Bond",
            "type": "Treasury Bond",
            "interest_rate": 5.25,
            "term": "4 years",
        },
        {
            "id": 2,
            "name": "Example Bank Deposit",
            "type": "Term Deposit",
            "interest_rate": 6.50,
            "term": "12 months",
        },
    ]

    return templates.TemplateResponse(
        request=request,
        name="pages/dashboard.html",
        context={
            "products": products,
        },
    )