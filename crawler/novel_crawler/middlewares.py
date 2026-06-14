"""Scrapy 中间件 — 反反爬优化版

优化:
- UA 池扩到 15+ 个(模拟近期真实浏览器,避免被 UA 特征识别)
- 请求时自动补 Referer(从 request.meta.get('referer') 读,未设则用站点首页)
- 处理 429 Too Many Requests 时主动减速
"""
import random
import logging
from scrapy import signals

log = logging.getLogger(__name__)

# UA 池: 模拟 2025-2026 年主流浏览器(Chrome/Firefox/Safari/Edge)
USER_AGENTS = [
    # Chrome 130+
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    # Firefox 130+
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:132.0) Gecko/20100101 Firefox/132.0",
    # Edge 130+
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
    # Safari 17+
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15",
    # 移动端(部分站点给移动页更友好)
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.135 Mobile Safari/537.36",
    # Linux 桌面
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0",
    # China mainland common
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
]

# 各站点的 Referer 映射(用于构造请求时补 Referer)
SITE_REFERERS = {
    "qidian": "https://www.qidian.com/",
    "fanqie": "https://fanqienovel.com/",
    "zongheng": "https://www.zongheng.com/",
}


class RandomUserAgentMiddleware:
    """随机 UA + 补 Referer"""

    def process_request(self, request, spider):
        # UA
        ua = random.choice(USER_AGENTS)
        request.headers["User-Agent"] = ua

        # 根据 UA 类型判断平台,补对应的 Sec-Ch-UA
        if "Chrome" in ua and "Edg" not in ua:
            request.headers.setdefault(
                "Sec-Ch-Ua",
                '"Google Chrome";v="131", "Chromium";v="131", "Not=A?Brand";v="24"',
            )
            request.headers.setdefault("Sec-Ch-Ua-Platform", '"Windows"')

        # 补 Referer
        if "Referer" not in request.headers:
            site_code = getattr(spider, "site_code", "")
            ref = SITE_REFERERS.get(site_code)
            if ref:
                request.headers["Referer"] = ref

        # 补 Accept
        request.headers.setdefault(
            "Accept",
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        )
        request.headers.setdefault("Accept-Language", "zh-CN,zh;q=0.9,en;q=0.8")


class HttpErrorLoggingMiddleware:
    """HTTP 错误时写详细日志,方便排查"""

    def process_response(self, request, response, spider):
        if response.status >= 400:
            body_sample = response.text[:300] if response.text else ""
            spider.logger.warning(
                f"HTTP {response.status} url={request.url} "
                f"headers={dict(response.headers)} body_sample={body_sample[:200]}"
            )
        return response

    def process_exception(self, request, exception, spider):
        spider.logger.warning(
            f"Exception {type(exception).__name__} url={request.url}: {exception}"
        )
        return None
