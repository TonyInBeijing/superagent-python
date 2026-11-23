from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


def request_id_of(request: Request) -> str:
    return request.scope.get("state", {}).get("request_id", "")


def respond(request: Request, status: int, code: str, message: str, data: Any = None) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"code": code, "message": message, "data": data if data is not None else {}, "request_id": request_id_of(request)},
    )


def ok(request: Request, data: Any = None) -> JSONResponse:
    return respond(request, 200, "OK", "success", data)
