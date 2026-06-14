## Why

当前 `scripts/dev.sh` / `dev.bat` (本地模式) 和 `start.sh` / `start.bat` (Docker 模式) 在 README 中号称"一键启动",但实际首次跑起来需要用户手工完成 5+ 步:
1. 装 MySQL 或起 Docker MySQL
2. 找到/记住 root 密码
3. `CREATE DATABASE novel_rank` + `CREATE USER novel`
4. 改 `.env` 注入 `MYSQL_*` 环境变量
5. `mvn package`
6. 启后端 / 爬虫 / 前端 三件套
7. 单独跑 `seed_data.py` 灌测试数据

更糟的是 dev.bat 启动后端**不传 `MYSQL_*` 环境变量**,默认连 `localhost:3306` 大概率对不上用户的 MySQL 配置。`start.sh` 在 Docker 模式首跑 init.sql 但**不灌 seed**,列表空白。两条脚本都缺少环境预检,失败时报红原因不明确。

需要把"一键"做实。

## What Changes

### 本地模式 (`scripts/dev.sh` / `dev.bat`)

- **新增 `check` 子命令**: 预检 JDK 17+ / Python 3.11+ / Node 18+ / MySQL 可达性 / 端口占用,失败时给出明确修复指引
- **新增 `init-db` 子命令**: 用 `.env` 中 `MYSQL_ROOT_PASSWORD` 跑 `CREATE DATABASE / CREATE USER / GRANT / SOURCE init.sql`,支持 `--mysql-port` 显式指定端口
- **新增 `seed` 子命令**: 跑 `python seed_data.py`,默认 60 本测试数据,`--clean` 先清后灌
- **新增 `reset` 子命令**: `DROP DATABASE novel_rank` + 重建
- **增强 `start` 子命令**:
  - 默认执行顺序变为 `check → init-db → seed → mvn package → 启动三件套`
  - `--no-seed` 跳过 seed
  - `--reset` 在 init-db 前先 reset
  - `--mysql-port=3307` 显式指定端口(覆盖 .env)
  - 启动后端 / 爬虫时**自动注入** `MYSQL_*` / `DB_*` 环境变量
  - 等待 health check 通过再返回(最多 30s),失败打印最后 30 行日志

### Docker 模式 (`scripts/start.sh` / `start.bat`)

- **新增 `check` 子命令**: 预检 `docker` 和 `docker compose` 可用性
- **新增 `seed` 子命令**: 在 mysql 容器内 `SOURCE /docker-entrypoint-initdb.d/01-init.sql` 之后,跑 seed 容器/命令
- **新增 `reset` 子命令**: `docker compose down -v`(含 `db_data` 卷,清空数据)
- **增强 `up` 子命令**:
  - `--seed` 在启动后自动灌测试数据
  - `--reset` 先 down -v 再 up
  - 等 healthcheck 全部通过再返回
- **保留 `down` / `logs` / `status`**: 不破坏现有用法

### 共享基础

- **新增 `scripts/_lib.sh` / `scripts/_lib.bat`**: 共享的彩色输出、.env 加载、MySQL 探测、jar 探活函数,避免双份重复实现
- **更新 `.env.example`**: 补 `MYSQL_ROOT_PASSWORD` 字段(自动 init-db 用)
- **更新 `scripts/README.md`**: 列出全部子命令 + 用法示例
- **更新根 `README.md` 与 `docs/quickstart.md`**: "快速开始"段落改为引用 `./scripts/dev.sh start` / `./scripts/start.sh up` 而非手工命令

> 不删除 `build.sh` / `build.bat` / `stop.sh` / `stop.bat`,保持向后兼容(`stop.sh` 仍可单独使用)。

## Capabilities

### New Capabilities

- `local-one-click-startup`: 本地无 Docker 一键启动,自动预检 + 初始化 MySQL + 灌 seed + 启三件套
- `docker-one-click-deployment`: Docker 一键部署,可选 --seed 与 --reset,等 healthcheck 通过
- `mysql-bootstrap`: MySQL 数据库自动建库 + 建用户 + 灌 schema + 可选 seed
- `env-prerequisites-check`: 启动前环境预检(JDK / Python / Node / MySQL / Docker),失败给出可操作的修复指引
- `one-click-reset`: 销毁当前数据库(含 Docker 卷)/ 重建干净环境

### Modified Capabilities

无 — 这是新功能,无现有 spec 受影响。

## Impact

| 类型 | 文件 |
|---|---|
| 增强 | `scripts/dev.sh`, `scripts/dev.bat` |
| 增强 | `scripts/start.sh`, `scripts/start.bat` |
| 新增 | `scripts/_lib.sh`, `scripts/_lib.bat`(共享库) |
| 修改 | `.env.example`(补 `MYSQL_ROOT_PASSWORD`) |
| 修改 | `scripts/README.md`, `README.md`, `docs/quickstart.md` |

**兼容性**:
- 现有 `dev.sh start / stop / status / restart / logs` 行为完全保持,只是 start 内部多了 3 个步骤(均可 `--no-xxx` 关闭)
- 现有 `start.sh / stop.sh` 行为完全保持
- 不动 `docker-compose.yml` / `Dockerfile` / 后端 / 前端 / 爬虫代码

**风险**:
- `_lib.sh` / `_lib.bat` 跨 shell 兼容性:Windows 下用 `cmd` 直接调,避免依赖 bash/WSL
- MySQL root 密码缺失:首次跑会交互式询问;若用 `--non-interactive` 则打印手动修复命令后退出
- Docker 模式 `--reset` 会清掉 `db_data` 卷 — 需明显 WARN 输出
