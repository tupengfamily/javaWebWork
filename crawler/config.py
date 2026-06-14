"""Crawler 配置 - 从环境变量读取"""
import os
from dataclasses import dataclass


@dataclass
class Config:
    # DB
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "3306"))
    db_name: str = os.getenv("DB_NAME", "novel_rank")
    db_user: str = os.getenv("DB_USER", "novel")
    db_password: str = os.getenv("DB_PASSWORD", "novel123")

    # Scheduler
    reload_interval_seconds: int = 300   # 5 分钟
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # Dispatcher
    poll_interval_seconds: int = 5

    @property
    def db_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )


CFG = Config()
