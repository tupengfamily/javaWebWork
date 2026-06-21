"""Dispatcher - 任务分派器

核心职责
========
1. 每 5 秒轮询 `crawl_task` 表,认领 status='pending' 的任务
2. 用 `SELECT ... FOR UPDATE SKIP LOCKED` 原子认领(MySQL 8.0+),多 Worker 互不冲突
3. 通过 `subprocess.Popen` 启动 Scrapy 爬虫,日志落盘 `logs/{task_id}.log`
4. 监控运行中的子进程:超时 kill / 退出码判断成功失败 / 更新任务状态
5. 写 `crawl_log` 表记录关键事件,供前端"实时日志"读

关键设计点
==========
- **并发上限**: 从 `schedule_config.main.maxConcurrentTasks` 读,可热更新
- **超时机制**: 从 `schedule_config.main.taskTimeoutMinutes` 读,超时主动 kill
- **进程隔离**: 任务用 subprocess 跑,任一爬虫崩了不会拖死 Dispatcher
- **去重策略**: SQL 中 `NOT EXISTS` 子句避免同 site+type+category 重复 pending
"""
import json
import logging
import os
import subprocess
import time
import uuid
from datetime import datetime
from pathlib import Path

from sqlalchemy import bindparam, create_engine, text

from config import CFG


log = logging.getLogger("dispatcher")

# 全局唯一 worker 标识,写入 crawl_task.worker_id 便于排查
WORKER_ID = f"worker-{os.getpid()}-{uuid.uuid4().hex[:6]}"


class Dispatcher:
    """任务分派器 - 主循环每 N 秒一次,认领+启动+监控任务"""

    def __init__(self):
        # pool_pre_ping: 每次连接前 ping 一下,避免 MySQL 8 小时断连
        # pool_recycle: 1 小时回收,小于 MySQL wait_timeout
        self.engine = create_engine(CFG.db_url, pool_pre_ping=True, pool_recycle=3600)
        # 正在运行的任务字典: task_id -> _RunningTask
        self.running: dict[int, _RunningTask] = {}
        # 任务日志目录(Scrapy 子进程 stdout 重定向到这里)
        # scrapy crawl 必须在 project 根目录(scrapy.cfg 所在)运行
        self.project_dir = Path(__file__).resolve().parent
        self.log_dir = self.project_dir / "logs"
        self.log_dir.mkdir(exist_ok=True)

    def run_forever(self) -> None:
        """主循环,每 poll_interval_seconds 一次"""
        log.info(f"dispatcher started, worker_id={WORKER_ID}")
        while True:
            try:
                # 1. 检查运行中的任务是否超时
                self._check_timeouts()
                # 2. 回收已结束的任务,更新状态
                self._reap_finished()
                # 3. 计算剩余可用槽位
                max_conc = self._get_max_concurrent()
                slots = max(0, max_conc - len(self.running))
                # 4. 认领并启动新任务
                if slots > 0:
                    tasks = self._claim_pending_tasks(slots)
                    for t in tasks:
                        self._launch(t)
            except Exception as e:
                # 主循环任意异常都不能让 dispatcher 退出
                log.exception(f"dispatcher 主循环异常: {e}")
            time.sleep(CFG.poll_interval_seconds)

    # ============================================================
    # 内部方法
    # ============================================================

    def _get_max_concurrent(self) -> int:
        """读 schedule_config 中的最大并发数(支持热更新)"""
        try:
            with self.engine.connect() as conn:
                row = conn.execute(text("""
                    SELECT value FROM schedule_config WHERE `key` = 'main'
                """)).fetchone()
            if not row:
                return 2  # 默认 2
            value = row[0] if isinstance(row[0], dict) else json.loads(row[0])
            return int(value.get("maxConcurrentTasks", 2))
        except Exception:
            return 2

    def _claim_pending_tasks(self, limit: int) -> list[dict]:
        """认领 pending 任务(关键并发安全点)

        使用 MySQL 8.0+ 的 `SELECT ... FOR UPDATE SKIP LOCKED` 语法:
        - FOR UPDATE: 锁住选中的行
        - SKIP LOCKED: 跳过已被其他事务锁住的行
        - 效果: 多个 Dispatcher Worker 并发拉取时,不会抢同一个任务

        额外去重: NOT EXISTS 子句过滤掉"同 site+type+category 还有 pending/running 任务"的行
        避免同一站点的同一榜单被多次抓取(浪费资源)

        'all' 模式特殊处理: 与 daily/monthly/total 任一冲突都视为重复
        (因为 'all' 会展开为这三个,不能同时抓)
        """
        try:
            # 整个"认领 + 改状态"在一个事务里完成，
            # 借助 FOR UPDATE 的行锁避免多 Worker 重复认领
            with self.engine.begin() as conn:
                rows = conn.execute(text("""
                    SELECT t.id, t.site_id, t.ranking_type, t.category, s.code AS site_code
                    FROM crawl_task t
                    JOIN site s ON t.site_id = s.id
                    WHERE t.status = 'pending'
                      AND NOT EXISTS (
                        SELECT 1 FROM crawl_task t2
                        WHERE t2.site_id = t.site_id
                          AND t2.category <=> t.category       -- <=> 是 MySQL 的 NULL-safe 等于
                          AND t2.status IN ('pending', 'running')
                          AND t2.id <> t.id
                          AND (
                               t2.ranking_type = t.ranking_type            -- 完全相同
                            OR (t.ranking_type = 'all'
                                AND t2.ranking_type IN ('daily','monthly','total'))
                            OR (t2.ranking_type = 'all'
                                AND t.ranking_type IN ('daily','monthly','total'))
                          )
                      )
                    ORDER BY t.created_at ASC               -- 先进先出
                    LIMIT :limit
                    FOR UPDATE SKIP LOCKED                  -- 关键: 多 worker 安全
                """), {"limit": limit}).fetchall()

                if not rows:
                    return []

                # 批量更新 status='running' + 记录 worker_id + 启动时间
                # 注意：再次校验 status='pending' 是防御性写法，
                # 避免极端情况下（如手动 SQL 修改）把已运行的任务再次拉起
                ids = [r.id for r in rows]
                stmt = text("""
                    UPDATE crawl_task
                    SET status='running', started_at=NOW(3), worker_id=:wid
                    WHERE id IN :ids AND status='pending'
                """).bindparams(bindparam("ids", expanding=True))   # expanding=True 启用 IN (...) 展开
                conn.execute(stmt, {"wid": WORKER_ID, "ids": ids})

                # 写启动日志(每个任务一条)，便于前端"实时日志"立即可见
                for r in rows:
                    self._write_log(
                        conn, r.id, r.site_id, "INFO",
                        f"任务 {r.id} 启动 site={r.site_code} type={r.ranking_type}",
                    )
                return [dict(r._mapping) for r in rows]
        except Exception as e:
            log.exception(f"认领任务失败: {e}")
            return []

    def _launch(self, task: dict) -> None:
        """用 subprocess 启动 Scrapy 爬虫

        关键点:
        - stdout/stderr 重定向到 logs/{task_id}.log 文件,便于后续排查
        - 通过 -a 参数把 task_id/ranking_type/category 注入 Spider
        - ranking_type='all' 时,Spider 内部会自动展开 daily/monthly/total
        - 失败时直接 mark_failed,不会让任务卡在 running 状态
        """
        log_path = self.log_dir / f"{task['id']}.log"
        try:
            with open(log_path, "w", encoding="utf-8") as fp:
                cmd = [
                    "scrapy", "crawl", task["site_code"],
                    "-a", f"task_id={task['id']}",
                    "-a", f"ranking_type={task['ranking_type']}",
                    "-a", f"category={task.get('category') or ''}",
                ]
                # cwd 必须是 scrapy.cfg 所在目录(即 crawler/ 项目根)
                proc = subprocess.Popen(
                    cmd,
                    cwd=str(self.project_dir),
                    stdout=fp,
                    stderr=subprocess.STDOUT,    # 合并到同一文件
                )
            self.running[task["id"]] = _RunningTask(
                task_id=task["id"],
                site_id=task["site_id"],
                site_code=task["site_code"],
                ranking_type=task["ranking_type"],
                proc=proc,
                started_at=datetime.now(),
            )
            log.info(
                f"已启动 task={task['id']} site={task['site_code']} "
                f"type={task['ranking_type']} pid={proc.pid}"
            )
        except Exception as e:
            log.exception(f"启动 task={task['id']} 失败: {e}")
            self._mark_failed(task["id"], f"启动失败: {e}")

    def _check_timeouts(self) -> None:
        """检查运行中任务是否超时

        流程: 遍历 self.running,若 process 还活着但运行时间 > 超时阈值 → kill
        超时时间从 schedule_config.taskTimeoutMinutes 动态读取,支持热更新
        """
        timeout_min = self._get_timeout_minutes()
        cutoff_ts = datetime.now().timestamp() - timeout_min * 60
        for tid, rt in list(self.running.items()):
            # poll() 返回 None 表示进程还在跑
            if rt.proc.poll() is not None:
                continue  # 已结束,留给 _reap_finished 处理
            if rt.started_at.timestamp() < cutoff_ts:
                log.warning(f"task={tid} 超时({timeout_min}分钟),kill")
                try:
                    rt.proc.kill()    # 强制 SIGKILL
                except Exception:
                    pass
                self._mark_failed(tid, f"执行超时(>{timeout_min}分钟)")

    def _reap_finished(self) -> None:
        """回收已结束的子进程

        判定规则:
        - proc.poll() 返回 0: 正常退出 → status='success'
        - proc.poll() 返回非 0: 异常退出 → status='failed' + 错误码
        注: 这里只依赖 exit code,精确抓取数应在 Pipeline 的 stats 中收集
        """
        for tid, rt in list(self.running.items()):
            ret = rt.proc.poll()
            if ret is None:
                continue
            try:
                if ret == 0:
                    self._mark_success(tid, rt.site_id, rt.site_code)
                else:
                    self._mark_failed(tid, f"退出码 {ret}")
            finally:
                del self.running[tid]

    def _get_timeout_minutes(self) -> int:
        """读 schedule_config 中的超时分钟数(支持热更新)"""
        try:
            with self.engine.connect() as conn:
                row = conn.execute(text("""
                    SELECT value FROM schedule_config WHERE `key` = 'main'
                """)).fetchone()
            if not row:
                return 30  # 默认 30 分钟
            value = row[0] if isinstance(row[0], dict) else json.loads(row[0])
            return int(value.get("taskTimeoutMinutes", 30))
        except Exception:
            return 30

    def _mark_success(self, task_id: int, site_id: int, site_code: str) -> None:
        """标记任务成功: status='success' + finished_at = NOW"""
        try:
            with self.engine.begin() as conn:
                conn.execute(text("""
                    UPDATE crawl_task
                    SET status='success', finished_at=NOW(3)
                    WHERE id = :tid
                """), {"tid": task_id})
                self._write_log(
                    conn, task_id, site_id, "INFO",
                    f"{site_code}爬虫完成 (exit=0)",
                )
        except Exception as e:
            log.warning(f"mark_success 失败: {e}")

    def _mark_failed(self, task_id: int, error: str) -> None:
        """标记任务失败: status='failed' + finished_at + error_message(截 1000 字)"""
        try:
            with self.engine.begin() as conn:
                row = conn.execute(text(
                    "SELECT site_id FROM crawl_task WHERE id = :tid"
                ), {"tid": task_id}).fetchone()
                site_id = row[0] if row else None
                conn.execute(text("""
                    UPDATE crawl_task
                    SET status='failed', finished_at=NOW(3), error_message=:err
                    WHERE id = :tid
                """), {"tid": task_id, "err": error[:1000]})
                self._write_log(
                    conn, task_id, site_id, "ERROR",
                    f"任务失败: {error}",
                )
        except Exception as e:
            log.warning(f"mark_failed 失败: {e}")

    def _write_log(self, conn, task_id: int | None, site_id: int | None,
                   level: str, message: str) -> None:
        """写 crawl_log 表(供前端"实时日志"轮询读取)

        注意: 这里不抛异常 - 日志写入失败不应影响主流程
        """
        try:
            conn.execute(text("""
                INSERT INTO crawl_log (crawl_task_id, site_id, level, message, log_time)
                VALUES (:tid, :sid, :lvl, :msg, NOW(3))
            """), {
                "tid": task_id,
                "sid": site_id,
                "lvl": level,
                "msg": message[:1000],    # 截断防超长
            })
        except Exception:
            pass  # 写日志失败不影响主流程


class _RunningTask:
    """运行中任务的内存表示

    用 __slots__ 节省内存 - 长期运行的 dispatcher 可能有大量此类对象
    """
    __slots__ = ("task_id", "site_id", "site_code", "ranking_type", "proc", "started_at")

    def __init__(self, task_id: int, site_id: int, site_code: str,
                 proc: subprocess.Popen, started_at: datetime,
                 ranking_type: str = "daily"):
        self.task_id = task_id          # DB 主键（crawl_task.id）
        self.site_id = site_id          # 冗余存,写日志用
        self.site_code = site_code      # 冗余存,日志显示
        self.ranking_type = ranking_type  # daily/monthly/total/category/all
        self.proc = proc                # 子进程对象（subprocess.Popen）
        self.started_at = started_at    # 启动时间,用于超时判断
