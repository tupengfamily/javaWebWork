# API 完整参考

> 本文档列出所有 REST API 端点。
> Base URL: `http://localhost:8080/api`
> 鉴权: 除标注"公开"外,管理员接口需 `Authorization: Bearer <token>` 头

## 通用约定

### 响应结构

```json
{
  "code": 0,
  "message": "ok",
  "data": <object | array | null>
}
```

### 错误码

| code | 含义 | HTTP 状态 |
|---|---|---|
| 0 | 成功 | 200 |
| 400 | 参数错误 | 400 |
| 401 | 未登录 | 401 |
| 403 | 无权限 | 403 |
| 404 | 资源不存在 | 404 |
| 500 | 服务器异常 | 500 |
| 1001 | 用户名或密码错误 | 401 |
| 1002 | token 已过期 | 401 |
| 2001 | 任务已存在 | 409 |
| 2002 | 时间格式错误 | 400 |

### 分页响应

```json
{
  "code": 0,
  "data": {
    "records": [...],
    "total": 234,
    "pageNum": 1,
    "pageSize": 20,
    "pages": 12
  }
}
```

---

## 1. 鉴权 `/auth`

### 1.1 登录

```
POST /api/auth/login                    [公开]
```

请求:
```json
{ "username": "admin", "password": "admin123" }
```

响应:
```json
{
  "code": 0,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiJ9...",
    "expiresIn": 86400,
    "user": { "id": 1, "username": "admin", "role": "admin" }
  }
}
```

### 1.2 退出

```
POST /api/auth/logout                   [公开]
```

响应: `{ "code": 0, "data": null }`
注: 无状态,前端清 token 即可。

### 1.3 当前用户

```
GET  /api/auth/me                       [需 token,非管理也可用]
```

响应:
```json
{ "code": 0, "data": { "id": 1, "username": "admin", "role": "admin" } }
```

---

## 2. 站点 `/sites`

### 2.1 公开列表

```
GET  /api/sites                         [公开]
```

响应:
```json
{
  "code": 0,
  "data": [
    { "id": 1, "code": "qidian", "name": "起点中文网", "color": "#E72E2C",
      "sortOrder": 1, "baseUrl": "...", "spiderClass": "...",
      "enabled": true, "createdAt": "...", "updatedAt": "..." }
  ]
}
```

### 2.2 管理员分页

```
GET  /api/admin/sites?pageNum=1&pageSize=20    [需 admin]
```

### 2.3 创建

```
POST /api/admin/sites                   [需 admin]
```

请求:
```json
{ "code": "xxx", "name": "XXX 小说", "baseUrl": "https://xxx.com",
  "spiderClass": "novel_crawler.spiders.xxx.XxxSpider",
  "color": "#00CC99", "sortOrder": 4, "enabled": true }
```

### 2.4 更新

```
PUT  /api/admin/sites/{id}              [需 admin]
```
(只更新提供的字段)

### 2.5 删除

```
DELETE /api/admin/sites/{id}            [需 admin]
```
若有关联 novel / ranking_record,返回 400。

---

## 3. 排行榜 `/rankings`

### 3.1 最新榜单

```
GET  /api/rankings?site=qidian&type=daily&category=&keyword=&pageNum=1&pageSize=20  [公开]
```

| 参数 | 必填 | 说明 |
|---|---|---|
| site | 是 | 站点 code |
| type | 是 | daily / monthly / category |
| category | type=category 时必填 | 中文分类名 |
| keyword | 否 | 模糊匹配书名/作者 |
| pageNum | 否 | 默认 1 |
| pageSize | 否 | 默认 20,最大 100 |

响应:
```json
{
  "code": 0,
  "data": {
    "records": [
      { "rank": 1, "novelId": 123, "title": "大主宰", "author": "天蚕土豆",
        "category": "玄幻", "coverUrl": "...", "novelUrl": "...",
        "viewCount": 120000000, "recCount": 356000, "wordCount": 4950000,
        "status": "ongoing", "crawlTime": "2026-06-13T20:00:00" }
    ],
    "total": 200, "pageNum": 1, "pageSize": 20, "pages": 10
  }
}
```

---

## 4. 小说 `/novels`

### 4.1 详情

```
GET  /api/novels/{id}                   [公开]
```

响应: 小说详情 + 站点信息(`siteCode` / `siteName`)。

### 4.2 历史快照

```
GET  /api/novels/{id}/records?type=daily&startTime=&endTime=&pageNum=1&pageSize=20  [公开]
```

### 4.3 趋势(给 ECharts)

```
GET  /api/novels/{id}/trend?type=daily&days=30   [公开]
```

响应:
```json
{
  "code": 0,
  "data": {
    "ranking":   [{ "time": "06-01 08:00", "value": 5 }, ...],
    "viewCount": [{ "time": "06-01 08:00", "value": 118000000 }, ...],
    "recCount":  [{ "time": "06-01 08:00", "value": 350000 }, ...]
  }
}
```

---

## 5. 趋势分析 `/trends`

### 5.1 多小说对比

```
GET  /api/trends/compare?novelIds=1,2,3&metric=viewCount&days=7   [公开]
```

| 参数 | 必填 | 说明 |
|---|---|---|
| novelIds | 是 | 1-5 个 id,逗号分隔 |
| metric | 是 | rank / viewCount / recCount |
| days | 否 | 默认 7,最大 90 |

响应:
```json
{
  "code": 0,
  "data": {
    "metric": "viewCount",
    "series": [
      { "novelId": 1, "title": "大主宰", "siteCode": "qidian", "color": "#E72E2C",
        "points": [{ "time": "06-07", "value": 118000000 }, ...] }
    ]
  }
}
```

### 5.2 跨站 TOP

```
GET  /api/trends/top?limit=10&by=viewCount&category=    [公开]
```

响应: 跨站点按 viewCount 排序的最新一次日榜 TOP N。

---

## 6. 元数据 `/meta`

### 6.1 榜单类型

```
GET  /api/meta/ranking-types            [公开]
```

响应: `[{ code: "daily", name: "日榜", description: "..." }, ...]`

### 6.2 分类

```
GET  /api/meta/categories               [公开]
```

响应: `["玄幻", "都市", "仙侠", ...]`

---

## 7. 任务管理 `/admin/tasks`(全部需 admin)

### 7.1 任务列表

```
GET  /api/admin/tasks?status=&site=&triggerType=&startTime=&endTime=&pageNum=1&pageSize=20
```

| 参数 | 说明 |
|---|---|
| status | pending / running / success / failed / cancelled |
| site | 站点 code |
| triggerType | manual / scheduled |
| startTime | 创建时间起点,ISO-8601 |
| endTime | 创建时间终点,ISO-8601 |

每条含:
```json
{
  "id": 1001, "siteCode": "qidian", "siteName": "起点",
  "rankingType": "daily", "category": null,
  "triggerType": "scheduled", "status": "success",
  "progress": 100, "fetchedCount": 1240,
  "errorMessage": null, "createdBy": null,
  "createdAt": "2026-06-13T20:00:00",
  "startedAt": "2026-06-13T20:00:01",
  "finishedAt": "2026-06-13T20:08:32",
  "durationMs": 511000
}
```

### 7.2 手动触发

```
POST /api/admin/tasks
```

请求:
```json
{ "siteCode": "qidian", "rankingType": "daily", "category": null }
```

响应: `{ "code": 0, "data": { "taskId": 1002 } }`

**错误码 2001**: 同站点同榜单已有 pending/running。

### 7.3 取消

```
POST /api/admin/tasks/{id}/cancel
```
仅 pending 可取消。running 返回 400。

### 7.4 重试

```
POST /api/admin/tasks/{id}/retry
```
仅 failed 可重试。返回新 taskId。

### 7.5 任务日志

```
GET  /api/admin/tasks/{id}/log
```

响应:
```json
{
  "code": 0,
  "data": {
    "task": { ...任务信息... },
    "logs": [
      { "time": "2026-06-13T20:00:01", "level": "INFO", "message": "..." }
    ]
  }
}
```

---

## 8. 调度配置 `/admin/schedule`(全部需 admin)

### 8.1 获取

```
GET  /api/admin/schedule
```

响应:
```json
{
  "code": 0,
  "data": {
    "dailyCrawlTimes": ["08:00", "14:00", "20:00"],
    "maxConcurrentTasks": 2,
    "taskTimeoutMinutes": 30,
    "crawlAllRankingTypes": ["daily", "monthly", "category"],
    "updatedAt": "2026-06-13T10:00:00"
  }
}
```

### 8.2 更新

```
PUT  /api/admin/schedule
```

请求:
```json
{
  "dailyCrawlTimes": ["09:00", "15:00", "21:00"],
  "maxConcurrentTasks": 3,
  "taskTimeoutMinutes": 45,
  "crawlAllRankingTypes": ["daily", "monthly", "category"]
}
```

**校验规则**:
- `dailyCrawlTimes`: 1-5 个,每个符合 `HH:mm`,相邻间隔 ≥ 30 分钟
- `maxConcurrentTasks`: 1-10
- `taskTimeoutMinutes`: 5-240
- 不通过返回 400,错误码 2002 表示时间格式错

---

## 9. 仪表盘 `/admin/dashboard`(全部需 admin)

### 9.1 站点状态

```
GET  /api/admin/dashboard/sites
```

响应: 数组,每个站点含:
```json
{
  "siteId": 1, "siteCode": "qidian", "siteName": "起点",
  "color": "#E72E2C", "enabled": true,
  "lastTask": { "id": 1001, "status": "success",
                "finishedAt": "...", "fetchedCount": 1240 } | null,
  "novelCount": 1240,
  "recentFailureCount": 0
}
```

### 9.2 实时日志

```
GET  /api/admin/dashboard/logs?level=&site=&limit=100&before=
```

| 参数 | 说明 |
|---|---|
| level | INFO / WARN / ERROR |
| limit | 默认 100,最大 500 |
| before | 游标,只返回 log_time < before 的记录 |

响应:
```json
{
  "code": 0,
  "data": {
    "records": [
      { "time": "...", "level": "INFO", "site": "qidian", "message": "..." }
    ],
    "nextBefore": "2026-06-13T19:55:00"
  }
}
```

---

## 10. 调用示例

### 10.1 cURL

```bash
# 登录
TOKEN=$(curl -s -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.data.token')

# 触发抓取
curl -X POST http://localhost:8080/api/admin/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"siteCode":"qidian","rankingType":"daily"}'

# 查排行榜
curl "http://localhost:8080/api/rankings?site=qidian&type=daily" | jq
```

### 10.2 JavaScript (fetch)

```ts
const res = await fetch('/api/rankings?site=qidian&type=daily')
const json = await res.json()
if (json.code === 0) {
  console.log(json.data.records)
}
```

### 10.3 Python

```python
import requests

r = requests.post('http://localhost:8080/api/auth/login',
                  json={'username': 'admin', 'password': 'admin123'})
token = r.json()['data']['token']

r = requests.get('http://localhost:8080/api/rankings',
                 params={'site': 'qidian', 'type': 'daily'})
print(r.json()['data']['records'][:3])
```
