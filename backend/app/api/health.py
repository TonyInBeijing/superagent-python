import logging

from fastapi import APIRouter, Request
from sqlalchemy import text

from app.api.response import ok, request_id_of, respond
from app.db.session import get_engine

router = APIRouter(prefix="/health")
log = logging.getLogger("superagent.app")


@router.get("/live")
def live(request: Request):
    return ok(request, {"status": "alive"})


@router.get("/ready")
def ready(request: Request):
    # 同步路由：由 FastAPI 放入线程池执行，不阻塞事件循环
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        log.warning("database not ready", extra={"error_type": type(exc).__name__, "request_id": request_id_of(request)})
        return respond(request, 503, "DEPENDENCY_UNAVAILABLE", "dependency unavailable", {"status": "not_ready", "database": "down"})
    return ok(request, {"status": "ready", "database": "up"})
