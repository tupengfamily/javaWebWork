# Design — rich-crawler-data

## Context

**当前抓取数据**:
- 每个 Spider (qidian / fanqie / zongheng) 一次只抓第 1 页
- 起点 3 个榜单 (daily/monthly/total) × 20 本 = 60 本/次
- 番茄同,纵横同 → 180 本/3 站/次
- 详情页只补 `word_count` / `cover_url` / `status` / `novel_url`,**不抓 description** (DB 字段已有) 也不抓 **tags** (DB 无字段)
- 失败无重试,单次 500 即整条任务失败

**前端已暴露但数据空缺**:
- `NovelVO` 接口返回字段: `id / siteCode / siteName / title / author / category / coverUrl / novelUrl / wordCount / status / firstSeen / lastCrawlTime` — 无 `description` / `tags`
- 详情页 [NovelDetail.vue](../openspec/changes/rich-crawler-data/../../frontend/src/views/NovelDetail.vue) 没有任何简介区段
- 排行榜 [Rankings.vue](../openspec/changes/rich-crawler-data/../../frontend/src/views/Rankings.vue) 表格无封面、无站点色 tag

**约束**:
- 必须在反爬承受范围内抓更多 (3 站 × 5-6 榜单 × 60-100 本 ≈ 900-1800 本/次)
- 不引入代理池(成本高,B11 推迟)
- 后端只补字段(用户已定),不改架构
- 字段不破坏现有 API 兼容性
- `ranking_type` 字典不暴露新 code,前端 "榜单类型" 下拉保持现有 5 项(daily/monthly/category/total/all)

## Goals / Non-Goals

**Goals:**
- 单 Spider 单次抓取覆盖到 60-100 本(2-3 页)
- 单 Spider 支持 6-7 种榜单(原 3 + 新 3-4)
- novel.description 写库 + API 透出
- novel.tags 写库(逗号分隔) + API 透出
- 单次抓取失败时,scrapy 自动重试 2 次 + 指数退避
- `crawlAllRankingTypes` 默认值含新榜单,前端不改

**Non-Goals:**
- 不加新站点(刺猬猫 / SF / QQ 阅读 → 推迟到下一 change)
- 不做代理池(B11 推迟)
- 不改前端(留到 `frontend-polish` change)
- 不改 `ranking_type` 字典,新 code 不在"榜单类型"下拉里出现(只在 spider 内部白名单)
- 不重写 dispatcher,失败任务由 scrapy retry + dispatcher status=success/failed 兜底

## Decisions

### 决策 1: 分页 URL 拼接方式

**当前**: `_HTML_URLS = {"daily": "https://www.qidian.com/rank/daily/"}` 单页硬编码

**改为**: 拆为 `_RANK_BASE` (基础模板) + `_RANK_PATHS` (path 列表):

```python
# qidian.py
_RANK_BASE = "https://www.qidian.com/rank"
_RANK_PATHS = {
    "daily":   "/rank/daily/",         # ?page=2
    "monthly": "/rank/monthly/",
    "total":   "/rank/total/",
    "yuepiao": "/rank/yuepiao/",       # 新: 月票榜
    "newbook": "/rank/newbook/",       # 新: 新书榜
    "finish":  "/rank/finish/",        # 新: 完本榜
}
_PAGES = 2  # 默认翻 2 页(可被 -a pages=N 覆盖)
```

**start()**:
```python
for rt in self.iter_all_types():
    for page in range(1, self.pages + 1):
        url = self._RANK_BASE + self._RANK_PATHS[rt] + f"?page={page}"
        yield scrapy.Request(url, callback=self.parse, meta={"ranking_type": rt, "page": page})
```

**Alternatives considered**:
- ❌ 用 `&page=N` query (旧版格式):部分站点不识别
- ❌ Scrapy 增量爬取(Rule 链接提取): 复杂、容易爆抓
- ✅ **显式 N 个 Request**:简单可控,反爬参数 (delay) 一调全调

### 决策 2: 新榜单的 URL 来源

**起点** (qidian.com/rank/ 系列):
| code | 真实 URL | 来源 |
|---|---|---|
| daily | /rank/daily/ | 已知 |
| monthly | /rank/monthly/ | 已知 |
| total | /rank/total/ | 已知 |
| yuepiao | /rank/yuepiao/ | 起点公开 |
| newbook | /rank/newbook/ | 起点公开 |
| finish | /rank/finish/ | 起点公开 |

**番茄** (fanqienovel.com):
| code | 真实 URL | 来源 |
|---|---|---|
| daily | /rank/0 | 已知 (rank_id=0) |
| monthly | /rank/1 | 已知 (rank_id=1) |
| total | /rank/2 | 已知 (rank_id=2) |
| hot | /rank/3 | 推 (rank_id=3 热搜) |
| newbook | /rank/4 | 推 (rank_id=4 新书) |
| good | /rank/5 | 推 (rank_id=5 好评) |
| finish | /rank/6 | 推 (rank_id=6 完本) |

**纵横** (zongheng.com):
| code | 真实 URL | 来源 |
|---|---|---|
| daily | /rank/daily.html | 已知 |
| monthly | /rank/monthly.html | 已知 |
| total | /rank/total.html | 已知 |
| yuepiao | /rank/yuepiao.html | 推 |
| subscribe | /rank/subscribe.html | 推 |
| newbook | /rank/newbook.html | 推 |

> 新 URL 是基于公开站点结构推断,**实施时如发现 404,降级为 WARN 日志 + 跳过**(不阻断任务)。

### 决策 3: description / tags 字段设计

**`NovelData` dataclass** (crawler/items.py) 加字段:
```python
@dataclass
class NovelData:
    external_id: str
    site_code: str
    title: str
    author: str
    novel_url: str
    category: str = ""
    cover_url: str = ""
    word_count: int = 0
    status: str = "ongoing"
    description: str = ""      # 新增: 简介 (200-1000 字符)
    tags: str = ""             # 新增: 逗号分隔标签 (2-8 个)
```

**Pipeline (NovelUpsertPipeline)**:
- `description`: 截断到 1000 字符 (`.strip()[:1000]`)
- `tags`: 拆分后取前 8 个,逗号 `.join()`,去除空格 / emoji(用 regex `\W` 过滤空标签)
- UPSERT 写入新列

**`novel.tags` DB 列**:
```sql
tags VARCHAR(1024) DEFAULT NULL COMMENT '逗号分隔的标签(2-8 个)'
```

**后端 `NovelVO` 接口**:
- `description: String` 透出(原 DB 字段,直接 SELECT 即可)
- `tags: String` 透出(新 DB 字段)
- 前端按 `,` split 即得数组

### 决策 4: 失败重试 + 指数退避

**scrapy settings** (全局):
```python
RETRY_ENABLED = True
RETRY_TIMES = 3                  # 1 次主 + 2 次重试
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]
DOWNLOAD_TIMEOUT = 30
DOWNLOAD_DELAY = 2.0             # 起点原 2.0
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
RANDOMIZE_DOWNLOAD_DELAY = True
```

**Alternatives considered**:
- ❌ 在 dispatcher 层加重试逻辑:需要持久化任务状态,复杂
- ❌ 站点级 retry 中间件:每个 spider 写一遍
- ✅ **scrapy 全局 settings**:一行配置所有 spider 生效

### 决策 5: 调度器默认值扩展

`crawler/scheduler.py` 的 `_trigger_scheduled` 内部:
```python
self.current_types: list[str] = ["daily", "monthly", "total",
                                 "yuepiao", "newbook", "finish"]  # 默认扩展
```

scheduler 从 `schedule_config.main.value.crawlAllRankingTypes` 读,默认值只在第一次启动 / 配置缺失时用。`init.sql` 的 INSERT:
```sql
'crawlAllRankingTypes', JSON_ARRAY('daily','monthly','total','yuepiao','newbook','finish')
```

**降级**: 站点 spider 不支持的新榜单 code(如 fanqie 不支持 `yuepiao`)? → `iter_all_types()` 内部用 `getattr(self, "ALL_RANKING_TYPES", ["daily","monthly","total"])` 即 spider 默认值;新榜单若没在 spider 白名单,自然被跳过,无报错。

### 决策 6: description / tags 不缓存到 ranking_record

**理由**:
- 列表页一次抓 60-100 本 → 详情页 N 次请求 = 60-100 次额外 HTTP
- 每次抓都全量重抓详情太重
- 详情内容相对稳定(简介几天不变),适合放 `novel` 主表 UPSERT,不放 `ranking_record` 时序表
- 前端按 `novelId` 关联查一次即可

**Pipeline 行为**:
- `description` / `tags` 只走 `NovelUpsertPipeline`(写 novel 表)
- 不写 `RankingData`(ranking_record 不变)

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| 新榜单 URL 失效(404) | 兜底 5 次重试 + WARN 日志 + dispatcher 标 partial success |
| 分页 2 页后被站点限流 | AUTOTHROTTLE 自动降低并发 + DOWNLOAD_DELAY 2s 起步 |
| description 长度超限 | `.strip()[:1000]` 截断 |
| tags 含 emoji / 特殊字符 | 入库前 `re.sub(r'[^\w\u4e00-\u9fff,]', '', tags)` |
| 新增 `novel.tags` 列导致旧库读取失败 | migration 用 `ALTER TABLE novel ADD COLUMN tags VARCHAR(1024) DEFAULT NULL` 加列 |
| 反爬严苛导致大量 403 | 暂不引入代理(B11 推迟),改用更长的 `DOWNLOAD_DELAY` + 限速 |
| `RankingItemVO` 没 tags → 前端表格不能直接显示 | 留到 `frontend-polish` change 决定(详情页显示 tags 即可) |
| 爬虫单进程跑全部新榜单,任务时长变长(原 5min → 估 15-20min) | `taskTimeoutMinutes` 调大到 60;前端 "上次任务耗时" 列已存在 |

## Migration Plan

**纯增量**,无破坏性变更。

1. `ALTER TABLE novel ADD COLUMN tags VARCHAR(1024) DEFAULT NULL` — 加列(已有库用)
2. `db/init.sql` 同步加列(新库用)
3. 部署爬虫新版本 + 触发一次手动任务验证
4. 部署后端新版本 + curl `/api/novels/1` 验证 description / tags 透出
5. `schedule_config.main.value.crawlAllRankingTypes` 通过 SQL UPDATE 扩展(可选;scheduler 默认值已变)

**回滚**:
- `tags` 列不删,留 `NULL` 即可,无副作用
- 爬虫 settings 改 `RETRY_TIMES=0` 即退化为不重试
- 新榜单 URL 失效 → 删除 spider `_RANK_PATHS` 对应行

## Open Questions

1. **起点新榜单 `yuepiao` / `newbook` / `finish` URL 真实存在?** — 实施 task 1.x 需先 curl 验证
2. **番茄 rank_id=3/4/5/6 对应的真实榜单?** — 实施 task 1.x 需先 curl 验证(可能 1-2 个 ID 不对)
3. **分页参数(每页 30 本 vs 20 本)如何确定?** — 抓首页看页码格式
4. **description 截断到 1000 是否够?** — 多数站点简介 100-500,够;少数(如起点)到 800,截 1000 安全
5. **`schedule_config.crawlAllRankingTypes` 是否需要前端可配?** — 暂不管,scheduler 默认值够用;前端 Tasks.vue 只配时间不配榜单
