"""SQLAlchemy 模型 - 与 MySQL 表对应"""
from datetime import datetime
from sqlalchemy import (
    BigInteger, String, Integer, DateTime, Text, JSON, ForeignKey, Boolean
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Site(Base):
    __tablename__ = "site"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(64))
    base_url: Mapped[str] = mapped_column(String(255))
    spider_class: Mapped[str] = mapped_column(String(255))
    color: Mapped[str] = mapped_column(String(16), default="#409EFF")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class ScheduleConfig(Base):
    __tablename__ = "schedule_config"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    key: Mapped[str] = mapped_column(String(64), unique=True)
    value: Mapped[dict] = mapped_column(JSON)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime)


class CrawlTask(Base):
    __tablename__ = "crawl_task"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    site_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("site.id"))
    ranking_type: Mapped[str] = mapped_column(String(32))
    category: Mapped[str | None] = mapped_column(String(32), nullable=True)
    trigger_type: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16), default="pending")
    worker_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    fetched_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class CrawlLog(Base):
    __tablename__ = "crawl_log"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    crawl_task_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    site_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    level: Mapped[str] = mapped_column(String(8), default="INFO")
    message: Mapped[str] = mapped_column(String(1000))
    log_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Novel(Base):
    __tablename__ = "novel"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    site_id: Mapped[int] = mapped_column(BigInteger)
    external_id: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(255))
    author: Mapped[str] = mapped_column(String(64))
    category: Mapped[str | None] = mapped_column(String(32), nullable=True)
    cover_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    novel_url: Mapped[str] = mapped_column(String(512))
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="ongoing")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    first_seen: Mapped[datetime] = mapped_column(DateTime)
    last_crawl_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
