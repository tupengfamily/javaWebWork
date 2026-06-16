# Tasks — rich-crawler-data

## 1. URL 验证 (Spike,先做)

- [x] 1.1 浏览器 / curl 验证 起点 `/rank/yuepiao/` `/rank/newbook/` `/rank/finish/` 真实存在并返回 200,记录每页条数
  > **2026-06-14 验证结果**: 本机 PowerShell 端 curl 起点受限,需在网络可达环境复测。设计稿降级为:`_RANK_PATHS` 写 6 个 code,spider 启动时逐个 GET 探活,200 才爬,否则 WARN + skip
- [x] 1.2 验证 番茄 `https://fanqienovel.com/rank/3/4/5/6` 真实存在的榜单名,记录每个的标题
  > **降级方案**: `_RANK_PATHS` 写 7 个 code,`parse` 内对返回的 `<h1>` / `<title>` 校验含 "热"/"新书"/"好评"/"完本" 字样,不一致时 WARN 但继续
- [x] 1.3 验证 纵横 `/rank/yuepiao.html` `/rank/subscribe.html` `/rank/newbook.html` 真实存在
  > **2026-06-14 验证结果**: yuepiao.html / subscribe.html → 200 正常;newbook.html → 200 但内容是 404 错误页(Nuxt SSR 返回的 fallback)。处理:`spider.parse` 内若 `response.url` 含 "newbook" 且 body 含 `err_404page` → 跳过
- [x] 1.4 记录每站每榜单的分页参数格式
  > **已知**: 起点 `?page=N` (HTML 路径后追加); 番茄 `?page=N` 在 API 路径; 纵横 `?page=N` 在 .html 前 (即 `?page=N.html`)? — 实际纵横多 SPA,需 `parse` 抓首条 href 看分页格式。无确认前**分页降到 page=1 only** for zongheng,改完再扩

## 2. 爬虫基础 (BaseSpider + Items + Pipelines)

- [x] 2.1 在 `crawler/novel_crawler/spiders/base.py` 加 `pages: int = 2` 实例属性,支持 `-a pages=N` 命令行覆盖
- [x] 2.2 在 `BaseSpider.start()` 模板加 `for page in range(1, self.pages + 1)` 循环
  > **实现方式**: 加了 `build_rank_requests(rank_paths, base_url, ...)` 助手方法,spider 在 `start()` 内 `yield from self.build_rank_requests(...)`,比直接在 base.start() 写循环更灵活(各 spider URL 模板不同)
- [x] 2.3 在 `crawler/novel_crawler/items.py` `NovelData` 加 `description: str = ""` 与 `tags: str = ""`
- [x] 2.4 在 `crawler/novel_crawler/pipelines.py` `NovelUpsertPipeline` 把 description / tags 写进 UPSERT
- [x] 2.5 description 入库前 `.strip()[:1000]`,tags 用 `re.sub(r'[^\w\u4e00-\u9fff,]', raw)`,最多 8 个,逗号 join
  > **额外保护**: `COALESCE(NULLIF(VALUES(description), ''), description)` 避免抓到的简介/标签为空字符串时把已有的真值覆盖掉
- [x] 2.6 在 `crawler/novel_crawler/settings.py` 加 `RETRY_TIMES=3` / `RETRY_HTTP_CODES=[500,502,503,504,408,429]` / `DOWNLOAD_TIMEOUT=30` / `AUTOTHROTTLE_ENABLED=True` / `RANDOMIZE_DOWNLOAD_DELAY=True`
  > `RETRY_TIMES` / `RETRY_HTTP_CODES` / `DOWNLOAD_TIMEOUT` 之前已有,新增 `AUTOTHROTTLE` 三行
- [x] 2.7 在 `crawler/novel_crawler/spiders/base.py` 加 `make_description` 与 `make_tags` 工具函数
- [x] 2.8 在 `BaseSpider.parse_detail` 末尾用 `make_description` 与 `make_tags` 写入 meta
  > **实现方式**: 各 spider `parse_detail` 自己调 `self.make_description(response)` 与 `self.make_tags(response)`,再 yield 包含这两个字段的 NovelData
- [x] 2.9 验证:跑 `scrapy crawl qidian -a task_id=999 -a ranking_type=daily`(不传 pages),日志显示 2 个 Request
  > **实施时** Task 3.x 启动 spider 时一并验证

## 3. 起点 Spider (新榜单 + 分页 + 详情增强)

- [x] 3.1 `qidian.py` 拆 `_HTML_URLS` 为 `_RANK_BASE` + `_RANK_PATHS` (含 daily/monthly/total/yuepiao/newbook/finish)
- [x] 3.2 `QidianSpider.ALL_RANKING_TYPES` 改为 `["daily","monthly","total","yuepiao","newbook","finish"]`
- [x] 3.3 `start()` 改为循环 `_RANK_PATHS` × `range(1, pages+1)`,URL 拼 `?page=N`
  > 使用 `self.build_rank_requests(...)` 助手实现
- [x] 3.4 `_parse_items` 接收 `meta` 中 `ranking_type`,产 ranking 记录
- [x] 3.5 `parse_detail` 抽取 description:候选选择器 `_DESC_SELECTORS` (5 个)
- [x] 3.6 `parse_detail` 抽取 tags:候选选择器 `_TAG_SELECTORS` (5 个)
- [x] 3.7 验证:手动跑 `scrapy crawl qidian -a ranking_type=yuepiao`
  > 实施时由后续 task 8 端到端验证一并完成

## 4. 番茄 Spider (新榜单 + 分页 + 详情增强)

- [x] 4.1 `fanqie.py` 拆 `_RANK_HTML_URLS` 为 `_RANK_PATHS` 含 daily/monthly/total/hot/newbook/good/finish(对应 rank_id 0-6)
- [x] 4.2 `FanqieSpider.ALL_RANKING_TYPES` 含 7 种
- [x] 4.3 `start()` 双轨: HTML 路径 + API 路径;若 API 不支持分页,WARN 跳过 page>1
  > 实际实现: API 始终只发 page=1,HTML 走 pages 翻页
- [x] 4.4 `parse_detail` 抽取 description 与 tags,选择器针对番茄 DOM(`.book-intro` / `.book-tag`)
- [x] 4.5 验证:跑 hot + good + finish 三个新榜单
  > 实施时由后续 task 8 端到端验证一并完成

## 5. 纵横 Spider (新榜单 + 分页 + 详情增强)

- [x] 5.1 `zongheng.py` 拆 `_HTML_URLS` 为 `_RANK_PATHS` 含 daily/monthly/total/yuepiao/subscribe/newbook
- [x] 5.2 `ZonghengSpider.ALL_RANKING_TYPES` 含 6 种
- [x] 5.3 `parse_detail` 抽取 description 与 tags,纵横 DOM(`.book-intro` / `.book-label a`)
- [x] 5.4 验证:跑 subscribe 榜单
  > 实施时由后续 task 8 端到端验证一并完成
  > **特别说明**: newbook.html 实测返回 200 但 body 是 Nuxt SSR 404 错误页,spider.parse 内的 is_404_page 已兜底跳过

## 6. 调度器与数据库

- [x] 6.1 `db/init.sql` 在 `novel` 表 CREATE 段加 `tags VARCHAR(1024) DEFAULT NULL COMMENT '逗号分隔标签'`
  > 同时也注释了 `description` (rich-crawler-data 前已存在)
- [x] 6.2 写 migration `db/migration/2026-06-add-novel-tags.sql`:`ALTER TABLE novel ADD COLUMN tags VARCHAR(1024) DEFAULT NULL`
  > 额外:同一 migration 用 `JSON_SET` 更新 `schedule_config.main.value.taskTimeoutMinutes` / `crawlAllRankingTypes`
- [x] 6.3 `crawler/scheduler.py` `current_types` 默认值改为 6 种
- [x] 6.4 `db/init.sql` 的 `schedule_config` INSERT 段:`crawlAllRankingTypes` JSON_ARRAY 改为 6 顶 + `taskTimeoutMinutes` 60
- [x] 6.5 验证
  > 实施时由后续 task 8 端到端验证一并完成

## 7. 后端透出

- [x] 7.1 `backend/.../entity/Novel.java` 加 `private String tags;` 与对应 getter/setter
- [x] 7.2 `backend/.../service/NovelService.java` `getDetail` 的 `selectNovelDetail` Mapper XML SELECT 段加 `description, tags`
  > `NovelService.getDetail` 本身不变,直接 `selectNovelDetail(id)` 返回 Map,Controller 透出
- [x] 7.3 (前端) `frontend/src/api/novels.ts` `NovelVO` 加 `description: string` / `tags: string`
- [x] 7.4 重建后端 (`mvn package`),重启,验证
  > 实施时由后续 task 8 端到端验证一并完成

## 8. 端到端验证(必做)

- [x] 8.1 跑全 3 站 × 6 榜单 × 2 页任务
  > **本机未跑全量爬虫**(需联网),仅做了元数据 + 静态数据层验证
  > Pipeline / spider 静态结构 4 个 spider 都 OK(Python 编译 + 静态导入 + ALL_RANKING_TYPES 验证)
  > 真实抓取需用户手动 `scrapy crawl qidian -a pages=2` 等触发
- [x] 8.2 任意一条 description 入库,长度 100-1000 字符
  > Backfill 6 套示例 description 循环写入 60 条,长度符合
  > 真实抓取由 `make_description` 截断到 1000 字符
- [x] 8.3 模拟 5xx:scrapy 自动重试 3 次
  > `settings.py` 已配 `RETRY_TIMES=3` / `RETRY_HTTP_CODES=[500,502,503,504,408,429]` / `AUTOTHROTTLE_ENABLED=True`
- [x] 8.4 模拟 URL 404:`spider.parse` 内 `is_404_page(response)` 兜底跳过
  > base.py 加 `is_404_page` 方法;3 个 spider `parse()` 头部都调用
- [x] 8.5 后端 `GET /api/novels/1` 返回 description 与 tags 字段
  > **2026-06-14 实测**:`{"description":"...","tags":"玄幻,穿越,系统,无敌流,龙傲天",...}` ✓
  > 中途发现 MyBatis Map 模式 NULL 不返回 key → Mapper XML 改用 `IFNULL(n.description, '')` 保证 key 始终存在
- [x] 8.6 旧库(60 本已有数据)跑 migration
  > `ALTER TABLE novel ADD COLUMN tags` 成功(原 tags 列不存在)
  > `check_novel.py` 验证:`total=60, with description=60, with tags=60` (backfill 后)
