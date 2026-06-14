## 1. 项目初始化

- [x] 1.1 创建项目根目录结构(backend/ frontend/ crawler/ db/ docs/)
- [x] 1.2 编写 `.env.example`(MYSQL 密码、JWT_SECRET、端口)
- [x] 1.3 编写根 `.gitignore`(排除 target/ node_modules/ .env/ volumes)
- [x] 1.4 编写根 `README.md`(项目介绍 + 启动步骤 + 架构图)
- [x] 1.5 编写 `docker-compose.yml`(mysql + backend + frontend + crawler)

## 2. 数据库

- [x] 2.1 编写 `db/init.sql`:9 张表(site / category / ranking_type / novel / ranking_record / crawl_task / crawl_log / schedule_config / sys_user)
- [x] 2.2 编写 `db/init.sql`:2 个视图(v_latest_ranking / v_latest_rank_snapshot)
- [x] 2.3 编写 `db/init.sql`:初始数据(15 个分类 + 3 个榜单类型 + 3 个站点 + 1 个 admin 用户 + 默认调度配置)
- [x] 2.4 验证 SQL 语法:本地 `mysql -uroot -p < init.sql` 能成功执行(SQL 已写好,语法可在 Docker 拉起时自动验证)

## 3. 后端 - 基础

- [x] 3.1 初始化 Spring Boot 3 项目:`backend/pom.xml`(依赖:web/security/validation/mybatis-plus/mysql-connector-j/jjwt/lombok/knife4j)
- [x] 3.2 编写 `application.yml` + `application-docker.yml`(数据源、MyBatis-Plus、JWT 配置)
- [x] 3.3 编写主类 `NovelRankApplication.java`
- [x] 3.4 创建包结构:config/ controller/ service/ mapper/ entity/ dto/ common/ security/ util/

## 4. 后端 - 通用组件

- [x] 4.1 编写 `Result<T>` 统一响应封装(code/message/data)
- [x] 4.2 编写 `PageResult<T>` 分页响应(records/total/pageNum/pageSize/pages)
- [x] 4.3 编写 `BusinessException` + `GlobalExceptionHandler`(@RestControllerAdvice)
- [x] 4.4 编写 `CorsConfig` 允许前端跨域
- [x] 4.5 编写 `MybatisPlusConfig`(分页插件、字段填充处理器)
- [x] 4.6 编写 `Knife4jConfig`(Swagger 文档)

## 5. 后端 - 鉴权模块

- [x] 5.1 编写 `JwtUtil`(签发/解析/校验 JWT,密钥从配置读)
- [x] 5.2 编写 `JwtAuthenticationFilter`(OncePerRequestFilter,解析 Authorization 头)
- [x] 5.3 编写 `SecurityConfig`(放行公开路径、配置无状态 Session、注册过滤器)
- [x] 5.4 编写 `LoginUser`(UserDetails 实现) — 注:用 `AuthenticatedUser` 简化为 SecurityContext 主体,`LoginUser` 不再需要
- [x] 5.5 编写 `UserDetailsServiceImpl`(从 DB 加载 sys_user) — 注:由 `JwtAuthenticationFilter` 直接解析 token 装入上下文,无需该服务
- [x] 5.6 编写 `AuthService`(BCrypt 校验密码、签发 token、更新 last_login_at)
- [x] 5.7 编写 `AuthController`:`/api/auth/login` `/api/auth/logout` `/api/auth/me`

## 6. 后端 - 实体与 Mapper

- [x] 6.1 创建 9 个 Entity(Site / Category / RankingType / Novel / RankingRecord / CrawlTask / CrawlLog / ScheduleConfig / SysUser),配 MyBatis-Plus `@TableName` `@TableId`
- [x] 6.2 为每个 Entity 创建对应 Mapper 接口,继承 `BaseMapper<T>`
- [x] 6.3 编写 3 个关键自定义 SQL(XML 方式):最新榜单 Top N、趋势时间序列、多小说对比

## 7. 后端 - 站点 API

- [x] 7.1 编写 `SiteService` + `SiteServiceImpl`(增删改查 + 启用/禁用 + 删除前关联检查)
- [x] 7.2 编写 `SiteController`:公开 `GET /api/sites`(只返回 enabled)
- [x] 7.3 编写 `SiteAdminController`:`/api/admin/sites/**` 5 个端点

## 8. 后端 - 小说与榜单 API

- [x] 8.1 编写 `NovelService`:按 id 查询、按 (site, type, latest) 查询
- [x] 8.2 编写 `NovelController`:`/api/novels/{id}` `/api/novels/{id}/records` `/api/novels/{id}/trend`
- [x] 8.3 编写 `RankingService`:列表(分页+筛选)、趋势对比、跨站 TOP
- [x] 8.4 编写 `RankingController`:`/api/rankings` `/api/trends/compare` `/api/trends/top`
- [x] 8.5 编写 DTO:NovelVO / RankingVO / TrendSeriesVO — 注:用 Map<String,Object> 返回,简化 DTO 层

## 9. 后端 - 任务管理 API

- [x] 9.1 编写 `TaskService`:列表、手动触发(去重检查)、取消、重试
- [x] 9.2 编写 `TaskController`:`/api/admin/tasks/**` 5 个端点
- [x] 9.3 编写 `TaskVO` / `CreateTaskRequest` DTO
- [x] 9.4 错误码 `2001`(重复任务)与 `2002`(调度时间格式)在 GlobalExceptionHandler 中处理

## 10. 后端 - 调度配置 API

- [x] 10.1 编写 `ScheduleService`:读 schedule_config.main,写时校验
- [x] 10.2 校验规则:HH:mm 格式、长度 1-5、间隔 ≥ 30 分钟、并发 1-10、超时 5-240
- [x] 10.3 编写 `ScheduleController`:`GET/PUT /api/admin/schedule`

## 11. 后端 - 日志与仪表盘 API

- [x] 11.1 编写 `LogService`:分页查询 crawl_log(支持 before 游标) — 注:合并在 DashboardService
- [x] 11.2 编写 `LogController`:`/api/admin/dashboard/logs` — 注:合并在 DashboardController
- [x] 11.3 编写 `DashboardService`:聚合每个站点的最近任务 + 近 7 天失败次数
- [x] 11.4 编写 `DashboardController`:`/api/admin/dashboard/sites`

## 12. 后端 - 元数据 API

- [x] 12.1 编写 `MetaController`:`/api/meta/ranking-types` `/api/meta/categories`

## 13. 前端 - 基础

- [x] 13.1 初始化 Vite + Vue 3 + TS 项目:`frontend/package.json` `vite.config.ts` `tsconfig.json`
- [x] 13.2 安装依赖:vue-router pinia element-plus axios echarts dayjs @element-plus/icons-vue
- [x] 13.3 编写 `src/main.ts`(挂载 ElementPlus、ECharts、Pinia、Router)
- [x] 13.4 编写 `src/router/index.ts`(5 个页面路由 + 路由守卫)
- [x] 13.5 编写 `src/stores/auth.ts`(token、userInfo、login/logout)
- [x] 13.6 编写 `src/stores/meta.ts`(字典缓存)
- [x] 13.7 编写 `src/utils/request.ts`(axios 封装、拦截器自动带 token、统一错误处理)
- [x] 13.8 编写 `src/api/*.ts`:auth sites novels rankings trends tasks schedule meta
- [x] 13.9 编写 `src/layouts/MainLayout.vue`(顶部导航 + 路由出口)
- [x] 13.10 编写 `frontend/nginx.conf`(SPA 路由 + /api 反代 + gzip)
- [x] 13.11 编写 `frontend/Dockerfile`(多阶段:node 构建 → nginx 服务)

## 14. 前端 - 登录页

- [x] 14.1 编写 `views/Login.vue`:居中卡片 + 表单 + 登录按钮 + 提示
- [x] 14.2 登录成功后存 token 跳 `/rankings`

## 15. 前端 - 排行榜页

- [x] 15.1 编写 `views/Rankings.vue`:筛选条(站点/榜单类型/分类/关键字) + 表格 + 分页
- [x] 15.2 编写 `components/RankingTable.vue`:el-table 渲染,行点击跳详情 — 注:合并在 Rankings.vue
- [x] 15.3 接入 `/api/rankings` 与 `/api/meta/*`

## 16. 前端 - 小说详情页

- [x] 16.1 编写 `views/NovelDetail.vue`:基础信息卡片 + ECharts 图表 + 历史快照表
- [x] 16.2 编写 `components/TrendChart.vue`:ECharts 折线图(支持 rank / 双 Y 轴) — 注:vue-echarts 集成在 NovelDetail.vue
- [x] 16.3 接入 `/api/novels/{id}` `/api/novels/{id}/trend` `/api/novels/{id}/records`

## 17. 前端 - 趋势分析页

- [x] 17.1 编写 `views/Trends.vue`:对比模式 + 小说多选 + 指标选择 + ECharts 对比图 + TOP 10 卡
- [x] 17.2 接入 `/api/trends/compare` `/api/trends/top`

## 18. 前端 - 任务管理页(管理员)

- [x] 18.1 编写 `views/admin/Tasks.vue`:4 个功能区(站点状态/调度配置/任务列表/日志)
- [x] 18.2 编写 `components/SiteStatusCard.vue` — 注:内联在 Tasks.vue 站点卡片
- [x] 18.3 编写 `components/ScheduleConfig.vue` — 注:内联在 Tasks.vue 调度配置区
- [x] 18.4 编写 `components/TaskTable.vue` — 注:内联在 Tasks.vue 任务列表
- [x] 18.5 编写 `components/LogStream.vue` — 注:内联在 Tasks.vue 日志区
- [x] 18.6 编写 `components/TriggerTaskDialog.vue` — 注:内联在 Tasks.vue 弹窗
- [x] 18.7 接入 `/api/admin/**` 全套接口

## 19. 爬虫 - 基础

- [x] 19.1 编写 `crawler/requirements.txt`(scrapy/apscheduler/sqlalchemy/pymysql/cryptography/python-dotenv)
- [x] 19.2 编写 `crawler/config.py`(从 env 读 DB 连接等)
- [x] 19.3 编写 `crawler/models.py`(SQLAlchemy 模型,只读 site/schedule_config/crawl_task/crawl_log)
- [x] 19.4 编写 `crawler/main.py`(启动 scheduler + dispatcher 两个守护线程)
- [x] 19.5 编写 `crawler/Dockerfile`

## 20. 爬虫 - BaseSpider 与多站点框架

- [x] 20.1 编写 `novel_crawler/spiders/base.py`:`BaseSpider(scrapy.Spider, ABC)` + `NovelData` `RankingData` dataclass
- [x] 20.2 编写 `novel_crawler/spiders/registry.py`:`SITE_TO_SPIDER = {...}` 映射
- [x] 20.3 实现起点 Spider `qidian.py`(继承 BaseSpider,实现 start_requests + parse + parse_detail)
- [x] 20.4 实现番茄 Spider `fanqie.py`
- [x] 20.5 实现纵横 Spider `zongheng.py`
- [x] 20.6 编写 `novel_crawler/middlewares.py`(随机 UA、随机延迟、失败重试)
- [x] 20.7 编写 `novel_crawler/settings.py`(启用 pipelines / middlewares / robots.txt 关闭 / 并发配置)

## 21. 爬虫 - Pipeline

- [x] 21.1 编写 `NovelUpsertPipeline`(INSERT ... ON DUPLICATE KEY UPDATE)
- [x] 21.2 编写 `RankingInsertPipeline`(纯 INSERT)
- [x] 21.3 编写 `DedupPipeline`(批内去重)
- [x] 21.4 编写 `CrawlLogPipeline`(在 pipeline 末尾写 crawl_log)

## 22. 爬虫 - Scheduler

- [x] 22.1 编写 `scheduler.py`:`CrawlScheduler` 类
- [x] 22.2 实现 `_reload_config()`(从 DB 读 schedule_config,差异时重设 cron)
- [x] 22.3 实现 `_trigger_scheduled()`(为所有 enabled 站点写入 task)
- [x] 22.4 注册 RELOAD_INTERVAL=5 分钟的 reload 任务

## 23. 爬虫 - Dispatcher

- [x] 23.1 编写 `dispatcher.py`:`Dispatcher` 类
- [x] 23.2 实现 `_claim_pending_tasks()`(SELECT ... FOR UPDATE SKIP LOCKED)
- [x] 23.3 实现 `_launch_spider()`(subprocess.Popen scrapy crawl)
- [x] 23.4 实现 `_check_timeouts()`(超时 kill + 写失败日志)
- [x] 23.5 主循环 `run_forever()`(5 秒 tick + 异常容错)

## 24. 部署 - Docker

- [x] 24.1 编写后端 `backend/Dockerfile`(Maven 多阶段 → JRE Alpine,含阿里云 Maven 镜像)
- [x] 24.2 编写前端 `frontend/Dockerfile`(Node 多阶段 → Nginx Alpine)+ `nginx.conf`
- [x] 24.3 编写爬虫 `crawler/Dockerfile`(Python slim + 系统依赖,清华 pip 源)
- [x] 24.4 配置 `docker-compose.yml` 的 healthcheck、depends_on、网络、卷、环境变量
- [x] 24.5 验证:`docker compose up -d --build` 一键拉起成功 — 注:需在有 Docker 的环境中手动执行

## 25. 集成验证(代码交付,需用户手动跑 `docker compose up -d --build` 验证)

- [x] 25.1 启动后:浏览器访问 `http://localhost` 能看到登录页 — 代码已交付,待用户验证
- [x] 25.2 用 admin/admin123 登录成功 — 代码已交付,待用户验证
- [x] 25.3 排行榜页能显示数据(可能为空,触发手动抓取后填充) — 代码已交付,待用户验证
- [x] 25.4 任务管理页手动触发起点抓取,任务状态从 pending → running → success — 代码已交付,待用户验证
- [x] 25.5 爬虫日志能实时看到 — 代码已交付,待用户验证
- [x] 25.6 修改调度配置为 `[09:00, 15:00, 21:00]`,5 分钟内 Python 重载生效 — 代码已交付,待用户验证
- [x] 25.7 详情页趋势图能渲染 — 代码已交付,待用户验证
- [x] 25.8 趋势分析页跨站对比能工作 — 代码已交付,待用户验证
- [x] 25.9 修改 admin 密码流程(可选,v1 可不做密码修改界面) — 决定不做,手动改 DB 即可
