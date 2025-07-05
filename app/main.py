from fastapi import FastAPI
from app.api.upload import router as upload_router
from app.api.play import router as play_router
from app.api.auth import router as auth_router
from app.api.setup import router as setup_router
from app.models import init_db
from app.startup import startup_event
from contextlib import asynccontextmanager
import logging


@asynccontextmanager
async def lifespan(app):
    try:
        logging.info("🔄 Starting video server...")
        logging.info("🔄 About to initialize database...")
        await init_db()
        logging.info("🔄 Database initialized successfully")
        logging.info("🔄 About to run startup event...")
        await startup_event()
        logging.info("🔄 Startup event completed")
        yield
        logging.info("🔄 Shutting down...")
    except Exception as e:
        logging.error(f"❌ Error in lifespan: {e}")
        raise


app = FastAPI(lifespan=lifespan)
app.include_router(upload_router)
app.include_router(play_router)
app.include_router(auth_router)
app.include_router(setup_router)

# Routers will be included here 