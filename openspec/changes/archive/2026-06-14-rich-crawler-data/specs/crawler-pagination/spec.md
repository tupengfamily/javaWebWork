## ADDED Requirements

### Requirement: 每个榜单自动翻 N 页,N 默认 2 可由参数覆盖
BaseSpider MUST 在 `start()` 内对每个 ranking_type 发起 N 个 Request(默认 N=2),N 由 Spider 实例属性 `pages` 或命令行 `-a pages=N` 控制。N=1 时退化为"只抓第 1 页"(向后兼容)。

#### Scenario: 默认 2 页
- **WHEN** 启动 spider 不带 `-a pages=`
- **THEN** 每个 ranking_type 发出 2 个 Request(?page=1 与 ?page=2),dedup Pipeline 跨 (ranking_type, novel_external_id) 去重

#### Scenario: 显式 1 页
- **WHEN** `-a pages=1`
- **THEN** 每个 ranking_type 只发 1 个 Request,行为与改前完全一致

#### Scenario: 显式 5 页
- **WHEN** `-a pages=5`
- **THEN** 发 5 个 Request,理论上可获 100 本;若某页失败,scrapy retry 兜底

#### Scenario: 第 2 页返回空列表
- **WHEN** 站点只有 1 页数据(?page=2 返回 0 项)
- **THEN** spider 解析为空,WARN 日志 "no items on page 2",不阻断整条任务

### Requirement: 分页 URL 模板与 API 路径分离
Spider MUST 拆分为 `_RANK_BASE` (域名) + `_RANK_PATHS` (path 列表) 二元组,以便 `?page=N` 拼接;同时保留现有 `_HTML_URLS` / `_API_MAPS` 字段名以最小化 diff。

#### Scenario: HTML 路径拼分页
- **WHEN** qidian daily `?page=2`
- **THEN** URL = `https://www.qidian.com/rank/daily/?page=2`

#### Scenario: 番茄 API 分页 (若支持)
- **WHEN** fanqie 榜单 `?page=2`
- **THEN** URL = `https://fanqienovel.com/api/author/rank/0?page=2`;若 API 不支持,降级为"WARN: API 不支持分页,跳过 page>1"
