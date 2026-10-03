from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes.pages import router as pages_router

app = FastAPI(
    title="SafeVesting",
    description="Web application for comparing passive investment products.",
    version="0.1.0",
)


app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static",
)


app.include_router(pages_router)