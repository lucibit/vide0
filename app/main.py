from fastapi import FastAPI
from app.api.upload import router as upload_router
from app.api.play import router as play_router
from app.api.auth import router as auth_router
from app.models import init_db
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app):
    await init_db()
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(upload_router)
app.include_router(play_router)
app.include_router(auth_router)

# Routers will be included here 