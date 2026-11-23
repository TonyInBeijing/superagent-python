import os

# 必须在导入 app 之前：测试只使用独立测试库
os.environ["DB_NAME"] = "superagent_test"

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.session import get_engine


def reset_caches():
    get_engine.cache_clear()
    get_settings.cache_clear()


@pytest.fixture
def client():
    from app.main import create_app

    reset_caches()
    with TestClient(create_app(), raise_server_exceptions=False) as c:
        yield c
    get_engine().dispose()
    reset_caches()


@pytest.fixture
def db_down(monkeypatch):
    # 127.0.0.1:1 不会有服务监听
    monkeypatch.setenv("DB_HOST", "127.0.0.1")
    monkeypatch.setenv("DB_PORT", "1")
    reset_caches()
    yield
    reset_caches()


@pytest.fixture
def stdout_logs(capsys):
    s = get_settings()
    setup_logging(s.log_level, s.service_name)  # 绑定到当前被捕获的 stdout
    return capsys
