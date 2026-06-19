## Why

当前爬虫每个榜单只抓**第 1 页的 20 本**小说,数据深度严重不足:
- 起点/番茄/纵横 每个站点只覆盖 `daily/monthly/total` 3 个榜单,缺月票榜/新书榜/完本榜等高价值榜单
- 详情页只补全 `word_count` / `cover_url`,`description` 字段(`novel.description TEXT`)在建表时就预留但爬虫从未写入,前端也读不到
- `tags` 字段(作品标签)完全没有
- 单次抓取失败后没有重试,凌晨高峰偶发 500 整条任务就废

需要扩充数据广度(更多榜单)、深度(分页 + 简介/标签)、健壮性(重试),为后续前端展示(详情页 description、tags chips)提供数据基础。

## What Changes

### 爬虫 (Python — `crawler/novel_crawler/spiders/`)

- **新增分页抓取**: 每个榜单翻 2-3 页,从 20 本 → 60-100 本/次;`_HTML_URLS` / `_API_MAPS` 改为 `_RANK_URLS[type]` 支持 `?page=N` 拼接
- **新增榜单类型**:
  - 起点: 月票榜 `yuepiao`、新书榜 `newbook`、完本榜 `finish`
  - 番茄: 热搜榜 `hot`、新书榜 `newbook`、好评榜 `good`、完本榜 `finish`
  - 纵横: 月票榜 `yuepiao`、订阅榜 `subscribe`、新书榜 `newbook`
- **详情页抽取 `description`**: 从详情页的 `<meta name="description">` / `.book-intro` / `.intro` 等节点抓 200-500 字简介
- **详情页抽取 `tags`**: 从详情页的标签区 `.tag a` / `.book-tag span` 抓逗号分隔的标签列表(2-8 个)
- **失败任务自动重试 2 次**: scrapy `RETRY_TIMES=3` + `RETRY_HTTP_CODES=[500, 502, 503, 504, 408]`;指数退避 `DOWNLOAD_DELAY *= 2`

### 后端字段透出 (Java — `backend/src/main/java/.../entity/Novel.java` + `NovelService.java` + `NovelController.java`)

- **`novel` 表加 `tags` 列**: `VARCHAR(1024)` 存逗号分隔标签(预留 `description` 已有,无需新增)
- **`NovelVO` 接口返回新增 `description` / `tags`**: `getNovel(id)` 和 `getRecords` 返回的扁平 map 都加这两个字段
- **`RankingItemVO` 不变**: 不缓存简介/标签在 ranking_record(节省存储)
- **初始化脚本**: `db/init.sql` 的 `novel` 表 CREATE 段补 `tags VARCHAR(1024) DEFAULT NULL COMMENT '逗号分隔标签'`

### 调度配置 (Python — `crawler/scheduler.py`)

- `crawlAllRankingTypes` 数组扩展为默认包含新榜单:
  ```json
  ["daily", "monthly", "total", "yuepiao", "newbook", "finish"]
  ```
- 站点配置(SQL `site.spider_class`)不动,各 spider 内部已 `iter_all_types()` 自管理

### 不动

- `docker-compose.yml` / `Dockerfile`
- 前端 (留到 `frontend-polish` change 一起做)
- 现有 dev/start/stop 脚本(独立 change 已铺)
- 现有 `ranking_type` 字典(daily/monthly/category/total/all 不变,新榜单名进 spider 内部白名单不暴露到字典)

## Capabilities

### New Capabilities

- `crawler-pagination`: 列表页支持分页参数,每榜单默认翻 2 页,可配置
- `new-ranking-types`: spider 支持 7+ 种新榜单(yuepiao/newbook/finish/hot/good/subscribe),通过内部白名单
- `novel-detail-enrichment`: 详情页抽取 description(简介)和 tags(标签),写入 novel 表
- `crawler-retry-and-backoff`: HTTP 5xx/408 自动重试 2 次 + 指数退避,失败任务由 dispatcher 记录

### Modified Capabilities

无(纯增量)。

## Impact

| 类型 | 文件 |
|---|---|
| 增强 | `crawler/novel_crawler/spiders/qidian.py` (URL/分页/详情选择器) |
| 增强 | `crawler/novel_crawler/spiders/fanqie.py` (同上) |
| 增强 | `crawler/novel_crawler/spiders/zongheng.py` (同上) |
| 增强 | `crawler/novel_crawler/spiders/base.py` (description / tags 字段) |
| 增强 | `crawler/novel_crawler/items.py` (NovelData 加 description / tags) |
| 增强 | `crawler/novel_crawler/pipelines.py` (NovelUpsertPipeline 写新字段) |
| 增强 | `crawler/novel_crawler/settings.py` (RETRY_TIMES / RETRY_HTTP_CODES / DOWNLOAD_DELAY 退避) |
| 增强 | `crawler/scheduler.py` (crawlAllRankingTypes 默认值) |
| 修改 | `db/init.sql` (novel 表加 tags 列) |
| 修改 | `backend/.../entity/Novel.java` (加 tags 字段映射) |
| 修改 | `backend/.../service/NovelService.java` (getDetail 透出 description / tags) |
| 修改 | `backend/.../controller/NovelController.java` (返回字段透出) |
| 修改 | `backend/.../dto/RankingItemVO` (无需) |
| 文档 | `db/init.sql` 字段注释 / `docs/crawler.md` (新增榜单 URL 来源说明) |

**兼容性**:
- 数据库 migration:`novel.tags` 是新增列(可空),旧库 ALTER TABLE 加列零风险
- API 向后兼容:`description` / `tags` 是新增字段,旧客户端不读无影响
- 调度 `crawlAllRankingTypes` 默认值变了,但 `schedule_config.main.value` 是 JSON,前端 Tasks.vue 没限制枚举,改完自动重新拉

**风险**:
- 反爬:分页到 2-3 页后请求频率 ×2,可能触发反爬 → 通过 B10 退避缓解
- 新榜单 URL 失效:各站结构 1-2 年内可能改版 → 兜底 API + 多选择器容错(现有模式)
- 详情页 description 长度可能 > 500 字 → 截断到 1000 字符防止 TEXT 过载
- tags 中可能有 emoji / 特殊字符 → 入库前 `.strip()` + 限制 8 个
