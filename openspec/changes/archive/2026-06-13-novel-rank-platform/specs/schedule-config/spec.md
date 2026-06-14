## ADDED Requirements

### Requirement: 获取调度配置
系统 MUST 提供 `GET /api/admin/schedule` 接口,返回 schedule_config 表中 `key='main'` 的解析后配置。

#### Scenario: 默认配置
- **WHEN** 管理员调用此接口
- **THEN** 系统返回 `{ dailyCrawlTimes: ["08:00", "14:00", "20:00"], maxConcurrentTasks: 2, taskTimeoutMinutes: 30, crawlAllRankingTypes: ["daily","monthly","category"], updatedAt }`

#### Scenario: 配置不存在
- **WHEN** schedule_config 表中无 `key='main'` 记录
- **THEN** 系统返回 HTTP 404 错误码 `404`

### Requirement: 更新调度配置
系统 MUST 提供 `PUT /api/admin/schedule` 接口,管理员可修改 `dailyCrawlTimes`、`maxConcurrentTasks`、`taskTimeoutMinutes`。

#### Scenario: 合法更新
- **WHEN** 管理员提交合法配置
- **THEN** 系统写入 schedule_config.value(JSON 序列化的整个对象),返回 HTTP 200

#### Scenario: 时间格式错误
- **WHEN** `dailyCrawlTimes` 中任一项不符合 `HH:mm`
- **THEN** 系统返回 HTTP 400 错误码 `2002` 与消息"时间格式错误"

#### Scenario: 时间点过多
- **WHEN** `dailyCrawlTimes` 数组长度 > 5
- **THEN** 系统返回 HTTP 400 错误码 `400` 与消息"最多 5 个时间点"

#### Scenario: 时间点过少
- **WHEN** `dailyCrawlTimes` 数组长度 = 0
- **THEN** 系统返回 HTTP 400 错误码 `400` 与消息"至少 1 个时间点"

#### Scenario: 时间间隔过近
- **WHEN** 任意两个时间点的差值 < 30 分钟
- **THEN** 系统返回 HTTP 400 错误码 `400` 与消息"时间间隔需 ≥ 30 分钟"

#### Scenario: 并发数非法
- **WHEN** `maxConcurrentTasks` 不在 [1, 10] 范围
- **THEN** 系统返回 HTTP 400 错误码 `400` 与消息"并发数需在 1-10 之间"

#### Scenario: 超时非法
- **WHEN** `taskTimeoutMinutes` 不在 [5, 240] 范围
- **THEN** 系统返回 HTTP 400 错误码 `400` 与消息"超时需在 5-240 分钟之间"

### Requirement: 变更即时生效
系统 MUST 保证 schedule_config 的更新在下一次 Python 调度器 RELOAD_INTERVAL(5 分钟)内被读取并应用,正在运行的任务不受影响。

#### Scenario: 下次 tick 生效
- **WHEN** 管理员保存新配置
- **THEN** 最迟 5 分钟内 Python 调度器会移除旧 cron 任务并注册新 cron 任务
