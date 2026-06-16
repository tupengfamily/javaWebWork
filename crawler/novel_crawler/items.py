"""Item dataclasses - 与 BaseSpider 共用"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any


@dataclass
class NovelData:
    """小说基础数据 - 用于 upsert 到 novel 表"""
    external_id: str
    site_code: str
    title: str
    author: str
    novel_url: str
    category: str = ""
    cover_url: str = ""
    word_count: int = 0
    status: str = "ongoing"
    description: str = ""    # 简介 (200-1000 字符,详情页抓)
    tags: str = ""           # 逗号分隔标签 (2-8 个,详情页抓)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RankingData:
    """排行榜条目 - 用于插入到 ranking_record 表"""
    novel_external_id: str
    site_code: str
    ranking_type: str
    rank: int
    category: str = ""
    view_count: int = 0
    rec_count: int = 0
    crawl_time: str = ""

    def __post_init__(self):
        if not self.crawl_time:
            self.crawl_time = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CategoryData:
    """小说分类字典 - 用于同步到 category 表

    一个任务里如果列表页给出多个 novel 都属于"玄幻",只会入库一次
    (由 CategorySyncPipeline 的 DedupPipeline 配合 + UNIQUE KEY 双重保障)
    """
    code: str                  # 分类 code (拼音/英文),为空则用 name
    name: str                  # 分类中文名,展示用
    sort_order: int = 100      # 排序权重(数字越小越靠前)

    def __post_init__(self):
        # 若 code 为空,用 name 生成稳定 hash code
        if not self.code:
            self.code = "auto_" + str(abs(hash(self.name)) % 10_000_000)

    def to_dict(self) -> dict:
        return asdict(self)
