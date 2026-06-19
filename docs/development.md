# 二次开发指南

> 本文档面向需要修改/扩展本项目的开发者。

## 1. 开发环境搭建

### 1.1 本地开发(不用 Docker)

适合快速调试某个模块。

**MySQL**:
```bash
docker run -d --name novel-mysql -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=root123 \
  -e MYSQL_DATABASE=novel_rank \
  -e MYSQL_USER=novel -e MYSQL_PASSWORD=novel123 \
  -v $PWD/db/init.sql:/docker-entrypoint-initdb.d/01-init.sql:ro \
  mysql:8.0
```

**后端** (用 IDE 直接 Run `NovelRankApplication`):
- IDE 装 Spring Boot 插件
- `application.yml` 默认读 `application-dev.yml`,连 localhost:3306

**前端**:
```bash
cd frontend
npm install
npm run dev    # http://localhost:5173,自动代理 /api 到 8080
```

**爬虫**:
```bash
cd crawler
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### 1.2 Docker 开发

```bash
docker compose up -d --build
# 改代码后:
docker compose up -d --build backend
```

## 2. 加新站点(完整流程)

以"加一个新小说网站 `xxx-novel`"为例。

### 2.1 在 `site` 表注册

```sql
INSERT INTO site (code, name, base_url, spider_class, color, sort_order) VALUES
('xxx', 'XXX 小说', 'https://www.xxx.com', 'novel_crawler.spiders.xxx.XxxSpider', '#00CC99', 4);
```

### 2.2 创建 Spider

```python
# crawler/novel_crawler/spiders/xxx.py
import re
import scrapy
from .base import BaseSpider


def parse_int(s):
    if not s: return 0
    m = re.search(r"\d+", s.replace(",", ""))
    return int(m.group()) if m else 0


class XxxSpider(BaseSpider):
    site_code = "xxx"
    name = "xxx"

    custom_settings = {
        "DOWNLOAD_DELAY": 1.0,    # 根据反爬调整
    }

    def start_requests(self):
        # 实际 URL 看站点规则
        url = f"https://www.xxx.com/rank/{self.ranking_type}"
        yield scrapy.Request(url, callback=self.parse, dont_filter=True)

    def parse(self, response):
        # 用浏览器 DevTools 查看真实选择器
        items = response.css(".rank-item") or []
        if not items:
            self.logger.warning(f"xxx 榜单页选择器失效: {response.url}")
            return

        for idx, book in enumerate(items, start=1):
            # 抓 book_id(按站点规律)
            href = book.css("a::attr(href)").get() or ""
            m = re.search(r"/book/(\d+)", href)
            if not m: continue
            bid = m.group(1)

            title = book.css(".title::text").get() or ""
            author = book.css(".author::text").get() or ""
            view = parse_int(book.css(".view::text").get())

            yield self.make_ranking(
                novel_external_id=str(bid),
                ranking_type=self.ranking_type,
                rank=idx,
                view_count=view,
            )

            if href:
                yield response.follow(
                    href, callback=self.parse_detail,
                    meta={"external_id": str(bid), "title": title, "author": author},
                )

    def parse_detail(self, response):
        meta = response.meta
        cover = response.css(".cover img::attr(src)").get() or ""
        word = parse_int(response.css(".word::text").get() or "0")
        yield self.make_novel(
            external_id=meta["external_id"],
            title=meta.get("title", ""),
            author=meta.get("author", ""),
            cover_url=cover,
            novel_url=response.url,
            word_count=word,
        )
```

### 2.3 注册到调度表

```python
# crawler/novel_crawler/spiders/registry.py
SITE_TO_SPIDER: dict[str, str] = {
    "qidian":   "novel_crawler.spiders.qidian.QidianSpider",
    "fanqie":   "novel_crawler.spiders.fanqie.FanqieSpider",
    "zongheng": "novel_crawler.spiders.zongheng.ZonghengSpider",
    "xxx":      "novel_crawler.spiders.xxx.XxxSpider",   # ← 新增
}
```

### 2.4 重启 crawler

```bash
docker compose restart crawler
```

定时调度会自动给新站点生成 task。

## 3. 加新指标(如"收藏数")

假设要在详情页加"收藏数"趋势。

### 3.1 数据库

```sql
ALTER TABLE ranking_record ADD COLUMN fav_count INT NOT NULL DEFAULT 0 AFTER rec_count;
```

### 3.2 后端 XML(TrendMapper.xml)

```xml
<select id="selectNovelTrend" resultType="java.util.Map">
    SELECT
        DATE_FORMAT(crawl_time, '%m-%d %H:%i') AS `time`,
        `rank`, view_count AS viewCount,
        rec_count AS recCount, fav_count AS favCount
    FROM ranking_record
    WHERE novel_id = #{novelId} AND ranking_type = #{rankingType}
      AND crawl_time >= DATE_SUB(NOW(3), INTERVAL #{days} DAY)
    ORDER BY crawl_time ASC
</select>
```

### 3.3 后端 Service(NovelService)

```java
List<Map<String, Object>> fav = new ArrayList<>();
for (Map<String, Object> r : rows) {
    fav.add(point(t, ((Number) r.get("favCount")).intValue()));
}
out.put("favCount", fav);
```

### 3.4 爬虫 Pipeline

```python
# RankingInsertPipeline.process_item 增加字段
conn.execute(text("""
    INSERT INTO ranking_record
      (novel_id, site_id, ranking_type, category, `rank`,
       view_count, rec_count, fav_count, crawl_time, crawl_task_id)
    VALUES
      (:novel_id, :site_id, :ranking_type, :category, :rank,
       :view_count, :rec_count, :fav_count, :crawl_time, :task_id)
"""), {...})
```

### 3.5 前端 NovelDetail.vue

```vue
<el-col :span="12">
  <el-card><h3>收藏数趋势</h3>
    <v-chart class="chart" :option="favChartOpt" autoresize />
  </el-card>
</el-col>
```

```ts
const favChartOpt = computed(() => ({
  ...baseLineOpt.value,
  xAxis: { type: 'category', data: trend.value.favCount.map(p => p.time) },
  series: [{ name: '收藏数', type: 'line', data: trend.value.favCount.map(p => p.value) }]
}))
```

## 4. 加新榜单类型(如"完结榜")

### 4.1 数据库

```sql
INSERT INTO ranking_type (code, name, description) VALUES
('finished', '完结榜', '已完结小说的热度排行');
```

### 4.2 前端 UI 自动识别

`useMetaStore.loadAll()` 已通过 `GET /api/meta/ranking-types` 动态加载,无需改前端代码。

### 4.3 爬虫支持

`self.ranking_type` 已是动态值,爬虫需要按 `ranking_type` 拼 URL。
如果新类型有独立 URL 模板,可在 `BaseSpider` 加方法或重写 `start_requests`。

## 5. 加新管理功能(如"导出 CSV")

### 5.1 后端 Controller 加端点

```java
@GetMapping("/api/admin/export")
public void exportCSV(HttpServletResponse resp) throws IOException {
    resp.setContentType("text/csv;charset=utf-8");
    resp.setHeader("Content-Disposition", "attachment; filename=rankings.csv");
    List<Map<String, Object>> data = rankingService.listLatest("qidian", "daily", null, null, 1, 1000).getRecords();
    PrintWriter w = resp.getWriter();
    w.println("rank,title,author,viewCount,recCount");
    for (Map<String, Object> r : data) {
        w.printf("%s,%s,%s,%s,%s%n", r.get("rank"), r.get("title"), r.get("author"),
                r.get("viewCount"), r.get("recCount"));
    }
}
```

### 5.2 前端按钮

```vue
<el-button @click="exportCSV">导出 CSV</el-button>

<script>
const exportCSV = () => {
  window.open('/api/admin/export', '_blank')
}
</script>
```

## 6. 自定义错误码

在 [ErrorCode.java](../backend/src/main/java/com/novel/rank/common/ErrorCode.java) 中加枚举:

```java
EXPORT_FAILED(3001, "导出失败"),
```

## 7. 性能调优

### 7.1 SQL 索引

慢查询先用 `EXPLAIN` 分析。看 `ranking_record` 表的常用查询模式:
- 按 novel 查趋势 → `idx_novel_time` 已覆盖
- 按 type 查最新 → `idx_type_time` 已覆盖
- 按 site+type 查最新 → `idx_site_type_rank` 已覆盖

加新查询模式时,先看能否复用现有索引。

### 7.2 爬虫并发

`novel_crawler/settings.py`:
```python
CONCURRENT_REQUESTS = 8              # 默认 8,可调
CONCURRENT_REQUESTS_PER_DOMAIN = 4   # 单域名并发
DOWNLOAD_DELAY = 1.0                 # 全局延迟
```

### 7.3 后端 HikariCP

`application.yml`:
```yaml
spring:
  datasource:
    hikari:
      maximum-pool-size: 20    # 按需调整
      minimum-idle: 5
```

### 7.4 缓存热点数据

加 Spring Cache:
```java
@Cacheable(value = "rankings", key = "#site + ':' + #type")
public PageResult<Map<String, Object>> listLatest(...) {...}
```

需要先加依赖 `spring-boot-starter-data-redis` + Redis 容器。

## 8. 调试技巧

### 8.1 爬虫单独调试

```bash
cd crawler
scrapy crawl qidian -a task_id=999 -a ranking_type=daily
# 可看到实时日志,不受 Dispatcher 限制
```

### 8.2 后端热重载

`pom.xml` 加 `spring-boot-devtools`,代码改动自动重启。

### 8.3 前端 HMR

`npm run dev` 自带 HMR,改 .vue 即时刷新。

### 8.4 看爬虫写库的 SQL

`pip install sqlalchemy[logging]` + 配 engine 的 echo=True(开发环境)。

### 8.5 看 MySQL 慢查询

```sql
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1;
```

## 9. 测试

### 9.1 后端单元测试

```java
@SpringBootTest
class TaskServiceTest {
    @Autowired TaskService taskService;
    @MockBean CrawlTaskMapper taskMapper;

    @Test
    void shouldCreateTask() {
        // ...
    }
}
```

### 9.2 前端组件测试(Vitest)

```ts
import { mount } from '@vue/test-utils'
import Login from '@/views/Login.vue'

test('登录表单', async () => {
    const wrapper = mount(Login)
    await wrapper.find('input').setValue('admin')
    // ...
})
```

### 9.3 爬虫测试

```python
# tests/test_qidian.py
import pytest
from novel_crawler.spiders.qidian import parse_int

def test_parse_int():
    assert parse_int("1.2万") == 12
    assert parse_int("3,456") == 3456
    assert parse_int("") == 0
```

## 10. 发布检查清单

每次发版前:

- [ ] 跑通所有单元测试
- [ ] 改 `.env.example` 反映新配置项
- [ ] 写数据库迁移 SQL(若 schema 变)
- [ ] 更新 [OpenSpec 提案](../openspec/changes/) 的 tasks
- [ ] 写 CHANGELOG
- [ ] 在 staging 环境跑 `docker compose up -d --build` 验证
- [ ] 备份生产 DB(`mysqldump`)
- [ ] 灰度升级(可先升级 crawler 容器,观察 1 天)
- [ ] 监控 1 天看错误日志
