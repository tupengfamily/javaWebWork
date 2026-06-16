"""Scheduler - 定时调度器

核心职责
========
1. 启动一个 APScheduler BackgroundScheduler(基于 Asia/Shanghai 时区)
2. 启动时与每 5 分钟一次从 `schedule_config` 表读取 `dailyCrawlTimes` 数组
3. 按 `HH:mm` 注册 cron 任务(每个时间点一个 job)
4. cron 触发时为所有 enabled 站点的每个榜单类型写入 pending 任务
5. 监听 schedule_config 变化(下次 reload 时) - 实现"前端改时间自动生效"

关键设计点
==========
- **配置驱动**: 不写死时间,完全由 DB 决定
- **热更新**: 5 分钟内识别变化,无需重启进程
- **去重**: 同 site+type 已有 pending/running 任务则跳过(避免堆积)
- **错误隔离**: 写任务失败不影响调度器继续运行
- **日志**: 关键事件写 crawl_log,系统级用 crawl_task_id=NULL
"""
import json
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import create_engine, text

from config import CFG


log = logging.getLogger("scheduler")

# 调度主配置 key - 与前端约定的固定值
SCHEDULE_KEY = "main"


class CrawlScheduler:
    """基于 DB 配置的 cron 调度器

    工作流程:
    ┌────────────────────────────────────────────────────┐
    │  启动 → 读 schedule_config.main                    │
    │       → 解析 dailyCrawlTimes / crawlAllRankingTypes│
    │       → 注册 cron jobs                              │
    │  每 5 分钟 reload_config:                           │
    │       → 与内存中配置对比                            │
    │       → 不一致时 remove 旧 jobs + add 新 jobs       │
    │  cron 触发:                                        │
    │       → 遍历 enabled 站点                          │
    │       → 遍历 crawlAllRankingTypes                   │
    │       → 写 crawl_task(去重)                        │
    └────────────────────────────────────────────────────┘
    """

    def __init__(self):
        # BackgroundScheduler: 在独立线程中跑,不会阻塞主线程
        # timezone: 全部用上海时区,避免容器/系统时区差异
        self.scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
        self.engine = create_engine(CFG.db_url, pool_pre_ping=True, pool_recycle=3600)
        # 内存中的当前配置,用于 diff 判断是否需要 reload
        self.current_times: list[str] = []
        # rich-crawler-data: 默认值扩展为 6 种榜单
        # 注:实际值由 schedule_config.main.value.crawlAllRankingTypes 覆盖
        self.current_types: list[str] = [
            "daily", "monthly", "total", "yuepiao", "newbook", "finish"
        ]
        # 已注册的 cron job ID,reload 时要清掉
        self.job_ids: list[str] = []
        # reload 任务自身 ID(避免被清掉)
        self.reload_job_id: str | None = None

    def start(self) -> None:
        """启动调度器"""
        self._reload_config()
        # 注册 reload 任务自身 - 每 5 分钟检查一次配置变化
        self.reload_job_id = self.scheduler.add_job(
            self._reload_config, "interval",
            seconds=CFG.reload_interval_seconds,
            id="reload_config",
        ).id
        self.scheduler.start()
        log.info(f"scheduler started, jobs: {self.job_ids}")

    def stop(self) -> None:
        """停止调度器"""
        try:
            self.scheduler.shutdown(wait=False)
        except Exception:
            pass
        self.engine.dispose()

    def _reload_config(self) -> None:
        """从 DB 读最新配置,与内存对比,差异时重设 cron 任务

        容错:
        - DB 读失败: 保留旧配置,不中断
        - JSON 解析失败: 保留旧配置
        - dailyCrawlTimes 为空: 保留旧配置
        """
        # 1. 读 DB
        try:
            with self.engine.connect() as conn:
                row = conn.execute(text("""
                    SELECT value FROM schedule_config WHERE `key` = :k
                """), {"k": SCHEDULE_KEY}).fetchone()
        except Exception as e:
            log.warning(f"读 schedule_config 失败: {e}")
            return

        if not row:
            log.debug("schedule_config.main 不存在,跳过 reload")
            return

        # 2. 解析 JSON
        try:
            value = row[0] if isinstance(row[0], dict) else json.loads(row[0])
        except Exception as e:
            log.warning(f"schedule_config.main 解析失败: {e}")
            return

        new_times = list(value.get("dailyCrawlTimes", []))
        # rich-crawler-data: 6 种榜单兜底(与 init.sql / 当前 default 一致)
        new_types = list(value.get(
            "crawlAllRankingTypes",
            ["daily", "monthly", "total", "yuepiao", "newbook", "finish"]
        ))

        # 3. diff - 一样就不动
        if new_times == self.current_times and new_types == self.current_types:
            return

        # 4. 清掉旧 cron job
        for jid in self.job_ids:
            try:
                self.scheduler.remove_job(jid)
            except Exception:
                pass
        self.job_ids.clear()

        # 5. 注册新 cron job
        for t in new_times:
            try:
                hh, mm = t.split(":")
                jid = self.scheduler.add_job(
                    self._trigger_scheduled,
                    CronTrigger(hour=int(hh), minute=int(mm)),
                    id=f"sched-{t}",        # 用时间作为 ID,便于 reload 时识别
                    replace_existing=True,
                ).id
                self.job_ids.append(jid)
                log.info(f"已注册定时任务: 每天 {t}")
            except Exception as e:
                log.warning(f"注册 {t} 失败: {e}")

        self.current_times = new_times
        self.current_types = new_types

    def _trigger_scheduled(self) -> None:
        """cron 触发: 为所有 enabled 站点 × 所有榜单类型写入 task

        去重逻辑(应用层):
        - 同 (site_id, ranking_type) 已有 pending/running 则跳过
        - 原因: 同一站点的同一榜单没必要并发抓两次
        """
        try:
            with self.engine.begin() as conn:
                # 查出所有启用的站点
                sites = conn.execute(text("""
                    SELECT id, code FROM site WHERE enabled = 1
                """)).fetchall()

                for site in sites:
                    for rtype in self.current_types:
                        # 应用层去重
                        exists = conn.execute(text("""
                            SELECT 1 FROM crawl_task
                            WHERE site_id = :sid
                              AND ranking_type = :rtype
                              AND status IN ('pending', 'running')
                            LIMIT 1
                        """), {"sid": site.id, "rtype": rtype}).fetchone()
                        if exists:
                            log.debug(f"task 已存在,跳过 site={site.code} type={rtype}")
                            continue
                        # 写入新任务
                        conn.execute(text("""
                            INSERT INTO crawl_task
                              (site_id, ranking_type, trigger_type, status, created_at)
                            VALUES (:sid, :rtype, 'scheduled', 'pending', NOW(3))
                        """), {"sid": site.id, "rtype": rtype})
                        log.info(f"已写入定时任务 site={site.code} type={rtype}")
        except Exception as e:
            log.exception(f"到点写任务失败: {e}")
            # 写一条系统级 ERROR 日志(任务级 crawl_log)
            try:
                with self.engine.begin() as conn:
                    conn.execute(text("""
                        INSERT INTO crawl_log (level, message, log_time)
                        VALUES ('ERROR', :msg, NOW(3))
                    """), {"msg": f"调度器写任务失败: {e}"[:1000]})
            except Exception:
                pass
