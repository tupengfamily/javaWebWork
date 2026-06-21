# 常见问题 FAQ

> 按症状分类，优先看 § 1 速查表。启动指南见 [quickstart.md](./quickstart.md)。

## 1. 速查表

| # | 症状 | 根因 | 修复 |
|---|---|---|---|
| 1 | Docker Desktop 卡在 "starting engine" | 锁文件残留 / WSL 卡死 | 杀进程 + 清锁 + 重启 |
| 2 | `docker compose up` 端口冲突 | 本机 MySQL 占 3306 | `.env` 改 `MYSQL_PORT=3307` |
| 3 | `docker compose build` 拉镜像超时 | 国内访问 Docker Hub 慢 | 配 daemon.json 镜像加速 |
| 4 | 登录 `code=1001` 认证失败 | BCrypt 哈希与 Spring Security 不兼容 | 用 Python bcrypt 重新生成 hash |
| 5 | 后端启动 `factoryBeanObjectType` | mybatis-spring 3.0.3 bug | pom pin 3.0.4 |
| 6 | `npm run dev` 起不来 | node_modules 不全 | `npm install` |
| 7 | 排行榜为空 | 没有数据 | 触发一次抓取任务 |
| 8 | 改 `.env` 不生效 | 容器环境变量启动时已固定 | `docker compose down && docker compose up -d` |

---

## 2. Docker 环境

### 2.1 Docker Desktop 卡在 "Docker Engine starting..."

**症状**：Docker Desktop 一直转圈显示 "starting the Docker engine"，`docker info` 返回 500 错误。

**原因**：Docker Desktop 锁文件残留，或 WSL 后端卡死。

**修复（Windows）**：

```powershell
# 1. 强制终止所有 Docker 进程
taskkill /F /IM "Docker Desktop.exe"
taskkill /F /IM "com.docker.backend.exe"
taskkill /F /IM "com.docker.build.exe"

# 2. 关闭 WSL
wsl --shutdown

# 3. 清除锁文件（3 个常见锁）
Remove-Item "$env:LOCALAPPDATA\Docker\backend.lock" -Force -ErrorAction SilentlyContinue
Remove-Item "$env:LOCALAPPDATA\Docker\frontend.lock" -Force -ErrorAction SilentlyContinue
Remove-Item "$env:LOCALAPPDATA\Docker\launcher.lock" -Force -ErrorAction SilentlyContinue

# 4. 重新启动 Docker Desktop
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"

# 5. 等待 30 秒后验证
docker info
```

### 2.2 docker compose 拉基础镜像超时

**症状**：
```
ERROR: failed to solve: failed to fetch oauth token:
  Post "https://auth.docker.io/token": dial tcp ...:443: i/o timeout
```

**修复**：配国内镜像加速器。

```powershell
# Windows - 管理员 PowerShell
New-Item -ItemType Directory -Force 'C:\ProgramData\docker\config' | Out-Null
@'
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.mirrors.ustc.edu.cn",
    "https://mirror.ccs.tencentyun.com"
  ]
}
'@ | Set-Content 'C:\ProgramData\docker\config\daemon.json' -Encoding UTF8

Restart-Service com.docker.service -Force
# 然后重启 Docker Desktop
```

### 2.3 docker compose up 端口冲突（3306 / 80 / 8080）

**症状**：
```
Error: Ports are not available: exposing port TCP 0.0.0.0:3306 -> ...: bind: Only one usage of each socket address
```

**修复**：改 `.env` 换端口。
```ini
MYSQL_PORT=3307    # 避开本机 MySQL 的 3306
```

### 2.4 docker compose build 失败（BuildKit 不走镜像加速）

Docker Desktop BuildKit 与 daemon 网络栈不同，镜像加速器不生效。

**修复 A** - 预拉基础镜像：
```powershell
docker pull eclipse-temurin:17-jdk-alpine
docker pull maven:3.9-eclipse-temurin-17
docker pull node:20-alpine
docker pull python:3.11-slim
docker pull nginx:1.25-alpine
docker pull mysql:8.0
docker compose build
```

**修复 B** - 换 legacy builder：
```powershell
$env:DOCKER_BUILDKIT = "0"
docker compose build
```

### 2.5 OOM：容器被 kill

```powershell
docker compose ps   # 看到 OOMKilled
```

**修复**：在 `docker-compose.yml` 中给服务加内存限制。

---

## 3. 后端

### 3.1 `factoryBeanObjectType: java.lang.String` 启动失败

**症状**：后端启动日志报 `Invalid value type for attribute 'factoryBeanObjectType'`。

**原因**：mybatis-spring 3.0.3 + Spring Framework 6.1+ 兼容 bug。`pom.xml` 已修复（pin mybatis-spring 3.0.4）。

如果仍有问题：
```powershell
cd backend
mvn -B clean package -DskipTests
```

### 3.2 `Access denied for user 'novel'@'...'`

**原因**：后端连的 MySQL 端口/用户/密码不对。

**排查**：
```powershell
# 确认 MySQL 确实在运行
mysql -unovel -pnovel123 -e "SELECT 1"

# 检查 application-dev.yml 中的连接配置
```

**修复**：确保环境变量与实际 MySQL 一致。
```
MYSQL_HOST=localhost  MYSQL_PORT=3306  MYSQL_USER=novel  MYSQL_PASSWORD=novel123
```

### 3.3 后端用错 JDK 版本

**症状**：后端日志报 `Unrecognized VM option` 或 mybatis 错误。

**原因**：系统 PATH 中 JDK 26/21 排在 JDK 17 前面。

**修复**：
```powershell
# 直接指定 JDK 17 路径启动
& "C:\Program Files\Microsoft\jdk-17.0.19.10-hotspot\bin\java.exe" -jar target\app.jar --spring.profiles.active=dev
```

`scripts\dev.bat` 已自动查找 JDK 17，无需手动处理。

---

## 4. 登录

### 4.1 `code=1001` 用户名或密码错误

**症状**：登录 API 返回 200，但 body 为 `{"code":1001,"message":"用户名或密码错误"}`。

**根因**：`db/init.sql` 中 admin 的 BCrypt 哈希与 Spring Security `BCryptPasswordEncoder` 的算法参数不兼容。

**修复（Windows）**：

```powershell
# 1. 生成新哈希
python -c "import bcrypt; print(bcrypt.hashpw(b'admin123', bcrypt.gensalt(rounds=10)).decode())"
# 输出: $2b$10$sURTJ6kv1cfHps9YTOmOMuLsk2x4wwh0GkYzfQ04HHo2gMR3V.xBW

# 2. 更新数据库
$hash = '$2b$10$sURTJ6kv1cfHps9YTOmOMuLsk2x4wwh0GkYzfQ04HHo2gMR3V.xBW'
$sql = "UPDATE sys_user SET password_hash='$hash' WHERE username='admin';"
& "D:\MySQL\bin\mysql.exe" -unovel -pnovel123 novel_rank -e $sql

# 3. 也更新 init.sql 中的哈希值（避免重新初始化后问题复现）
```

### 4.2 登录后立刻跳回登录页

**原因**：JWT_SECRET 在重启后端前后不一致，旧 token 失效。重新登录即可。

### 4.3 Token 过期

**原因**：默认 24 小时过期。改 `.env` 中 `JWT_EXPIRE_HOURS` 后重启后端。

---

## 5. 前端

### 5.1 `npm run dev` 起不来

```powershell
cd frontend
npm install       # 确保依赖完整
npm run dev
```

### 5.2 端口 5173 被占用

```powershell
# 查看是谁占了 5173
netstat -ano | findstr 5173

# 换端口启动
npm run dev -- --port 5174
```

### 5.3 前端页面空白 / 401

- 检查 Vite 代理配置（`vite.config.ts`）
- 检查后端是否在 8080 端口运行
- 硬刷新浏览器 `Ctrl+F5`

---

## 6. 数据库

### 6.1 排行榜页面是空的

没有数据。登录 admin → 任务管理 → 选站点 → 手动触发一次抓取。

### 6.2 手动触发任务一直 pending

检查爬虫是否在运行：
```powershell
# 本地 dev 模式
.\scripts\dev.bat status

# Docker 模式
docker compose ps crawler
docker compose logs crawler
```

### 6.3 任务 success 但没有数据

可能是页面选择器失效（网站改版）。检查爬虫日志中的 WARNING。

### 6.4 详情页趋势图空白

该小说数据不足（需多次抓取后再看）。

---

## 7. 爬虫

### 7.1 单独调试一个 Spider

```powershell
cd crawler
scrapy crawl qidian -a task_id=999 -a ranking_type=daily
```

### 7.2 反爬导致大量 403

调大 `crawler/novel_crawler/settings.py` 中的 `DOWNLOAD_DELAY`，减小 `CONCURRENT_REQUESTS`。

### 7.3 Python import 报错 `ModuleNotFoundError`

确认在 `crawler` 目录下运行，且 `pip install -r requirements.txt` 已执行。

---

## 8. 配置变更

### 8.1 改 .env 不生效

```powershell
# Docker 模式需重建容器
docker compose down
docker compose up -d

# 本地模式重启进程即可
.\scripts\dev.bat restart all
```

### 8.2 生成随机 JWT_SECRET

```powershell
# PowerShell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % { [char]$_ })
```

### 8.3 怎么改 admin 密码

```powershell
# 生成新哈希
python -c "import bcrypt; print(bcrypt.hashpw(b'新密码', bcrypt.gensalt(rounds=10)).decode())"

# 更新数据库
& "D:\MySQL\bin\mysql.exe" -unovel -pnovel123 novel_rank -e "UPDATE sys_user SET password_hash='<新哈希>' WHERE username='admin';"
```
