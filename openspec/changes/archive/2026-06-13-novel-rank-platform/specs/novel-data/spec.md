## ADDED Requirements

### Requirement: 小说详情
系统 MUST 提供 `GET /api/novels/{id}` 公开接口,根据 novel 主键返回完整小说信息(基础字段 + 站点名 + 首末次抓取时间)。

#### Scenario: 小说存在
- **WHEN** 客户端传入有效 novel id
- **THEN** 系统返回小说详情对象,HTTP 200

#### Scenario: 小说不存在
- **WHEN** 客户端传入不存在的 id
- **THEN** 系统返回 HTTP 404 与错误码 `404` 与消息"小说不存在"

### Requirement: 小说排行榜历史
系统 MUST 提供 `GET /api/novels/{id}/records` 公开接口,分页返回该小说在 `ranking_record` 表中的所有历史快照。

#### Scenario: 查询全部历史
- **WHEN** 客户端不传筛选条件
- **THEN** 系统按 `crawl_time DESC` 返回分页结果,每条含 `rankingType, category, rank, viewCount, recCount, crawlTime`

#### Scenario: 按榜单类型筛选
- **WHEN** 客户端传 `type=daily`
- **THEN** 系统只返回 ranking_type='daily' 的记录

#### Scenario: 按时间范围筛选
- **WHEN** 客户端传 `startTime` 与 `endTime`
- **THEN** 系统只返回 `crawl_time` 在该闭区间内的记录,时间格式 ISO-8601

### Requirement: 小说趋势数据
系统 MUST 提供 `GET /api/novels/{id}/trend` 公开接口,按时间正序返回该小说在指定榜单类型下的 `rank / viewCount / recCount` 三组序列,供 ECharts 直接消费。

#### Scenario: 默认 30 天
- **WHEN** 客户端不传 `days`
- **THEN** 系统返回近 30 天 daily 类型的数据,三组数组各点形如 `{ time: "MM-dd HH:mm", value: number }`

#### Scenario: 自定义天数
- **WHEN** 客户端传 `days=7`
- **THEN** 系统返回近 7 天数据,时间格式按数据粒度自适应(7 天内逐 snapshot,> 7 天可按日聚合)

#### Scenario: 数据缺失
- **WHEN** 该小说在所选时段内无任何 ranking_record
- **THEN** 三组数组都返回 `[]`,HTTP 200
