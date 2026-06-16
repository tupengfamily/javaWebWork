## ADDED Requirements

### Requirement: 起点 Spider 支持 6 种榜单 (含新 3 种)
QidianSpider MUST 在 `iter_all_types()` 返回 `["daily", "monthly", "total", "yuepiao", "newbook", "finish"]`;`_RANK_PATHS` MUST 包含 6 个 path 映射,缺失时降级为 WARN 日志而非崩溃。

#### Scenario: yuepiao 真实存在
- **WHEN** `https://www.qidian.com/rank/yuepiao/` 返回 200
- **THEN** spider 正常解析,与 daily 同流程

#### Scenario: yuepiao URL 404
- **WHEN** URL 返回 404
- **THEN** spider 记录 WARN "qidian[yuepiao] URL 404, skip" + dispatcher 标 success(fetchedCount=0)

#### Scenario: dispatcher 写入 yuepiao 任务
- **WHEN** `schedule_config.crawlAllRankingTypes` 含 `"yuepiao"`
- **THEN** dispatcher 写 `crawl_task(ranking_type='yuepiao')` 任务,QidianSpider 消费

### Requirement: 番茄 Spider 支持 7 种榜单
FanqieSpider MUST 支持 `daily/monthly/total/hot/newbook/good/finish`;`hot` 对应 `rank_id=3`,`newbook`=4,`good`=5,`finish`=6;若某个 rank_id 失效,spider 降级为 WARN。

#### Scenario: hot 抓取成功
- **WHEN** `https://fanqienovel.com/rank/3` 返回有效数据
- **THEN** 产出 ranking_type='hot' 记录

#### Scenario: rank_id 错位
- **WHEN** `/rank/3` 实际是另一榜单
- **THEN** spider 仍按返回内容解析,只 warn "fanqie[hot] rank_id=3 实际命中 ...榜单,继续"

### Requirement: 纵横 Spider 支持 6 种榜单
ZonghengSpider MUST 支持 `daily/monthly/total/yuepiao/subscribe/newbook`;URL 形如 `/rank/yuepiao.html`;失效 URL 降级 WARN。

#### Scenario: subscribe 抓取成功
- **WHEN** `https://www.zongheng.com/rank/subscribe.html` 返回 200 + 列表
- **THEN** 产出 ranking_type='subscribe' 记录

#### Scenario: URL 失效
- **WHEN** `/rank/subscribe.html` 404
- **THEN** WARN 日志 + 跳过

### Requirement: 新榜单的 code 不出现在 ranking_type 字典
`ranking_type` 表 MUST 保持现有 5 项(daily/monthly/category/total/all);前端 "榜单类型" 下拉 MUST 不暴露新 code;新 code 只能在 `crawlAllRankingTypes` 配置里用。

#### Scenario: 字典表内容
- **WHEN** SELECT * FROM ranking_type
- **THEN** 5 行,与改前完全一致

#### Scenario: 前端下拉值
- **WHEN** GET /api/meta/ranking-types
- **THEN** data 数组 5 项,不含 yuepiao/newbook/finish
