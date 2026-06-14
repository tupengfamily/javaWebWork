# 小说数据看板 (Novel Rank Platform)

> 抓取起点 / 番茄 / 纵横等多个小说阅读站点的浏览数据与排行榜,定时刷新,前端可视化展示。

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue 3 + Vite + Element Plus + ECharts + Pinia |
| 后端 | Spring Boot 3 + MyBatis-Plus + Spring Security + JWT |
| 爬虫 | Python 3.11 + Scrapy + APScheduler + SQLAlchemy |
| 数据库 | MySQL 8.0 |
| 部署 | Docker Compose |

## 架构

```
┌──────────────────────┐  HTTP/JSON  ┌──────────────────────┐
│   Frontend (Nginx)   │ ◀─────────▶ │   Backend (Spring)   │
│   Vue 3 SPA          │             │   REST API + JWT     │
└──────────────────────┘             └──────────┬───────────┘
                                                │ 读
                                                ▼
┌──────────────────────┐             ┌──────────────────────┐
│   Crawler (Python)   │ ─写表──────▶ │        MySQL         │
│   APScheduler +      │ ◀──读配置─── │   9 tables + 2 views │
│   Scrapy Dispatcher  │             │                      │
└──────────────────────┘             └──────────────────────┘
```

## 快速开始

### 前置条件

- Docker 20+
- Docker Compose v2
- 8GB 内存,10GB 磁盘

### 一键启动

```bash
# 1. 准备环境变量
cp .env.example .env
# (建议) 编辑 .env 修改 JWT_SECRET

# 2. 启动(首次会自动构建镜像并执行 init.sql)
docker compose up -d --build

# 3. 查看启动日志
docker compose logs -f crawler   # 爬虫调度器
docker compose logs -f backend   # 后端服务
```

### 访问

| 服务 | 地址 |
|---|---|
| 前端 | http://localhost |
| 后端 API | http://localhost:8080/api |
| Swagger | http://localhost:8080/doc.html |
| MySQL | localhost:3306 (user: novel, pwd: novel123) |

### 默认账号

- 用户名: `admin`
- 密码: `admin123`

**首次登录后请修改密码**(v1 可手动改库或后续 v2 加修改页面)。

## 项目结构

```
.
├── backend/                 # Spring Boot 后端
│   ├── src/main/java/
│   ├── src/main/resources/
│   ├── pom.xml
│   └── Dockerfile
├── frontend/                # Vue 3 前端
│   ├── src/
│   ├── package.json
│   ├── vite.config.ts
│   ├── nginx.conf
│   └── Dockerfile
├── crawler/                 # Python 爬虫
│   ├── novel_crawler/spiders/
│   ├── scheduler.py
│   ├── dispatcher.py
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── db/
│   └── init.sql             # 数据库建表 + 初始数据
├── docs/                    # 文档
├── openspec/                # OpenSpec 规范(项目元数据)
├── docker-compose.yml
├── .env.example
└── README.md
```

## 默认调度

每天 08:00 / 14:00 / 20:00 自动抓取所有启用的站点的日榜 / 月榜 / 分类榜。
可在管理后台 → 任务管理 → 调度配置 修改。

## 文档

- [OpenSpec 提案](openspec/changes/novel-rank-platform/) - 设计 / 规范 / 任务
- [架构详解](docs/architecture.md) - 系统架构、数据流、关键技术决策
- [部署指南](docs/deployment.md) - 本地/生产部署、备份、监控、HTTPS
- [API 参考](docs/api.md) - 所有 REST 端点、请求/响应、错误码
- [二次开发指南](docs/development.md) - 加新站点/榜单/指标/功能的完整流程
- [常见问题 FAQ](docs/troubleshooting.md) - 启动/数据/性能/调试故障排查
- [测试报告](docs/testing.md) - 23 个测试文件 / 123 个测试方法
- [快速开始](docs/quickstart.md) - 一键运行指南(8 个脚本)

## 一键脚本

`scripts/` 目录提供 4 对核心脚本(.sh + .bat):

```bash
./scripts/dev.sh         # 本地运行(无 Docker)
./scripts/build.sh       # 构建 Docker 镜像
./scripts/start.sh       # 部署(Docker up)
./scripts/stop.sh        # 停止 Docker 栈
```

详细见 [scripts/README.md](scripts/README.md) 和 [docs/quickstart.md](docs/quickstart.md)。

## 开发

```bash
# 单独启动某个服务
docker compose up -d mysql      # 先起 DB
docker compose up -d backend    # 再起后端
docker compose up -d frontend   # 最后前端

# 查看实时日志
docker compose logs -f

# 停止
docker compose down

# 完全清理(含数据卷)
docker compose down -v
```

## License

MIT
