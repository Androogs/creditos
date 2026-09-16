from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.controllers.health_controller import router as health_router
from backend.middlewares.error_middleware import register_error_handlers

app = FastAPI(title="Creditos API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
register_error_handlers(app)
