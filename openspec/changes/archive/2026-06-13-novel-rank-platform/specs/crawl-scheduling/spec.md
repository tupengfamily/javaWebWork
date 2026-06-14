## ADDED Requirements

### Requirement: 定时调度器
Python 端 MUST 启动一个 APScheduler 实例,启动时与每 5 分钟一次从 `schedule_config` 表读取 `dailyCrawlTimes` 数组,按 `HH:mm` 注册 cron 任务。

#### Scenario: 启动加载
- **WHEN** crawler 进程启动
- **THEN** 调度器读取 `schedule_config.key='main'` 的 value 字段,解析 `dailyCrawlTimes` 数组,逐个注册 cron 任务,并写 INFO 日志

#### Scenario: 配置变更生效
- **WHEN** 调度器在 RELOAD_INTERVAL(5 分钟)tick 时发现 `dailyCrawlTimes` 与内存不一致
- **THEN** 调度器移除旧 cron 任务,按新值重新注册,变更写入 INFO 日志

#### Scenario: 配置无效
- **WHEN** 数据库中 `dailyCrawlTimes` 为空或格式错误
- **THEN** 调度器保留上一次的有效配置,写 WARN 日志,不中断运行

### Requirement: 到点写任务
调度器 MUST 在每个 cron 时间点为所有 `enabled = true` 站点生成 `crawl_task` 记录,`trigger_type = 'scheduled'`,`status = 'pending'`,ranking_type 取自配置的 `crawlAllRankingTypes`。

#### Scenario: 单次触发写入
- **WHEN** 时间到达 `08:00`
- **THEN** 系统为 N 个启用站点 × M 个榜单类型 写入 N×M 条 task 记录,均为 pending

#### Scenario: 重复触发去重
- **WHEN** 同一分钟重复触发(系统时钟回拨/手动测试)
- **THEN** 由于 (site_id, ranking_type, category, status='pending') 在应用层有去重检查,不会出现重复 pending

### Requirement: 任务分派器
Dispatcher MUST 每 5 秒轮询 `crawl_task` 表,认领 status='pending' 的任务并启动 Scrapy 子进程执行。

#### Scenario: 认领任务
- **WHEN** Dispatcher tick 时发现 pending 任务
- **THEN** 使用 `SELECT ... FOR UPDATE SKIP LOCKED` 原子认领 N 条(由 `maxConcurrentTasks` 决定),更新 status='running' 并写入 worker_id

#### Scenario: 并发上限
- **WHEN** 已有任务数达到 `maxConcurrentTasks`
- **THEN** Dispatcher 停止认领新任务,等待运行中任务结束释放槽位

#### Scenario: 启动爬虫
- **WHEN** 任务被认领
- **THEN** Dispatcher 通过 `subprocess.Popen` 启动 `scrapy crawl <site> -a task_id=... -a ranking_type=... -a category=...`,stdout/stderr 重定向到 `logs/{task_id}.log`

#### Scenario: 子进程结束
- **WHEN** Scrapy 子进程退出
- **THEN** Dispatcher 根据 exit code: 0 → status='success',非 0 → status='failed' + error_message,均写 finished_at

#### Scenario: 任务超时
- **WHEN** 任务运行时间超过 `taskTimeoutMinutes`
- **THEN** Dispatcher 强制 kill 子进程,标记 status='failed',error_message="执行超时"

### Requirement: 多站点适配器
系统 MUST 定义 `BaseSpider` 抽象类,所有具体站点 Spider 继承并实现 `start_requests` 与 `parse`。新增站点 MUST 通过继承 + 在 `SITE_TO_SPIDER` 注册完成,不动其他代码。

#### Scenario: 抽象方法未实现
- **WHEN** 子类未实现 `start_requests` 或 `parse`
- **THEN** 抽象类在 import 时立即抛 `TypeError`,系统启动失败

#### Scenario: 动态加载
- **WHEN** Dispatcher 需要启动某站点 Spider
- **THEN** 通过 `spider_class` 字符串(`module.path.ClassName`)用 `importlib` 动态导入并实例化

### Requirement: 失败重试策略(手动)
系统 MUST 不自动重试失败任务,但 MUST 在 UI 上提供"重试"按钮,由管理员决定是否重跑。

#### Scenario: 重试成功
- **WHEN** 管理员对 failed 任务点击"重试"
- **THEN** 系统复制一条新 task(原任务保留),新 task 状态为 pending,trigger_type='manual'

#### Scenario: 重试失败
- **WHEN** 同一任务的连续失败次数 ≥ 3
- **THEN** 仍可重试,但前端 MUST 显示"该任务已重试 N 次"提示
