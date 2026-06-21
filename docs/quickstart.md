# 项目启动运行指南

> 本文档整合 Docker 一键部署、本地开发运行、手动启动三种方式，附验证清单与常见问题速查。
> 开发指南见 [development.md](./development.md)，部署见 [deployment.md](./deployment.md)，FAQ 见 [troubleshooting.md](./troubleshooting.md)。

**默认账号**：`admin` / `admin123`

---

## 1. 选你的路径

| 场景 | 路径 | 一句话 |
|---|---|---|
| 第一次跑，想看效果 | **Docker 一键** | `.\scripts\start.bat`（3 个命令） |
| 本地开发调试 | **本地 dev 模式** | `.\scripts\dev.bat start all` |
| 手动控制每个进程 | **手动启动** | 4 个终端各跑一个进程 |
| 上线部署 | **见 [deployment.md](./deployment.md)** | Docker + HTTPS |

---

## 2. 路径 A：Docker 一键部署（推荐）

### 2.1 前置条件

```powershell
docker --version          # ≥ 20.10
docker compose version    # v2 内置
```

> 如果 Docker Desktop 卡在 "starting the Docker engine"：见 § 5.1 修复。

### 2.2 首次启动

```powershell
# 1. 准备环境变量（首次）
copy .env.example .env

# 2. 一键启动（自动构建镜像 + 启动 4 个容器）
.\scripts\start.bat
```

输出：
```
  Frontend:   http://localhost
  Backend:    http://localhost:8080/api
  Swagger:    http://localhost:8080/doc.html
```

### 2.3 常用操作

```powershell
# 停止
.\scripts\stop.bat

# 停止并删除数据（危险）
.\scripts\stop.bat --volumes

# 重新构建并启动
docker compose build
docker compose up -d

# 查看日志
docker compose logs -f              # 所有服务
docker compose logs -f backend      # 仅后端
docker compose logs -f crawler      # 仅爬虫

# 查看容器状态
docker compose ps
```

### 2.4 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端 | http://localhost | Nginx 端口 80 |
| 后端 API | http://localhost:8080/api | Spring Boot |
| Swagger 文档 | http://localhost:8080/doc.html | Knife4j |
| MySQL | localhost:3307 | 见 .env 的 MYSQL_PORT |

---

## 3. 路径 B：本地 dev 模式（无需 Docker）

### 3.1 前置条件

| 组件 | 版本 | 检查命令 |
|------|------|----------|
| JDK | 17 | `java --version` |
| MySQL | 8.0 | `mysql --version` |
| Python | 3.10+ | `python --version` |
| Node.js | 18+ | `node --version` |

> JDK 17 是硬性要求，21+ 会导致 MyBatis 兼容问题。

### 3.2 准备数据库

确保 MySQL 已运行且数据库 `novel_rank` 已创建。

```powershell
# Powershell - 首次执行初始化脚本
& "D:\MySQL\bin\mysql.exe" -unovel -pnovel123 < db\init.sql
```

或在 MySQL Workbench / Navicat 中打开 `db\init.sql` 执行。

### 3.3 一键启动

```powershell
# 启动所有服务（后端 + 爬虫 + 前端）
.\scripts\dev.bat start all

# 仅启动后端
.\scripts\dev.bat start backend

# 仅启动前端
.\scripts\dev.bat start frontend

# 仅启动爬虫
.\scripts\dev.bat start crawler
```

### 3.4 管理命令

```powershell
.\scripts\dev.bat status           # 查看运行状态
.\scripts\dev.bat stop all         # 停止所有
.\scripts\dev.bat restart backend  # 重启后端
.\scripts\dev.bat logs backend     # 查看后端日志（实时）
.\scripts\dev.bat logs crawler     # 查看爬虫日志
.\scripts\dev.bat logs frontend    # 查看前端日志
```

### 3.5 访问地址

| 服务 | 地址 |
|------|------|
| 前端 (Vite) | http://localhost:5173 |
| 后端 API | http://localhost:8080/api |
| Swagger | http://localhost:8080/doc.html |

---

## 4. 路径 C：手动启动（完全控制）

适合不用脚本、每个进程单独开终端调试的场景。

### 4.1 MySQL

确保 MySQL 8.0 运行中，`novel_rank` 库已通过 `db/init.sql` 初始化。

### 4.2 后端

```powershell
cd backend
mvn -B clean package -DskipTests                        # 构建
java -XX:MaxRAMPercentage=75.0 -jar target\app.jar --spring.profiles.active=dev
```

或用 IDE 直接 Run `NovelRankApplication.java`。

环境变量默认值（无需显式设置，MySQL 本机情况）：
```
MYSQL_HOST=localhost  MYSQL_PORT=3306  MYSQL_USER=novel  MYSQL_PASSWORD=novel123
```

### 4.3 爬虫

```powershell
cd crawler
pip install -r requirements.txt

# 设置数据库连接
set DB_HOST=localhost
set DB_PORT=3306
set DB_USER=novel
set DB_PASSWORD=novel123
set DB_NAME=novel_rank

python main.py
```

### 4.4 前端

```powershell
cd frontend
npm install                      # 仅首次
npm run dev -- --host 0.0.0.0 --port 5173
```

---

## 5. 启动后验证

```powershell
# 1. 前端页面
Invoke-WebRequest -Uri http://localhost:5173 -UseBasicParsing | Select-Object StatusCode
# 期望: 200

# 2. 后端 API
Invoke-WebRequest -Uri http://localhost:8080/api/sites -UseBasicParsing | Select-Object StatusCode
# 期望: 200

# 3. 登录测试
$body = '{"username":"admin","password":"admin123"}'
Invoke-WebRequest -Uri http://localhost:8080/api/auth/login -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
# 期望: {"code":0,"message":"ok","data":{"token":"eyJ...",...}}
```

---

## 6. 常见问题速查

| 症状 | 原因 | 修复 |
|------|------|------|
| Docker Desktop 卡在 "starting engine" | 锁文件残留 | `taskkill /F /IM "Docker Desktop.exe"` 然后重启 |
| `docker compose up` 端口 3306 冲突 | 本机 MySQL 占 3306 | `.env` 改 `MYSQL_PORT=3307` |
| 登录报"用户名或密码错误" | BCrypt 哈希不匹配 | 见 [troubleshooting.md § 4.2](./troubleshooting.md#42--q-登录-200-但-code1001-用户认证失败) |
| 后端启动报 `factoryBeanObjectType` | mybatis-spring 3.0.3 兼容 bug | `pom.xml` 已 pin 3.0.4 |
| 后端连不上数据库 | dev profile 连错端口 | 确认 `.env` 的 `MYSQL_PORT` 与 MySQL 实际端口一致 |
| `npm run dev` 启动失败 | node_modules 不全 | `cd frontend && npm install` |
| 前端代理 401 | Vite 代理未转发 | 检查 `vite.config.ts` 的 proxy 配置 |

详细 FAQ 见 [troubleshooting.md](./troubleshooting.md)。

---

## 7. 脚本速查

| 脚本 | 用途 | 示例 |
|------|------|------|
| `scripts\start.bat` | Docker 启动全栈 | `.\scripts\start.bat` |
| `scripts\stop.bat` | Docker 停止 | `.\scripts\stop.bat` |
| `scripts\dev.bat` | 本地运行（无 Docker） | `.\scripts\dev.bat start all` |
| `scripts\build.bat` | 仅构建 Docker 镜像 | `.\scripts\build.bat` |

---

## 8. 项目结构

```
├── backend/          Spring Boot 3 后端 (Java 17)
├── crawler/          Python Scrapy 爬虫
├── frontend/         Vue 3 + Vite 前端
├── db/
│   └── init.sql      数据库初始化脚本（含表结构 + 种子数据）
├── scripts/          一键启动/停止脚本
├── docs/             项目文档
├── docker-compose.yml
├── .env.example      环境变量模板
└── .env              实际环境配置（gitignore）
```
