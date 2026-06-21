# Scripts 说明

> 4 对核心脚本，覆盖本地运行 / 构建 / 部署 / 停止。
> 完整文档见 [docs/quickstart.md](../docs/quickstart.md)。

## 脚本清单

| 脚本 (Windows) | 脚本 (Linux/macOS) | 用途 | 何时用 |
|---|---|---|---|
| `dev.bat` | `dev.sh` | 本地运行（无 Docker） | 日常开发、IDE Debug |
| `build.bat` | `build.sh` | 仅构建 Docker 镜像 | 改完代码要重新 build |
| `start.bat` | `start.sh` | Docker 拉起整个栈 | 演示 / 测试 / 生产部署 |
| `stop.bat` | `stop.sh` | 停止 Docker 栈 | 收工 / 重启前 |

## 用法

### 本地运行（无 Docker）

```powershell
# Windows
.\scripts\dev.bat start all          # 启动所有
.\scripts\dev.bat start backend      # 仅后端
.\scripts\dev.bat start frontend     # 仅前端
.\scripts\dev.bat start crawler      # 仅爬虫

.\scripts\dev.bat status             # 查看状态
.\scripts\dev.bat stop all           # 停止所有
.\scripts\dev.bat restart backend    # 重启后端
.\scripts\dev.bat logs backend       # 查看后端日志
.\scripts\dev.bat logs crawler       # 查看爬虫日志
```

```bash
# Linux/macOS
./scripts/dev.sh start all
./scripts/dev.sh status
./scripts/dev.sh stop all
./scripts/dev.sh logs backend
```

### Docker 部署

```powershell
# Windows - 首次启动
copy .env.example .env
.\scripts\start.bat

# 自定义构建
.\scripts\build.bat                  # 构建所有镜像
.\scripts\build.bat backend          # 仅构建后端

# 停止
.\scripts\stop.bat                   # 停止（保留数据）
.\scripts\stop.bat --volumes         # 停止 + 删除数据卷（危险）
```

```bash
# Linux/macOS
cp .env.example .env
./scripts/start.sh
./scripts/stop.sh
./scripts/stop.sh --volumes
```


### 常用开发循环

**改后端代码**：
```powershell
# 本地模式
.\scripts\dev.bat restart backend

# Docker 模式
docker compose build backend && docker compose up -d backend
```

**改前端代码**：Vite HMR 自动热更新，保存即生效。

**改爬虫代码**：
```powershell
# 本地模式
.\scripts\dev.bat restart crawler

# Docker 模式
docker compose build crawler && docker compose up -d crawler
```

## 日志位置

| 模式 | 日志路径 |
|------|----------|
| 本地 dev | `logs\backend.log` / `logs\crawler.log` / `logs\frontend.log` |
| Docker | `docker compose logs -f [service]` |

## 环境要求

`dev.bat` 会自动查找 JDK 17：
1. `C:\Program Files\Microsoft\jdk-17.0.19.10-hotspot\bin\java.exe`
2. `%JAVA_HOME%\bin\java.exe`
3. PATH 中的 `java`

`start.bat` 会自动检查 Docker 和 docker compose，缺失时给出提示。
