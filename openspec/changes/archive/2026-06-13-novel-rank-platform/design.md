## Context

项目从零起步构建一个多站点小说数据看板。三个独立技术栈(Java 后端、Vue 前端、Python 爬虫)需要在一个共享 MySQL 数据库上协作,目标是为读者、作者、运营人员提供跨站点的热门趋势与读者偏好洞察。

**关键约束**:
- 零历史代码,新仓库,可自由选择技术栈与目录结构
- 三个进程物理隔离:Java jar、Vue 静态文件 + Nginx、Python 守护进程
- 调度责任必须完全在 Python 侧(避免 Java 进程感知 Python 存在)
- 部署需支持 Docker Compose 一键拉起
- 数据量预估 3 站点 × 2000 本 × 3 榜单 × 3 次/天 × 90 天 ≈ 486 万行,MySQL 单机可承受

**干系人**:作者本人(也充当管理员、读者、运营三种角色)

## Goals / Non-Goals

**Goals**:
- 单一数据源(MySQL),三个进程通过共享 schema 解耦
- 多站点可扩展:加新站点 = 写一个 Spider 子类 + 在 site 表注册,不修改其他代码
- 调度时间可配置:前端管理页可改,Python 下次 tick 自动 reload
- 排行榜展示含历史趋势,前端 ECharts 图表直接消费后端数据,无需二次加工
- 管理员可手动触发、取消、重试爬虫任务,实时看到日志
- Docker Compose 一键启动完整开发与生产级运行环境

**Non-Goals**:
- 不实现用户系统(只一个 admin)
- 不实现 HTTPS 证书与负载均衡(由反向代理/Nginx 上层处理)
- 不实现高级反爬(JS 渲染、验证码、代理池)
- 不实现消息推送/邮件告警
- 不实现数据导出 Excel/CSV(简单 HTTP 列表已够用,后期再加)
- 不实现分布式 Worker 调度(单 Python 进程足够)

## Decisions

### 1. 三层进程架构(Java + Vue + Python)

**决策**:三个独立进程,共享 MySQL,无 HTTP/RPC 直连。

**替代方案**:
- A. Java 调用 Python 脚本:耦合强,日志处理差
- B. Python 作为微服务提供 REST:增加部署复杂度
- C. 消息队列(Kafka/RabbitMQ):杀鸡用牛刀,运维成本高
- D. **共享 DB(已选)**:零耦合,任意进程挂了不影响其他;最简单可靠

**理由**:三个进程职责清晰(Java=API、Python=抓取、Vue=展示),用 DB 当协调介质最直接。Python 完全不知道 Java 的存在,反之亦然,各自可独立扩展与替换。

### 2. Python 侧独立调度(APScheduler + DB poll)

**决策**:Python 进程内同时运行 APScheduler(读 schedule_config 写 task)与 Dispatcher(轮询 task 启动 Scrapy),两个守护线程。

**替代方案**:
- A. Java 端 @Scheduled 写 task:Java 必须感知 Python 存在,违反解耦原则
- B. Celery + Redis:杀鸡用牛刀
- C. 系统 cron + Python 脚本:无法读取 DB 配置做动态调整
- D. **进程内 APScheduler(已选)**:Python 自给自足,5 分钟 reload 配置

**理由**:用户明确要求"调度责任全在 Python 侧"。APScheduler 的 BackgroundScheduler 与 DB poll 的 Dispatcher 共用一个进程简单可靠,故障时一个容器重启即恢复。

### 3. 任务队列基于 MySQL 而非 Redis

**决策**:`crawl_task` 表同时承担"持久化任务状态"和"进程间任务队列"两重角色,用 `SELECT ... FOR UPDATE SKIP LOCKED` 原子认领。

**替代方案**:
- A. Redis 队列:增加组件,数据易失
- B. **MySQL 行锁(已选)**:无新增组件,任务状态可查询可追溯
- C. 文件队列:难以实现并发安全

**理由**:MySQL 8.0 的 `SKIP LOCKED` 让"多个 worker 互不冲突地拉取任务"原生支持,无需应用层锁。任务状态天然持久化,前端可查。

### 4. Scrapy 子进程 via subprocess

**决策**:Dispatcher 通过 `subprocess.Popen("scrapy crawl ...")`,stdout/stderr 重定向到 `logs/{task_id}.log`。

**替代方案**:
- A. 进程内 `CrawlerProcess` 串行:无法并发,无法超时 kill
- B. **subprocess(已选)**:任务完全隔离,任意一个崩溃不影响 Dispatcher
- C. scrapyd:增加组件,本项目规模不需要

**理由**:subprocess 提供最干净的隔离,`proc.poll()` 检测结束,`proc.kill()` 处理超时。日志落盘方便后续查询。

### 5. Spring Boot 3 + MyBatis-Plus + JWT

**决策**:后端使用 Spring Boot 3.2+,MyBatis-Plus 3.5+ 简化单表 CRUD,JWT 用 jjwt 0.12+ 无状态认证。

**替代方案**:
- A. Spring Data JPA:ORM 黑盒,复杂 SQL 调优难
- B. **MyBatis-Plus(已选)**:SQL 透明可控,ActiveRecord 风格写起来快
- C. Spring Security OAuth2:对单 admin 系统过重
- D. **JWT 无状态(已选)**:无 session,水平扩展友好

**理由**:MyBatis-Plus 在"CRUD 为主 + 少量复杂 SQL"的场景是最佳平衡。JWT 配合 Spring Security 的 RequestMatch 注解实现"公开/管理"路由隔离极简。

### 6. Vue 3 + Vite + Element Plus + ECharts

**决策**:Vue 3 Composition API + Vite 5 + Element Plus 2.x + ECharts 5.x + Pinia + Vue Router 4。

**替代方案**:
- A. Nuxt 3:本项目是 SPA 性质,SSR 收益不大
- B. **Vite + Vue 3(已选)**:启动快,HMR 体验好,生态成熟
- C. Ant Design Vue:用户明确选 Element Plus

**理由**:Element Plus 的 admin 模板生态最丰富(虽然本项目用不到模板),ECharts 几乎是中国数据可视化的事实标准,Vue 3 响应式系统对图表组件非常友好。

### 7. 软删除不做,改用状态字段

**决策**:`crawl_task` 用 status 字段表达生命周期,不用 is_deleted。

**理由**:时序数据需要"曾发生过"的记忆,软删除会丢失历史。状态机简单:pending → running → success/failed/cancelled。

### 8. 数据库时序数据保留策略

**决策**:`ranking_record` 永久保留,不做归档。

**替代方案**:
- A. 按月分区表:增加运维复杂度
- B. **不分区(已选)**:486 万行 / 1GB 在 MySQL 8 完全无压力
- C. 定期归档到 OSS:对 v1 过重

**理由**:MVP 阶段数据量小,简单优先。后期量超千万再考虑分区或冷热分层。

### 9. 反爬策略 v1 简化

**决策**:随机 UA + 1-3 秒随机间隔 + Scrapy 内置重试 3 次。

**替代方案**:
- A. **简化版(已选)**:足够应对多数公开榜单
- B. 浏览器自动化(Selenium/Playwright):慢且重
- C. 代理池:成本高,v1 收益小

**理由**:起点/番茄/纵横的公开榜单页面通常无强反爬,简化策略足够。如果某站点频繁失败,可在 v2 单独为该站点加特殊处理。

### 10. 实时日志走 5 秒轮询而非 WebSocket

**决策**:前端每 5 秒 `GET /api/admin/dashboard/logs`。

**替代方案**:
- A. **轮询(已选)**:实现简单,日均日志量小,延迟可接受
- B. SSE / WebSocket:对管理页面(非高频实时)过度设计

**理由**:管理员 5 秒延迟无感,实现复杂度低一个数量级。

### 11. JWT 签发 24 小时过期

**决策**:token 24 小时过期,过期需重新登录。

**替代方案**:
- A. **24h(已选)**:平衡安全与体验
- B. 短期 token + refresh token:对单 admin 系统过重
- C. 永久 token:有安全风险

**理由**:管理员是低频操作场景,24 小时无需重新登录足够好用。

### 12. 部署用单一 docker-compose.yml

**决策**:不用 Kubernetes,所有服务在单机 docker compose 内编排。

**替代方案**:
- A. **docker compose(已选)**:单机场景最简
- B. Kubernetes:用户场景不需要
- C. 裸机部署:用户希望一键起

**理由**:符合"Docker Compose 一键起"的需求,适合开发与小规模生产。

## Risks / Trade-offs

**[R1] 第三方站点结构变动导致 Spider 失效** → 抽象 BaseSpider 让每个站点独立维护,失效只影响单个站点;UI 提供"手动重试"让管理员快速恢复

**[R2] 单 Python 进程成为瓶颈** → v1 数据量小(每天 3×N×M 次任务),单进程足够;后期可横向扩展(多 crawler 容器 + 共享 DB)

**[R3] 任务堆积导致 MySQL 压力** → `maxConcurrentTasks` 限流 + task 表按 status 索引,前端"日志"和"任务列表"读旧数据不阻塞写

**[R4] JWT secret 泄露** → 通过 `.env` 注入,部署文档明确警告必须修改;支持 JWT secret 轮换(后端重启)

**[R5] 中文/Emoji 字符问题** → 全链路 `utf8mb4` + URL 编码 + MySQL 连接串 `characterEncoding=utf8`

**[R6] Docker 构建慢(尤其首次)** → 多阶段构建 + npm/pip 国内镜像源,后续构建利用层缓存

**[R7] 时区混乱导致 crawl_time 错位** → 容器统一 `TZ=Asia/Shanghai` + MySQL `--default-time-zone=+08:00` + JDBC `serverTimezone=Asia/Shanghai`

**[R8] 调度器挂掉导致任务不再生成** → 容器 `restart: unless-stopped` 自动拉起;管理员可手动触发兜底

## Migration Plan

v1 全新项目无迁移成本。部署步骤:

1. 准备环境:`docker`, `docker compose`
2. `cp .env.example .env` 并修改 `JWT_SECRET` 与数据库密码
3. `docker compose up -d --build`(首次构建镜像,需数分钟)
4. 等待 MySQL healthcheck 通过 → backend 启动 → frontend 启动
5. 浏览器访问 `http://localhost` 即可
6. 默认账号 `admin / admin123`,**首次登录后必须改密码**

**回滚策略**:无状态服务(bFrontend、backend)任意时刻 `docker compose down` 即可;MySQL 数据在 `novel_db_data` 卷中,删除卷才会丢失;crawler 无状态,重起即恢复。

## Open Questions

1. **站点的"可扩展"机制是否需要 UI 引导?**
   - 当前设计:管理员手动编辑 `spider_class` 字符串,Python 启动时按路径动态加载
   - 替代:前端提供"Spider 配置向导",自动生成类路径模板
   - 决定:先按当前设计实现,UI 向导 v2 再说

2. **跨站小说去重(同一本小说在多个站点都存在)如何表达?**
   - 当前设计:每条 novel 独立,跨站 TOP 列表中"斗破苍穹"可能出现在起点和纵横两行
   - 替代:增加 `novel_alias` 表手动关联
   - 决定:v1 不做,需求真实出现再加

3. **多 crawler 容器并行时,如何保证单站点任务不并发?**
   - 当前设计:每容器内 Dispatcher 串行认领;多容器可能造成同站点并发
   - 解决:用 MySQL 行级锁 `(site_id, status='running')` 唯一约束,加 UNIQUE INDEX
   - 决定:v1 单容器,加约束作为 v2 扩展

4. **历史数据全量回填需求**
   - 当前设计:只能抓取当前榜单,无法回溯历史
   - 替代:每日凌晨额外跑"补全任务"
   - 决定:v1 不做,看用户实际使用反馈
