import json
import logging
import sys
from datetime import datetime, timezone

FIELDS = ("method", "path", "status_code", "duration_ms", "request_id", "error_type")


class JsonFormatter(logging.Formatter):
    def __init__(self, service: str):
        super().__init__()
        self.service = service

    def format(self, record: logging.LogRecord) -> str:
        data = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "level": record.levelname,
            "service": self.service,
        }
        if record.name != "superagent.access":
            data["message"] = record.getMessage()
        for f in FIELDS:
            if hasattr(record, f):
                data[f] = getattr(record, f)
        return json.dumps(data, ensure_ascii=False)


class StdoutHandler(logging.StreamHandler):
    """每次输出时取当前的 sys.stdout（容器里即标准输出；测试里可被捕获）。"""

    def __init__(self):
        logging.Handler.__init__(self)

    @property
    def stream(self):
        return sys.stdout

    @stream.setter
    def stream(self, _):
        pass


def setup_logging(level: str, service: str) -> None:
    handler = StdoutHandler()
    handler.setFormatter(JsonFormatter(service))
    root = logging.getLogger("superagent")
    root.handlers = [handler]
    root.setLevel(level.upper())
    root.propagate = False
