"""Crawler 入口 - 启动 Scheduler + Dispatcher 两个守护线程"""
import logging
import threading
import time

from config import CFG
from scheduler import CrawlScheduler
from dispatcher import Dispatcher


logging.basicConfig(
    level=CFG.log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("crawler")


def main() -> None:
    sched = CrawlScheduler()
    disp = Dispatcher()

    t1 = threading.Thread(target=sched.start, daemon=True, name="scheduler")
    t2 = threading.Thread(target=disp.run_forever, daemon=True, name="dispatcher")

    t1.start()
    t2.start()

    log.info("crawler started, scheduler + dispatcher running")

    # 主线程保活
    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()
