from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.response import respond


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation(request: Request, exc: RequestValidationError):
        return respond(request, 422, "VALIDATION_ERROR", "request validation failed")

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException):
        if exc.status_code == 404:
            return respond(request, 404, "NOT_FOUND", "resource not found")
        if exc.status_code == 405:
            return respond(request, 405, "METHOD_NOT_ALLOWED", "method not allowed")
        return respond(request, exc.status_code, "HTTP_ERROR", "request failed")
