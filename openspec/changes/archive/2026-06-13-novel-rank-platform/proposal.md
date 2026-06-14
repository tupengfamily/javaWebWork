## Why

阅读爱好者、写作者、运营人员都希望了解多个小说站点的热门趋势与读者偏好,但这些数据分散在起点、番茄、纵横等不同平台,人工汇总既费时又滞后。本项目构建一个**多站点小说数据看板**:后端定时抓取榜单与基础信息,前端可视化呈现排行榜、历史趋势与跨站对比,帮助用户一站式洞察小说市场动态。

## What Changes

- 新增 **后端 REST API 服务**(Spring Boot 3 + MyBatis-Plus + Spring Security + JWT),提供公开数据接口与管理员接口
- 新增 **前端 SPA**(Vue 3 + Vite + Element Plus + ECharts),包含登录、排行榜、详情、趋势分析、任务管理 5 个核心页面
- 新增 **Python 爬虫层**(Scrapy + APScheduler + SQLAlchemy),采用多站点适配器模式,直接写 MySQL
- 新增 **MySQL 数据库**(9 张表 + 2 个视图),存储站点、小说、榜单快照、任务、日志、调度配置、管理员
- 新增 **Docker Compose 一键部署**(MySQL + Backend + Frontend + Crawler),含多阶段构建与健康检查
- 新增 **可配置定时刷新**(默认 08:00 / 14:00 / 20:00),通过前端管理页修改,Python 侧 APScheduler 读取生效

## Capabilities

### New Capabilities

- `admin-auth`: 管理员登录、JWT 颁发与校验、当前用户信息接口
- `site-config`: 站点字典管理(增删改查、启用/禁用、spider 类路径注册)
- `novel-data`: 小说主数据(列表、详情、按 novel_id 跨时间序列查询)
- `ranking-display`: 多站点排行榜展示(最新快照、跨站 TOP、趋势对比、ECharts 数据接口)
- `crawl-scheduling`: Python 调度器读取 DB 配置写入任务,Dispatcher 拉取并启动 Scrapy 子进程
- `crawl-tasks`: 爬虫任务管理(列表、手动触发、取消、重试、详细日志)
- `schedule-config`: 调度时间配置(三时段、最大并发、超时分钟数)
- `crawl-logs`: 爬虫日志流(分页查询、按级别/站点过滤)
- `meta-dictionaries`: 系统字典接口(分类、榜单类型)

### Modified Capabilities

无(全新项目,无既有 specs)

## Impact

**新增代码/目录**:

```
backend/       Spring Boot 后端 (≈30 Java 文件,1 SQL 视图)
frontend/      Vue 前端 (≈25 Vue 组件/页面,1 store,1 router)
crawler/       Python 爬虫 (≈12 Python 文件,3 spider 实现)
db/init.sql    数据库建表 + 初始数据
docker-compose.yml + 3 个 Dockerfile + nginx.conf
.env.example
```

**外部依赖**:

- Java 17, Maven 3.9
- Node.js 20, npm
- Python 3.11
- MySQL 8.0
- Docker / Docker Compose(部署用)

**库依赖**(主要):

- 后端: spring-boot-starter-web/security/validation, mybatis-plus-boot-starter, mysql-connector-j, jjwt, lombok, knife4j(Swagger)
- 前端: vue@3, vue-router@4, pinia, element-plus, axios, echarts, dayjs
- 爬虫: scrapy, apscheduler, sqlalchemy, pymysql, cryptography, python-dotenv

**风险与缓解**:

- 第三方站点反爬可能影响数据完整性 → 抽取 BaseSpider 抽象便于按站点定制,失败任务可手动重试
- 任务堆积导致并发压力 → DB 层 `maxConcurrentTasks` 配置,Dispatcher 拉取时遵循并发上限
- 时区/字符集不一致 → 统一 `Asia/Shanghai` + `utf8mb4`

**不在本 change 范围内**(后续可扩展):

- 短信/邮件告警
- 多语言切换
- 移动端 APP
- 真实生产部署(K8s/负载均衡/HTTPS 证书)
- 高级反爬(JS 渲染、验证码、代理池)
