import logging

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import Engine

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.database.connection import engine
from app.routers.auth import router as auth_router
from app.routers.restaurants import router as restaurants_router
from app.routers.menu import router as menu_router
from app.routers.cart import router as cart_router
from app.routers.orders import router as orders_router
from app.routers.deliveries import router as deliveries_router
from app.routers.payments import router as payments_router
from app.routers.reviews import router as reviews_router
from app.routers.notifications import router as notifications_router
from pathlib import Path
from fastapi.staticfiles import StaticFiles

setup_logging()

logger = logging.getLogger(__name__)


app = FastAPI(
    title=settings.APP_NAME,
    description="Food Delivery Platform API",
    version="1.0.0"
)

# Restaurant image storage
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Serve uploaded restaurant images
app.mount(
    "/uploads",
    StaticFiles(directory=str(UPLOAD_DIR)),
    name="uploads"
)

app.include_router(auth_router)
app.include_router(restaurants_router)
app.include_router(menu_router)
app.include_router(cart_router)
app.include_router(orders_router)
app.include_router(deliveries_router)
app.include_router(payments_router)
app.include_router(reviews_router)
app.include_router(notifications_router)

# Secure CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS"
    ],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept"
    ]
)

@app.get("/")
def home():
    return {
        "message": "Welcome to FoodieExpress API",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "application": settings.APP_NAME
    }


@app.get("/health/db")
def database_health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "connected",
            "database": "food_delivery_db"
        }

    except SQLAlchemyError:
        logger.exception("Database connection failed")

        raise HTTPException(
            status_code=503,
            detail="Database connection failed"
        )
