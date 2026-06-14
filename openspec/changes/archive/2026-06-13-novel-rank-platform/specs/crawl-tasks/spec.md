## ADDED Requirements

### Requirement: 任务列表
系统 MUST 提供 `GET /api/admin/tasks` 接口,分页返回 crawl_task 列表,支持按 status、site、triggerType、时间范围筛选。

#### Scenario: 默认查询
- **WHEN** 管理员不带参调用
- **THEN** 系统按 `created_at DESC` 返回第一页 20 条,响应含分页结构

#### Scenario: 多条件筛选
- **WHEN** 管理员传 `status=failed&site=qidian&startTime=2026-06-01`
- **THEN** 系统同时应用所有条件,索引命中 `(status, created_at)`

#### Scenario: 列表字段
- **WHEN** 返回任务列表
- **THEN** 每条 MUST 含 `id, siteCode, siteName, rankingType, category, triggerType, status, fetchedCount, errorMessage, createdAt, startedAt, finishedAt, durationMs`

### Requirement: 手动触发任务
系统 MUST 提供 `POST /api/admin/tasks` 接口,管理员可立即创建一条 trigger_type='manual' 的 pending 任务。

#### Scenario: 触发成功
- **WHEN** 管理员提交 `{ siteCode: "qidian", rankingType: "daily", category: null }`
- **THEN** 系统插入新 task 记录,返回 `{ taskId }`,HTTP 200

#### Scenario: 重复任务拒绝
- **WHEN** 同一 (site_id, ranking_type, category) 已存在 pending 或 running 任务
- **THEN** 系统返回 HTTP 409 错误码 `2001` 与消息"该任务已在队列中"

#### Scenario: 站点未启用
- **WHEN** 管理员对 `enabled=false` 站点提交
- **THEN** 系统返回 HTTP 400 错误码 `400` 与消息"该站点未启用"

#### Scenario: 站点不存在
- **WHEN** 管理员提交未注册的 siteCode
- **THEN** 系统返回 HTTP 404 错误码 `404` 与消息"站点不存在"

### Requirement: 取消任务
系统 MUST 提供 `POST /api/admin/tasks/{id}/cancel` 接口,仅允许取消 pending 状态的任务。

#### Scenario: 取消 pending
- **WHEN** 管理员对 status='pending' 任务调用此接口
- **THEN** 系统更新 status='cancelled',HTTP 200

#### Scenario: 取消已运行
- **WHEN** 管理员对 status='running' 任务调用此接口
- **THEN** 系统返回 HTTP 400 错误码 `400` 与消息"任务已开始,无法取消"

### Requirement: 任务重试
系统 MUST 提供 `POST /api/admin/tasks/{id}/retry` 接口,基于失败任务创建一条新任务。

#### Scenario: 重试 failed
- **WHEN** 管理员对 status='failed' 任务调用此接口
- **THEN** 系统创建新 task,trigger_type='manual',status='pending',返回新 taskId

#### Scenario: 重试非失败
- **WHEN** 管理员对非 failed 任务调用此接口
- **THEN** 系统返回 HTTP 400 错误码 `400` 与消息"仅可重试失败任务"

### Requirement: 任务详情与日志
系统 MUST 提供 `GET /api/admin/tasks/{id}/log` 接口,返回该任务的全部 crawl_log 记录(按时间正序)。

#### Scenario: 任务有日志
- **WHEN** 管理员调用此接口
- **THEN** 系统返回 `{ task, logs: [{ time, level, message }] }`

#### Scenario: 任务无日志
- **WHEN** 任务尚未产生 crawl_log
- **THEN** `logs` 为空数组,HTTP 200
