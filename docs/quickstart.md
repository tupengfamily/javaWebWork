# Quickstart - 一键运行指南(实战版)

> 本文档是 5 分钟上手指南,**包含 Windows 实战中所有踩坑的修复**。
> 优先看 § 1 选路径,然后跳到对应章节。

## 1. 选你的路径

| 场景 | 路径 | 章节 |
|---|---|---|
| 第一次跑,想最快看效果 | **Docker 一键**(推荐) | § 2 |
| 不想装 Docker,本机直接跑 | **本地 dev 模式** | § 3 |
| 想自己控制每个进程 | **手动零脚本** | § 4 |
| 用 IDE Debug | 见 [docs/development.md](./development.md) | — |
| 部署到生产/服务器 | 见 [docs/deployment.md](./deployment.md) | — |
| 遇到问题 | 见 [docs/troubleshooting.md](./troubleshooting.md) | — |

**默认账号**:`admin` / `admin123`

---

## 2. 路径 A:Docker 一键启动(推荐)

### 2.1 前置要求

| 工具 | 最低版本 | 检查命令 |
|---|---|---|
| Docker | 20.10+ | `docker --version` |
| Docker Compose | v2 (内置) | `docker compose version` |
| Git | 任意 | `git --version` |

> ⚠️ **Windows 必看**: Docker Desktop 会自动配 WSL2,首次安装需重启。
> ⚠️ **国内用户必看**: 见 § 2.5 配镜像加速器,否则拉基础镜像可能超时。

### 2.2 首次启动

```bash
# 1. 克隆
git clone <repo-url>
cd javaWebWork

# 2. 准备 .env(首次会自动从 .env.example 复制)
cp .env.example .env              # Linux/macOS
# copy .env.example .env          # Windows cmd

# 3. 部署(构建镜像 + 启 4 容器)
./scripts/start.sh                # 等同 scripts\start.bat (Windows)
```

`start.sh` 跑完会打印:

```
==========================================
  Services started!
==========================================
  Frontend:   http://localhost
  Backend:    http://localhost:8080/api
  Swagger:    http://localhost:8080/doc.html
==========================================
```

### 2.3 访问

| 服务 | 地址 |
|---|---|
| 前端 | http://localhost |
| 后端 API | http://localhost:8080/api |
| Swagger | http://localhost:8080/doc.html |
| MySQL | `localhost:3306` (novel / 见 `.env`) |

### 2.4 常用操作

```bash
./scripts/stop.sh                  # 停止
./scripts/stop.sh --volumes        # 停止 + 删数据(危险!)

./scripts/build.sh --no-cache      # 重新构建所有镜像
./scripts/start.sh                 # 用现有镜像启动
./scripts/start.sh --build         # 构建 + 启动

# 看日志(直接用 docker compose,不再用单独脚本)
docker compose logs -f             # 所有服务实时日志
docker compose logs -f crawler     # 仅爬虫
docker compose logs -f backend     # 仅后端

# 跑测试(直接用各自测试命令,不再用单独脚本)
cd backend  && mvn test
cd crawler  && pytest
cd frontend && npm run test
```

### 2.5 ⚠️ 国内用户必看:配 Docker 镜像加速器

Docker 默认从 `auth.docker.io` 拉 token 走 https,经常超时。解决:写 daemon.json 配国内镜像。

**Windows / macOS / Linux 通杀**(用 root / 管理员):

```bash
# Linux
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<'EOF'
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.mirrors.ustc.edu.cn",
    "https://mirror.ccs.tencentyun.com",
    "https://registry.docker-cn.com"
  ]
}
EOF
sudo systemctl restart docker

# Windows (PowerShell 管理员) — 路径 C:\ProgramData\docker\config\daemon.json
```

```powershell
# 一次性写 daemon.json
New-Item -ItemType Directory -Force 'C:\ProgramData\docker\config' | Out-Null
@'
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.mirrors.ustc.edu.cn",
    "https://mirror.ccs.tencentyun.com",
    "https://registry.docker-cn.com"
  ]
}
'@ | Set-Content 'C:\ProgramData\docker\config\daemon.json' -Encoding UTF8

# 重启 Docker 服务
Restart-Service com.docker.service -Force
Restart-Service "Docker Desktop Service" -Force
Start-Sleep 5

# 验证
docker info | Select-String "Mirrors"
```

### 2.6 ⚠️ 端口冲突:本机 3306 已被占用

很多开发机装了 XAMPP / WAMP / 自带 MySQL,占着 3306 端口。`docker compose up` 会因端口冲突启动失败。

**解决**:改 `.env` 把 docker mysql 映射到别的端口(如 3307):

```ini
MYSQL_PORT=3307
```

后端和爬虫在 docker 容器内仍用容器名 `mysql:3306` 标准端口,只 host 端换 3307。

如果你**没有 Docker 模式要用本机 MySQL 80**,直接看 § 3 本地模式。

---

## 3. 路径 B:本地 dev 模式(无 Docker)

适合不想装 Docker / 想用 IDE 直接 Debug / 节省资源。

### 3.1 前置要求

| 工具 | 用途 | 检查命令 |
|---|---|---|
| **Java 17** | 后端(JDK 17 LTS) | `java --version` |
| **Maven 3.6+** | 后端构建 | `mvn -v` |
| **Python 3.10+** | 爬虫 | `python --version` |
| **Node.js 20+** | 前端(可选) | `node --version` |
| **MySQL 8.0** | 数据库 | `mysql --version` |

> ⚠️ **Java 版本要求**:**必须是 Java 17**,**不能是 Java 21+**。
> 项目用 Spring Boot 3.3.5 + MyBatis-Plus 3.5.5,需 Java 17(实测 Java 21+ 报 mybatis-spring factoryBeanObjectType 错)。
> ⚠️ **Windows 必看**:本机如有 Java 26,装 Java 17 后要在 PATH 把 Java 17 放前面(后端 + 脚本会自动找 `JAVA_HOME`)。

### 3.2 装 MySQL(三种方式任选)

#### 选项 1:Windows 安装包(最直接)
- 下载 https://dev.mysql.com/downloads/installer/ 装 MySQL Server 8.0
- 记住 root 密码(下面用)

#### 选项 2:Chocolatey(Windows)
```powershell
choco install mysql
```

#### 选项 3:用 Docker 起 MySQL(混合模式,推荐)
```bash
docker run -d --name novel-mysql -p 3307:3306 \
  -e MYSQL_ROOT_PASSWORD=root123 \
  -e MYSQL_DATABASE=novel_rank \
  -e MYSQL_USER=novel -e MYSQL_PASSWORD=novel123 \
  -v "$(pwd)/db/init.sql":/docker-entrypoint-initdb.d/01-init.sql:ro \
  mysql:8.0
```

### 3.3 初始化数据库

如果选项 3(Docker),已经自动导入 init.sql,跳过本节。

如果选项 1 或 2(本机 MySQL),手动导入:

```bash
# Linux/macOS
mysql -uroot -p < db/init.sql

# Windows
mysql -uroot -p < db\init.sql
```

或在 MySQL Workbench / Navicat 中打开 `db/init.sql` 并执行。

### 3.4 修改 `.env`

```ini
# 镜像本机 MySQL
MYSQL_HOST=localhost
MYSQL_PORT=3306                    # 如用选项 3(docker)改 3307
MYSQL_USER=novel
MYSQL_PASSWORD=novel123

# 镜像 docker mysql 容器(如选项 3)
# MYSQL_HOST=localhost
# MYSQL_PORT=3307

# ⚠️ 必须改的:
JWT_SECRET=<32字节以上随机字符串>   # 用 openssl rand -hex 32 生成
```

### 3.5 一键启动后端 + 爬虫

```bash
./scripts/dev.sh start
```

输出:

```
[DEV] Starting Spring Boot backend...
[DEV] Backend started, log: .../logs/backend.log
[DEV] Starting Python crawler...
[DEV] Crawler started, log: .../logs/crawler.log
```

### 3.6 启动前端

```bash
cd frontend
npm install        # 仅首次
npm run dev        # Vite dev server
```

前端默认 http://localhost:5173,自动代理 `/api` → `http://localhost:8080`。

### 3.7 dev 脚本速查

```bash
./scripts/dev.sh start         # 启动
./scripts/dev.sh status        # 查看状态
./scripts/dev.sh stop          # 停止
./scripts/dev.sh restart       # 重启
```

### 3.8 ⚠️ 常见报错

#### `Unrecognized VM option 'UseContainerSupport'`

**原因**:`dev.sh` 启 Java 时加了 `-XX:+UseContainerSupport`,Java 21+ 已删除此选项。
**解决**:`dev.sh` 已修(用 `-XX:MaxRAMPercentage=75.0` 即可)。如果你 fork 早于本次修复的版本,改 `scripts/dev.sh` 删 `+UseContainerSupport`。

#### `factoryBeanObjectType: java.lang.String` 错

**原因**:`mybatis-spring 3.0.3` 与 Spring Framework 6.1+ 的兼容 bug。
**解决**:`backend/pom.xml` 已显式 pin `mybatis-spring 3.0.4` + 排除 starter 传递的 3.0.3。
如果你 fork 早于本次修复的版本,见 [deployment.md § 5](./deployment.md#5-常见构建问题)。

#### Login 返回 500 + `Access denied for user 'novel'@'localhost'`

**原因**:后端连了本机 MySQL 80(占着 3306)而不是你期望的 MySQL。
**解决**:检查 `.env` 的 `MYSQL_HOST` / `MYSQL_PORT`,确认指向你跑的 MySQL。

#### Login 200 但页面跳不回首页(老 bug,已修)

**原因**:后端统一用 `Result<T>` 包装响应,前端 axios 拦截器没 unwrap 第二层,导致 `resp.token` = undefined。
**解决**:`frontend/src/utils/request.ts` 已修,刷新浏览器即可。

---

## 4. 路径 C:手动零脚本启动(完全控制)

适合调试或不想用脚本的情况。

### 4.1 启 MySQL

任选 § 3.2 的一种方式。

### 4.2 启后端

```bash
cd backend
mvn -B clean package -DskipTests
java -XX:MaxRAMPercentage=75.0 -jar target/app.jar --spring.profiles.active=dev
```

或用 IDE 直接跑 `NovelRankApplication.java`。

### 4.3 启爬虫

```bash
cd crawler
pip install -r requirements.txt
DB_HOST=localhost DB_PORT=3306 DB_USER=novel DB_PASSWORD=novel123 \
  python main.py
```

### 4.4 启前端

```bash
cd frontend
npm install
npm run dev
```

---

## 5. 验证清单

启动后挨个检查:

```bash
# 1. 前端
curl.exe -sS -o nul -w "frontend: HTTP %{http_code}\n" http://localhost:5173/
# 期望: HTTP 200

# 2. 后端
curl.exe -sS -o nul -w "backend:  HTTP %{http_code}\n" http://localhost:8080/api/sites
# 期望: HTTP 200

# 3. 登录
curl.exe -sS -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
# 期望: {"code":0,"message":"ok","data":{"token":"eyJ...","expiresIn":86400,"user":{...}}}

# 4. Swagger
curl.exe -sS -o nul -w "swagger:  HTTP %{http_code}\n" http://localhost:8080/doc.html
# 期望: HTTP 200
```

全部 HTTP 200 = 启动成功。

---

## 6. 脚本速查表(精简 4 对)

| 脚本 | 用途 | 用法 |
|---|---|---|
| `dev.sh` / `.bat` | 本地运行(无 Docker) | `./scripts/dev.sh [start\|stop\|status\|restart\|logs] [target]` |
| `build.sh` / `.bat` | 构建 Docker 镜像 | `./scripts/build.sh [service...] [--no-cache]` |
| `start.sh` / `.bat` | 部署(Docker up) | `./scripts/start.sh [--build] [service...]` |
| `stop.sh` / `.bat` | 停止 Docker 栈 | `./scripts/stop.sh [--volumes]` |

> 已删除:`setup` / `logs` / `reset-db` / `test` 4 对冗余脚本。日志用 `docker compose logs -f` / `dev.sh logs <svc>`,测试用 `mvn test` / `pytest` / `npm run test`。

---

## 7. 常见场景

### 7.1 第一次跑,想看效果
```bash
cp .env.example .env   # 1 次
./scripts/start.sh     # 3 分钟(首次构建)
# 浏览器 http://localhost
```

### 7.2 改前端代码,想立即看
`Vite HMR` 自动刷新。改完保存,浏览器 1 秒内更新。
如不更新: `Ctrl+R` 硬刷新。

### 7.3 改后端代码,想立即看
Docker 模式:
```bash
./scripts/stop.sh backend
./scripts/start.sh --build backend
```
本地模式:
```bash
./scripts/dev.sh restart
# 或在 IDE 直接 restart main()
```

### 7.4 改爬虫代码,想调试
```bash
# 跑单个 Spider 调试
cd crawler
scrapy crawl qidian -a task_id=999 -a ranking_type=daily
```

### 7.5 清理一切从头开始
Docker 模式:
```bash
./scripts/stop.sh --volumes    # 删容器 + 数据卷
rm -rf .env
cp .env.example .env
./scripts/start.sh
```
本地模式:删数据库 + 清 logs + 重启即可。

### 7.6 跑 CI
```yaml
# .github/workflows/ci.yml
- name: Build
  run: ./scripts/build.sh --no-cache
- name: Test backend
  run: cd backend && mvn test
- name: Test crawler
  run: cd crawler && pytest
- name: Test frontend
  run: cd frontend && npm run test
```

---

## 8. 环境要求汇总

| 工具 | 最低版本 | 备注 |
|---|---|---|
| Docker | 20.10+ | Docker 模式必需 |
| Docker Compose | v2 | Docker 模式必需 |
| MySQL | 8.0 | 本地模式必需 |
| **Java** | **17** | **JDK 17 LTS,不能用 21+** |
| Maven | 3.6+ | 后端构建 |
| Python | 3.10+ | 爬虫 |
| Node.js | 20+ | 前端 |
| Git | 任意 | — |

## 9. 下一步

- [architecture.md](./architecture.md) — 架构详解
- [api.md](./api.md) — 26 个 API 完整参考
- [development.md](./development.md) — 加新站点/榜单/指标
- [deployment.md](./deployment.md) — 生产部署 + HTTPS
- [troubleshooting.md](./troubleshooting.md) — 所有问题速查
- [testing.md](./testing.md) — 测试报告
