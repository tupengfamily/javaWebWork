## ADDED Requirements

### Requirement: start.sh up 一条命令拉起完整 Docker 栈
`./scripts/start.sh up` MUST 在内部依次执行 `check → docker compose up -d → 等待 healthcheck 全通过`,失败时打印 `docker compose ps` + 失败服务最近 30 行日志。

#### Scenario: 首次 up + build + seed
- **WHEN** 用户跑 `start.sh up --build --seed`
- **THEN** 系统 `check` → `docker compose build` → `docker compose up -d` → 等 mysql healthy → 等 backend healthy → `seed` 子命令灌测试数据 → 打印 "Frontend http://localhost"

#### Scenario: 已有镜像,up 快速启动
- **WHEN** 镜像已存在,用户跑 `start.sh up`
- **THEN** 跳过 build,直接 up,30s 内返回

#### Scenario: backend 健康检查超时
- **WHEN** backend 容器启动 60s 内未通过 `wget http://localhost:8080/actuator/health`
- **THEN** 打印 `docker compose ps` + `docker compose logs --tail 30 backend`,退出码 1

### Requirement: start.sh seed 在容器内灌测试数据
`start.sh seed` MUST 等 mysql 容器 healthy 后,执行 `docker compose exec mysql` 调用灌 seed 的 SQL,默认与 dev.sh seed 一致(60 本小说,3 站点)。

#### Scenario: 库为空时 seed 成功
- **WHEN** novel_rank 表无数据
- **THEN** seed 子命令执行后 `SELECT COUNT(*) FROM novel` = 60

#### Scenario: 库已有数据时 seed 提示并跳过
- **WHEN** novel_rank 已有 >= 5 本
- **THEN** 打印 "DB already seeded, skip" + 退出码 0

#### Scenario: --clean 先清后灌
- **WHEN** 用户跑 `start.sh seed --clean`
- **THEN** 先 `TRUNCATE` novel / ranking_record,再灌

### Requirement: start.sh 现有 down / logs / status 命令保持兼容
`start.sh down / logs [service] / status` MUST 与改前行为一致(只重构内部,不改对外接口)。

#### Scenario: 老的 start.sh 调用方式仍工作
- **WHEN** 用户跑 `start.sh down` (老用法)
- **THEN** 等价于 `docker compose down`,行为不变

#### Scenario: logs 子命令支持指定服务
- **WHEN** `start.sh logs backend`
- **THEN** `docker compose logs -f backend`,Ctrl+C 退出
