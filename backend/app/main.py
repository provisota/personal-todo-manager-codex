from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, lists, tasks
from app.api.errors import http_exception_handler, validation_exception_handler
from app.core.config import get_settings
from app.websocket import notifications


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Personal To-Do Manager API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_origin_regex=settings.cors_allowed_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(auth.router)
    app.include_router(lists.router)
    app.include_router(tasks.router)
    app.include_router(notifications.router)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
