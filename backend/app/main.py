from fastapi import FastAPI

from app.api.errors import register_error_handlers
from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.middleware import RequestContextMiddleware


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level, settings.service_name)
    app = FastAPI(title="SuperAgent Python")
    register_error_handlers(app)
    app.include_router(api_router)
    app.add_middleware(RequestContextMiddleware)
    return app


app = create_app()
