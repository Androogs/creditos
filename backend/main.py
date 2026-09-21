<<<<<<< HEAD
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
=======
from fastapi import FastAPI
from fastapi.middleware.cors import (
    CORSMiddleware
)
>>>>>>> 6c057cfb599491e2d6d35b8d8a9c99e955203838

from backend.config import get_settings
from backend.controllers.health_controller import (
    router as health_router,
)
from backend.controllers.datacredito_controller import (
    router as datacredito_router,
)
from backend.middlewares.error_middleware import (
    register_error_handlers,
)


settings = get_settings()


app = FastAPI(
<<<<<<< HEAD
    title="Creditos API",
    version="0.2.0",
)


cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173",
    ).split(",")
    if origin.strip()
]

=======
    title=settings.app_title,
    version=settings.app_version,
    docs_url="/api-docs",
    redoc_url="/redoc",
    openapi_url="/api/openapi.json",
)


cors_origins = settings.cors_origin_list()
>>>>>>> 6c057cfb599491e2d6d35b8d8a9c99e955203838

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    health_router,
    prefix="/api",
)


app.include_router(
    datacredito_router,
    prefix="/api",
)


register_error_handlers(app)