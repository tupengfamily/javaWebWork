# Scripts

> 4 对核心脚本,覆盖**本地运行 / 构建 / 部署 / 停止**。
> 完整文档见 [docs/quickstart.md](../docs/quickstart.md) + [docs/deployment.md](../docs/deployment.md)。

## 脚本清单

| 脚本 | 用途 | 何时用 |
|---|---|---|
| `dev.sh` / `dev.bat` | 本地运行(无 Docker) | 日常开发、IDE Debug |
| `build.sh` / `build.bat` | 仅构建 Docker 镜像(不启动) | 改完代码要重新 build 时 |
| `start.sh` / `start.bat` | 部署(Docker 拉起整个栈) | 演示 / 测试 / 生产部署 |
| `stop.sh` / `stop.bat` | 停止 Docker 栈 | 收工 / 重启前 |

> 已删除 `setup` / `logs` / `reset-db` / `test` 脚本(冗余,见下方"替代方案")。

## 用法

### 本地运行(无 Docker)

```bash
# 启后端 + 爬虫 + 前端
./scripts/dev.sh start

# 只启后端
./scripts/dev.sh start backend

# 状态
./scripts/dev.sh status

# 重启
./scripts/dev.sh restart

# 停
./scripts/dev.sh stop

# 看后端日志(实时)
./scripts/dev.sh logs backend
```

**Windows**:

```bat
scripts\dev.bat start
scripts\dev.bat status
scripts\dev.bat stop
scripts\dev.bat logs backend
```

### 构建 Docker 镜像

```bash
# 构建全部服务
./scripts/build.sh

# 构建后端 + 前端
./scripts/build.sh backend frontend

# 强制重建(代码改了)
./scripts/build.sh --no-cache
```

**Windows**: `scripts\build.bat [services...]`

### 部署(Docker up)

```bash
# 用现有镜像启动
./scripts/start.sh

# 启动前先构建
./scripts/start.sh --build

# 启动前强制重建
./scripts/start.sh --no-cache

# 只启动某个服务
./scripts/start.sh backend
```

**Windows**: `scripts\start.bat [--build]`

### 停止

```bash
./scripts/stop.sh                # 停(保留数据)
./scripts/stop.sh --volumes      # 停 + 删数据(危险)
```

**Windows**: `scripts\stop.bat [--volumes]`

## 已删脚本的替代方案

| 旧脚本 | 替代 |
|---|---|
| `setup.sh` | 首次跑: `cp .env.example .env`(首次 `start.sh` 会自动 copy)+ `mvn package`(dev.sh 自动) |
| `logs.sh` | `docker compose logs -f` 或 `./scripts/dev.sh logs backend` |
| `reset-db.sh` | `docker compose down -v && docker compose up -d`(跑 init.sql 重新导入) |
| `test.sh` | 后端:`cd backend && mvn test` / 爬虫:`cd crawler && pytest` / 前端:`cd frontend && npm run test` |
| `build.sh` | **保留**(本表) |

## 平台说明

| 平台 | 用 `.sh` | 用 `.bat` |
|---|---|---|
| Linux | ✅ 原生 | ❌ |
| macOS | ✅ 原生 | ❌ |
| Windows(Git Bash) | ✅ 推荐 | ✅ 也支持 |
| Windows(cmd) | ❌ | ✅ 推荐 |

Windows 用户推荐装 **Git for Windows**(自带 Git Bash),用 `.sh` 脚本更省事。
不想装 Git Bash 也行,用 `.bat` 即可。

## 故障排查

- 脚本失败?先看 [docs/troubleshooting.md](../docs/troubleshooting.md)
- 想看完整 8 脚本版历史?`git log -- scripts/`
