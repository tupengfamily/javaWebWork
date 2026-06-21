"""Scrapy Pipelines - 数据落地层

Pipeline 链(顺序由 settings.ITEM_PIPELINES 决定):
1. DedupPipeline (100)        → 批内去重,同 novel 在一次抓取中只入库一次
2. CategoryDedupPipeline (150)→ 批内分类去重,同 (code,name) 只入库一次
3. CategorySyncPipeline (180) → 同步分类字典到 category 表
4. NovelUpsertPipeline (200)  → 写/更新 novel 表(主数据)
5. RankingInsertPipeline (300)→ 写 ranking_record 表(时序数据,纯 INSERT)
6. CrawlLogPipeline (900)     → 抓取进度日志

每条 item 依次经过所有 Pipeline(除非前一个用 DropItem 抛掉)
"""
import logging
from typing import Set

from sqlalchemy import create_engine, text
from scrapy.exceptions import DropItem

from config import CFG
from novel_crawler.items import NovelData, RankingData, CategoryData


log = logging.getLogger(__name__)


def _engine():
    """创建 SQLAlchemy 引擎(每个 Pipeline 各自一个)"""
    return create_engine(CFG.db_url, pool_pre_ping=True, pool_recycle=3600)


# ============================================================
# 1. DedupPipeline - 批内去重
# ============================================================
class DedupPipeline:
    """同一批抓取内,同一 (site_code, external_id) 的 novel 只入库一次

    作用: 详情页可能通过不同入口被请求到(列表 + 详情),避免重复写入
    范围: 仅本进程本次抓取(批内),跨进程不做去重(由 DB 唯一索引兜底)
    """

    def __init__(self):
        self._seen_novel: Set[tuple] = set()

    def process_item(self, item, spider):
        if isinstance(item, NovelData):
            key = (item.site_code, item.external_id)
            if key in self._seen_novel:
                raise DropItem(f"duplicate novel {key}")
            self._seen_novel.add(key)
        return item


# ============================================================
# 2. CategoryDedupPipeline - 批内分类去重
# ============================================================
class CategoryDedupPipeline:
    """同一批抓取内,同一 (code, name) 的 CategoryData 只入库一次

    列表页里 20 本小说可能都属于"玄幻",只产生 1 条入库
    """

    def __init__(self):
        self._seen_cat: Set[tuple] = set()

    def process_item(self, item, spider):
        if isinstance(item, CategoryData):
            key = (item.code, item.name)
            if key in self._seen_cat:
                raise DropItem(f"duplicate category {key}")
            self._seen_cat.add(key)
        return item


# ============================================================
# 3. CategorySyncPipeline - 同步分类字典到 category 表
# ============================================================
class CategorySyncPipeline:
    """Category 表 UPSERT(INSERT ... ON DUPLICATE KEY UPDATE)

    流程:
    1. 根据 code/name 匹配,已存在则跳过(name 由前端列表展示)
    2. 不存在则 INSERT,触发前端"分类"下拉自动出现新分类

    设计要点:
    - 不删除旧分类:已有 novel 引用了,删了会破坏外键
    - 不更新 code:code 是稳定的 pinyin 标识,改了等于另起一类
    - 只更新 sort_order/name:保持最新
    """

    def open_spider(self, spider):
        self.engine = _engine()

    def close_spider(self, spider):
        self.engine.dispose()

    def process_item(self, item, spider):
        if not isinstance(item, CategoryData):
            return item
        with self.engine.begin() as conn:
            # 优先按 code 查;code 为空时按 name 查
            if item.code:
                row = conn.execute(text(
                    "SELECT id FROM category WHERE code = :code"
                ), {"code": item.code}).fetchone()
            else:
                row = None

            if not row:
                # code 没匹配上,尝试按 name 匹配
                row = conn.execute(text(
                    "SELECT id FROM category WHERE name = :name"
                ), {"name": item.name}).fetchone()

            if row:
                # 已存在:仅更新 name/sort_order(不更新 code,避免破坏引用)
                conn.execute(text("""
                    UPDATE category
                    SET name = :name, sort_order = :sort_order
                    WHERE id = :id
                """), {"id": row[0], "name": item.name,
                       "sort_order": item.sort_order})
                return item

            # 不存在:INSERT 新分类
            conn.execute(text("""
                INSERT INTO category (code, name, sort_order)
                VALUES (:code, :name, :sort_order)
                ON DUPLICATE KEY UPDATE
                    name = VALUES(name),
                    sort_order = VALUES(sort_order)
            """), {"code": item.code, "name": item.name,
                   "sort_order": item.sort_order})
            log.info(f"新增分类: {item.code} / {item.name}")
        return item


# ============================================================
# 4. NovelUpsertPipeline - 写/更新小说主数据
# ============================================================
class NovelUpsertPipeline:
    """Novel 表 UPSERT(INSERT ... ON DUPLICATE KEY UPDATE)

    流程:
    1. 根据 site_code 查 site.id
    2. INSERT 小说,若 (site_id, external_id) 已存在则更新
    3. ON DUPLICATE KEY UPDATE 字段:
       - 基础字段(title/author/cover_url 等): 用新值覆盖
       - last_crawl_time: 每次抓取都刷新,标记最近活跃

    注意: 该 Pipeline 必须在 RankingInsertPipeline 之前
    (Ranking 写库时需要先有 novel_id)
    """

    def open_spider(self, spider):
        self.engine = _engine()

    def close_spider(self, spider):
        self.engine.dispose()

    def process_item(self, item, spider):
        if not isinstance(item, NovelData):
            return item
        with self.engine.begin() as conn:
            # 1. 查 site_id
            row = conn.execute(text(
                "SELECT id FROM site WHERE code = :code"
            ), {"code": item.site_code}).fetchone()
            if not row:
                log.warning(f"site {item.site_code} 不存在,跳过 novel {item.external_id}")
                raise DropItem(f"unknown site {item.site_code}")
            site_id = row[0]

            # 2. UPSERT
            # description: 截断 1000 字符
            desc = (item.description or "")[:1000]
            # tags: 过滤空值,限制 8 个,逗号 join(去重已在 make_tags 中做)
            tags_raw = (item.tags or "").split(",")
            tags_clean = ",".join(
                t.strip() for t in tags_raw if t.strip()
            )[:1024]

            conn.execute(text("""
                INSERT INTO novel
                  (site_id, external_id, title, author, category, cover_url, novel_url,
                   word_count, status, description, tags, first_seen, last_crawl_time)
                VALUES
                  (:site_id, :external_id, :title, :author, :category, :cover_url, :novel_url,
                   :word_count, :status, :description, :tags, NOW(3), NOW(3))
                ON DUPLICATE KEY UPDATE
                  title           = VALUES(title),
                  author          = VALUES(author),
                  category        = VALUES(category),
                  cover_url       = VALUES(cover_url),
                  novel_url       = VALUES(novel_url),
                  word_count      = VALUES(word_count),
                  status          = VALUES(status),
                  description     = COALESCE(NULLIF(VALUES(description), ''), description),
                  tags            = COALESCE(NULLIF(VALUES(tags), ''), tags),
                  last_crawl_time = NOW(3)
                  -- 注意: first_seen 不更新(首次抓取时间保持原值)
                  -- COALESCE 避免抓取到的简介/标签为空字符串时把已有的真值覆盖掉
            """), {
                "site_id": site_id,
                "external_id": item.external_id,
                "title": item.title,
                "author": item.author,
                "category": item.category,
                "cover_url": item.cover_url,
                "novel_url": item.novel_url,
                "word_count": item.word_count,
                "status": item.status,
                "description": desc,
                "tags": tags_clean or None,
            })
        return item


# ============================================================
# 5. RankingInsertPipeline - 写排行榜快照
# ============================================================
class RankingInsertPipeline:
    """Ranking 表纯 INSERT(时序数据,只追加不更新)

    流程:
    1. 缓存 site_code -> site_id(避免每条都查)
    2. 缓存 (site_id, external_id) -> novel_id(同上)
    3. INSERT ranking_record(每条 item 一行)

    关键点:
    - novel 必须先入库(由 NovelUpsertPipeline 保证顺序)
    - 若 novel 找不到,DropItem 跳过(理论上不应发生)
    """

    def open_spider(self, spider):
        self.engine = _engine()
        # 缓存减少 DB 查询
        self._novel_id_cache: dict[tuple, int] = {}
        self._site_id_cache: dict[str, int] = {}

    def close_spider(self, spider):
        self.engine.dispose()

    def _get_novel_id(self, conn, site_id: int, external_id: str) -> int | None:
        """查 novel_id(带缓存)"""
        key = (site_id, external_id)
        if key in self._novel_id_cache:
            return self._novel_id_cache[key]
        row = conn.execute(text(
            "SELECT id FROM novel WHERE site_id = :sid AND external_id = :eid"
        ), {"sid": site_id, "eid": external_id}).fetchone()
        if row:
            self._novel_id_cache[key] = row[0]
            return row[0]
        return None

    def _get_site_id(self, conn, site_code: str) -> int | None:
        """查 site_id(带缓存)"""
        if site_code in self._site_id_cache:
            return self._site_id_cache[site_code]
        row = conn.execute(text(
            "SELECT id FROM site WHERE code = :code"
        ), {"code": site_code}).fetchone()
        if row:
            self._site_id_cache[site_code] = row[0]
            return row[0]
        return None

    def process_item(self, item, spider):
        if not isinstance(item, RankingData):
            return item
        with self.engine.begin() as conn:
            # 1. 拿 site_id
            site_id = self._get_site_id(conn, item.site_code)
            if site_id is None:
                raise DropItem(f"unknown site {item.site_code}")
            # 2. 拿 novel_id
            novel_id = self._get_novel_id(conn, site_id, item.novel_external_id)
            if novel_id is None:
                # novel 还没入库 → 占位创建(让 ranking 能先入库)
                # 占位 title 用"site_code:external_id",后续详情页 NovelUpsertPipeline 会覆盖
                placeholder_title = f"{item.site_code}:{item.novel_external_id}"
                placeholder_url = ""
                if item.site_code == "douban":
                    placeholder_url = f"https://book.douban.com/subject/{item.novel_external_id}/"
                elif item.site_code == "dangdang":
                    placeholder_url = f"http://product.dangdang.com/{item.novel_external_id}.html"
                elif item.site_code == "baidu":
                    placeholder_url = f"https://www.baidu.com/s?wd={item.novel_external_id}"
                conn.execute(text("""
                    INSERT INTO novel
                      (site_id, external_id, title, author, novel_url, status, first_seen, last_crawl_time)
                    VALUES
                      (:site_id, :eid, :title, '未知', :url, 'ongoing', NOW(3), NOW(3))
                    ON DUPLICATE KEY UPDATE last_crawl_time = NOW(3)
                """), {
                    "site_id": site_id, "eid": item.novel_external_id,
                    "title": placeholder_title, "url": placeholder_url,
                })
                novel_id = self._get_novel_id(conn, site_id, item.novel_external_id)
                if novel_id is None:
                    raise DropItem(f"failed to create placeholder novel for {item.site_code}/{item.novel_external_id}")
            # 3. INSERT ranking_record
            conn.execute(text("""
                INSERT INTO ranking_record
                  (novel_id, site_id, ranking_type, category, `rank`,
                   view_count, rec_count, crawl_time, crawl_task_id)
                VALUES
                  (:novel_id, :site_id, :ranking_type, :category, :rank,
                   :view_count, :rec_count, :crawl_time, :task_id)
            """), {
                "novel_id": novel_id,
                "site_id": site_id,
                "ranking_type": item.ranking_type,
                "category": item.category or None,
                "rank": item.rank,
                "view_count": item.view_count,
                "rec_count": item.rec_count,
                "crawl_time": item.crawl_time,
                # spider.task_id 由 dispatcher 通过 -a 注入
                "task_id": int(spider.task_id) if getattr(spider, "task_id", None) else None,
            })
        return item


# ============================================================
# 6. CrawlLogPipeline - 抓取进度日志
# ============================================================
class CrawlLogPipeline:
    """每收到 N 条 item 写一次进度日志,避免日志爆炸

    - 每 50 条 item 写一行 INFO(本地 + DB)
    - close_spider 时写一条完成日志(统计总数)
    """

    INTERVAL = 50    # 每 50 条写一次

    def open_spider(self, spider):
        self.engine = _engine()
        self.count = 0
        # site_code -> site_id 缓存(写日志用)
        self.site_id_cache: dict[str, int] = {}

    def close_spider(self, spider):
        # 写一条收尾日志
        if self.count > 0:
            self._write_log(spider, "INFO",
                            f"{getattr(spider, 'site_code', '?')}爬虫完成,共抓取 {self.count} 条")
        self.engine.dispose()

    def _write_log(self, spider, level: str, message: str) -> None:
        """写 crawl_log 表 - 失败不影响主流程"""
        try:
            site_id = self.site_id_cache.get(getattr(spider, "site_code", ""))
            with self.engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO crawl_log (crawl_task_id, site_id, level, message, log_time)
                    VALUES (:tid, :sid, :lvl, :msg, NOW(3))
                """), {
                    "tid": int(spider.task_id) if getattr(spider, "task_id", None) else None,
                    "sid": site_id,
                    "lvl": level,
                    "msg": message[:1000],    # 截断防超长
                })
        except Exception as e:
            log.warning(f"写 crawl_log 失败: {e}")

    def process_item(self, item, spider):
        self.count += 1
        if self.count == 1 or self.count % self.INTERVAL == 0:
            site_code = getattr(spider, "site_code", "?")
            # 查 site_id 一次,后续直接用
            if site_code not in self.site_id_cache:
                try:
                    with self.engine.connect() as conn:
                        row = conn.execute(text(
                            "SELECT id FROM site WHERE code = :c"
                        ), {"c": site_code}).fetchone()
                        if row:
                            self.site_id_cache[site_code] = row[0]
                except Exception:
                    pass
            log.info(f"[{site_code}] 已抓取 {self.count} 条")
        return item
