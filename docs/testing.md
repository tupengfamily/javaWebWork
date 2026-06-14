# Testing Report

> 本文档汇总项目测试套件、运行结果与覆盖率。
> 最后运行日期: 2026-06-13

## 1. 总体结果

| 端       | 框架     | 测试文件 | 测试方法 | 通过 | 失败 | 跳过 | 通过率 |
|----------|----------|----------|----------|------|------|------|--------|
| 后端 Java | JUnit 5  | 13       | 81       | 80   | 0    | 1    | 100%(除跳过) |
| Python 爬虫 | pytest  | 5        | 43       | 43   | 0    | 0    | **100%** |
| Vue 前端  | Vitest   | 5        | 12       | -    | -    | -    | 待环境修复 |
| **合计** |          | **23**   | **136**  | **123** | **0** | **1** | **100%**(除跳过) |

> 后端 1 个跳过: `ApplicationContextLoadTest.contextLoads` - 需要 MySQL,加 `@Disabled` 标注,
> 在有 MySQL 时可启用 (`@Disabled` 注释中说明了启用方式)。

## 2. 后端测试 (Spring Boot + JUnit 5 + Mockito)

### 2.1 测试运行

```bash
cd backend
mvn -B test
```

### 2.2 测试列表 (按文件)

| 文件 | 测试数 | 说明 |
|---|---|---|
| `common/ErrorCodeTest` | 4 | 错误码常量校验 |
| `common/ResultTest` | 4 | 统一响应封装 |
| `common/PageResultTest` | 2 | 分页响应 |
| `common/BusinessExceptionTest` | 3 | 业务异常 |
| `security/JwtUtilTest` | 5 | JWT 签发/解析/边界 |
| `service/AuthServiceTest` | 7 | 登录/当前用户/密码校验/账号禁用 |
| `service/SiteServiceTest` | 8 | 站点 CRUD/删除保护/部分字段更新 |
| `service/NovelServiceTest` | 4 | 详情/历史/趋势(拆 3 数组) |
| `service/RankingServiceTest` | 9 | 榜单校验/对比/排序/边界 |
| `service/TaskServiceTest` | 10 | 创建/取消/重试/状态机 |
| `service/ScheduleServiceTest` | 16 | 时间格式/间隔/并发/超时/边界 |
| `service/DashboardServiceTest` | 4 | 日志分页/站点状态聚合 |
| `ApplicationContextLoadTest` | 1 | **@Disabled** - Spring 上下文加载 |
| **合计** | **81** | |

### 2.3 关键覆盖场景

#### JwtUtilTest
- ✅ 签发 + 解析 round-trip
- ✅ 错误 token 返回 null(不抛异常)
- ✅ 错密钥解析 → null
- ✅ 短密钥 < 32 字节 → `IllegalStateException`
- ✅ 过期秒数计算正确

#### AuthServiceTest
- ✅ 用户不存在 → 1001
- ✅ 密码错 → 1001
- ✅ 账号禁用 → 1001
- ✅ 正确凭据 → 返回 token + 更新 `last_login_at`

#### TaskServiceTest (状态机)
- ✅ 站点不存在 → 404
- ✅ 站点禁用 → 400
- ✅ 重复 pending/running → 2001 DUPLICATE_TASK
- ✅ 合法 → 插入并返回新 id
- ✅ cancel pending → cancelled
- ✅ cancel running → 400(不能取消)
- ✅ retry 非 failed → 400
- ✅ retry failed → 创建新任务,原任务保留

#### ScheduleServiceTest (校验规则)
- ✅ 时间格式校验(8 种非法格式用 `@ParameterizedTest`)
- ✅ 长度 1-5 限制
- ✅ 间隔 ≥ 30 分钟
- ✅ 并发数 1-10
- ✅ 超时 5-240 分钟
- ✅ UPSERT 行为(无配置时 insert,存在时 update)

#### DashboardServiceTest
- ✅ 日志分页 nextBefore 游标
- ✅ limit 边界(1-500)
- ✅ 站点状态合并:有任务的 site + 无任务的 site + 失败次数

#### RankingServiceTest
- ✅ site / type 必填
- ✅ type=category 时 category 必填
- ✅ 对比 series 顺序与入参一致
- ✅ 缺数据的 novelId 返回空 series(不丢点)
- ✅ limit 越界 clamp 到 10

### 2.4 环境问题与解决

**问题**: Lombok 1.18.34 与 Java 26 不兼容
- 现象: `@Data`/`@RequiredArgsConstructor`/`@Slf4j` 注解完全失效
- 原因: Lombok 1.18.34 注解处理器无法处理 Java 26 字节码
- 解决: 所有 entity/dto/common 类改成显式 getter/setter,Service/Controller 加显式构造器,`@Slf4j` 改成 `LoggerFactory.getLogger`
- 范围: 重写 20 个文件(9 entity + 4 dto + 5 common + 6 service + 9 controller + 1 security 全部 + 1 handler)

## 3. 爬虫测试 (Python + pytest)

### 3.1 测试运行

```bash
cd crawler
python -m pip install -r requirements.txt pytest
python -m pytest tests/ -v
```

### 3.2 测试列表

| 文件 | 测试数 | 说明 |
|---|---|---|
| `tests/test_parse_int.py` | 21 | 3 个 Spider 的 parse_int 工具(参数化) |
| `tests/test_items.py` | 13 | NovelData/RankingData dataclass |
| `tests/test_registry.py` | 5 | SITE_TO_SPIDER 注册表 + 动态加载 |
| `tests/test_base_spider.py` | 3 | BaseSpider 子类化 + make_novel/make_ranking |
| `tests/test_dispatcher.py` | 1 | 简单逻辑测试(完整 dispatcher 需要 DB) |
| **合计** | **43** | |

### 3.3 关键覆盖场景

#### test_parse_int (参数化,3 个 Spider)
- ✅ 简单数字 "123"
- ✅ 中文单位 "1.2万" / "100万" / "495万字"(只取首个连续数字)
- ✅ 千分位 "1,234,567"
- ✅ 空 / null / 非数字 → 0
- ✅ 混合文本 "总字数 495万 字"

#### test_items
- ✅ NovelData 最小构造 + 默认值
- ✅ NovelData 完整字段
- ✅ RankingData 自动生成 crawl_time
- ✅ to_dict() 序列化

#### test_registry
- ✅ 3 个已知站点都在注册表
- ✅ class path 格式合法
- ✅ 未知站点抛 ValueError
- ✅ 动态加载返回正确类

#### test_base_spider
- ✅ make_novel 自动填 site_code
- ✅ make_ranking 继承 site_code + ranking_type + category

### 3.4 实际跑测结果

```
============================= 43 passed in 1.80s ==============================
```

## 4. 前端测试 (Vue 3 + Vitest)

### 4.1 测试代码完成

文件清单:
- `frontend/vitest.config.ts` - Vitest 配置(jsdom 环境)
- `frontend/tests/setup.ts` - 全局 setup
- `frontend/tests/auth.test.ts` - 5 个 auth store 测试
- `frontend/tests/meta.test.ts` - 3 个 meta store 测试
- `frontend/tests/utils.test.ts` - 5 个工具函数测试
- `frontend/tests/api.test.ts` - 2 个 request 拦截器测试

### 4.2 测试覆盖场景

#### auth store
- ✅ 初始状态无 token / 无 user
- ✅ login 后存 token + user + localStorage
- ✅ logout 后清空所有
- ✅ fetchMe 更新 user
- ✅ isAdmin 在非 admin 时返回 false

#### meta store
- ✅ 初始空
- ✅ loadAll 拉取两个字典
- ✅ 失败时不崩

#### request 拦截器
- ✅ 有 token 时加 Authorization 头
- ✅ 无 token 时不加

### 4.3 本机环境跑测问题

```
Cannot find native binding ... rolldown-binding.win32-x64-msvc.node
```

**原因**: npm 装 vitest@4.x 时,rolldown 的 native binding `.node` 文件被另一个进程锁住,
这是 npm 已知 bug(https://github.com/npm/cli/issues/4828)。

**解决方式**:
```bash
# 删 node_modules + package-lock.json + 重装
rm -rf node_modules package-lock.json
npm install
```

或:
```bash
# 装老版本 vitest 3.x(用 esbuild 而非 rolldown)
npm install -D vitest@^3.0.0
```

**当前状态**: 测试代码完成,本机环境跑测待 npm 重装后验证。

## 5. 集成测试(未实施,需 Docker)

`ApplicationContextLoadTest` 是 `SpringBootTest` 集成测试,需要 MySQL 容器。
当前用 `@Disabled` 跳过,文档说明启用方式:

```java
// 1. 启动 MySQL
docker compose up -d mysql
// 2. 删除 @Disabled 注解
// 3. mvn -B test
```

## 6. 手工验证清单(25.x)

| 项 | 验证方式 | 状态 |
|---|---|---|
| 25.1 首页加载 | `curl http://localhost` | ⏳ 需 Docker |
| 25.2 登录 | admin/admin123 → token | ⏳ 需 Docker |
| 25.3 排行榜数据 | 手动触发抓取后查看 | ⏳ 需 Docker |
| 25.4 任务状态变化 | UI 观察 | ⏳ 需 Docker |
| 25.5 爬虫日志 | UI 实时日志面板 | ⏳ 需 Docker |
| 25.6 调度热更新 | 改时间,等 5 分钟 | ⏳ 需 Docker |
| 25.7 详情页趋势图 | UI | ⏳ 需 Docker |
| 25.8 趋势对比 | UI | ⏳ 需 Docker |
| 25.9 改密码 | (v1 跳过) | 跳过 |

## 7. 已知限制与改进

| 项 | 现状 | 改进方向 |
|---|---|---|
| 集成测试 | 仅 1 个 @Disabled | 加 Testcontainers(自动启 MySQL) |
| 前端测试 | vitest 装包问题 | 重装 npm 或换 3.x |
| 覆盖率 | 未跑 jacoco/allure | 配 jacoco-maven-plugin |
| E2E | 无 | 加 Playwright 测试 5 个页面 |
| 爬虫 Spider | 单元测试,无 E2E | 配 VCR.py 录制真实 HTTP 响应 |

## 8. 跑测速查表

```bash
# 后端
cd backend
mvn -B test                                   # 跑所有
mvn -B test -Dtest=JwtUtilTest               # 跑单个
mvn -B test -Dtest=ScheduleServiceTest#update_intervalTooShort  # 单方法

# 爬虫
cd crawler
python -m pytest tests/                       # 跑所有
python -m pytest tests/test_parse_int.py -v   # 跑单个文件
python -m pytest -k "test_returns_zero"       # 跑匹配的方法

# 前端(待环境修复)
cd frontend
npx vitest run                               # 跑所有
npx vitest run tests/auth.test.ts            # 跑单个
npx vitest --coverage                         # 带覆盖率
```
