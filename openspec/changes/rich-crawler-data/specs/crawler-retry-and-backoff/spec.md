## ADDED Requirements

### Requirement: scrapy 全局开启重试 3 次 + 指数退避
`crawler/novel_crawler/settings.py` MUST 设置 `RETRY_TIMES=3` / `RETRY_HTTP_CODES=[500, 502, 503, 504, 408, 429]` / `DOWNLOAD_TIMEOUT=30`;`AUTOTHROTTLE_ENABLED=True`;`RANDOMIZE_DOWNLOAD_DELAY=True` 让间隔在 0.5x-1.5x 浮动。

#### Scenario: 单次 5xx 自动重试
- **WHEN** 详情页返回 503
- **THEN** scrapy 等待 backoff 后重试;若第 3 次仍 503,放弃该 URL 但其他 URL 继续

#### Scenario: 4xx 不重试
- **WHEN** 详情页返回 404
- **THEN** 不重试(404 不在 RETRY_HTTP_CODES),spider 记录 WARN "404 not retried"

#### Scenario: 反爬 429
- **WHEN** 详情页返回 429 Too Many Requests
- **THEN** 重试且 backoff 时间递增(2s → 4s → 8s),AUTOTHROTTLE 自动降低并发

### Requirement: dispatcher 任务超时放宽到 60 分钟
`schedule_config.main.value.taskTimeoutMinutes` 默认值 MUST 改 60(原 30);`taskTimeoutMinutes=60` 适配 5 站 × 7 榜单 × 3 页的更大任务量。

#### Scenario: 任务默认超时
- **WHEN** SELECT * FROM schedule_config WHERE `key`='main'
- **THEN** JSON `taskTimeoutMinutes: 60`(原 30)

#### Scenario: 用户在 Tasks.vue 改超时
- **WHEN** 用户在调度配置 "超时(分钟)" 改为 90
- **THEN** UPDATE schedule_config 写入 90,scheduler 下次 reload 生效

### Requirement: 抓取失败时 dispatcher 仍标 success
dispatcher MUST 等到 spider 子进程退出码 0 即 `status='success'`,即使部分 URL 失败(RETRY_TIMES 用尽);只在子进程崩溃 / 异常退出时标 failed。

#### Scenario: 部分 URL 失败
- **WHEN** spider 抓 50 个 URL,3 个 5xx 重试后仍失败
- **THEN** status='success',fetched_count=47(实际入库条数),crawl_log 记录 3 条 WARN

#### Scenario: 整个 spider 崩溃
- **WHEN** spider 进程退出码非 0
- **THEN** status='failed',error_message 含 stderr 末尾 30 行
