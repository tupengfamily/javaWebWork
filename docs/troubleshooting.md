# 常见问题 FAQ(实战版)

> 本文档按问题**症状 + 根因 + 修复**组织,优先看 § 1 速查表。
> 5 分钟上手见 [quickstart.md](./quickstart.md),部署见 [deployment.md](./deployment.md)。

## 1. 速查表(实战 6 大坑,本次都踩到过)

| # | 症状 | 根因 | 修复 | 见 |
|---|---|---|---|---|
| 1 | `auth.docker.io:443 timeout` 拉基础镜像失败 | 国内访问 Docker Hub 慢 | 配 `daemon.json` + 国内 mirror | § 2.1 |
| 2 | `Ports are not available: 3306` 端口冲突 | 本机 MySQL 80 占着 3306 | 改 `.env` 用 3307 | § 2.2 |
| 3 | 后端启动 `Invalid value type for attribute 'factoryBeanObjectType'` | mybatis-spring 3.0.3 + Spring 6.1 兼容 bug | 显式 pin mybatis-spring 3.0.4 | § 3.1 |
| 4 | `Unrecognized VM option 'UseContainerSupport'` | Java 21+ 删了该 JVM 参数 | 改 `dev.sh` 删参数 | § 3.2 |
| 5 | Login 200 但页面跳不回首页 | axios 拦截器没 unwrap 后端 `Result<T>` 包装 | 改 `request.ts` 多 unwrap 一层 | § 4.1 |
| 6 | Login 1001 用户认证失败 | init.sql 中 admin hash 与 Spring Security BCrypt 不兼容 | 用 Python bcrypt 重置 | § 4.2 |

---

## 2. Docker 类

### 2.1 ⚠️ Q: 拉基础镜像超时

**症状**:
```
ERROR: failed to solve: failed to fetch oauth token:
  Post "https://auth.docker.io/token": dial tcp 199.59.148.247:443: i/o timeout
```

**原因**:`auth.docker.io` 国内访问慢 / 超时。

**修复**:写 daemon.json 配国内镜像。

```bash
# Linux
sudo tee /etc/docker/daemon.json <<'EOF'
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.mirrors.ustc.edu.cn",
    "https://mirror.ccs.tencentyun.com"
  ]
}
EOF
sudo systemctl restart docker
```

```powershell
# Windows (PowerShell 管理员)
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
Restart-Service "Docker Desktop Service" -Force
```

详细步骤见 [deployment.md § 4](./deployment.md#4-实战踩坑--镜像加速器配置国内必看)。

### 2.2 ⚠️ Q: 端口冲突 3306

**症状**:
```
Error response from daemon: Ports are not available:
  exposing port TCP 0.0.0.0:3306 -> ...: bind: Only one usage of each socket
```

**原因**:本机已装 MySQL 80 / XAMPP / WAMP 占着 3306。

**修复**:改 `.env`:

```ini
MYSQL_PORT=3307    # 改 3307
```

容器内仍用 `mysql:3306`(标准),只 host 端换端口。

### 2.3 ⚠️ Q: docker compose build 慢 / 失败

**症状**:
```
failed to compute cache key: failed to resolve ...: pull access denied
```

**原因**:Docker Desktop BuildKit(默认 28+)与 daemon 用不同网络栈,镜像加速器对 BuildKit 不生效。

**修复**(任选一):

```bash
# A. 预拉基础镜像
docker pull eclipse-temurin:17-jdk-alpine
docker pull maven:3.9-eclipse-temurin-17
docker pull node:20-alpine
docker pull python:3.11-slim
docker pull nginx:1.25-alpine
docker compose build

# B. 换 legacy builder
DOCKER_BUILDKIT=0 docker compose build

# C. BuildKit 配 mirror
docker buildx create --name mirror --use --driver docker-container \
  --config <(echo '[registry."docker.io"]\n  mirrors = ["docker.m.daocloud.io"]')
```

详细见 [deployment.md § 6](./deployment.md#6-实战踩坑--buildkit-拉基础镜像失败)。

### 2.4 Q: `docker compose up` 后 frontend 起不来

**症状**:frontend 日志报 `ECONNREFUSED 8080`。

**原因**:depends_on 保证启动顺序但不保证 healthcheck。

**修复**:
```bash
docker compose restart frontend
```

或等 30s + 看 `docker compose logs -f frontend`。

### 2.5 Q: 数据卷被清空了

**原因**:跑了 `docker compose down -v` 或 `docker volume rm`。

**预防**:定期 `mysqldump` 备份(见 [deployment.md § 11](./deployment.md#11-备份与恢复))。

**恢复**:从 SQL 备份恢复:
```bash
gunzip < backup/novel_rank_20260613.sql.gz | \
  docker compose exec -T mysql mysql -uroot -p"$MYSQL_ROOT_PASSWORD" novel_rank
```

### 2.6 Q: 容器 OOM killed

**排查**:
```bash
docker compose ps
# 看到 OOMKilled
dmesg | grep -i oom
```

**修复**:
- 加内存限制(需 deploy.resources)
- 减小 `MaxRAMPercentage` 到 60
- 减小 MySQL `innodb_buffer_pool_size`

---

## 3. 后端 Java / Spring Boot 类

### 3.1 ⚠️ Q: `Invalid value type for attribute 'factoryBeanObjectType': java.lang.String`

**症状**:后端启动失败,日志:
```
java.lang.IllegalArgumentException: Invalid value type for attribute
  'factoryBeanObjectType': java.lang.String
at FactoryBeanRegistrySupport.getTypeForFactoryBeanFromAttributes(...)
```

**根因**:
- `mybatis-spring 3.0.3`(Spring Boot 3.3.5 BOM 默认)+ Spring Framework 6.1.14+ 兼容 bug
- `MapperFactoryBean` 字节码 `factoryBeanObjectType` 是 `String` 类型
- Spring 6.1 读此属性时**期望 `ResolvableType`** → 抛异常

**触发版本组合**:Spring Framework 6.1.14+ / mybatis-spring 3.0.3 / Java 17+ 全部触发。

**修复**:[backend/pom.xml](../../backend/pom.xml) 显式 pin mybatis-spring 3.0.4 + exclude starter 传递的 3.0.3。

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
<dependency>
    <groupId>org.mybatis</groupId>
    <artifactId>mybatis-spring</artifactId>
    <version>3.0.4</version>
</dependency>
```

重编 + 启动:
```bash
cd backend
mvn -B clean package -DskipTests
./scripts/dev.sh restart
```

### 3.2 ⚠️ Q: `Unrecognized VM option 'UseContainerSupport'`

**症状**:Java 21+ 启后端:
```
Unrecognized VM option 'UseContainerSupport'
Error: Could not create the Java Virtual Machine
```

**根因**:`-XX:+UseContainerSupport` 在 Java 10+ 引入,Java 21 删除(已默认开启)。本项目脚本里写了。

**修复**:改 [scripts/dev.sh](../../scripts/dev.sh) 删该参数,只保留 `MaxRAMPercentage`:

```bash
nohup "$JAVA_CMD" \
    -XX:MaxRAMPercentage=75.0 \
    -jar target/app.jar \
    > "$LOGS_DIR/backend.log" 2>&1 &
```

(已修复,见 [quickstart § 3.8](./quickstart.md#38-常见报错))

### 3.3 ⚠️ Q: dev.sh 启了 Java 26(本机)而不是 Java 17

**症状**:`./scripts/dev.sh start` 后 `nohup java` 跑的是 Java 26,后端崩。

**根因**:`nohup java` 默认走 PATH 找 java,本机 PATH 第一个是 Java 26(高版本),不是 Java 17。

**修复**:改 [scripts/dev.sh](../../scripts/dev.sh) 显式选 `JAVA_HOME` 的 java:

```bash
# Prefer JAVA_HOME (for cross-version setup) over PATH
if [ -n "$JAVA_HOME" ] && [ -x "$JAVA_HOME/bin/java" ]; then
    JAVA_CMD="$JAVA_HOME/bin/java"
elif [ -x "/c/Program Files/Microsoft/jdk-17.0.19.10-hotspot/bin/java" ]; then
    JAVA_CMD="/c/Program Files/Microsoft/jdk-17.0.19.10-hotspot/bin/java"
else
    JAVA_CMD="java"
fi
log "Using: $JAVA_CMD"
nohup "$JAVA_CMD" -XX:MaxRAMPercentage=75.0 -jar target/app.jar ...
```

(已修复)

### 3.4 Q: 后端日志一直报 `Access denied for user 'novel'@'172.x.x.x'`

**原因**:`.env` 的 `MYSQL_USER` / `MYSQL_PASSWORD` 与 `docker-compose.yml` 不一致,或容器没建 user。

**修复**:
```bash
docker compose exec mysql mysql -uroot -p"$MYSQL_ROOT_PASSWORD" \
  -e "SELECT user, host FROM mysql.user;"
```

确认 `novel` user 存在,然后清理数据卷重来:
```bash
docker compose down -v && docker compose up -d --build
```

---

## 4. 登录类

### 4.1 ⚠️ Q: 登录 200 但页面跳不回首页(老 bug,已修)

**症状**:
- 浏览器:F12 Network 看到 `/api/auth/login` 返回 200 + JWT token
- 页面:弹"登录成功"提示,但瞬间又被弹回登录页
- localStorage.token 是字符串 `"undefined"`

**根因**:
- 后端统一用 `Result<T>` 包装响应:`{"code":0, "message":"ok", "data":{...}}`
- 前端 axios 响应拦截器**只 unwrap 了 axios 响应的 `.data`**,没 unwrap **后端 Result 的 `.data`**
- `apiLogin` 实际拿到 `Result<LoginResponse>`,不是 `LoginResponse`
- `resp.token` 实际是 `undefined` → token 没存 → 路由守卫 `!auth.isLogin` 把 push 跳回 `/login`

**修复**:改 [frontend/src/utils/request.ts](../../frontend/src/utils/request.ts) 拦截器,多 unwrap 一层:

```ts
// 修复前
const data = resp.data
if (data && 'code' in data && data.code !== 0) { ... }
return data  // ← 还是 Result<T> 包装

// 修复后
const wrapped = resp.data
if (wrapped && 'code' in wrapped) {
  if (wrapped.code !== 0) { ElMessage.error(wrapped.message); return Promise.reject(wrapped) }
  return wrapped.data  // ← 真正的 T
}
return wrapped
```

(已修复,Vite HMR 自动 reload 后刷新浏览器即可)

### 4.2 ⚠️ Q: 登录 200 但 code=1001 "用户认证失败"

**症状**:
```json
{"code":1001,"message":"用户认证失败","data":null}
```

**根因**:`db/init.sql` 中 admin 的 `password_hash` 是用 passlib BCrypt 生成,与 Spring Security `BCryptPasswordEncoder` 算法参数略有不同 → `matches("admin123", hash)` 返回 false。

**修复**:用 Python bcrypt 重置:

```bash
pip install bcrypt
HASH=$(python -c "import bcrypt; print(bcrypt.hashpw(b'admin123', bcrypt.gensalt(10)).decode())")
echo "New hash: $HASH"

# 写回 DB
docker exec novel-mysql mysql -uroot -proot123 -e \
  "UPDATE novel_rank.sys_user SET password_hash='$HASH' WHERE username='admin';"
```

或在 init.sql 中**直接用新生成的 hash 替换**。

### 4.3 Q: 登录 500 + `Access denied for user 'novel'@'localhost'`

**根因**:`.env` 配 `MYSQL_PORT=3307` 避本机 3306 冲突,但后端 dev profile 没读到 → 连了本机 3306(占着 MySQL 80)。

**修复**:启动后端时显式传环境变量:
```bash
MYSQL_HOST=localhost MYSQL_PORT=3307 MYSQL_USER=novel MYSQL_PASSWORD=novel123 \
  ./scripts/dev.sh start
```

或 docker compose(自动注入环境变量)。

### 4.4 Q: 登录后立刻跳到登录页(401)

**原因**:JWT_SECRET 在 backend 重启前后不一致,旧 token 失效。

**修复**:重新登录。或重启后端时**保持 JWT_SECRET 不变**(从 `.env` 读)。

### 4.5 Q: token 过期

**原因**:默认 24 小时后过期。

**修复**:重新登录。改过期时间:`.env` 里的 `JWT_EXPIRE_HOURS`,后端需重启。

---

## 5. 前端类

### 5.1 Q: `npm run dev` 起不来

**症状**:
```
'vue-tsc' 不是内部或外部命令
```

**修复**:
```bash
cd frontend
rm -rf node_modules
npm install
```

### 5.2 Q: 端口 5173 已被占

**症状**:`Port 5173 is already in use`。

**修复**:
```bash
# Linux
lsof -i :5173 | awk 'NR>1{print $2}' | xargs -r kill -9

# Windows
Get-Process node -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*node*" } | Stop-Process -Force

# 或换端口
cd frontend
npm run dev -- --port 5174
```

### 5.3 Q: Vite 代理 401 / CORS

**症状**:前端调 `/api/*` 返回 401 或 CORS 错。

**修复**:
- 401:看后端日志 + `Authorization` 头
- CORS:已配 `*`,无需改

### 5.4 Q: HMR 不刷新

**症状**:改完前端代码浏览器不更新。

**修复**:`Ctrl+R` / `F5` 硬刷新。或:
```bash
# 重启 vite
cd frontend
npm run dev
```

### 5.5 Q: TypeScript 编译错 / 泛型重载警告

**症状**:`vue-tsc` 报 `No overload matches this call`。

**原因**:axios 泛型推断 + 自定义拦截器返回 `T` vs `AxiosResponse<T>` 类型不匹配。

**修复**:用断言或加 module augmentation,见 [development.md § TS 技巧](./development.md)。

---

## 6. 数据库类

### 6.1 Q: `Unknown column 'password' in 'field list'`

**根因**:`sys_user` 表字段叫 `password_hash`,代码用错字段名。

**修复**:看 [auth.ts store](../../frontend/src/stores/auth.ts) 用了 `password` 还是 `password_hash`。修复后端代码。

### 6.2 Q: 排行榜页是空的

**根因**:还没抓过数据(数据库为空)。

**修复**:
1. admin 登录
2. "任务管理" → 选站点 → "手动触发"
3. 等任务完成(status: running → success)
4. 刷新排行榜页

### 6.3 Q: 手动触发任务,一直 pending

**根因**:crawler 容器没启动 / DB 连不上。

**排查**:
```bash
docker compose ps crawler
docker compose logs crawler
```

### 6.4 Q: 任务 success 但 ranking_record 表没数据

**根因**:Spider 选择器失效(网站改版)。

**修复**:用浏览器 DevTools 查真实 DOM,改 `crawler/novel_crawler/spiders/xxx.py` 的 CSS 选择器。

### 6.5 Q: 详情页趋势图空白

**根因**:该小说没足够历史数据(< 1 个时间点)。

**修复**:等几次抓取任务跑完,数据累积后再看。

---

## 7. 爬虫类

### 7.1 Q: 子进程日志在哪

`crawler/logs/{task_id}.log`,可通过卷 `novel_crawler_logs` 访问:
```bash
docker volume inspect novel_crawler_logs
# 实际路径: /var/lib/docker/volumes/novel_crawler_logs/_data
ls /var/lib/docker/volumes/novel_crawler_logs/_data/
```

### 7.2 Q: 怎么手动跑一个 Spider

```bash
docker compose exec crawler bash
cd /app
scrapy crawl qidian -a task_id=999 -a ranking_type=daily
```

### 7.3 Q: 反爬严重(大量 403/429)

**应急**:
- 临时禁用该站点的 `enabled = false`
- 调大 `DOWNLOAD_DELAY` 到 3-5 秒
- 减小 `CONCURRENT_REQUESTS` 到 2-4

**长期方案**(v2):
- 加代理池
- 用 Playwright 渲染 JS
- 接入打码平台

### 7.4 Q: 改了调度时间不生效

**根因**:Python 调度器每 5 分钟 reload 一次。

**修复**:等 5 分钟,看 `docker compose logs -f crawler | grep "已注册定时任务"`。

### 7.5 Q: Python 包 import 错

**症状**:
```
ModuleNotFoundError: No module named 'novel_crawler.items'
```

**根因**:`base.py` 中 `from items import ...` 路径错。

**修复**:改为 `from novel_crawler.items import NovelData, RankingData`(已修)。

---

## 8. 性能类

### 8.1 Q: 排行榜页加载慢(> 3 秒)

**排查**:
```sql
EXPLAIN SELECT * FROM v_latest_rank_snapshot
WHERE ranking_type = 'daily' AND site_id = 1
ORDER BY `rank` ASC LIMIT 20;
```
应命中 `idx_site_type_rank` 索引。

**修复**:
- 加索引(如果缺失)
- 缩小 pageSize
- 加 Redis 缓存

### 8.2 Q: 抓取任务经常超时(> 30 分钟)

**根因**:网络慢 / 反爬 / 单次抓取量太大。

**修复**:
- 调大 `schedule_config.taskTimeoutMinutes`
- 减小 `CONCURRENT_REQUESTS` + 加大 `DOWNLOAD_DELAY`
- 给某站点单独调 `custom_settings`

### 8.3 Q: 后端启动慢(> 30 秒)

**排查**:
```bash
# 看启动各阶段耗时
grep "Started NovelRankApplication" logs/backend.log
# 期望 < 25 秒
```

**修复**:
- 减 JPA 扫描包
- 减 MyBatis 启动 mapper 数量
- 加 `@Lazy` 注解

---

## 9. 配置类

### 9.1 Q: 改了调度时间不生效

**根因**:Python 调度器每 5 分钟 reload 一次。

**修复**:等待 5 分钟,看 crawler 日志:
```bash
docker compose logs -f crawler | grep "已注册定时任务"
```

### 9.2 Q: 改 admin 密码怎么操作

v1 没有改密码 UI,手动改 DB:
```bash
# 1. 生成新 hash
python -c "import bcrypt; print(bcrypt.hashpw(b'new_password', bcrypt.gensalt(10)).decode())"

# 2. 替换
docker compose exec -T mysql mysql -uroot -p"$MYSQL_ROOT_PASSWORD" novel_rank -e "
UPDATE sys_user SET password_hash = '<NEW_HASH>' WHERE username = 'admin';
"
```

### 9.3 Q: 改了 .env 容器不生效

**根因**:容器内环境变量在启动时已经定下来,改 `.env` 需重启容器。

**修复**:
```bash
docker compose down   # 停容器
docker compose up -d  # 重启(自动读新 .env)
```

---

## 10. 调试技巧

### 10.1 Q: 怎么从浏览器看 API 请求

DevTools → Network → XHR,看每个 `/api/*` 请求的:
- URL + Query Params
- Request Headers(`Authorization`)
- Response Body(`code` / `data` / `message`)

### 10.2 Q: 后端怎么打断点

IDE 里 `NovelRankApplication` Run 而不是 Debug,IDE 自动 attach。然后在代码左侧打断点。

### 10.3 Q: 爬虫怎么打断点

```python
# 在要调试的 Spider 里
import pdb; pdb.set_trace()
# 然后 docker compose logs -f crawler
```

或用 IDE Remote Debug(Python 远程调试,需 pydevd)。

---

## 11. 实战问题速查表

按"出现频率"和"难发现程度"排序:

| 优先级 | 症状 | 见 |
|---|---|---|
| ⭐⭐⭐ | 拉基础镜像超时 | § 2.1 |
| ⭐⭐⭐ | 端口冲突 3306 | § 2.2 |
| ⭐⭐⭐ | factoryBeanObjectType 错 | § 3.1 |
| ⭐⭐⭐ | UseContainerSupport 错 | § 3.2 |
| ⭐⭐⭐ | 登录不跳页 | § 4.1 |
| ⭐⭐⭐ | 登录 1001 BCrypt 不匹配 | § 4.2 |
| ⭐⭐ | dev.sh 用 Java 26 | § 3.3 |
| ⭐⭐ | Login 500 Access denied | § 4.3 |
| ⭐⭐ | 登录 401 (JWT_SECRET 变) | § 4.4 |
| ⭐ | Vite 5173 端口占 | § 5.2 |
| ⭐ | npm install 慢 | § 5.1 |
| ⭐ | 排行榜空(没抓过) | § 6.2 |
| ⭐ | 趋势图空(数据<1) | § 6.5 |
| ⭐ | 抓取超时 | § 8.2 |

## 12. 下一步

- [quickstart.md](./quickstart.md) — 5 分钟上手
- [deployment.md](./deployment.md) — 部署 + HTTPS
- [architecture.md](./architecture.md) — 架构
- [development.md](./development.md) — 加新站点/榜单
- [api.md](./api.md) — 26 个 API
- [testing.md](./testing.md) — 测试报告
