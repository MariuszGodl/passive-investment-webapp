import os
import secrets

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes.pages import router as pages_router

app = FastAPI(
    title="SafeVesting",
    description="Web application for comparing passive investment products.",
    version="0.1.0",
)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET", secrets.token_urlsafe(32)),
    same_site="lax",
)


app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static",
)


app.include_router(pages_router)
