"""百度热搜 Spider — 公开热搜榜单

数据源: https://top.baidu.com/board?tab=realtime (服务端渲染 JSON)

榜单映射:
- hot → 百度实时热搜

字段映射:
- novel_external_id = 热搜词（唯一标识）
- title             = 热搜词
- author            = '百度热搜'（固定）
- view_count        = 热搜指数（score）
- rec_count         = 0（无此字段）
- rank              = 排名
"""
import scrapy

from .base import BaseSpider


class BaiduHotSpider(BaseSpider):
    """百度热搜爬虫"""

    site_code = "baidu"
    name = "baidu"

    custom_settings = {
        "DOWNLOAD_DELAY": 2.0,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
    }

    # 热搜榜只有一种类型
    _RANK_URLS = {
        "hot": "https://top.baidu.com/board?tab=realtime",
    }

    _UA = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.6778.140 Safari/537.36"
    )

    async def start(self):
        for rt in self.iter_all_types():
            url = self._RANK_URLS.get(rt)
            if not url:
                url = self._RANK_URLS.get("hot")
                rt = "hot"
            if not url:
                self.logger.warning(f"baidu 无 {rt} 榜单映射")
                continue
            yield scrapy.Request(
                url,
                callback=self.parse,
                dont_filter=True,
                meta={"ranking_type": rt},
                headers={
                    "User-Agent": self._UA,
                    "Referer": "https://top.baidu.com/",
                    "Accept-Language": "zh-CN,zh;q=0.9",
                },
            )

    def parse(self, response):
        rt = response.meta.get("ranking_type", self.ranking_type)

        if not self.validate_response(response, min_length=1000):
            return

        # 百度热搜页面中数据嵌在 <script> 标签的 JSON 中
        # 或在 SSR 的 React 组件 props 中
        # 尝试从页面 JS 中提取 JSON
        import json
        import re

        body = response.text

        # 方法1: 从 script 标签中找 SSR 数据
        ssr_match = re.search(
            r'window\.__INITIAL_STATE__\s*=\s*(\{.+?\});?\s*</script>',
            body, re.DOTALL
        )
        if not ssr_match:
            # 方法2: 从 data 中提取
            ssr_match = re.search(
                r'"data":\s*(\[.+?\])\s*[,}]',
                body, re.DOTALL
            )

        items_data = []
        if ssr_match:
            try:
                raw = ssr_match.group(1)
                data = json.loads(raw)
                if isinstance(data, dict):
                    # __INITIAL_STATE__ 结构
                    cards = data.get("data", {}).get("cards", [])
                    for card in cards:
                        for item in card.get("content", []):
                            if isinstance(item, dict) and "word" in item:
                                items_data.append({
                                    "word": item.get("word", ""),
                                    "desc": item.get("desc", ""),
                                    "score": int(item.get("hotScore", 0) or 0),
                                    "url": item.get("url", ""),
                                })
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "word" in item:
                            items_data.append({
                                "word": item.get("word", ""),
                                "desc": item.get("desc", ""),
                                "score": int(item.get("hotScore", 0) or 0),
                                "url": item.get("url", ""),
                            })
            except (json.JSONDecodeError, TypeError):
                pass

        # 方法3: 回退到 HTML 选择器
        if not items_data:
            hot_items = response.css("div.category-wrap_iQLoo, div[class*='category-wrap']")
            if not hot_items:
                hot_items = response.css("div.content_1YWBm, div[class*='content_']")
            for idx, item in enumerate(hot_items, start=1):
                title = (item.css("div.c-single-text-ellipsis::text").get()
                         or item.css("div.hot-title::text").get()
                         or item.css("a::text").get() or "").strip()
                score_text = (item.css("div.hot-index::text").get()
                              or item.css("div.index-bg-K8UwF::text").get() or "0").strip()
                try:
                    score = int(score_text.replace(",", "").replace(" ", ""))
                except ValueError:
                    score = 0
                if title:
                    items_data.append({
                        "word": title,
                        "desc": "",
                        "score": score,
                        "url": "",
                    })

        if not items_data:
            self.logger.warning(f"baidu[{rt}] 未提取到热搜数据: {response.url}")
            return

        self.logger.info(f"baidu[{rt}] 提取到 {len(items_data)} 条热搜")

        for idx, item in enumerate(items_data, start=1):
            word = item.get("word", "").strip()
            if not word:
                continue
            # 用排名作为 external_id（更稳定）
            yield self.make_ranking_with_type(
                rt,
                novel_external_id=str(idx),
                rank=idx,
                view_count=item.get("score", 0),
                rec_count=0,
            )

            yield self.make_novel(
                external_id=str(idx),
                title=word,
                author="百度热搜",
                novel_url=item.get("url", f"https://www.baidu.com/s?wd={word}"),
                category="",
                cover_url="",
                word_count=0,
                status="completed",
                description=item.get("desc", ""),
                tags="热搜",
            )
