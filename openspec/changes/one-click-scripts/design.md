# Design — one-click-scripts

## Context

`scripts/` 下现已有 4 对脚本 (`dev` / `build` / `start` / `stop` × `.sh` / `.bat`),README 把它们定位为"本地运行 / 构建 / 部署 / 停止"的 4 个动作。

**真实使用情况**(从用户在本机启动项目的实际踩坑经验):

1. **本地模式链路断**: `dev.bat` 不传 `MYSQL_*` 环境变量 → 后端用默认 `localhost:3306` 常连不上;数据库不存在时无任何提示,后端反复报 `Communications link failure`;`seed_data.py` 要单独跑。
2. **Docker 模式缺 seed**: `start.sh` 跑 init.sql 但不灌测试数据 → 列表空白。
3. **无环境预检**: JDK 缺失、端口被占、MySQL 不通,失败时只看到一段 stack trace。
4. **无 reset 入口**: 改 schema 后想从零开始,只能手动 `docker compose down -v` + `DROP DATABASE`,新人不知道。
5. **`.env.example` 缺 `MYSQL_ROOT_PASSWORD`**: 自动 init-db 需要 root 密码,目前没占位。

**约束**:
- 4 对脚本**保持独立**(`dev.sh` / `start.sh` 各管各的),不引入 Makefile 或顶层 `run.sh`
- Windows 用 `.bat` + PowerShell,Linux/macOS 用 `.sh` + bash,不依赖 WSL/Git Bash
- 不改后端 / 前端 / 爬虫代码,不引入新依赖
- 现有 dev.sh / start.sh / build.sh / stop.sh 的**对外接口不变**(老命令不破坏)

## Goals / Non-Goals

**Goals:**
- `./scripts/dev.sh start` 一次跑完预检 + 初始化 + seed + 三件套启动
- `./scripts/start.sh up --seed --build` 一次跑完构镜像 + 拉起容器 + 灌 seed
- 失败时**明确指出**缺什么、怎么修
- `.env` 集中管理所有配置(MySQL 端口、密码、seed 行为)
- 新增子命令均为**可选**,老用法 100% 兼容

**Non-Goals:**
- 不做"统一入口"(`run.sh local|docker`),保持两条独立脚本
- 不改 docker-compose.yml / Dockerfile
- 不引入 Python 子进程调用(避免在 .bat 里调 .py 启动器)
- 不做"动态端口分配",MySQL 端口冲突时让用户改 `.env` 或传 `--mysql-port`
- 不做容器内 Web 终端(没需求)

## Decisions

### 决策 1: 共享库抽到 `_lib.sh` / `_lib.bat`

**Why**: dev.sh 和 start.sh 都需要 .env 加载、彩色输出、MySQL 探测、jar 探活。复制粘贴两份会飘。

**做法**:
- `_lib.sh`: 纯 bash 函数,`source "$(dirname "$0")/_lib.sh"` 引入
- `_lib.bat`: 用 `call :func_name` 调用,不引入新依赖
- 函数清单(两个文件对应实现):
  | 函数 | 作用 |
  |---|---|
  | `log_info / log_warn / log_err` | 彩色输出,带 `[dev]` / `[start]` 前缀 |
  | `load_env` | 解析 `.env`,导出为 shell 变量;`.bat` 用 `for /f` |
  | `check_java / check_python / check_node / check_docker` | 单项预检,失败返回非 0 |
  | `wait_for_url URL TIMEOUT` | HTTP 探活,30s 默认超时 |
  | `port_listening PORT` | 端口占用检查(避免端口冲突) |

**Alternatives considered**:
- ❌ 写 Python 启动器 (`scripts/_common.py`):.bat 调 Python 又多一层,debug 麻烦
- ❌ Makefile:Windows 原生不支持,需要 mingw
- ✅ **.sh / .bat 双份实现**:每份 100-200 行,差异可控,各自依赖本机环境

### 决策 2: MySQL 端口探测优先级

**Why**: 用户机器上 MySQL 端口可能是 3306(本机服务)/ 3307(Docker 常见)/ 33060(X Protocol)。

**优先级**:
```
.env MYSQL_PORT > --mysql-port 参数 > 自动探测 (3306 → 3307 → 33060)
```

**自动探测**:
- 用 `mysqladmin ping` 或 `nc -z localhost 3306` 依次试
- 命中即停,探测结果写回 `.env` 缓存(下次不再扫)

**Non-Goals 化**: 不做端口协商,冲突时让用户改 `.env` 重跑。

### 决策 3: 自动 init-db 的 root 密码获取

**Why**: init-db 要 `CREATE DATABASE` / `CREATE USER`,需要 root 权限。

**优先级**:
```
1. .env MYSQL_ROOT_PASSWORD (有就直接用)
2. ~/.my.cnf (Linux 自动登录)
3. -pmysqladmin ping -uroot  (Windows 常见,密码为空)
4. 交互式 prompt: "请输入 MySQL root 密码: "
5. --non-interactive 模式: 提示失败,打印手动修复命令后退出(退出码 1)
```

**安全**: root 密码**不写回 .env**,只缓存到本次进程内存。.env 仍由用户自己填。

### 决策 4: seed 行为

**默认**:
- `dev.sh start` → 默认 seed(60 本小说,3 个站点)
- `start.sh up` → 默认**不** seed(生产/演示环境应给空 DB)
- `dev.sh start --no-seed` / `start.sh up --seed` 显式切换

**实现**:
- 本地: `python crawler/seed_data.py` 之前 `cd crawler/`
- Docker: `docker compose exec mysql mysql -unovel -pnovel123 novel_rank < /path/to/seed/seed.sql` — seed_data.py 改造为 SQL 输出,或新写 `crawler/seed_data_sql.py` 走 `INSERT INTO` 路径

**具体实现选择**: `seed_data.py` 已能输出 SQL(stdout 重定向),但目前是直接 INSERT 到 MySQL。
- 改造成 `--emit-sql` 选项,生成 `/tmp/seed.sql`
- init 子命令 `mysql < /tmp/seed.sql` 灌入
- 不引入新文件,扩展 seed_data.py

### 决策 5: dev.sh start 启动顺序与并发

```
check → init-db → seed → mvn package(若需要) → 并行启三件套 → wait health
```

- 前三步**串行**(有依赖)
- mvn package 可与 init-db 并行(无依赖)
- 三件套**并行启动**,节省 5-10s
- wait health **串行**(frontend 依赖 backend 起来)

**前后台模型**:
- 三件套用 `start /B` 或 `nohup` 拉后台
- PID 写到 `.pids/{backend,crawler,frontend}.pid`
- `stop` 子命令读 PID 文件,优雅停止(先 taskkill,再兜底 tasklist by window title)

### 决策 6: Docker reset 的安全提示

**Why**: `docker compose down -v` 会清掉 `db_data` 卷,数据不可恢复。

**做法**:
- `start.sh reset` 默认**必须** `--yes` 才执行
- 无 `--yes` 时:打印 WARN + 列出将被清理的卷 + 退出码 0(不报错)
- `--yes` 才真正执行 `down -v`

**Alternatives considered**:
- ❌ 直接强制执行:用户误操作丢数据
- ✅ **必须确认**:友好提示 + 强制确认两步

### 决策 7: 日志输出路径统一到 `logs/`

- `dev.sh start` 输出 → `logs/{backend,crawler,frontend}.log`
- `start.sh up` 输出 → `docker compose logs -f` 转发到 `logs/docker-{service}.log`
- `dev.sh logs backend` → `Get-Content -Tail 50 -Wait` 实时输出

**已有 `.gitignore`** 已包含 `logs/*.log` 等,无需扩展。

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| `.bat` 调 `.bat` 时的 `cd` 路径污染 | 每个子命令 `pushd %~dp0\.. & popd` 严格成对 |
| MySQL root 密码错误导致反复 retry | init-db 子命令第一次失败就退出,不重试,打印修复指引 |
| seed_data.py 改 `--emit-sql` 模式时语法 bug | 保留默认行为兼容,加新 flag;老用法 0 改动 |
| Docker reset 误删 db_data | 强制 `--yes` + WARN 输出 |
| 后端 health check 30s 内未起来 | 超时后打印 `logs/backend.log` 最后 30 行,不直接报错退出(可能慢启动) |
| Windows 上 `taskkill /F` 误杀其他 java 进程 | 用 PID 文件精准定位,只在 PID 文件存在时 taskkill,无文件回退到 window title |
| 跨平台差异:`command -v` vs `where` | `_lib.sh` 用 `command -v`,`_lib.bat` 用 `where` |
| MySQL 8.x 默认 caching_sha2_password auth | seed/init 流程用 `mysql_native_password` 兼容;若 MySQL 拒绝,在 .env 加 `MYSQL_AUTH_PLUGIN=mysql_native_password` |

## Migration Plan

本 change 是**纯增量的脚本增强**,不需要数据迁移。

**部署步骤**:
1. 修改 `scripts/_lib.sh` / `_lib.bat` / `dev.sh` / `dev.bat` / `start.sh` / `start.bat`
2. 扩展 `seed_data.py` 加 `--emit-sql` 选项
3. 更新 `.env.example` 加 `MYSQL_ROOT_PASSWORD` 注释
4. 更新 `scripts/README.md` / `README.md` / `docs/quickstart.md` 文档
5. 在干净的 Linux + Windows 各跑一次端到端验证:
   - `dev.sh start` (空 MySQL) → 30s 内起来 + 列表有数据
   - `dev.sh start --no-seed` → 30s 内起来 + 列表空白
   - `start.sh up --build --seed` → 60s 内起来 + 列表有数据
   - `start.sh reset --yes` → db_data 清理

**回滚**:
- 全部改动都在 `scripts/` + 文档,git revert 即可
- 不动 `docker-compose.yml` / `Dockerfile` / 后端 / 前端 / 爬虫

## Open Questions

1. **MySQL 8.x `caching_sha2_password` 兼容性**: 用户环境默认是哪个?若 mysql 拒绝 `mysql_native_password`,是否需要改 my.cnf? — 暂时按 .env 开关处理,真出问题再加
2. **mvn 在用户机器上是 `mvn` 还是 `./mvnw`**: 目前 dev.bat 用 `mvn`,Linux 没 mvnw,是否引入 Maven Wrapper? — 推迟到 v2,本次先用系统 mvn
3. **Node 版本**: Vite 5 要求 Node 18+,但 .env 没强制;`check` 子命令检测到 Node < 18 时给 WARN 而非 error(允许老 node 试运行)
