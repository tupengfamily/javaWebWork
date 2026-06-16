"""起点中文网 Spider — 一体化版

新增能力(相对上一版):
1. 支持 ranking_type='all': 一次任务产出 daily/monthly/total 三个榜单的记录
2. 列表页给出的 category 字段 → 同步写入 category 字典表(CategoryData item)
3. 列表页已拿到的字段(title/author/category/cover)直接透传给 NovelData,
   parse_detail 不再"全量重新解析",而是"补全缺失字段"减少重复解析。
"""
import json
import re
import scrapy

from .base import BaseSpider, parse_int


class QidianSpider(BaseSpider):
    """起点中文网榜单爬虫 — 多选择器容错 + API 兜底 + all 模式"""

    site_code = "qidian"
    name = "qidian"

    custom_settings = {
        "DOWNLOAD_DELAY": 2.0,
    }

    # ---- 候选选择器(优先级从高到低,第一个命中即用到整页) ----
    _ITEM_SELECTORS = [
        ".rank-list li",                      # 2025+
        ".rank-list .rank-list-item",         # 备选 2025
        ".book-img-text li",                  # 2024 及之前
        "li[data-bid]",                       # 通用: 有 data-bid 属性的 li
        "li.rank-item",                       # 旧版
    ]

    _TITLE_SELECTORS = [
        "h3 a::text", ".book-name a::text", "h2 a::text",
        ".name a::text", ".book-info-title a::text",
    ]
    _AUTHOR_SELECTORS = [
        ".author a::text", ".author-name::text", ".book-author::text",
        "a.name::text", ".author .name::text",
    ]
    _CATEGORY_SELECTORS = [
        ".category a::text", ".book-category::text", ".tag::text",
    ]
    _VIEW_SELECTORS = [
        ".total::text", ".count::text", ".view-count::text",
        ".read-num::text", "em::text",
    ]

    # ---- API 兜底 URL 模板 ----
    _API_MAPS = {
        "daily":   "https://www.qidian.com/rank/h5_rank_list?channelId=0&rankId=1",
        "monthly": "https://www.qidian.com/rank/h5_rank_list?channelId=0&rankId=2",
        "total":   "https://www.qidian.com/rank/h5_rank_list?channelId=0&rankId=3",
    }

    # ---- HTML URL 模板(rank_path,base_url 用 https://www.qidian.com)----
    # rich-crawler-data: 新增 yuepiao / newbook / finish 三个榜单
    _RANK_PATHS = {
        "daily":   "/rank/daily/",
        "monthly": "/rank/monthly/",
        "total":   "/rank/total/",
        "yuepiao": "/rank/yuepiao/",
        "newbook": "/rank/newbook/",
        "finish":  "/rank/finish/",
    }
    _RANK_BASE = "https://www.qidian.com"

    # "all" 模式覆盖为 6 个榜单
    ALL_RANKING_TYPES = ["daily", "monthly", "total", "yuepiao", "newbook", "finish"]

    # 详情页描述 / 标签 候选选择器(起点 DOM 特征)
    _DESC_SELECTORS = [
        "meta[name='description']::attr(content)",
        ".book-intro::text",
        ".book-desc::text",
        "#book-intro::text",
        ".intro p::text",
    ]
    _TAG_SELECTORS = [
        ".book-intro-tags a::text",
        ".book-tag a::text",
        ".labels a::text",
        ".tag-list a::text",
        ".book-info .tag a::text",
    ]

    async def start(self):
        """构造初始请求:根据 ranking_type 决定单榜单还是 all 模式,每榜单翻 N 页

        rich-crawler-data:
        - 使用 BaseSpider.build_rank_requests 助手,自动按 self.pages 翻页
        - "all" 模式遍历 ALL_RANKING_TYPES 6 种榜单
        - 单 ranking_type 模式只发起 1 种榜单 × N 页
        """
        for req in self.build_rank_requests(
            rank_paths=self._RANK_PATHS,
            base_url=self._RANK_BASE,
            callback=self.parse,
            meta_extra={"site_code": self.site_code},
        ):
            req.headers["Referer"] = "https://www.qidian.com/"
            yield req

    # ============================================================
    # HTML 解析
    # ============================================================
    def parse(self, response):
        """解析列表页: 先试 HTML, 失败后走 API"""
        ranking_type = response.meta.get("ranking_type", self.ranking_type)
        page = response.meta.get("page", 1)

        # 200 + 404 错误页兜底(SPA 类站点常见)
        if self.is_404_page(response):
            self.logger.warning(
                f"qidian[{ranking_type}] page={page} 返回 200 但内容是 404 错误页,跳过"
            )
            return

        items, selector_used = self._try_selectors(response)

        if items:
            self.logger.info(
                f"qidian[{ranking_type}] 使用选择器 '{selector_used}' 命中 {len(items)} 项"
            )
            yield from self._parse_items(items, response, ranking_type)
            self.log_parse_summary(response, len(items), len(items))
            return

        # HTML 全失败 → 走 API 兜底
        self.logger.warning(
            f"qidian[{ranking_type}] HTML 选择器全未命中,尝试 API 兜底: {response.url}"
        )
        api_url = self._API_MAPS.get(ranking_type)
        if api_url:
            yield scrapy.Request(
                api_url,
                callback=self._parse_api,
                meta={"ranking_type": ranking_type},
                headers={"Referer": "https://www.qidian.com/",
                         "Accept": "application/json, text/plain, */*",
                         "X-Requested-With": "XMLHttpRequest"},
                dont_filter=True,
            )
        else:
            self.logger.error(f"qidian 无 API 映射: {ranking_type}")

    def _try_selectors(self, response):
        """试所有候选选择器,返回 (items, selector_name)"""
        for sel in self._ITEM_SELECTORS:
            items = response.css(sel)
            if items:
                return items, sel
        return [], ""

    def _parse_items(self, items, response, ranking_type: str):
        """解析条目列表,产出 ranking + category + detail 请求

        一次性产出 3 类 item:
        - RankingData: 排行榜快照(每个榜单一条)
        - CategoryData: 分类字典同步(去重后入库)
        - scrapy.Request: 详情页(补全 word_count/status/cover)
        """
        for idx, book in enumerate(items, start=1):
            # --- book_id ---
            bid = self._extract_bid(book)
            if not bid:
                continue

            title = self._pick_text(book, self._TITLE_SELECTORS).strip()
            author = self._pick_text(book, self._AUTHOR_SELECTORS).strip()
            category = self._pick_text(book, self._CATEGORY_SELECTORS).strip()
            view = parse_int(self._pick_text(book, self._VIEW_SELECTORS))

            # 1) ranking record
            yield self.make_ranking_with_type(
                ranking_type,
                novel_external_id=bid,
                rank=idx,
                view_count=view,
                category=category,
            )

            # 2) category 同步(列表页给出 category 时)
            if category:
                cat_item = self.make_category(
                    name=category,
                    code=self.category_from_cn_name(category),
                )
                if cat_item:
                    yield cat_item

            # 3) 详情页请求(补全缺失字段)
            href = book.css("a::attr(href)").get()
            if href:
                yield response.follow(
                    href,
                    callback=self.parse_detail,
                    meta={
                        "external_id": bid,
                        "title": title,
                        "author": author,
                        "category": category,
                        "view_count": view,
                        "ranking_type": ranking_type,
                    },
                )

    def _extract_bid(self, book) -> str | None:
        """从条目提取 book_id: data-bid → href 正则 → None"""
        for sel in ["::attr(data-bid)", "a::attr(data-bid)", ".book-name a::attr(data-bid)"]:
            v = book.css(sel).get()
            if v and v.strip():
                return v.strip()
        href = book.css("a::attr(href)").get() or ""
        m = re.search(r"/book/(\d+)", href)
        return m.group(1) if m else None

    @staticmethod
    def _pick_text(sel, candidates):
        """依次试候选选择器,返回第一个非空文本"""
        for c in candidates:
            v = sel.css(c).get()
            if v:
                return v
        return ""

    # ========================
    # API 兜底解析
    # ========================
    def _parse_api(self, response):
        """解析起点 H5 榜单 JSON API"""
        ranking_type = response.meta.get("ranking_type", self.ranking_type)
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error(f"qidian API 返回非 JSON: {response.text[:200]}")
            return

        books = (
            data.get("data", {})
                .get("rank", {})
                .get("bookList", [])
            or data.get("data", {}).get("bookList", [])
            or []
        )

        if not books:
            self.logger.warning(f"qidian API 返回空列表: {response.text[:300]}")
            return

        self.logger.info(f"qidian[{ranking_type}] API 命中 {len(books)} 本书")

        for idx, book in enumerate(books, start=1):
            bid = str(book.get("bookId", book.get("bid", "")))
            if not bid:
                continue

            title = book.get("bookName", book.get("title", ""))
            author = book.get("authorName", book.get("author", ""))
            category = book.get("categoryName", book.get("category", ""))
            view = parse_int(str(book.get("totalRead", book.get("readCount", "0"))))
            cover = book.get("coverUrl", book.get("imgUrl", ""))

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

            detail_url = f"https://www.qidian.com/book/{bid}/"
            yield scrapy.Request(
                detail_url,
                callback=self.parse_detail,
                meta={"external_id": bid, "title": title,
                      "author": author, "category": category, "cover": cover,
                      "view_count": view, "ranking_type": ranking_type},
            )

    # ========================
    # 详情页(只补全缺失字段,不再重复解析列表已给的字段)
    # ========================
    def parse_detail(self, response):
        meta = response.meta

        # 404 兜底
        if self.is_404_page(response):
            self.logger.warning(
                f"qidian 详情页 404: {meta.get('external_id')} {response.url}"
            )
            return

        # cover: 优先用列表页/榜单 API 给的,否则从详情页抽
        cover = meta.get("cover", "") or (
            response.css(".book-img img::attr(src)").get()
            or response.css(".book-cover img::attr(src)").get()
            or ""
        )

        # word_count: 详情页才有
        word = parse_int(
            response.css(".book-info p em::text").re_first(r"\d+")
            or "".join(response.css(".book-info p::text").re_findall(r"\d+"))
        ) or 0

        # status: 详情页判断
        status_text = response.css(".book-info .status::text").get() or ""
        status = "completed" if "完" in status_text else "ongoing"

        # title/author/category 优先用 meta(列表页已给的)
        title = meta.get("title") or self._pick_text(
            response, ["h1::text", ".book-info-title::text", ".title::text"]
        ).strip()
        author = meta.get("author") or self._pick_text(
            response, [".author a::text", ".author-name::text"]
        ).strip()
        category = meta.get("category") or self._pick_text(
            response, [".category a::text", ".tag::text"]
        ).strip()

        # 若详情页补出了 category 但列表没给,补一条 CategoryData
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
            title=title,
            author=author,
            category=category,
            cover_url=cover,
            novel_url=response.url,
            word_count=word,
            status=status,
            description=description,
            tags=tags,
        )