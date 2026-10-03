from fastapi import FastAPI

from app.api.routes.pages import router as pages_router

app = FastAPI(
    title="Passive Investment Web App",
    description="Web application for comparing passive investment products.",
    version="0.1.0",
)


app.include_router(pages_router)
# class Item(BaseModel):
#     name: str
#     price: float
#     is_offer: bool | None = None
#
# @app.get("/")
# def read_root():
#     return {"Hello": "World"}
#
#
# @app.get("/items/{item_id}")
# def read_item(item_id: int, q: str | None = None):
#     return {"item_id": item_id, "q": q}
#
# @app.put("/items/{item_id}")
# def update_item(item_id: int, item: Item):
#     return {"item_name": item.name, "item_id": item_id}