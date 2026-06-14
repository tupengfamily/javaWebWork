"""纵横中文网 Spider — 一体化版

新增能力:
1. ranking_type='all' 一次产出 daily/monthly/total 三类榜单
2. 列表/API 给出的 category 同步到 category 字典表
3. 列表/meta 透传字段,详情页只补缺失字段
"""
import json
import re
import scrapy

from .base import BaseSpider, parse_int


class ZonghengSpider(BaseSpider):
    """纵横中文网榜单爬虫 — 多选择器容错 + API 兜底 + all 模式"""

    site_code = "zongheng"
    name = "zongheng"

    custom_settings = {
        "DOWNLOAD_DELAY": 2.0,
    }

    _ITEM_SELECTORS = [
        ".rank-list li",        # 2025+
        ".book-list li",        # 备选
        ".rank_d_list li",      # 旧版
        ".bookbox",             # 更旧版
    ]
    _TITLE_SELECTORS = [
        ".book-name a::text", ".title a::text", ".bookname a::text",
        "h3 a::text", "a .name::text",
    ]
    _AUTHOR_SELECTORS = [
        ".author a::text", ".author-name::text", ".au a::text",
        ".book-author::text",
    ]
    _CATEGORY_SELECTORS = [
        ".category::text", ".book-category::text",
        ".classify a::text", ".tag::text",
    ]
    _VIEW_SELECTORS = [
        ".read-num::text", ".nums::text", ".count::text",
        ".total::text", "em::text",
    ]

    # API 兜底
    # rich-crawler-data: 新增 yuepiao / subscribe / newbook 3 种榜单
    _API_MAPS = {
        "daily":     "https://www.zongheng.com/api/rank?type=daily",
        "monthly":   "https://www.zongheng.com/api/rank?type=monthly",
        "total":     "https://www.zongheng.com/api/rank?type=total",
        "yuepiao":   "https://www.zongheng.com/api/rank?type=yuepiao",
        "subscribe": "https://www.zongheng.com/api/rank?type=subscribe",
        "newbook":   "https://www.zongheng.com/api/rank?type=newbook",
    }
    # HTML URL
    # 注意:rich-crawler-data spike 显示 /rank/newbook.html 返回 200 但内容是 404 错误页(Nuxt SSR fallback)
    # spider.parse 内有 is_404_page 兜底,直接跳过
    _HTML_URLS = {
        "daily":     "https://www.zongheng.com/rank/daily.html",
        "monthly":   "https://www.zongheng.com/rank/monthly.html",
        "total":     "https://www.zongheng.com/rank/total.html",
        "yuepiao":   "https://www.zongheng.com/rank/yuepiao.html",
        "subscribe": "https://www.zongheng.com/rank/subscribe.html",
        "newbook":   "https://www.zongheng.com/rank/newbook.html",
    }

    # "all" 模式覆盖为 6 种
    ALL_RANKING_TYPES = ["daily", "monthly", "total", "yuepiao", "subscribe", "newbook"]

    # 详情页描述 / 标签 候选选择器(纵横 DOM)
    _DESC_SELECTORS = [
        "meta[name='description']::attr(content)",
        ".book-intro::text",
        ".book-dec::text",
        ".book-info-intro::text",
        ".intro::text",
    ]
    _TAG_SELECTORS = [
        ".book-label a::text",
        ".label a::text",
        ".book-tag a::text",
        ".tag-list a::text",
        ".tags a::text",
    ]

    async def start(self):
        """Scrapy 2.16+ async entry,支持 all 模式 + 分页

        rich-crawler-data:
        - 6 种榜单(daily/monthly/total/yuepiao/subscribe/newbook)
        - 用 build_rank_requests 翻页,但纵横是 SPA,分页参数格式未确认,
          实施时观察;目前 pages=1 保险起见
        - newbook URL 虽 200 但实际 404,parse 内 is_404_page 兜底
        """
        for req in self.build_rank_requests(
            rank_paths=self._HTML_URLS,
            base_url="",
            callback=self.parse,
            meta_extra={"site_code": self.site_code},
        ):
            req.headers["Referer"] = "https://www.zongheng.com/"
            yield req

    def parse(self, response):
        ranking_type = response.meta.get("ranking_type", self.ranking_type)
        page = response.meta.get("page", 1)

        # 200 + 404 错误页兜底(Nuxt SSR 已知 newbook 是这种情况)
        if self.is_404_page(response):
            self.logger.warning(
                f"zongheng[{ranking_type}] page={page} 返回 200 但内容是 404 错误页,跳过"
            )
            return

        items, sel_used = self._try_selectors(response)

        if items:
            self.logger.info(
                f"zongheng[{ranking_type}] 使用选择器 '{sel_used}' 命中 {len(items)} 项"
            )
            yield from self._parse_items(items, response, ranking_type)
            self.log_parse_summary(response, len(items), len(items))
            return

        self.logger.warning(
            f"zongheng[{ranking_type}] HTML 选择器全未命中,尝试 API: {response.url}"
        )
        api_url = self._API_MAPS.get(ranking_type)
        if api_url:
            yield scrapy.Request(
                api_url, callback=self._parse_api, dont_filter=True,
                meta={"ranking_type": ranking_type},
                headers={"Accept": "application/json, text/plain, */*"},
            )

    def _try_selectors(self, response):
        for sel in self._ITEM_SELECTORS:
            items = response.css(sel)
            if items:
                return items, sel
        return [], ""

    def _parse_items(self, items, response, ranking_type: str):
        for idx, book in enumerate(items, start=1):
            bid = self._extract_bid(book)
            if not bid:
                continue

            title = self._pick_text(book, self._TITLE_SELECTORS).strip()
            author = self._pick_text(book, self._AUTHOR_SELECTORS).strip()
            category = self._pick_text(book, self._CATEGORY_SELECTORS).strip()
            view = parse_int(self._pick_text(book, self._VIEW_SELECTORS))

            yield self.make_ranking_with_type(
                ranking_type,
                novel_external_id=bid,
                rank=idx,
                view_count=view,
                category=category,
            )

            if category:
                cat_item = self.make_category(
                    name=category,
                    code=self.category_from_cn_name(category),
                )
                if cat_item:
                    yield cat_item

            href = book.css("a::attr(href)").get()
            if href:
                yield response.follow(
                    href, callback=self.parse_detail,
                    meta={"external_id": bid, "title": title, "author": author,
                          "category": category, "ranking_type": ranking_type},
                )

    def _extract_bid(self, book) -> str | None:
        href = book.css("a::attr(href)").get() or ""
        m = re.search(r"/book/(\d+)", href)
        return m.group(1) if m else None

    @staticmethod
    def _pick_text(sel, candidates):
        for c in candidates:
            v = sel.css(c).get()
            if v:
                return v
        return ""

    # ============ API 兜底 ============
    def _parse_api(self, response):
        ranking_type = response.meta.get("ranking_type", self.ranking_type)
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error(f"zongheng API 返回非 JSON: {response.text[:200]}")
            return

        books = (
            data.get("data", {}).get("bookList", [])
            or data.get("result", [])
            or data.get("data", [])
        )
        if isinstance(books, dict):
            books = books.get("records", books.get("list", []))

        if not books:
            self.logger.warning(f"zongheng API 空列表: {response.text[:300]}")
            return

        self.logger.info(f"zongheng[{ranking_type}] API 命中 {len(books)} 本")

        for idx, b in enumerate(books, start=1):
            bid = str(b.get("bookId", b.get("id", "")))
            if not bid:
                continue
            title = b.get("bookName", b.get("name", ""))
            author = b.get("authorName", b.get("author", ""))
            category = b.get("categoryName", b.get("category", ""))
            view = parse_int(str(b.get("readCount", b.get("totalRead", "0"))))
            cover = b.get("coverUrl", b.get("cover", ""))

            yield self.make_ranking_with_type(
                ranking_type,
                novel_external_id=bid,
                rank=idx,
                view_count=view,
                category=category,
            )

            if category:
                cat_item = self.make_category(
                    name=category,
                    code=self.category_from_cn_name(category),
                )
                if cat_item:
                    yield cat_item

            detail_url = f"https://www.zongheng.com/book/{bid}.html"
            yield scrapy.Request(
                detail_url, callback=self.parse_detail, dont_filter=True,
                meta={"external_id": bid, "title": title, "author": author,
                      "category": category, "cover": cover,
                      "ranking_type": ranking_type},
            )

    def parse_detail(self, response):
        meta = response.meta
        if self.is_404_page(response):
            self.logger.warning(
                f"zongheng 详情页 404: {meta.get('external_id')} {response.url}"
            )
            return

        cover = meta.get("cover", "") or (
            response.css(".book_img img::attr(src)").get()
            or response.css(".cover img::attr(src)").get()
            or ""
        )
        word = parse_int(
            response.css(".bookword::text, .word::text, .word-count::text").get() or "0"
        ) or 0

        category = meta.get("category") or self._pick_text(
            response, [".category::text", ".classify a::text", ".tag::text"]
        ).strip()

        if category and not meta.get("category"):
            cat_item = self.make_category(
                name=category,
                code=self.category_from_cn_name(category),
            )
            if cat_item:
                yield cat_item

        # rich-crawler-data: 抽取 description / tags
        description = self.make_description(response, self._DESC_SELECTORS)
        tags = self.make_tags(response, self._TAG_SELECTORS)

        yield self.make_novel(
            external_id=meta["external_id"],
            title=meta.get("title", ""),
            author=meta.get("author", ""),
            category=category,
            cover_url=cover,
            novel_url=response.url,
            word_count=word,
            description=description,
            tags=tags,
        )