from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    """惰性创建：导入和应用启动都不连接数据库。"""
    s = get_settings()
    t = s.db_timeout_seconds
    return create_engine(
        s.database_url(),
        pool_pre_ping=True,
        connect_args={"connect_timeout": t, "read_timeout": t, "write_timeout": t},
    )


def get_db() -> Iterator[Session]:
    session = sessionmaker(bind=get_engine(), expire_on_commit=False)()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
