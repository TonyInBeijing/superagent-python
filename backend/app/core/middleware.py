import json
import logging
import time
import uuid

from starlette.types import ASGIApp, Message, Receive, Scope, Send

access_log = logging.getLogger("superagent.access")


class RequestContextMiddleware:
    """服务端生成 request_id（忽略客户端同名头），写入 scope、响应头和访问日志。"""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request_id = uuid.uuid4().hex
        scope.setdefault("state", {})["request_id"] = request_id
        start = time.perf_counter()
        status = {"code": 500}

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                status["code"] = message["status"]
                status["started"] = True
                headers = [(k, v) for k, v in message.get("headers", []) if k.lower() != b"x-request-id"]
                headers.append((b"x-request-id", request_id.encode()))
                message["headers"] = headers
            await send(message)

        try:
            try:
                await self.app(scope, receive, send_wrapper)
            except Exception as exc:
                # 未处理异常：只记录类别，不记录堆栈/消息；在此生成 500，保证带 request_id
                logging.getLogger("superagent.app").error(
                    "unhandled error", extra={"error_type": type(exc).__name__, "request_id": request_id}
                )
                if status.get("started"):
                    raise
                body = json.dumps({"code": "INTERNAL_ERROR", "message": "internal server error", "data": {}, "request_id": request_id}).encode()
                await send_wrapper({"type": "http.response.start", "status": 500, "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())]})
                await send_wrapper({"type": "http.response.body", "body": body})
        finally:
            access_log.info(
                "request",
                extra={
                    "method": scope["method"],
                    "path": scope["path"],
                    "status_code": status["code"],
                    "duration_ms": round((time.perf_counter() - start) * 1000),
                    "request_id": request_id,
                },
            )
