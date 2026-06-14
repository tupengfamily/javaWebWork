# 架构详解

> 本文档详细描述系统的架构设计、数据流、关键技术决策与权衡。
> 适合需要深入理解系统行为或做二次开发的开发者。

## 1. 总体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                          Docker Host                             │
│                                                                  │
│  ┌─────────────── novel_net (bridge) ───────────────────────┐  │
│  │                                                            │  │
│  │   ┌──────────────┐         ┌─────────────────────┐        │  │
│  │   │  frontend    │  HTTP   │      backend        │        │  │
│  │   │  Nginx + Vue │ ◀─────▶ │   Spring Boot 3     │        │  │
│  │   │  (port 80)   │         │   (port 8080)       │        │  │
│  │   └──────────────┘         └──────────┬──────────┘        │  │
│  │                                        │ SQL                │  │
│  │   ┌──────────────┐                    │                    │  │
│  │   │   crawler    │  写表(直连)         │  读表(直连)        │  │
│  │   │  Python      │ ◀─────────────▶ ┌───▼────────────────┐  │  │
│  │   │  (无端口)     │                 │      MySQL 8        │  │  │
│  │   │              │                 │   (port 3306)       │  │  │
│  │   └──────────────┘                 │  9 tables + 2 views │  │  │
│  │                                    └─────────────────────┘  │  │
│  │                                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  端口暴露: 80 (前端) / 8080 (后端,可选) / 3306 (MySQL,可选)     │
└─────────────────────────────────────────────────────────────────┘
```

**关键特征**:
- 三个独立进程,**零 HTTP/RPC 直连**
- **MySQL 是唯一协调介质**: Java 读、Python 写
- 每个进程可独立扩展/替换

## 2. 进程职责

| 进程 | 职责 | 不做什么 |
|---|---|---|
| **Vue 前端** | 用户界面 / 路由 / ECharts 图表 | 不知道后端是什么语言 |
| **Spring Boot 后端** | REST API / JWT 鉴权 / 业务查询 | 不知道 Python 存在,不知道爬虫何时跑 |
| **Python 爬虫** | 抓取数据 / 调度任务 / 写 MySQL | 不知道 Java 存在,只通过 DB 与之协调 |

## 3. 数据流: 一次完整抓取

```
┌─────────────────────────────────────────────────────────────┐
│  T0  - APScheduler 到点(或管理员手动触发)                    │
│         ↓                                                    │
│  T1  - Scheduler 写一条 crawl_task 记录(status=pending)     │
│         ↓                                                    │
│  T2  - Dispatcher 轮询(每 5 秒)发现 pending 任务             │
│         ↓                                                    │
│  T3  - 用 `SELECT ... FOR UPDATE SKIP LOCKED` 原子认领       │
│         - 标记 status=running,记录 worker_id                 │
│         ↓                                                    │
│  T4  - subprocess.Popen 启动 scrapy crawl 站点 Spider       │
│         - stdout/stderr → logs/{task_id}.log                │
│         ↓                                                    │
│  T5  - Spider 抓列表页 + 详情页                              │
│         - 每个 item 经 Pipeline 链:                          │
│           Dedup → NovelUpsert → RankingInsert → CrawlLog     │
│         - ranking_record 累积(一条/条)                       │
│         ↓                                                    │
│  T6  - 子进程退出                                            │
│         - exit 0 → Dispatcher 标 success                     │
│         - exit ≠ 0 → Dispatcher 标 failed + 错误码          │
│         - 超时(默认 30 分) → 强制 kill,标 failed             │
└─────────────────────────────────────────────────────────────┘
```

## 4. 关键技术决策

### 4.1 为什么用 MySQL 当任务队列而不用 Redis

**选 MySQL**:
- 任务状态可查询(前端任务列表直接读 crawl_task)
- 持久化免费(MySQL 是核心存储,顺便用)
- 跨进程可视(Java 写 / Python 读天然共享)
- 性能: 每天最多产生 9 个任务 × 365 = 3285 行/年,完全不是瓶颈

**没用 Redis**:
- 多一个组件,运维成本
- 数据易失,任务丢了要靠重试

### 4.2 为什么用 subprocess 而不是进程内 CrawlerProcess

**选 subprocess**:
- 任务完全隔离,任一爬虫崩了不会拖死 Dispatcher
- 可用 `proc.kill()` 强制超时
- 日志直接重定向到 `logs/{task_id}.log`,简单可靠

**没用进程内**:
- 任务互相阻塞,无法并发
- 没有强制 kill 机制
- 一个 Spider 抛异常可能影响 Dispatcher

### 4.3 为什么用 SELECT ... FOR UPDATE SKIP LOCKED

MySQL 8.0+ 特性。多个 Dispatcher 进程(或以后横向扩展)并发拉取任务时:
- 传统 `SELECT FOR UPDATE`: 锁冲突,后面的进程阻塞等锁
- `SKIP LOCKED`: 跳过已被锁的行,各自拉各自的 → **零冲突**

配合事务认领 + 状态翻转:
```
Worker A: SELECT ... FOR UPDATE SKIP LOCKED LIMIT 5 → 拿 task 1,2,3
Worker B: 同时 SELECT ... FOR UPDATE SKIP LOCKED LIMIT 5 → 拿 task 4,5,6,7,8
Worker A: UPDATE crawl_task SET status='running' WHERE id IN (1,2,3)
```

### 4.4 为什么用 JSON 列存调度配置

`schedule_config.value` 用 MySQL 原生 JSON 类型,好处:
- 加字段不用 ALTER TABLE
- Python 直接 `json.loads()` / Java 用 Jackson
- DB 还能对 JSON 内部做索引(MySQL 8.0+)

## 5. 数据库 ER 简图

```
            ┌────────┐
            │  site  │─────────┐
            └────┬───┘         │
                 │1            │N
                 │             │
                 │             ▼
            ┌────▼────┐   ┌─────────┐
            │  novel  │◀──┤ranking_ │
            └────┬────┘   │ record  │
                 │        └────┬────┘
                 │1            │N
                 │             │
                 │             ▼
                 │        ┌──────────┐
                 │        │crawl_task│
                 │        └────┬─────┘
                 │             │1
                 │             │
                 │             ▼
                 │        ┌──────────┐
                 └───────▶│crawl_log │
                          └──────────┘

         字典(无外键):
         - category
         - ranking_type
         - schedule_config
         - sys_user
```

**关系说明**:
- `site` 1:N `novel` / `ranking_record` / `crawl_task` / `crawl_log`
- `novel` 1:N `ranking_record`
- `crawl_task` 1:N `crawl_log`
- 字典表无外键,纯静态
- 复合唯一键: `novel(site_id, external_id)`,保证同站点内 book_id 不重复

## 6. 视图说明

### 6.1 v_latest_ranking

每个 (novel_id, ranking_type) 的最新一条 ranking_record(带 `rn` 行号)。

```sql
SELECT * FROM v_latest_ranking WHERE novel_id = 123 AND rn = 1;
-- 拿该小说的所有榜单类型的最新一条
```

### 6.2 v_latest_rank_snapshot

某 (ranking_type, category) 的最新一次抓取的所有条目。

```sql
SELECT * FROM v_latest_rank_snapshot WHERE ranking_type = 'daily' AND category IS NULL;
-- 最新一次日榜的全部条目
```

视图的好处: 把"取最新"这个 GROUP BY 预计算,避免每次业务查询都扫表。

## 7. 时区与字符集

| 维度 | 设定 |
|---|---|
| 时区 | `Asia/Shanghai` (UTC+8) |
| MySQL | `--default-time-zone=+08:00` |
| 容器 | `TZ=Asia/Shanghai` |
| JDBC | `serverTimezone=Asia/Shanghai` |
| APScheduler | `timezone="Asia/Shanghai"` |
| 字符集 | `utf8mb4 / utf8mb4_unicode_ci` |
| 连接串 | `characterEncoding=utf8&useUnicode=true` |

**为什么这样**: 防止时区漂移导致 `crawl_time` 错位,防止 emoji / 特殊字符乱码。

## 8. 性能特征

| 操作 | 性能 | 备注 |
|---|---|---|
| 排行榜列表(分页) | < 50ms | 走 v_latest_rank_snapshot 视图 + 索引 |
| 单小说趋势(30 天) | < 30ms | 命中 idx_novel_time |
| 跨站 TOP 10 | < 100ms | 走视图,数据量小 |
| 调度写入任务 | < 10ms/条 | 每天 ~9 条 |
| Dispatcher 轮询 | < 50ms/tick | 5 秒一次 |
| 单次抓取(1000 本) | 3-8 分钟 | 含 1.5s 延迟 × 1000 = 25 分钟理论值,实际并发压缩 |

## 9. 安全模型

| 维度 | 机制 |
|---|---|
| 鉴权 | JWT (HS256,密钥从 env 注入) |
| Token 过期 | 24 小时(可配) |
| 密码存储 | BCrypt 哈希 |
| SQL 注入 | MyBatis-Plus 参数绑定 |
| XSS | 前端 Vue 自动转义 |
| CSRF | 无状态 JWT,不依赖 cookie |
| 公开/管理路由隔离 | Spring Security + 路径前缀 |
| 失败登录 | 无锁定(单 admin 系统,管理员自己改密码) |

## 10. 扩展点

**加新站点**(5 步):
1. 在 `site` 表 INSERT 一行(code/name/spider_class)
2. 在 `crawler/novel_crawler/spiders/` 加一个 `xxx.py`,继承 `BaseSpider`
3. 在 `crawler/novel_crawler/spiders/registry.py` 的 `SITE_TO_SPIDER` 加映射
4. 实现 `start_requests` + `parse` + 可选 `parse_detail`
5. 重启 crawler 容器即可

**加新榜单类型**(2 步):
1. `ranking_type` 表加一行
2. `schedule_config.crawlAllRankingTypes` 数组加一项

**加新指标**(如点击率) — 见 [development.md](./development.md)
