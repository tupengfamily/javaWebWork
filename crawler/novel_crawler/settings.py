"""Scrapy 项目设置 — 生产优化版
"""
import os

# 修复 tldextract 在 Windows 上的锁文件目录权限问题
os.environ.setdefault("TLDEXTRACT_CACHE", os.path.join(os.path.expanduser("~"), ".tldextract_cache"))

BOT_NAME = "novel_crawler"

SPIDER_MODULES = ["novel_crawler.spiders"]
NEWSPIDER_MODULE = "novel_crawler.spiders"

# 不遵守 robots.txt(小说站点通常不允许)
ROBOTSTXT_OBEY = False

# ---- 并发控制(适当降低,避免触发反爬) ----
CONCURRENT_REQUESTS = 4
CONCURRENT_REQUESTS_PER_DOMAIN = 2

# 启用 cookies(很多站点需要)
COOKIES_ENABLED = True

# 重试
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# 下载延迟(适当加大,模拟人类阅读速度)
DOWNLOAD_DELAY = 2.0
RANDOMIZE_DOWNLOAD_DELAY = True  # 0.5*delay ~ 1.5*delay

# 自动限速(根据响应时间动态调整,降低被封概率)
# rich-crawler-data 引入分页后,启用 AUTOTHROTTLE 进一步保护
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.5
AUTOTHROTTLE_DEBUG = False

# 默认请求头(补全浏览器特征)
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}

# Pipeline 顺序
ITEM_PIPELINES = {
    "novel_crawler.pipelines.DedupPipeline": 100,
    "novel_crawler.pipelines.CategoryDedupPipeline": 150,
    "novel_crawler.pipelines.CategorySyncPipeline": 180,
    "novel_crawler.pipelines.NovelUpsertPipeline": 200,
    "novel_crawler.pipelines.RankingInsertPipeline": 300,
    "novel_crawler.pipelines.CrawlLogPipeline": 900,
}

# 中间件
DOWNLOADER_MIDDLEWARES = {
    "novel_crawler.middlewares.RandomUserAgentMiddleware": 400,
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": 550,
    "novel_crawler.middlewares.HttpErrorLoggingMiddleware": 850,
}

# 默认 UA
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

# 下载超时(防止某个请求卡死)
DOWNLOAD_TIMEOUT = 30

# 关闭 Telnet
TELNETCONSOLE_ENABLED = False

# 字符集
FEED_EXPORT_ENCODING = "utf-8"

# 日志
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# DNS 缓存(减少 DNS 查询)
DNSCACHE_ENABLED = True

# 减少内存:不缓存磁盘请求
HTTPCACHE_ENABLED = False

# 自动限速(如果站点返回 429,自动减速)
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1.5
AUTOTHROTTLE_MAX_DELAY = 10.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# 强制使用 asyncio reactor(Windows + Python 3.14 + Twisted 26.x 兼容)
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
