"""番茄小说 Spider — 一体化版

新增能力:
1. ranking_type='all' 一次产出 daily/monthly/total 三类榜单
2. 列表/API 给出的 category 同步到 category 字典表
3. 列表/meta 透传字段,详情页只补缺失字段
"""
import json
import re
import scrapy

from .base import BaseSpider, parse_int


class FanqieSpider(BaseSpider):
    """番茄小说榜单爬虫 — API 优先 + HTML 兜底 + all 模式"""

    site_code = "fanqie"
    name = "fanqie"

    custom_settings = {
        "DOWNLOAD_DELAY": 2.5,  # 番茄反爬较严,延迟更大
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
    }

    # ---- HTML 候选选择器(当 API 不可用时尝试) ----
    _ITEM_SELECTORS = [
        ".rank-item", ".book-list li", ".book-card",
        "li.rank-item", "[class*='rank-item']",
    ]
    _TITLE_SELECTORS = [
        ".book-title a::text", ".title::text", "h3::text",
        ".book-name::text",
    ]
    _AUTHOR_SELECTORS = [
        ".author-name::text", ".author::text", ".book-author::text",
    ]
    _CATEGORY_SELECTORS = [
        ".category::text", ".book-category::text",
        ".tag::text", ".genre::text",
    ]
    _VIEW_SELECTORS = [
        ".read-count::text", ".read-num::text", ".heat::text",
    ]

    # ---- API 入口(优先使用) ----
    # rich-crawler-data: 新增 hot / newbook / good / finish 4 种榜单(rank_id 3-6)
    _RANK_API_URLS = {
        "daily":   "https://fanqienovel.com/api/author/rank/0",
        "monthly": "https://fanqienovel.com/api/author/rank/1",
        "total":   "https://fanqienovel.com/api/author/rank/2",
        "hot":     "https://fanqienovel.com/api/author/rank/3",
        "newbook": "https://fanqienovel.com/api/author/rank/4",
        "good":    "https://fanqienovel.com/api/author/rank/5",
        "finish":  "https://fanqienovel.com/api/author/rank/6",
    }
    # HTML 兜底 URL
    _RANK_HTML_URLS = {
        "daily":   "https://fanqienovel.com/rank/0",
        "monthly": "https://fanqienovel.com/rank/1",
        "total":   "https://fanqienovel.com/rank/2",
        "hot":     "https://fanqienovel.com/rank/3",
        "newbook": "https://fanqienovel.com/rank/4",
        "good":    "https://fanqienovel.com/rank/5",
        "finish":  "https://fanqienovel.com/rank/6",
    }

    # "all" 模式覆盖为 7 种
    ALL_RANKING_TYPES = ["daily", "monthly", "total", "hot", "newbook", "good", "finish"]

    # 详情页描述 / 标签 候选选择器(番茄 DOM)
    _DESC_SELECTORS = [
        "meta[name='description']::attr(content)",
        ".book-intro::text",
        ".book-desc::text",
        ".page-abstract::text",
        ".info-content p::text",
    ]
    _TAG_SELECTORS = [
        ".book-tag a::text",
        ".tag-list a::text",
        ".book-intro-tags a::text",
        ".book-info-tags a::text",
        ".info-tags a::text",
    ]

    _MOBILE_UA = (
        "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.6778.135 Mobile Safari/537.36"
    )

    async def start(self):
        """Scrapy 2.16+ async entry — API 优先 + HTML 兜底,支持 all 模式 + 分页

        rich-crawler-data:
        - 7 种榜单(daily/monthly/total/hot/newbook/good/finish)
        - API 默认不支持分页(无 ?page 参数),HTML 路径会自动拼分页
        - pages=1 即可防止 API 重复请求
        """
        # 临时把 pages 设为 1 走 API(API 不分页);HTML 兜底才用 pages
        # 但 build_rank_requests 会同时跑 API + HTML,需自定义逻辑
        for rt in self.iter_all_types():
            # 首选: API(只请求 page=1)
            api_url = self._RANK_API_URLS.get(rt)
            if api_url:
                yield scrapy.Request(
                    api_url, callback=self._parse_api, dont_filter=True,
                    meta={"ranking_type": rt, "page": 1},
                    headers={
                        "Accept": "application/json, text/plain, */*",
                        "Referer": "https://fanqienovel.com/rank/",
                        "User-Agent": self._MOBILE_UA,
                    },
                )
            # 兜底: HTML(支持分页)
            for page in range(1, max(1, int(self.pages)) + 1):
                html_url_base = self._RANK_HTML_URLS.get(rt) or f"https://fanqienovel.com/rank/{rt}"
                html_url = f"{html_url_base}?page={page}" if page > 1 else html_url_base
                yield scrapy.Request(
                    html_url, callback=self._parse_html, dont_filter=True,
                    meta={"ranking_type": rt, "page": page},
                    headers={"Referer": "https://fanqienovel.com/",
                             "User-Agent": self._MOBILE_UA},
                )

    # ============ API 解析(主路径) ============
    def _parse_api(self, response):
        ranking_type = response.meta.get("ranking_type", self.ranking_type)
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.warning(
                f"fanqie[{ranking_type}] API 返回非 JSON: {response.text[:200]}"
            )
            return

        code = data.get("code", -1)
        if code != 0 and code != "0":
            self.logger.warning(
                f"fanqie[{ranking_type}] API 错误码 {code}: {data.get('message', '')}"
            )
            return

        books = (
            data.get("data", {}).get("bookList", [])
            or data.get("data", {}).get("list", [])
            or data.get("data", [])
        )
        if isinstance(books, dict):
            books = books.get("records", books.get("items", []))

        if not books:
            self.logger.warning(
                f"fanqie[{ranking_type}] API 空列表, len={len(response.text)}"
            )
            return

        self.logger.info(f"fanqie[{ranking_type}] API 命中 {len(books)} 本")

        for idx, book in enumerate(books, start=1):
            bid = str(book.get("bookId", book.get("book_id", book.get("id", ""))))
            if not bid:
                continue

            title = book.get("bookName", book.get("title", book.get("name", "")))
            author = book.get("authorName", book.get("author", ""))
            category = book.get("categoryName", book.get("category",
                              book.get("categoryNameV2", "")))
            view = parse_int(
                str(book.get("readCount", book.get("read_count",
                     book.get("heat", "0"))))
            )
            cover = book.get("cover", book.get("coverUrl", book.get("thumbUrl", "")))

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

            detail_url = f"https://fanqienovel.com/page/{bid}"
            yield scrapy.Request(
                detail_url, callback=self.parse_detail, dont_filter=True,
                headers={"Referer": "https://fanqienovel.com/rank/",
                         "User-Agent": self._MOBILE_UA},
                meta={"external_id": bid, "title": title,
                      "author": author, "cover": cover, "category": category,
                      "ranking_type": ranking_type},
            )

    # ============ HTML 兜底 ============
    def _parse_html(self, response):
        ranking_type = response.meta.get("ranking_type", self.ranking_type)
        items, sel_used = self._try_selectors(response)

        if not items:
            self.logger.warning(
                f"fanqie[{ranking_type}] HTML 选择器全未命中, body_len={len(response.text or '')}"
            )
            return

        self.logger.info(f"fanqie[{ranking_type}] HTML 命中 {len(items)} 项 (sel={sel_used})")

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

    def _try_selectors(self, response):
        for sel in self._ITEM_SELECTORS:
            items = response.css(sel)
            if items:
                return items, sel
        return [], ""

    def _extract_bid(self, book) -> str | None:
        href = book.css("a::attr(href)").get() or ""
        for pat in [
            r"/page/(\d+)",
            r"book_id=(\d+)",
            r"/book/(\d+)",
            r"/detail/(\d+)",
        ]:
            m = re.search(pat, href)
            if m:
                return m.group(1)
        return None

    @staticmethod
    def _pick_text(sel, candidates):
        for c in candidates:
            v = sel.css(c).get()
            if v:
                return v
        return ""

    def parse_detail(self, response):
        meta = response.meta
        if self.is_404_page(response):
            self.logger.warning(
                f"fanqie 详情页 404: {meta.get('external_id')} {response.url}"
            )
            return

        cover = meta.get("cover", "") or (
            response.css(".book-cover img::attr(src)").get()
            or response.css(".cover-img img::attr(src)").get()
            or ""
        )
        word = parse_int(
            response.css(".info-word::text, .word-count::text, .info-item em::text").get()
            or "0"
        ) or 0
        status_text = response.css(".status::text, .book-status::text").get() or ""
        status = "completed" if "完" in status_text else "ongoing"

        category = meta.get("category") or self._pick_text(
            response, [".category::text", ".book-category::text", ".tag::text"]
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
            status=status,
            description=description,
            tags=tags,
        )