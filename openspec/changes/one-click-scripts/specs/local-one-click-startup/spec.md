## ADDED Requirements

### Requirement: dev.sh start 串行执行预检 → 初始化 → seed → 启动三件套
`./scripts/dev.sh start` MUST 按顺序执行 `check → init-db → seed → mvn package(按需) → 启 backend/crawler/frontend` 六个阶段;任一阶段失败 MUST 立即停止并打印修复指引。

#### Scenario: 首次启动,MySQL 空库
- **WHEN** 用户在空 MySQL 环境跑 `dev.sh start`
- **THEN** 系统先 `check` 通过 → `init-db` 用 root 密码建库建 user + 灌 init.sql → `seed` 灌 60 本测试数据 → `mvn package` → 并行启三件套 → 等待 backend 8080 health → 打印 "Frontend http://localhost:5173"

#### Scenario: 已有库,跳过 init
- **WHEN** novel_rank 已存在且 sys_user 表有数据
- **THEN** init-db 步骤直接跳过(显示 "DB ready"),不重复 CREATE

#### Scenario: --no-seed 跳过 seed
- **WHEN** 用户跑 `dev.sh start --no-seed`
- **THEN** seed 阶段被跳过,启动后列表为空(预期)

#### Scenario: --reset 先清后建
- **WHEN** 用户跑 `dev.sh start --reset`
- **THEN** init-db 之前先 `DROP DATABASE novel_rank`,然后重建

#### Scenario: 后端启动失败时不静默退出
- **WHEN** backend 30s 内未响应 /api/meta/categories
- **THEN** 打印 logs/backend.log 最后 30 行 + 退出码非 0

### Requirement: 启动后端 / 爬虫时自动注入数据库环境变量
`dev.sh start` MUST 在启动 backend / crawler 子进程前**自动注入** `MYSQL_HOST / MYSQL_PORT / MYSQL_USER / MYSQL_PASSWORD / MYSQL_DB` (crawler 对应 `DB_*`),从 `.env` 读取,无需用户手工 `export`。

#### Scenario: .env 有完整配置
- **WHEN** `.env` 包含 `MYSQL_PORT=3306` 与 `MYSQL_PASSWORD=novel123`
- **THEN** 启动后端时 `MYSQL_PORT=3306 MYSQL_PASSWORD=novel123 java -jar app.jar` 完整传递

#### Scenario: .env 缺失字段时回退到默认值
- **WHEN** `.env` 没有 `MYSQL_PORT`
- **THEN** 用默认 3306,并在日志显示 "[dev] using default MYSQL_PORT=3306"

#### Scenario: --mysql-port 命令行覆盖 .env
- **WHEN** 用户跑 `dev.sh start --mysql-port=3307`
- **THEN** 实际启动的 backend 用 3307,忽略 .env 里的 3306

### Requirement: 三件套并行启动,各自独立 PID 文件
`dev.sh start` MUST 并行拉起 backend / crawler / frontend,各自 PID 写到 `.pids/{name}.pid`,stop / status / restart 子命令读 PID 精准停止。

#### Scenario: 启动后 .pids 目录有 3 个文件
- **WHEN** `dev.sh start` 成功
- **THEN** `.pids/backend.pid` / `.pids/crawler.pid` / `.pids/frontend.pid` 各自存在,内容是进程 PID

#### Scenario: dev.sh stop backend 只停后端
- **WHEN** 用户跑 `dev.sh stop backend`
- **THEN** 用 .pids/backend.pid taskkill,不动 crawler / frontend
