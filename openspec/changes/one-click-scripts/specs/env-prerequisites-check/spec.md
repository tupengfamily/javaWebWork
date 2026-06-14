## ADDED Requirements

### Requirement: dev.sh check 预检本机环境
`dev.sh check` MUST 检测 JDK 17+ / Python 3.11+ / Node 18+ / MySQL 可达性 / 关键端口(3306/3307/8080/5173)空闲,任一项失败 MUST 打印 "✗ <name> — 修复方法" 列表,整体退出码 = 失败项数(0 表示全通过)。

#### Scenario: 全通过
- **WHEN** JDK 17、Python 3.11、Node 18、MySQL 在 3306 都 OK
- **THEN** 打印 "✓ all checks passed" + 退出码 0

#### Scenario: JDK 缺失
- **WHEN** `java` 命令找不到
- **THEN** 打印 "✗ JDK 17+ — 安装 OpenJDK 17 (winget install Microsoft.OpenJDK.17) 或 Oracle JDK 17"

#### Scenario: Node 版本过低
- **WHEN** Node 16.20.0
- **THEN** 打印 "✗ Node 18+ required, found 16.20.0 — nvm install 18 && nvm use 18" (WARN 而非 error,允许试运行)

#### Scenario: 端口 8080 被占
- **WHEN** 8080 已被其他 java 进程占用
- **THEN** 打印 "✗ port 8080 busy (PID xxx) — 停掉该进程或改 backend 端口"

### Requirement: start.sh check 预检 Docker 环境
`start.sh check` MUST 检测 `docker` 和 `docker compose` 命令可用,Docker daemon 在跑,退出码语义同 dev.sh check。

#### Scenario: Docker 未安装
- **WHEN** `docker` 命令找不到
- **THEN** 打印 "✗ Docker not found — 安装 Docker Desktop (https://docker.com)"

#### Scenario: Docker daemon 停了
- **WHEN** `docker info` 失败
- **THEN** 打印 "✗ Docker daemon not running — 启动 Docker Desktop"

#### Scenario: 全部就绪
- **WHEN** docker / docker compose / daemon 都 OK
- **THEN** 打印 "✓ Docker ready" + 退出码 0
