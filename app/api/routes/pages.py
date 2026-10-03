from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


@router.get("/invest")
async def invest_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="pages/dashboard.html"
    )