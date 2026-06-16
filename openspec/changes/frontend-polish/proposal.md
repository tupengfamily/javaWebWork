## Why

当前 4 个页面 ([Rankings.vue](../../frontend/src/views/Rankings.vue) / [NovelDetail.vue](../../frontend/src/views/NovelDetail.vue) / [Trends.vue](../../frontend/src/views/Trends.vue) / [Tasks.vue](../../frontend/src/views/admin/Tasks.vue)) 实现"能用",但视觉密度与交互效率与同类产品(七猫/起点数据)有差距:

- 排行榜表格无封面缩略图、缺站点色 tag、pageSize 写死 20、不能按浏览量排序、缺分类快捷筛选
- 详情页缺 description 简介(后端字段已存但未读)、缺 tags chips
- 趋势页默认 novelIds 写死 "1",站点/分类过滤缺失,TOP10 只按 viewCount 一个 tab
- 任务页运行中任务无视觉高亮,实时日志无自动滚动

而且伴随 `rich-crawler-data` change 即将注入 description / tags / 更多榜单数据,前端必须**同步升级**才能让数据可见。

需要做一轮专注前端的视觉与交互优化。

## What Changes

### Rankings.vue (排行榜)

- **A1** 表格加封面缩略图(60×80)+ 站点色 tag(用 `site.color` 字段)
- **A2** pageSize 可选 `20 / 50 / 100`,默认 50,`el-pagination` layout 加 `sizes` 选项
- **A3** 表格列可排序:`rank` 升序 / `viewCount` 降序 / `recCount` 降序,点表头切换
- **A4** 分类快捷 chip(玄幻/都市/... 一键过滤,顶部一行 el-tag)
- **A14** 视图模式切换:列表 / 卡片(图墙),右上角 el-radio-button

### NovelDetail.vue (小说详情)

- **A5** 显示 `description` 简介区段(在 info-card 下方新增 el-card)
- **A6** 显示 `tags` chips(把 novel.tags 字符串按逗号 split 后用 el-tag 渲染,带颜色)

### Trends.vue (趋势分析)

- **A7** 页面加载时自动从 `/api/trends/top` 拉 TOP5,自动填入 novelIds 输入框
- **A8** 站点 / 分类两个新 el-select 过滤
- **A9** "跨站 TOP 10" 三个 tab 切换:`浏览量` / `推荐数` / `排名`,调用 `topList({by: 'viewCount' | 'recCount' | 'rank'})`

### Tasks.vue (任务管理)

- **A10** 运行中任务 `running` 状态卡片化高亮(el-tag type='warning' + 黄色边框),日志流自动滚到底部

### 全局

- **A12** 暗黑模式 toggle(右上角月亮/太阳图标),localStorage 持久化,CSS 变量切换

## Capabilities

### New Capabilities

- `rankings-table-enrichment`: 排行榜表格封面/站点/排序/分页/chip/卡片视图 6 项
- `novel-detail-display`: 详情页显示 description 简介区段 + tags chips
- `trends-page-enhancement`: 趋势页默认 top 5 + 站点/分类过滤 + TOP10 三 tab
- `tasks-page-highlight`: 任务页运行中任务高亮 + 日志自动滚动
- `global-dark-mode`: 全局暗黑模式 toggle,localStorage 持久化

### Modified Capabilities

无(纯前端增强,不动后端 spec)。

## Impact

| 文件 | 类型 |
|---|---|
| `frontend/src/views/Rankings.vue` | 大改 (6 项) |
| `frontend/src/views/NovelDetail.vue` | 中改 (2 项) |
| `frontend/src/views/Trends.vue` | 中改 (3 项) |
| `frontend/src/views/admin/Tasks.vue` | 小改 (1 项) |
| `frontend/src/layouts/MainLayout.vue` | 小改 (加暗黑模式按钮) |
| `frontend/src/styles/dark.css` (新) | 暗黑模式 CSS 变量 |
| `frontend/src/main.ts` | 引入 dark.css / 暗黑模式初始化 |
| `frontend/src/api/novels.ts` | `NovelVO` 加 `description` / `tags` 字段类型(运行时由后端透出) |
| `frontend/src/api/rankings.ts` | (无需改,后端已支持) |
| `frontend/src/api/sites.ts` | `SiteVO` 加 `color` 字段类型(后端已返回) |
| `frontend/src/stores/darkMode.ts` (新) | Pinia store 持久化 toggle |

**不动的文件**:
- 路由 / Pinia auth/meta / utils/request / 单元测试
- 后端代码(无新增接口,后端只补字段已在 `rich-crawler-data` 处理)

**兼容性**:
- 暗黑模式默认关闭,旧用户无感
- 表格排序 / 卡片视图默认与现行为一致(列表 + 默认按 rank)
- 任何 description / tags 字段缺失时 UI 优雅降级(不显示对应区段)
- 仅在前端 changelog 提醒,无需后端配合

**风险**:
- ECharts 在暗黑模式下的颜色配置:需为 chart option 加 `darkMode` 分支
- 卡片视图(60+ 卡片)性能:虚拟滚动或限制分页到 20,否则浏览器卡
- Element Plus 暗黑模式:依赖 `el-config-provider` 的 `:theme` 或 CSS 变量覆盖(选后者,改动小)

## Dependencies

- **`rich-crawler-data` change 先完成** — description / tags 数据可看,封面列也对得上数据
- 之后无依赖,可独立运行

## Out of Scope

- 响应式布局(A11 推迟)
- header 全局搜索(A13 推迟)
- 详情页相关推荐侧栏(A15 — 需新接口,本 change 不加接口)
- ECharts 主题色(留作 P2)
