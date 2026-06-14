# 部署指南(实战版)

> 本文档覆盖 **Docker 部署** + **生产部署** + **实战踩坑修复**。
> 5 分钟上手看 [quickstart.md](./quickstart.md),遇到问题看 [troubleshooting.md](./troubleshooting.md)。

## 1. 部署模式选择

| 模式 | 场景 | 复杂度 | 优势 | 章节 |
|---|---|---|---|---|
| **Docker 一键** | 单机 / 演示 / 测试 | ⭐ | 1 句命令 | § 3 |
| **Docker + Nginx + HTTPS** | 准生产 / 小团队 | ⭐⭐ | HTTPS + 反代 | § 4 |
| **K8s 多副本** | 大规模生产 | ⭐⭐⭐ | 弹性 | 见 [development.md § K8s](./development.md) |
| **本地 dev 模式** | 日常开发 | ⭐ | IDE Debug | [quickstart § 3](./quickstart.md#3-路径-b本地-dev-模式无-docker) |

---

## 2. 环境要求

### 2.1 硬件

| 场景 | CPU | 内存 | 磁盘 |
|---|---|---|---|
| 开发 / 测试 | 2 核 | 4 GB | 20 GB |
| 单机生产(小规模,< 10w 小说) | 4 核 | 8 GB | 50 GB |
| 单机生产(中等规模,10-100w) | 8 核 | 16 GB | 100 GB+ |
| 大规模 / 高频抓取 | 16+ 核 | 32+ GB | SSD 推荐 |

### 2.2 软件

| 工具 | 最低版本 | 检查命令 |
|---|---|---|
| Docker Engine | 20.10+ | `docker --version` |
| Docker Compose | v2 (内置) | `docker compose version` |
| (生产推荐) Nginx | 1.18+ | `nginx -v` |
| (生产推荐) 域名 + SSL 证书 | — | — |

> ⚠️ **国内用户必读**:见 § 5 配 Docker 镜像加速器,否则拉基础镜像超时。

---

## 3. Docker 一键部署(实战版)

### 3.1 准备

```bash
# 1. 克隆
git clone <repo-url>
cd javaWebWork

# 2. 准备 .env
cp .env.example .env
```

### 3.2 改 `.env`(重要!)

```ini
# === 必须改 ===
JWT_SECRET=<32字节以上随机字符串>   # openssl rand -hex 32
MYSQL_ROOT_PASSWORD=<强密码>        # 例:Root@2026_Rank!
MYSQL_PASSWORD=<强密码>              # 例:Novel@2026_Pass!

# === 可选:端口冲突时改 ===
MYSQL_PORT=3306                     # 本机 3306 已被占 → 改 3307
BACKEND_PORT=8080
FRONTEND_PORT=80

# === 可选:调度 ===
SCHEDULE_HOURS=8,14,20              # 每天 3 次抓取
SCHEDULE_MINUTES=0
```

### 3.3 启动

```bash
# 首次(自动构建 + 初始化)
docker compose up -d --build
```

跑完:

```bash
# 看 4 个容器状态
docker compose ps
# NAME              STATUS              PORTS
# novel-mysql       Up (healthy)        0.0.0.0:3306->3306/tcp
# novel-backend     Up                  0.0.0.0:8080->8080/tcp
# novel-frontend    Up                  0.0.0.0:80->80/tcp
# novel-crawler     Up

# 验证
docker compose exec mysql mysql -uroot -p"$MYSQL_ROOT_PASSWORD" \
  -e "SELECT COUNT(*) FROM novel_rank.site;"
# 期望 ≥ 3
```

### 3.4 访问

| 服务 | 地址 |
|---|---|
| 前端 | http://localhost |
| 后端 API | http://localhost:8080/api |
| Swagger | http://localhost:8080/doc.html |
| MySQL | `localhost:3306` (novel / 见 .env) |

**默认账号**:`admin` / `admin123`

### 3.5 目录与卷

```yaml
# docker-compose.yml 持久化
volumes:
  novel_db_data:        # MySQL 数据(必须备份!)
    driver: local
  novel_crawler_logs:   # 爬虫子进程日志
    driver: local
```

查看卷:

```bash
docker volume ls | grep novel
docker volume inspect novel_db_data
# 实际路径: /var/lib/docker/volumes/novel_db_data/_data
```

---

## 4. ⚠️ 实战踩坑 — 镜像加速器配置(国内必看)

### 4.1 症状

```
ERROR: failed to solve: failed to fetch oauth token:
  Post "https://auth.docker.io/token": dial tcp 199.59.148.247:443: i/o timeout
```

**原因**:`auth.docker.io` 是 Docker Hub 的认证服务,国内访问超时。

### 4.2 解决:写 daemon.json

#### Linux

```bash
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
docker info | grep "Registry Mirrors" -A 4
```

#### Windows(Docker Desktop)

```powershell
# 1. 创建 daemon.json
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

# 2. 重启 Docker Desktop 服务
Restart-Service com.docker.service -Force -ErrorAction SilentlyContinue
Restart-Service "Docker Desktop Service" -Force -ErrorAction SilentlyContinue
Start-Sleep 5

# 3. 验证(Docker Desktop 通常不显示 mirror,但会生效)
docker pull hello-world
docker pull mysql:8.0
```

#### macOS

Docker Desktop → Settings → Docker Engine → 加 `registry-mirrors` → Apply & Restart。

### 4.3 镜像源对比

| 镜像源 | 速度 | 同步延迟 | 稳定性 |
|---|---|---|---|
| docker.m.daocloud.io(道客) | ⭐⭐⭐ | 实时 | 高 |
| docker.mirrors.ustc.edu.cn(中科大) | ⭐⭐⭐ | 1-2h | 高 |
| mirror.ccs.tencentyun.com(腾讯云) | ⭐⭐ | 实时 | 中(需登录) |
| registry.docker-cn.com(老) | ⭐ | 数小时 | 中(可能失效) |

**推荐**:`docker.m.daocloud.io` + `docker.mirrors.ustc.edu.cn` 双备。

---

## 5. ⚠️ 实战踩坑 — 端口冲突

### 5.1 症状

```
Error response from daemon: Ports are not available:
  exposing port TCP 0.0.0.0:3306 -> 0.0.0.0:0: listen tcp 0.0.0.0:3306:
  bind: Only one usage of each socket address ...
```

**原因**:本机 3306 被 XAMPP / WAMP / 自带 MySQL 占用。

### 5.2 解决:改 `.env` 用别的端口

```ini
MYSQL_PORT=3307    # 改 3307
```

⚠️ 注意:容器内部仍用容器名 `mysql:3306`(标准),后端/爬虫不受影响,只 host 端换端口。

### 5.3 验证

```bash
# 看本机谁占 3306
netstat -ano | findstr 3306
# 看到 PID 1234 占着 → 关那个进程
# 或: Get-Process -Id 1234 | Stop-Process -Force

# 或直接用 3307(改 .env 后)
netstat -ano | findstr 3307
# 期望: docker-proxy 占着
```

---

## 6. ⚠️ 实战踩坑 — BuildKit 拉基础镜像失败

### 6.1 症状

`docker compose build` 时:

```
failed to solve: failed to fetch oauth token: ... timeout
```

或:

```
failed to compute cache key: failed to resolve ...: pull access denied
```

**原因**:Docker Desktop BuildKit(默认 28+)与 daemon 用不同的网络栈,daemon 配的镜像加速器不生效给 BuildKit。

### 6.2 解决 A:用 `--no-cache` + 预拉

```bash
# 1. 手动预拉所有基础镜像
docker pull eclipse-temurin:17-jdk-alpine
docker pull maven:3.9-eclipse-temurin-17
docker pull node:20-alpine
docker pull python:3.11-slim
docker pull nginx:1.25-alpine

# 2. 重新构建
docker compose build
```

### 6.3 解决 B:换 legacy builder

```bash
DOCKER_BUILDKIT=0 docker compose build
```

### 6.4 解决 C:BuildKit 配 mirror(高级)

```bash
docker buildx create --name mirror --use \
  --driver docker-container \
  --config <(echo '
[registry."docker.io"]
  mirrors = ["docker.m.daocloud.io"]
')
```

### 6.5 解决 D:不用 build,用预构建镜像(终极)

如果镜像源实在不可用,改用项目已发布到 Docker Hub 的镜像:

```bash
docker compose -f docker-compose.public.yml up -d
```

(需项目维护者发布镜像到 `yourorg/novel-{mysql,backend,frontend,crawler}`)

---

## 7. ⚠️ 实战踩坑 — mybatis-spring factoryBeanObjectType 错

### 7.1 症状

后端启动失败,日志报:

```
java.lang.IllegalArgumentException: Invalid value type for attribute
'factoryBeanObjectType': java.lang.String
at org.springframework.beans.factory.support.FactoryBeanRegistrySupport
  .getTypeForFactoryBeanFromAttributes(...)
```

### 7.2 原因

`mybatis-spring 3.0.3`(Spring Boot 3.3.5 BOM 默认)在 Spring Framework 6.1+ 下:

- `MapperFactoryBean` 字节码里 `factoryBeanObjectType` 属性是 `String` 类型
- Spring 6.1 读这个属性时**期望 `ResolvableType`**, 抛 `IllegalArgumentException`

**触发版本组合**:
- Spring Framework 6.1.14+(Spring Boot 3.3.5 / 3.4.x 自带)
- mybatis-spring 3.0.3(Spring Boot BOM 锁)
- Java 17+(用新版字节码)

**实测**:Java 17 / 21 / 26 全部触发,不是 Java 版本问题。

### 7.3 解决:pom 显式 pin mybatis-spring 3.0.4

[backend/pom.xml](../../backend/pom.xml) 已修:

```xml
<dependency>
    <groupId>com.baomidou</groupId>
    <artifactId>mybatis-plus-boot-starter</artifactId>
    <version>${mybatis-plus.version}</version>
    <exclusions>
        <exclusion>
            <groupId>org.mybatis</groupId>
            <artifactId>mybatis-spring</artifactId>
        </exclusion>
    </exclusions>
</dependency>
<!-- 修复 Spring 6.x 兼容 bug -->
<dependency>
    <groupId>org.mybatis</groupId>
    <artifactId>mybatis-spring</artifactId>
    <version>3.0.4</version>
</dependency>
```

如果你 fork 早于本次修复的版本,改 pom 后重编:

```bash
cd backend
mvn -B clean package -DskipTests
./scripts/dev.sh restart   # 或 ./scripts/start.sh --build
```

---

## 8. ⚠️ 实战踩坑 — 登录后端 500:Access denied for user

### 8.1 症状

```
GET /api/sites  =>  HTTP 500
{"code":999,"message":"系统异常: Access denied for user 'novel'@'localhost'..."}
```

### 8.2 原因

`.env` 配的 `MYSQL_PORT=3307`(避本机 3306 冲突),但后端 dev profile 没读到 `MYSQL_PORT`,连了本机 3306(占着 MySQL 80)。

### 8.3 解决:显式传环境变量启动

```bash
MYSQL_HOST=localhost MYSQL_PORT=3307 MYSQL_USER=novel MYSQL_PASSWORD=novel123 \
  ./scripts/dev.sh start
```

或写 .env 后用 docker compose(自动注入环境变量给容器)。

---

## 9. ⚠️ 实战踩坑 — admin BCrypt hash 不匹配

### 9.1 症状

Login 200 但响应 `code=1001`(用户认证失败)。

### 9.2 原因

`db/init.sql` 中 admin 用户的 `password_hash` 是用 passlib 生成的 BCrypt 格式,但**与 Spring Security `BCryptPasswordEncoder` 不完全兼容**(算法参数不同)。

### 9.3 解决:用 Python bcrypt 重置

```bash
# 1. 装 Python bcrypt
pip install bcrypt

# 2. 生成新 hash
python -c "import bcrypt; print(bcrypt.hashpw(b'admin123', bcrypt.gensalt(10)).decode())"
# 期望: $2b$10$...

# 3. 写回 DB
docker exec novel-mysql mysql -uroot -proot123 -e \
  "UPDATE novel_rank.sys_user SET password_hash='<NEW_HASH>' WHERE username='admin';"
```

或直接覆盖 init.sql 中的 password_hash 为新生成的值。

---

## 10. 单机生产部署(HTTPS)

### 10.1 架构

```
Internet
    ↓
[ Nginx :443 (SSL 终止) ]
    ↓
[ Frontend :80 ]   ← 静态资源
    ↓ /api
[ Backend :8080 ]  ← Spring Boot
    ↓
[ MySQL :3306 ]    ← docker
[ Crawler ]         ← docker
```

### 10.2 Nginx 配置

```nginx
# /etc/nginx/sites-available/novel-rank
server {
    listen 443 ssl http2;
    server_name novel.example.com;

    ssl_certificate     /etc/letsencrypt/live/novel.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/novel.example.com/privkey.pem;

    # 前端
    location / {
        proxy_pass http://127.0.0.1:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 后端 API(直接暴露 8080 也可,这里做反代更统一)
    location /api/ {
        proxy_pass http://127.0.0.1:8080/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 60s;
    }

    # Swagger
    location /doc.html {
        proxy_pass http://127.0.0.1:8080/doc.html;
    }
    location /webjars/ {
        proxy_pass http://127.0.0.1:8080/webjars/;
    }
    location /v3/api-docs/ {
        proxy_pass http://127.0.0.1:8080/v3/api-docs/;
    }
}
```

### 10.3 启用

```bash
sudo ln -s /etc/nginx/sites-available/novel-rank /etc/nginx/sites-enabled/
sudo certbot --nginx -d novel.example.com   # 自动签 Let's Encrypt
sudo nginx -t && sudo systemctl reload nginx
```

### 10.4 后端配置 CORS

生产域名下的前端调后端,不需要 CORS(同源)。但 `application.yml` 已配 `*`,足够。

---

## 11. 备份与恢复

### 11.1 备份 MySQL(每天 1 次)

```bash
# 加入 crontab: 0 2 * * * /opt/novel/backup.sh
# (此 backup.sh 需自行创建,内容如下)
#!/bin/bash
BACKUP_DIR=/opt/novel/backups
mkdir -p $BACKUP_DIR
cd $BACKUP_DIR

# 导出
docker compose exec -T mysql mysqldump \
  -uroot -p"$MYSQL_ROOT_PASSWORD" novel_rank \
  | gzip > "novel_rank_$(date +%Y%m%d_%H%M).sql.gz"

# 保留 7 天
find $BACKUP_DIR -name "novel_rank_*.sql.gz" -mtime +7 -delete
```

### 11.2 恢复

```bash
# 选最近的备份
ls -lh /opt/novel/backups/

# 恢复
gunzip < /opt/novel/backups/novel_rank_20260613_0200.sql.gz | \
  docker compose exec -T mysql mysql -uroot -p"$MYSQL_ROOT_PASSWORD" novel_rank
```

### 11.3 备份爬虫日志(可选)

```bash
tar czf /opt/novel/backups/crawler_logs_$(date +%Y%m%d).tar.gz \
  $(docker volume inspect novel_crawler_logs -f '{{ .Mountpoint }}')/_data
```

---

## 12. 监控

### 12.1 关键指标

| 指标 | 监控方式 |
|---|---|
| 容器运行状态 | `docker compose ps` + 自动告警 |
| MySQL 慢查询 | `slow_query_log` 开启 + 日志分析 |
| 后端 JVM | Spring Boot Actuator `/actuator/metrics` |
| 爬虫任务成功率 | `crawl_task` 表 `status` 统计 |
| 磁盘空间 | `df -h` + 监控 `/var/lib/docker` |

### 12.2 启用 Spring Boot Actuator(可选)

`backend/pom.xml` 加依赖:

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-actuator</artifactId>
</dependency>
```

`application-prod.yml`:

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics
  endpoint:
    health:
      show-details: when-authorized
```

访问 `http://localhost:8080/actuator/health`。

### 12.3 集中日志(可选)

`docker compose logs -f` → 转发到 Loki / ELK:

```yaml
# docker-compose.yml 加 logging driver
services:
  backend:
    logging:
      driver: loki
      options:
        loki-url: "http://loki:3100/loki/api/v1/push"
```

---

## 13. 升级

### 13.1 升级流程

```bash
# 1. 拉新代码
git pull

# 2. 看变更
cat CHANGELOG.md

# 3. 备份 DB(必做)
./scripts/backup.sh

# 4. 重新构建并滚动重启
docker compose up -d --build

# 5. 验证
docker compose ps
curl -s http://localhost/api/auth/login -X POST -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### 13.2 DB 迁移

```bash
# 跑迁移 SQL
docker compose exec -T mysql mysql -uroot -p"$MYSQL_ROOT_PASSWORD" novel_rank \
  < db/migrate/v2_add_novel_status.sql
```

### 13.3 回滚

```bash
git checkout <prev-tag>
docker compose up -d --build
# 如果有 DB 破坏,从备份恢复
```

---

## 14. 清理

### 14.1 停 + 删容器(保留数据)

```bash
docker compose down
```

### 14.2 彻底清理(删数据!)

```bash
docker compose down -v      # -v = 删卷
docker system prune -a      # 删未用镜像
```

### 14.3 重建镜像缓存

```bash
docker builder prune -a -f
```

---

## 15. 改 admin 密码

### 15.1 用 Python bcrypt 生成新 hash

```bash
python -c "import bcrypt; print(bcrypt.hashpw(b'NEW_PASS', bcrypt.gensalt(10)).decode())"
# $2b$10$...
```

### 15.2 写回 DB

```bash
docker compose exec -T mysql mysql -uroot -p"$MYSQL_ROOT_PASSWORD" novel_rank -e \
  "UPDATE sys_user SET password_hash='<NEW_HASH>' WHERE username='admin';"
```

或通过项目自带的改密 API(见 [api.md](./api.md) 后续版本)。

---

## 16. 故障恢复 Checklist

| 问题 | 第一步 | 见 |
|---|---|---|
| 前端 502 | 看 backend 容器是否健康 | [troubleshooting § 启动](./troubleshooting.md) |
| 后端 500 | 看 `docker compose logs backend` 末尾 | § 7 / § 8 |
| 登录失败 | 看 sys_user 表 + 跑 § 9 修复 | § 9 |
| 抓取任务空 | 看 crawler 日志 + 检查 init.sql | [troubleshooting § 数据类](./troubleshooting.md) |
| MySQL 拒绝连接 | 看 `docker compose ps mysql` | § 5 |

## 17. 下一步

- [architecture.md](./architecture.md) — 架构详解
- [api.md](./api.md) — 26 个 API
- [development.md](./development.md) — 加新站点/榜单
- [troubleshooting.md](./troubleshooting.md) — 所有问题速查
- [quickstart.md](./quickstart.md) — 5 分钟上手
- [testing.md](./testing.md) — 测试报告
