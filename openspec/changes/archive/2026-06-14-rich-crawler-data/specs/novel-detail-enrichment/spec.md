## ADDED Requirements

### Requirement: 详情页抽取 description (简介) 写入 novel 表
parse_detail MUST 从详情页抽取 100-1000 字符的简介,放入 `NovelData.description`;NovelUpsertPipeline MUST 截断到 1000 字符 + UPSERT 写入 `novel.description`。

#### Scenario: 起点详情页有 .book-intro
- **WHEN** 解析到 `<div class="book-intro">诡秘之主是一部...</div>`
- **THEN** description 字段填入截断到 1000 字符的文本

#### Scenario: 详情页无简介
- **WHEN** 多个选择器都没命中
- **THEN** description = "" (空字符串),不写入 NULL(留空兼容旧逻辑)

#### Scenario: 简介超过 1000 字符
- **WHEN** 详情页简介 2000 字
- **THEN** 入库截断到 1000,前段保留

### Requirement: 详情页抽取 tags (标签) 写入 novel 表
parse_detail MUST 从详情页的标签区抽取 2-8 个标签,逗号分隔存 `novel.tags`;标签含特殊字符 / emoji 时 MUST 用 regex `\W` 过滤空标签。

#### Scenario: 起点有 5 个标签
- **WHEN** 解析到 `<a class="tags">穿越</a><a class="tags">蒸汽朋克</a>...`
- **THEN** tags = "穿越,蒸汽朋克,西幻,克苏鲁,无限流" (按页面顺序,逗号分隔)

#### Scenario: 标签含 emoji
- **WHEN** 解析到 "🔥 玄幻 🔥 穿越"
- **THEN** 入库前正则过滤 → "玄幻,穿越"

#### Scenario: 标签 < 2 个
- **WHEN** 详情页只有 1 个标签
- **THEN** 仍写入(不强求 2+);空则存 NULL

### Requirement: 后端 NovelVO 接口透出 description / tags
`GET /api/novels/{id}` MUST 返回 `description` 和 `tags` 字段(后端 `NovelVO` 透出),与现有 `title` / `author` 等字段并列。

#### Scenario: 接口返回 description
- **WHEN** GET /api/novels/1
- **THEN** JSON 包含 `description: "诡秘之主是一部..."` (若 DB 有值)

#### Scenario: tags 字段返回
- **WHEN** GET /api/novels/1
- **THEN** JSON 包含 `tags: "穿越,蒸汽朋克,西幻,克苏鲁,无限流"`(逗号分隔,前端 split 为数组)

#### Scenario: 旧数据没 description
- **WHEN** novel.description IS NULL
- **THEN** JSON 返回 `description: null`,不抛错

### Requirement: novel 表新增 tags 列
`db/init.sql` MUST 给 `novel` 表加 `tags VARCHAR(1024) DEFAULT NULL` 列;migration 脚本 MUST `ALTER TABLE novel ADD COLUMN tags VARCHAR(1024) DEFAULT NULL`。

#### Scenario: 新部署
- **WHEN** 用 init.sql 建库
- **THEN** novel 表 11 列,含 tags

#### Scenario: 旧库升级
- **WHEN** 对已有 novel 表执行 ALTER
- **THEN** 成功加列,旧数据 tags 默认为 NULL,无破坏
