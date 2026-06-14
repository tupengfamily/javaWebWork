## ADDED Requirements

### Requirement: 最新榜单查询
系统 MUST 提供 `GET /api/rankings` 公开接口,返回某站点某榜单类型在**最新一次爬取**中的所有条目。

#### Scenario: 必填参数
- **WHEN** 客户端调用接口
- **THEN** `site` 与 `type` 为必填,缺失时返回 HTTP 400 错误码 `400`

#### Scenario: 排序与分页
- **WHEN** 客户端传 `pageNum=1, pageSize=20`
- **THEN** 系统按 `rank ASC` 返回前 20 条,响应含 `total, pageNum, pageSize, pages` 字段

#### Scenario: 关键字搜索
- **WHEN** 客户端传 `keyword=完美`
- **THEN** 系统在书名与作者上做模糊匹配(LIKE),结果仍按 rank 排序

#### Scenario: 分类榜 + 分类筛选
- **WHEN** `type=category` 时客户端传 `category=玄幻`
- **THEN** 系统只返回该分类下的条目;`category` 缺失时返回 HTTP 400 错误码 `400`

### Requirement: 趋势对比
系统 MUST 提供 `GET /api/trends/compare` 公开接口,接收 1-5 个 novelId,返回这些小说在某 metric 上的时间序列对比数据。

#### Scenario: 合法请求
- **WHEN** 客户端传 `novelIds=1,2,3, metric=viewCount, days=7`
- **THEN** 系统返回 `series: [{ novelId, title, siteCode, color, points: [{time, value}] }]`,每条 series 按 novel 顺序对应

#### Scenario: 超过 5 个
- **WHEN** `novelIds` 数量超过 5
- **THEN** 系统返回 HTTP 400 错误码 `400` 与消息"最多 5 个小说"

#### Scenario: 空 novelIds
- **WHEN** `novelIds` 为空或缺失
- **THEN** 系统返回 HTTP 400 错误码 `400` 与消息"请提供小说 id"

### Requirement: 跨站 TOP
系统 MUST 提供 `GET /api/trends/top` 公开接口,跨站点返回按某 metric 排序的 TOP N 列表。

#### Scenario: 默认参数
- **WHEN** 客户端不传参
- **THEN** 系统按 `viewCount DESC` 返回前 10 条,每条含 `rank, novelId, title, siteCode, siteName, color, viewCount`

#### Scenario: 按分类筛选
- **WHEN** 客户端传 `category=玄幻`
- **THEN** 系统只在该分类下排名,基于该分类最近一次抓取快照

### Requirement: 趋势数据 ECharts 格式兼容
系统 MUST 保证所有趋势接口的返回数据可直接喂给 ECharts `line`/`bar` 组件,无需前端二次转换。

#### Scenario: 时间序列点格式
- **WHEN** 任一趋势接口返回点数据
- **THEN** 数组元素形如 `{ time: string, value: number }`,time 按数据粒度选择 `MM-dd HH:mm` / `MM-dd` / `yyyy-MM-dd`
