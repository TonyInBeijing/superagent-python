from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL

# backend/app/core/config.py -> 仓库根目录；与启动时的工作目录无关
ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    # 环境变量优先于 .env
    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", extra="ignore")

    db_host: str = "127.0.0.1"
    db_port: int = 3307
    db_name: str = "superagent"
    db_user: str = "superagent"
    db_password: str = ""
    log_level: str = "INFO"
    service_name: str = "superagent-api"
    db_timeout_seconds: int = 3

    def database_url(self) -> URL:
        return URL.create(
            "mysql+pymysql",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            query={"charset": "utf8mb4"},
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
