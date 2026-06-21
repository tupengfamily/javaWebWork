"""当当图书榜 Spider — 公开畅销榜单

数据源: http://bang.dangdang.com/books (服务端渲染)

榜单映射:
- bestseller → 图书畅销榜  http://bang.dangdang.com/books/bestsellers/01.00.00.00.00.00-24hours-0-0-1-1
- newbook    → 新书热卖榜  http://bang.dangdang.com/books/newhotsales/01.00.00.00.00.00-24hours-0-0-1-1
- fivestars  → 好评榜      http://bang.dangdang.com/books/fivestars/01.00.00.00.00.00-24hours-0-0-1-1
- soaring    → 飙升榜      http://bang.dangdang.com/books/soaringsales/01.00.00.00.00.00-24hours-0-0-1-1

字段映射:
- novel_external_id = 当当 product_id (从详情页 URL 提取)
- title             = 书名
- author            = 作者
- view_count        = 推荐百分比 * 10000 (e.g. 99.6% → 996000)
- rec_count         = 评论数
- category          = 排行榜分类名
"""
import re
import scrapy

from .base import BaseSpider, parse_int


class DangdangSpider(BaseSpider):
    """当当图书榜爬虫"""

    site_code = "dangdang"
    name = "dangdang"

    custom_settings = {
        "DOWNLOAD_DELAY": 2.0,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
    }

    _BASE = "http://bang.dangdang.com"
    # 榜单 URL: {type}/{category}-{period}-0-0-{page}-1
    _RANK_URLS = {
        "bestseller": "/books/bestsellers/01.00.00.00.00.00-24hours-0-0-1-1",
        "newbook":    "/books/newhotsales/01.00.00.00.00.00-24hours-0-0-1-1",
        "fivestars":  "/books/fivestars/01.00.00.00.00.00-24hours-0-0-1-1",
        "soaring":    "/books/soaringsales/01.00.00.00.00.00-24hours-0-0-1-1",
    }

    pages: int = 1  # 每个榜单抓几页

    _UA = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.6778.140 Safari/537.36"
    )

    async def start(self):
        for rt in self.iter_all_types():
            path = self._RANK_URLS.get(rt)
            if not path:
                self.logger.warning(f"dangdang 无 {rt} 榜单映射,跳过")
                continue
            for page in range(1, max(1, int(self.pages)) + 1):
                # 翻页: URL 最后一段是页码
                page_path = re.sub(r'-\d+-1$', f'-{page}-1', path)
                url = self._BASE + page_path
                yield scrapy.Request(
                    url,
                    callback=self.parse_list,
                    dont_filter=True,
                    meta={"ranking_type": rt, "page": page},
                    headers={
                        "User-Agent": self._UA,
                        "Referer": "http://bang.dangdang.com/",
                        "Accept-Language": "zh-CN,zh;q=0.9",
                    },
                )

    def parse_list(self, response):
        rt = response.meta.get("ranking_type", self.ranking_type)
        page = response.meta.get("page", 1)

        if not self.validate_response(response, min_length=2000):
            return

        # 当当榜单列表: ul.bang_list li / li.list_item
        items = response.css("ul.bang_list li")
        if not items:
            items = response.css("li.list_item, li[class*='list_item']")
        if not items:
            # 回退: 查所有含 class 的 li
            items = response.css("div.bang_list li")

        if not items:
            self.logger.warning(f"dangdang[{rt}] p{page} 选择器全未命中: {response.url}")
            return

        self.logger.info(f"dangdang[{rt}] p{page} 命中 {len(items)} 本书")

        # 翻页 rank 累加
        page_size = 20  # 当当每页 20 本
        rank_offset = (page - 1) * page_size

        for idx, item in enumerate(items, start=1):
            # 提取 product_id
            link = item.css("a.name::attr(href)").get() or item.css("a::attr(href)").get() or ""
            pid_m = re.search(r'/(\d+)\.html', link)
            pid = pid_m.group(1) if pid_m else ""
            if not pid:
                # 尝试从 data-asin 或其他属性提取
                pid = item.attrib.get("id", "").replace("list_item_", "").strip()
            if not pid:
                continue

            title = (item.css("a.name::text").get()
                     or item.css("div.name a::text").get()
                     or item.css("a::text").get() or "").strip()
            # 作者
            author = ""
            desc_spans = item.css("div.publisher_info span, div.info span, p.author a::text")
            for sp in desc_spans:
                txt = sp.css("::text").get("").strip()
                if txt and ("著" in txt or "编" in txt or "/" in txt):
                    author = txt.split("/")[0].strip()
                    break
            if not author:
                author = (item.css("p.author a::text").get() or "").strip()

            # 推荐百分比 → view_count
            pct_text = (item.css("span.tuijian_percent::text").get()
                        or item.css("div.tuijian span::text").get() or "").strip()
            pct_m = re.search(r'([\d.]+)', pct_text)
            view_count = int(float(pct_m.group(1)) * 10000) if pct_m else 0

            # 评论数 → rec_count
            comment_text = (item.css("a.comment_num::text").get()
                            or item.css("span.comment_num::text").get() or "").strip()
            rec_count = parse_int(comment_text)

            yield self.make_ranking_with_type(
                rt,
                novel_external_id=pid,
                rank=rank_offset + idx,
                view_count=view_count,
                rec_count=rec_count,
            )

            # 详情页请求（补全字段）
            if link and not link.startswith("http"):
                link = "http://bang.dangdang.com" + link
            if link:
                yield scrapy.Request(
                    link,
                    callback=self.parse_detail,
                    dont_filter=True,
                    meta={
                        "external_id": pid, "title": title, "author": author,
                        "ranking_type": rt, "rank": rank_offset + idx,
                    },
                    headers={"User-Agent": self._UA},
                )

    def parse_detail(self, response):
        meta = response.meta
        if not self.validate_response(response, min_length=500):
            return

        pid = meta.get("external_id", "")
        title = meta.get("title", "").strip()
        if not title:
            title = (response.css("title::text").get() or "").strip()

        author = meta.get("author", "").strip()
        if not author:
            author = (response.css("span.author a::text").get()
                      or response.css("a.name::text").get() or "").strip()

        cover = (response.css("img#largePic::attr(src)").get()
                 or response.css("img[class*='large']::attr(src)").get() or "").strip()
        if cover and not cover.startswith("http"):
            cover = "http:" + cover

        # 出版社
        publisher = (response.css("span.publisher a::text").get() or "").strip()

        # 分类
        breadcrumb = response.css("div.crumb a::text").getall()
        category = breadcrumb[-1].strip() if breadcrumb else ""

        yield self.make_novel(
            external_id=pid,
            title=title,
            author=author,
            novel_url=response.url,
            category=category,
            cover_url=cover,
            word_count=0,
            status="completed",
            description="",
            tags=",".join(filter(None, [publisher, "当当图书"])),
        )
