## ADDED Requirements

### Requirement: 小说详情页显示 description 简介区段
NovelDetail.vue MUST 在 info-card 下方加 el-card "简介" 区段;仅当 `novel.description` 非空时渲染;最多显示 500 字,过长折叠。

#### Scenario: description 存在
- **WHEN** GET /api/novels/1 返回 description='诡秘之主是一部...'
- **THEN** 显示 `<el-card><h3>简介</h3><p>{{ description }}</p></el-card>`,样式 .desc line-height:1.8

#### Scenario: description 为空(rich-crawler-data 还没跑)
- **WHEN** novel.description === null 或 ''
- **THEN** 不渲染该卡片(整段 el-card v-if 隐藏),不显示空状态

#### Scenario: description 超 500 字折叠
- **WHEN** 简介超过 500 字
- **THEN** 默认显示前 500 + "展开全部" 按钮;点击后显示完整;折叠时省略号结尾

### Requirement: 小说详情页显示 tags chips
NovelDetail.vue MUST 在 info-card 同行 meta 中显示 tags chips(从 `novel.tags` 字符串按 `,` split);chips 用 el-tag effect="plain" + 不同颜色循环。

#### Scenario: tags 字符串解析
- **WHEN** novel.tags = "穿越,蒸汽朋克,西幻,克苏鲁,无限流"
- **THEN** 渲染 5 个 el-tag,每个 tag 显示一个分类

#### Scenario: tags 为空
- **WHEN** novel.tags === null 或 ''
- **THEN** 不渲染 chips 区域

#### Scenario: 单个 tag 颜色循环
- **WHEN** 多个 tag
- **THEN** 颜色按 `['primary', 'success', 'warning', 'info', 'danger']` 循环,提升视觉差异

### Requirement: 详情页 trends 卡片加 description 来源行
info-card meta 区 MUST 在已有 "跳转原文" 链接前加 `<el-link v-if="novel.novelUrl">跳转原文 ↗</el-link>` 链到原文;**无修改**(已存在,只是确认)。

#### Scenario: 链接存在
- **WHEN** novel.novelUrl 非空
- **THEN** 显示 el-link 链到该 URL,target=_blank
