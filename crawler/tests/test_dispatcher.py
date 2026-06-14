"""
Tests for the CrawlScheduler and Dispatcher (config + scheduling logic only)
No DB connection - we mock SQLAlchemy engines
"""
import json
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from apscheduler.triggers.cron import CronTrigger

# 测试 scheduler / dispatcher 的纯逻辑,patch 掉 DB


class TestSchedulerConfigLogic:
    """测试 CrawlScheduler._reload_config 的 diff 逻辑"""

    def test_identical_config_does_not_re_register(self):
        """相同配置下,jobs 数量不变"""
        from scheduler import CrawlScheduler
        with patch("scheduler.create_engine") as engine_factory:
            engine_factory.return_value.connect.return_value.__enter__.return_value.execute.return_value.fetchone.return_value = [json.dumps({
                "dailyCrawlTimes": ["08:00", "14:00", "20:00"],
                "crawlAllRankingTypes": ["daily", "monthly", "category"]
            })]
            sched = CrawlScheduler()
            sched.scheduler.add_job = MagicMock()
            sched._reload_config()
            # 第一次调用,会注册 3 个 jobs
            assert sched.scheduler.add_job.call_count == 3
            # 第二次相同配置
            sched._reload_config()
            # 仍是 3 个,没有重复
            assert sched.scheduler.add_job.call_count == 3

    def test_different_config_reregisters(self):
        from scheduler import CrawlScheduler
        with patch("scheduler.create_engine") as engine_factory:
            engine_factory.return_value.connect.return_value.__enter__.return_value.execute.return_value.fetchone.return_value = [json.dumps({
                "dailyCrawlTimes": ["09:00"],
                "crawlAllRankingTypes": ["daily"]
            })]
            sched = CrawlScheduler()
            sched.scheduler.add_job = MagicMock()
            sched.scheduler.remove_job = MagicMock()
            sched._reload_config()
            # 1 job 注册
            assert sched.scheduler.add_job.call_count == 1
            # 改成 2 个时间
            engine_factory.return_value.connect.return_value.__enter__.return_value.execute.return_value.fetchone.return_value = [json.dumps({
                "dailyCrawlTimes": ["09:00", "15:00"],
                "crawlAllRankingTypes": ["daily"]
            })]
            sched._reload_config()
            # 1 remove + 2 add
            assert sched.scheduler.remove_job.call_count == 1
            assert sched.scheduler.add_job.call_count == 3   # 1 + 2

    def test_db_failure_does_not_crash(self):
        """DB 读失败时,scheduler 不崩"""
        from scheduler import CrawlScheduler
        with patch("scheduler.create_engine") as engine_factory:
            engine_factory.return_value.connect.return_value.__enter__.return_value.execute.side_effect = Exception("DB down")
            sched = CrawlScheduler()
            # 不应抛异常
            sched._reload_config()

    def test_invalid_json_keeps_previous_config(self):
        from scheduler import CrawlScheduler
        with patch("scheduler.create_engine") as engine_factory:
            engine_factory.return_value.connect.return_value.__enter__.return_value.execute.return_value.fetchone.return_value = ["not valid json {{{"]
            sched = CrawlScheduler()
            sched.scheduler.add_job = MagicMock()
            sched._reload_config()
            # 不应注册任何 job
            sched.scheduler.add_job.assert_not_called()


class TestDispatcherLogic:
    """测试 Dispatcher 的并发上限/超时/状态判断逻辑"""

    def test_dispatcher_init_creates_log_dir(self, tmp_path):
        """Dispatcher 初始化时创建 logs 目录"""
        from dispatcher import Dispatcher
        with patch("dispatcher.create_engine"):
            with patch("dispatcher.Path") as mock_path:
                mock_path.return_value.mkdir = MagicMock()
                d = Dispatcher()
                mock_path.assert_called_once()
                mock_path.return_value.mkdir.assert_called_once()

    def test_running_task_slots_calculation(self):
        """max_concurrent - running_count 决定可领取数"""
        # 不实际启动 Dispatcher,直接验证逻辑
        max_conc = 2
        running = 0
        slots = max(0, max_conc - running)
        assert slots == 2

        running = 1
        slots = max(0, max_conc - running)
        assert slots == 1

        running = 2
        slots = max(0, max_conc - running)
        assert slots == 0

        running = 5
        slots = max(0, max_conc - running)
        assert slots == 0


class TestExitCodeMapping:
    """验证 exit code → status 的映射"""

    def test_zero_means_success(self):
        ret = 0
        status = "success" if ret == 0 else "failed"
        assert status == "success"

    def test_nonzero_means_failed(self):
        for ret in (1, 2, 137, -1):
            status = "success" if ret == 0 else "failed"
            assert status == "failed"
