## ADDED Requirements

### Requirement: 实时日志流
系统 MUST 提供 `GET /api/admin/dashboard/logs` 接口,返回 crawl_log 表中最近的日志记录,前端用 5 秒轮询实现"实时"展示。

#### Scenario: 默认查询
- **WHEN** 管理员调用此接口
- **THEN** 系统返回最近 100 条日志,按 `log_time DESC`,响应含 `records` 与 `nextBefore` 游标

#### Scenario: 按级别筛选
- **WHEN** 管理员传 `level=ERROR`
- **THEN** 系统只返回 level='ERROR' 的记录,命中索引 `(site_id, level, log_time DESC)`

#### Scenario: 按站点筛选
- **WHEN** 管理员传 `site=qidian`
- **THEN** 系统只返回该站点的日志

#### Scenario: 游标分页
- **WHEN** 客户端传 `before=2026-06-13T20:00:00`
- **THEN** 系统只返回 log_time 早于该值的记录,用于翻页

### Requirement: 日志写入
Python 爬虫层 MUST 在以下关键事件写 crawl_log 记录:调度器到点、Dispatcher 认领任务、Scrapy 启动、Scrapy 完成、Scrapy 失败、超时 kill。

#### Scenario: Scrapy 完成
- **WHEN** Scrapy 子进程退出码 0
- **THEN** 写一条 INFO 日志,`message = "{site}爬虫完成,共抓取 N 条"`,`crawl_task_id` 关联

#### Scenario: Scrapy 失败
- **WHEN** Scrapy 子进程退出码非 0
- **THEN** 写一条 ERROR 日志,`message = "{site}爬虫失败,退出码 N,错误: ..."`

#### Scenario: 系统级日志
- **WHEN** 调度器到点、Dispatcher 启动/结束等系统级事件
- **THEN** 写一条 crawl_log,`crawl_task_id = NULL`,`site_id = NULL`,用于系统全局日志展示

### Requirement: 站点状态概览
系统 MUST 提供 `GET /api/admin/dashboard/sites` 接口,聚合每个站点的最近一次任务状态与近 7 天失败次数。

#### Scenario: 返回字段
- **WHEN** 管理员调用此接口
- **THEN** 系统返回站点数组,每项含 `siteId, siteCode, siteName, color, enabled, lastTask{id,status,finishedAt,fetchedCount}, novelCount, recentFailureCount`
