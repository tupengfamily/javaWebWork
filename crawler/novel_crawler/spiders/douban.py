"""豆瓣读书 Spider — 公开页面榜单

数据源（无需登录）:
- Top250   https://book.douban.com/top250
- 热门      https://book.douban.com/  (首页每日推荐)
- 分类     https://book.douban.com/explore?cat={cat_id}

榜单映射:
- daily    → 热门(虚构+非虚构首页推荐)
- monthly  → Top250 翻页(取新书)
- total    → Top250(高评分经典)
- category → 分类浏览(按豆瓣 cat_id)

字段映射:
- view_count = rating * 10000     (豆瓣评分 0-10 → 我们的 view_count)
- rec_count  = rating_count        (评价人数)

反爬处理:
- USER_AGENT/Referer 必备
- DOWNLOAD_DELAY 加大到 3s
- 失败时返回空,前端展示为空
"""
import re
import scrapy

from .base import BaseSpider, parse_int


class DoubanSpider(BaseSpider):
    """豆瓣读书榜单爬虫"""

    site_code = "douban"
    name = "douban"

    custom_settings = {
        "DOWNLOAD_DELAY": 3.0,                      # 豆瓣反爬较严
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "COOKIES_ENABLED": False,                    # 不带 cookie,反爬更宽松
    }

    # ---- 榜单 URL 配置 ----
    # daily  用豆瓣首页(每日推荐/热门)
    # monthly 用 Top250 翻页(1-3 页)
    # total   用 Top250(高评分经典)
    # category 用分类浏览(各 cat_id)
    _RANK_URLS = {
        "daily":   "https://book.douban.com/",                          # 首页
        "monthly": "https://book.douban.com/top250?start=0",            # Top250 头页
        "total":   "https://book.douban.com/top250?start=0",            # Top250 头页
    }

    # 豆瓣图书分类 cat_id (用于 ranking_type=category)
    _CATEGORIES = {
        "1001": "文学",
        "1002": "流行",
        "1003": "文化",
        "1004": "生活",
        "1005": "经管",
        "1006": "科技",
    }
    _CATEGORY_URL_TEMPLATE = "https://book.douban.com/explore?cat={cat_id}"

    # Top250 翻页
    _TOP250_PAGE_SIZE = 25
    pages: int = 2   # Top250 抓 2 页(50 本)

    # ---- 选择器(豆瓣读书 DOM 特征) ----
    _TOP250_ITEM_SELECTORS = [
        "table.pl2 tr.item",        # Top250
        ".article .item",
        "li.subject-item",
    ]
    _TOP250_TITLE_SELECTORS = [
        "a.nbg::attr(title)",       # Top250 标题
        "a::attr(title)",
        "td a::text",
        "h2 a::text",
    ]
    _TOP250_RATING_SELECTORS = [
        ".rating_nums::text",
        "span.rating_nums::text",
        ".rating::text",
    ]
    _TOP250_PEOPLE_SELECTORS = [
        ".pl+::text",               # "1234人评价"
        "span.pl::text",
    ]
    _TOP250_LINK_SELECTORS = [
        "a.nbg::attr(href)",        # Top250 链接(包含 /subject/1234/)
        "a::attr(href)",
    ]

    # 首页推荐 item 选择器
    _HOME_ITEM_SELECTORS = [
        ".billboard-list li",
        ".popular-books li",
        ".books-list li",
        "li.media",
    ]

    # 详情页(用于补全简介/标签)
    _DESC_SELECTORS = [
        "meta[name='description']::attr(content)",
        "#link-report .intro p::text",
        ".intro p::text",
        "#content .intro p::text",
    ]
    _TAG_SELECTORS = [
        "#db-tags a::text",
        ".tag a::text",
        ".indent .tag a::text",
    ]

    _UA = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.6778.140 Safari/537.36"
    )

    async def start(self):
        """构造初始请求:按 ranking_type 选择不同 URL

        - daily  / monthly / total → 各自 URL
        - category → self.category 作为 cat_id
        - "all" 模式遍历 daily/monthly/total 三种榜单
        """
        for rt in self.iter_all_types():
            # category 模式由 -a category 传入 cat_id
            if rt == "category" or self.ranking_type == "category":
                cat_id = self.category or "1001"  # 默认文学
                url = self._CATEGORY_URL_TEMPLATE.format(cat_id=cat_id)
                yield scrapy.Request(
                    url,
                    callback=self.parse_category,
                    dont_filter=True,
                    meta={"ranking_type": rt, "cat_id": cat_id, "page": 1},
                    headers=self._headers(),
                )
                continue

            base_url = self._RANK_URLS.get(rt)
            if not base_url:
                self.logger.warning(f"douban 无 {rt} 榜单映射,跳过")
                continue

            # Top250 系列榜单翻页
            if "top250" in base_url:
                for page in range(1, max(1, int(self.pages)) + 1):
                    start = (page - 1) * self._TOP250_PAGE_SIZE
                    url = f"https://book.douban.com/top250?start={start}"
                    yield scrapy.Request(
                        url,
                        callback=self.parse_top250,
                        dont_filter=True,
                        meta={"ranking_type": rt, "page": page},
                        headers=self._headers(),
                    )
            else:
                yield scrapy.Request(
                    base_url,
                    callback=self.parse_home,
                    dont_filter=True,
                    meta={"ranking_type": rt, "page": 1},
                    headers=self._headers(),
                )

    def _headers(self) -> dict:
        """豆瓣必备 header:UA + Referer"""
        return {
            "User-Agent": self._UA,
            "Referer": "https://book.douban.com/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

    # ========================
    # Top250 解析
    # ========================
    def parse_top250(self, response):
        rt = response.meta.get("ranking_type", self.ranking_type)
        page = response.meta.get("page", 1)
        if not self.validate_response(response, min_length=2000):
            return

        items, sel = self._try_selectors(response, self._TOP250_ITEM_SELECTORS)
        if not items:
            self.logger.warning(
                f"douban[{rt}] Top250 选择器全未命中: {response.url}"
            )
            return

        self.logger.info(
            f"douban[{rt}] Top250 使用选择器 '{sel}' 命中 {len(items)} 本书"
        )

        # 跨页 rank 累加:第 N 页起始 rank = (N-1) * page_size + 1
        rank_offset = (page - 1) * self._TOP250_PAGE_SIZE
        for idx, item in enumerate(items, start=1):
            bid = self._extract_bid(item)
            if not bid:
                continue

            title = self._pick_text(item, self._TOP250_TITLE_SELECTORS).strip()
            author = self._extract_author_from_top250(item)
            rating = parse_int(self._pick_text(item, self._TOP250_RATING_SELECTORS))
            people = self._extract_people(item)

            yield self.make_ranking_with_type(
                rt,
                novel_external_id=bid,
                rank=rank_offset + idx,        # 跨页累加,避免重复
                view_count=rating * 10000,    # 评分 → view_count
                rec_count=people,             # 评价人数 → rec_count
            )

            # 详情页请求(补全 word_count=0, status, cover)
            yield scrapy.Request(
                f"https://book.douban.com/subject/{bid}/",
                callback=self.parse_detail,
                dont_filter=True,
                meta={"external_id": bid, "title": title, "author": author,
                      "category": "", "ranking_type": rt, "rank": idx},
                headers=self._headers(),
            )

    def _extract_bid(self, item) -> str | None:
        for sel in self._TOP250_LINK_SELECTORS:
            href = item.css(sel).get() or ""
            m = re.search(r"/subject/(\d+)", href)
            if m:
                return m.group(1)
        return None

    def _extract_author_from_top250(self, item) -> str:
        """Top250 第二列 <p class="pl">[作者] / 出版社 / 年份 / 价钱</p>"""
        pl = item.css("p.pl::text").get() or ""
        # 形如 "[美] 卡勒德·胡赛尼 / 李继宏 / 上海人民出版社 / 2006-5 / 29.00元"
        m = re.match(r"\s*\[?[^/\n]*\]?\s*([^/]+?)\s*/", pl)
        if m:
            return m.group(1).strip()
        return ""

    def _extract_people(self, item) -> int:
        for sel in self._TOP250_PEOPLE_SELECTORS:
            txt = item.css(sel).get() or ""
            m = re.search(r"(\d+)\s*人", txt)
            if m:
                return int(m.group(1))
        return 0

    # ========================
    # 分类页 解析
    # ========================
    def parse_category(self, response):
        rt = response.meta.get("ranking_type", self.ranking_type)
        cat_id = response.meta.get("cat_id", "1001")
        cat_name = self._CATEGORIES.get(cat_id, "")

        if not self.validate_response(response, min_length=2000):
            return

        # 分类页推荐用 ul#subject-list li
        items = response.css("ul#subject-list li")
        if not items:
            items = response.css(".article ul li")
        if not items:
            self.logger.warning(
                f"douban[{rt}] 分类页({cat_id}) 选择器全未命中: {response.url}"
            )
            return

        self.logger.info(
            f"douban[{rt}] 分类页 cat={cat_id} 命中 {len(items)} 本书"
        )

        for idx, item in enumerate(items, start=1):
            bid = self._extract_bid(item)
            if not bid:
                continue

            title = (item.css("h2 a::text").get() or "").strip()
            if not title:
                title = (item.css("a::attr(title)").get() or "").strip()

            rating = parse_int(item.css(".rating_nums::text").get() or "")
            people = self._extract_people(item)

            yield self.make_ranking_with_type(
                rt,
                novel_external_id=bid,
                rank=idx,
                view_count=rating * 10000,
                rec_count=people,
                category=cat_name,   # 分类榜写分类名
            )

            if cat_name:
                cat_item = self.make_category(
                    name=cat_name,
                    code=f"douban_{cat_id}",   # 避免与小说分类冲突
                    sort_order=int(cat_id) % 100,
                )
                if cat_item:
                    yield cat_item

            yield scrapy.Request(
                f"https://book.douban.com/subject/{bid}/",
                callback=self.parse_detail,
                dont_filter=True,
                meta={"external_id": bid, "title": title, "author": "",
                      "category": cat_name, "ranking_type": rt, "rank": idx},
                headers=self._headers(),
            )

    # ========================
    # 首页(热门) 解析
    # ========================
    def parse_home(self, response):
        rt = response.meta.get("ranking_type", self.ranking_type)
        if not self.validate_response(response, min_length=2000):
            return

        items, sel = self._try_selectors(response, self._HOME_ITEM_SELECTORS)
        if not items:
            self.logger.warning(
                f"douban[{rt}] 首页选择器全未命中: {response.url}"
            )
            return

        self.logger.info(
            f"douban[{rt}] 首页 使用选择器 '{sel}' 命中 {len(items)} 本书"
        )

        for idx, item in enumerate(items, start=1):
            bid = self._extract_bid(item)
            if not bid:
                continue

            title = (item.css("a::attr(title)").get()
                     or item.css("a::text").get() or "").strip()
            rating = parse_int(item.css(".rating_nums::text").get() or "")
            people = self._extract_people(item)

            yield self.make_ranking_with_type(
                rt,
                novel_external_id=bid,
                rank=idx,
                view_count=rating * 10000,
                rec_count=people,
            )

    # ========================
    # 详情页(只补全缺失字段)
    # ========================
    def parse_detail(self, response):
        meta = response.meta
        # 详情页可选,即使被反爬也不影响榜单数据
        if not self.validate_response(response, min_length=500):
            return

        bid = meta.get("external_id", "")
        title = meta.get("title", "").strip()
        if not title:
            title = (response.css("title::text").get() or "").strip()

        author = (response.css("#info span a::text").get()
                  or response.css("#info .writer a::text").get() or "").strip()
        if not author:
            # 详情页 #info 文本解析: <作者名> / <译者> / ...
            info_txt = " ".join(response.css("#info::text").getall())
            m = re.match(r"\s*作者[:：]?\s*([^\n/]+)", info_txt)
            if m:
                author = m.group(1).strip()

        cover = (response.css("#mainpic img::attr(src)").get() or "").strip()
        # status: 豆瓣用"出版年/页数/定价"等,无连载/完结概念,统一用"completed"
        status = "completed"

        yield self.make_novel(
            external_id=bid,
            title=title,
            author=author,
            novel_url=response.url,
            category=meta.get("category", ""),
            cover_url=cover,
            word_count=0,                # 豆瓣读书无统一字数,留 0
            status=status,
            description=self._pick_text(response, self._DESC_SELECTORS).strip(),
            tags=",".join(t.strip() for t in response.css("#db-tags a::text").getall() if t.strip()),
        )

    # ========================
    # 工具
    # ========================
    @staticmethod
    def _try_selectors(response, candidates: list[str]):
        for sel in candidates:
            items = response.css(sel)
            if items:
                return items, sel
        return [], ""

    @staticmethod
    def _pick_text(sel, candidates) -> str:
        for c in candidates:
            v = sel.css(c).get()
            if v:
                return v
        return ""
