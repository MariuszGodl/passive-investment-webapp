import asyncio

from fastapi import FastAPI

from app.core.db import Base, engine
from app.models import *

app = FastAPI()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.on_event("startup")
async def on_startup():
    await init_db()


@app.get("/")
async def root():
    return {"message": "API is running"}
