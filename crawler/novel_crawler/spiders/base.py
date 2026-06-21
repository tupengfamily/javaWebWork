"""BaseSpider - 所有站点爬虫的抽象基类

设计目标
========
1. 统一任务参数注入(task_id/ranking_type/category 由 dispatcher 通过 -a 传入)
2. 统一数据构造入口(make_novel / make_ranking 自动填 site_code)
3. 提供通用工具(parse_int 处理"万"/"亿"等中文数字,validate_response 判断页面是否可用)

子类必做
=======
- 设置 `site_code` 类属性(必须与 site.code 一致)
- 设置 `name` 类属性(Scrapy 内部使用)
- 实现 `start_requests()`: 构造初始请求
- 实现 `parse()`: 解析列表页,产出 NovelData / RankingData item

使用示例
========
class QidianSpider(BaseSpider):
    site_code = "qidian"
    name = "qidian"

    def start_requests(self):
        yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        if not self.validate_response(response): return
        for ...:
            yield self.make_ranking(novel_external_id=..., rank=..., ...)
            yield response.follow(url, callback=self.parse_detail)

    def parse_detail(self, response):
        yield self.make_novel(external_id=..., title=..., ...)
"""
import re
import logging

import scrapy
from scrapy.http import Response

from novel_crawler.items import NovelData, RankingData, CategoryData


def parse_int(s):
    """从字符串提取整数,自动处理中文数字单位(万/亿)

    示例:
        parse_int("120万")    -> 1200000
        parse_int("1.2万")    -> 12000
        parse_int("3,456")    -> 3456
        parse_int("1.5亿")    -> 150000000
        parse_int("")         -> 0
        parse_int(None)       -> 0
    """
    if not s:
        return 0

    raw = s.strip().replace(",", "").replace(" ", "").replace("+", "")

    # 处理 "亿"
    m = re.match(r"([\d.]+)\s*亿", raw)
    if m:
        base = float(m.group(1))
        tail = raw[m.end():]
        return int(base * 100_000_000) + parse_int(tail)

    # 处理 "万"
    m = re.match(r"([\d.]+)\s*万", raw)
    if m:
        base = float(m.group(1))
        tail = raw[m.end():]
        return int(base * 10_000) + parse_int(tail)

    # 处理 "千"
    m = re.match(r"([\d.]+)\s*千", raw)
    if m:
        base = float(m.group(1))
        tail = raw[m.end():]
        return int(base * 1_000) + parse_int(tail)

    # 纯数字
    m = re.search(r"(\d+)", raw)
    return int(m.group(1)) if m else 0


class BaseSpider(scrapy.Spider):
    """所有站点爬虫的抽象基类,统一任务参数和数据构造入口"""

    # ---- 子类必须覆盖 ----
    site_code: str = ""    # 与 site.code 一致(必填,否则 Pipeline 找不到站点)
    name: str = ""          # Scrapy 内部标识(必填,否则 scrapy crawl 无法调用)

    # ---- 由 dispatcher 通过 -a 注入(子类一般不用动) ----
    task_id: int = 0        # 当前 crawl_task.id
    ranking_type: str = "daily"    # daily / monthly / total / category / all
    category: str = ""      # 仅 ranking_type=category 时有意义

    # ---- "all" 模式下要爬取的子榜单类型列表(子类可覆盖) ----
    ALL_RANKING_TYPES: list[str] = ["daily", "monthly", "total"]

    # ---- 分页:每个榜单默认翻 2 页(20→40 本/次),命令行 -a pages=N 可覆盖 ----
    pages: int = 2

    # ---- 反爬敏感页面的常见字符串(如果返回这些,说明被反爬了) ----
    _ANTI_BOT_MARKERS = [
        "验证", "verify", "captcha", "拦截", "blocked",
        "Access Denied", "challenge", "请稍后重试",
        "安全检测", "频繁访问", "请求过于频繁",
    ]

    def validate_response(self, response: Response, min_length: int = 500) -> bool:
        """验证响应是否可用(非反爬页/非空页/非 JS 重定向页)

        返回 False 说明页面不可解析(反爬/JS 重定向/内容过短),子类应 return。

        使用示例:
            if not self.validate_response(response, min_length=800):
                return
        """
        url = response.url

        # HTTP 非 200
        if response.status != 200:
            self.logger.warning(f"HTTP {response.status} on {url}")
            return False

        # 兼容压缩/二进制响应(豆瓣偶尔返回非 text/html)
        try:
            body = response.text or ""
        except AttributeError:
            body = response.body.decode("utf-8", errors="ignore") if response.body else ""

        # 内容过短(可能是 JS 重定向或空白页)
        if len(body) < min_length:
            self.logger.warning(
                f"响应内容过短({len(body)} bytes),可能 JS 重定向: {url}"
            )
            return False

        # 检测反爬特征
        # 注：仅扫描 body 前 2000 字符以降低 CPU 开销，反爬标记通常在头部位置
        body_lower = body[:2000].lower()
        for marker in self._ANTI_BOT_MARKERS:
            if marker.lower() in body_lower:
                self.logger.warning(
                    f"检测到反爬标记 '{marker}' on {url}"
                )
                return False

        return True

    def log_parse_summary(
        self, response: Response, items_found: int, novels_found: int
    ):
        """打一条汇总日志,方便排查为什么没数据"""
        self.logger.info(
            f"parse done: {response.url} "
            f"items={items_found} novels={novels_found} "
            f"len={len(response.text or '')}"
        )

    def make_novel(self, **kwargs) -> NovelData:
        """构造 NovelData,自动填 site_code"""
        return NovelData(site_code=self.site_code, **kwargs)

    def make_ranking(self, **kwargs) -> RankingData:
        """构造 RankingData,自动填 site_code/ranking_type/category"""
        return RankingData(
            site_code=self.site_code,
            ranking_type=self.ranking_type,
            category=self.category,
            **kwargs,
        )

    def make_ranking_with_type(self, ranking_type: str, **kwargs) -> RankingData:
        """"all" 模式下,显式指定单个 ranking_type 构造 RankingData

        使用示例:
            for rt in self.iter_all_types():
                yield self.make_ranking_with_type(rt, novel_external_id=bid, rank=idx, ...)
        """
        # "all" 模式不指定 category(榜单维度的过滤)
        return RankingData(
            site_code=self.site_code,
            ranking_type=ranking_type,
            category="",
            **kwargs,
        )

    def make_category(self, name: str, code: str = "", sort_order: int = 100) -> CategoryData | None:
        """构造 CategoryData,name 为空时返回 None

        自动用 name 生成稳定的 code,保证数据库唯一键不冲突
        """
        if not name or not name.strip():
            return None
        return CategoryData(
            code=code.strip() if code else "",
            name=name.strip(),
            sort_order=sort_order,
        )

    def iter_all_types(self) -> list[str]:
        """"all" 模式下,返回要遍历的 ranking_type 列表

        非 "all" 模式返回当前 self.ranking_type 的单元素列表,
        让 Spider 内部循环代码不用关心自己处在哪种模式。
        """
        if self.ranking_type == "all":
            return list(self.ALL_RANKING_TYPES)
        return [self.ranking_type]

    def category_from_cn_name(self, cn: str) -> str:
        """把中文分类名转拼音 code(简版:仅做基础转换)

        真实项目中可以引入 pypinyin,这里做一个常见映射表 + 默认 fallback,
        避免每次都依赖第三方包。
        """
        if not cn:
            return ""
        _MAP = {
            "玄幻": "xuanhuan", "都市": "dushi", "仙侠": "xianxia",
            "科幻": "kehuan", "历史": "lishi", "军事": "junshi",
            "游戏": "youxi", "体育": "tiyu", "校园": "xiaoyuan",
            "奇幻": "qihuan", "言情": "yanqing", "悬疑": "xuanyi",
            "恐怖": "kongbu", "名著": "mingzhu", "其他": "qita",
            "灵异": "lingyi", "武侠": "wuxia", "同人": "tongren",
            "轻小说": "qingxiaoshuo", "现实": "xianshi", "短篇": "duanpian",
            "剧本": "juben",
        }
        return _MAP.get(cn.strip(), "")

    # ============================================================
    # description / tags 抽取(子类 parse_detail 调用)
    # ============================================================
    def make_description(self, response, selectors: list[str] | None = None) -> str:
        """从详情页抽取 description(简介)

        子类可覆盖 selectors 自定义;默认 5 个常见节点。
        返回值 .strip() 后截断到 1000 字符。
        """
        if selectors is None:
            selectors = [
                "meta[name='description']::attr(content)",
                ".book-intro::text",
                ".intro::text",
                "#book-intro::text",
                ".book-desc::text",
            ]
        text = ""
        for sel in selectors:
            v = response.css(sel).get()
            if v and v.strip():
                text = v.strip()
                break
        # 去除多余空白 + 截断
        text = re.sub(r"\s+", " ", text).strip()
        return text[:1000]

    def make_tags(self, response, selectors: list[str] | None = None, max_n: int = 8) -> str:
        """从详情页抽取 tags(逗号分隔字符串)

        子类可覆盖 selectors。最多 max_n 个,过滤空值 / emoji / 纯标点。
        """
        if selectors is None:
            selectors = [
                ".tag a::text",
                ".book-tag span::text",
                ".book-tag a::text",
                ".labels a::text",
                ".tag-list .tag::text",
            ]
        items: list[str] = []
        for sel in selectors:
            for v in response.css(sel).getall():
                v = v.strip()
                if not v:
                    continue
                # 过滤特殊字符 / emoji,仅保留中英数与逗号
                v = re.sub(r"[^\w\u4e00-\u9fff,]", "", v)
                if v and v not in items:
                    items.append(v)
                if len(items) >= max_n:
                    break
            if len(items) >= max_n:
                break
        return ",".join(items)

    # ============================================================
    # 分页 URL 助手
    # ============================================================
    def build_rank_requests(
        self,
        rank_paths: dict[str, str],
        base_url: str = "",
        callback=None,
        meta_extra: dict | None = None,
    ):
        """根据 `pages` 构造 N 个 Request(N = self.pages)

        用法 (在 spider.start() 内):
            for rt in self.iter_all_types():
                yield from self.build_rank_requests(
                    self._RANK_PATHS,
                    base_url="https://www.qidian.com",
                    callback=self.parse,
                    meta_extra={"ranking_type": rt},
                )
        """
        from scrapy import Request
        if callback is None:
            callback = self.parse
        for rt in self.iter_all_types():
            path = rank_paths.get(rt)
            if not path:
                self.logger.warning(
                    f"{self.site_code} 无榜单 {rt} 的 path 映射,跳过"
                )
                continue
            for page in range(1, max(1, int(self.pages)) + 1):
                # 拼分页:基础 URL + path + ?page=N (或路径分页)
                if "{page}" in path:
                    url = (base_url + path).format(page=page)
                else:
                    sep = "&" if "?" in path else "?"
                    url = f"{base_url}{path}{sep}page={page}"
                meta = {"ranking_type": rt, "page": page}
                if meta_extra:
                    meta.update(meta_extra)
                yield Request(
                    url,
                    callback=callback,
                    meta=meta,
                    dont_filter=True,
                )

    def is_404_page(self, response) -> bool:
        """检测返回 200 但内容是 404 错误页(SPA / Nuxt SSR 常见)

        起点 / 番茄 / 纵横 部分站点的 404 仍返回 200,body 含特定标记。
        """
        body = response.text or ""
        markers = ["err_404page", "page-not-found", "404", "页面不存在", "Not Found"]
        # 排除正文里"404"作为标题的合法页(如完结字数 404 万字不算)
        if any(m in body[:5000] for m in markers[:2]):  # err_404page / page-not-found
            return True
        # 4 类:在 title 标签里出现"404 / 页面不存在" 即判定
        title = response.css("title::text").get() or ""
        if "404" in title or "页面不存在" in title or "Not Found" in title:
            return True
        return False
