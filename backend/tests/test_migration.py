import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

from app.core.config import Settings

BACKEND = Path(__file__).resolve().parents[1]


def alembic(*args):
    env = {**os.environ, "DB_NAME": "superagent_test"}
    # 故意从 backend 之外的目录执行，验证能找到根目录配置
    return subprocess.run(
        [sys.executable, "-m", "alembic", "-c", str(BACKEND / "alembic.ini"), *args],
        cwd="/tmp", env=env, capture_output=True, text=True,
    )


def test_upgrade_on_empty_db_and_idempotent():
    engine = create_engine(Settings(db_name="superagent_test").database_url())
    with engine.begin() as c:
        c.execute(text("DROP TABLE IF EXISTS system_metadata"))
        c.execute(text("DROP TABLE IF EXISTS alembic_version"))
    r = alembic("upgrade", "head")
    assert r.returncode == 0, r.stderr
    with engine.connect() as c:
        cols = [row[0] for row in c.execute(text("SHOW COLUMNS FROM system_metadata"))]
        assert cols == ["id", "key", "value", "created_at"]
        idx = c.execute(text("SHOW INDEX FROM system_metadata WHERE Column_name='key'")).all()
        assert idx and all(row[1] == 0 for row in idx)  # Non_unique == 0
    r2 = alembic("upgrade", "head")
    assert r2.returncode == 0, r2.stderr
    assert "Running upgrade" not in r2.stderr
    engine.dispose()
