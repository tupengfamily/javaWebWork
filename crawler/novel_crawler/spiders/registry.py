"""Spider 注册表 - 用于 dispatcher 动态加载"""
import importlib
import logging

log = logging.getLogger(__name__)

# 类路径注册表
SITE_TO_SPIDER: dict[str, str] = {
    "qidian":   "novel_crawler.spiders.qidian.QidianSpider",
    "fanqie":   "novel_crawler.spiders.fanqie.FanqieSpider",
    "zongheng": "novel_crawler.spiders.zongheng.ZonghengSpider",
    "douban":   "novel_crawler.spiders.douban.DoubanSpider",
    "baidu":    "novel_crawler.spiders.baidu.BaiduHotSpider",
    "dangdang": "novel_crawler.spiders.dangdang.DangdangSpider",
}


def load_spider_class(site_code: str):
    """通过 site_code 加载对应的 Spider 类"""
    path = SITE_TO_SPIDER.get(site_code)
    if not path:
        raise ValueError(f"unknown site_code: {site_code}")
    module_path, class_name = path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)
    return cls
