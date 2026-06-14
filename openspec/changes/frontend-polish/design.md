# Design — frontend-polish

## Context

**当前前端状态**(行数 / 关键组件):
- Rankings.vue (161 行): `el-table` + 4 filter(站点/类型/分类/关键字),无封面列、pageSize 写死 20、不能排序
- NovelDetail.vue (157 行): 卡片+ 2 张 ECharts + 历史表,**无 description 区段、无 tags chips**
- Trends.vue (109 行): 默认 `novelIdsInput = '1'`,**只支持 viewCount 单 tab**,无站点/分类过滤
- Tasks.vue (314 行): 站点卡片 + 调度表单 + 任务表 + 日志流,无运行中任务高亮

**后端已具备但前端没用上**:
- `novel.coverUrl` — Rankings 表格没显示封面
- `site.color` — Rankings 表格没显示站点色
- `novel.description` — 后端 SELECT 还没包含(`rich-crawler-data` 才补)
- `novel.tags` — DB 列还没加(`rich-crawler-data` 才加)
- `/api/trends/top?by=recCount|rank` — Trends.vue 没用

**Element Plus 暗黑模式**:
- v2.5+ 支持 `el-config-provider` 的 `:theme` 注入(`dark` / `light`)
- 或 CSS 变量覆盖(本项目倾向后者,因为改动小,不必改 el-config)

**约束**:
- 4 个页面文件已存在,优先**改而不重建**
- 不动后端任何代码(用户已定)
- 暗黑模式默认关闭,旧用户无感
- 不引入新依赖(图表继续用 ECharts,UI 继续用 Element Plus)
- 必须**先等** `rich-crawler-data` 完成(否则 description/tags 列空,UI 看着假)

## Goals / Non-Goals

**Goals:**
- Rankings 表格:封面 + 站点色 + 排序 + pageSize 切换 + 分类 chip + 卡片视图
- NovelDetail:description 简介区段 + tags chips
- Trends:自动 top 5 + 站点/分类过滤 + 3 tab
- Tasks:运行中高亮 + 日志自动滚
- 全局:暗黑模式 toggle(右上角)

**Non-Goals:**
- 响应式布局(平板/手机)— 推迟
- header 全局搜索栏 — 推迟
- 详情页"同作者/同分类"侧栏 — 需新接口,本 change 不加
- ECharts 主题色定制 — 用 Element Plus 暗黑模式默认即可
- 拖拽列 / 列宽记忆 — 推迟

## Decisions

### 决策 1: 暗黑模式实现路径

**Element Plus 暗黑模式**两种实现:
- ❌ `:theme="dark"` 全局主题切换:侵入大,需 root 注入 `el-config-provider`
- ✅ **CSS 变量覆盖**:`html.dark` 下覆盖 Element Plus CSS 变量与本站点自定义颜色

**做法**:
- 新建 `frontend/src/styles/dark.css`,定义 `[data-theme="dark"]` 下的颜色变量
- Element Plus 暗黑:`html[data-theme="dark"]` → Element Plus 自带 dark tokens
- Pinia store 持久化(`localStorage.theme`),main.ts 启动时根据值给 `<html>` 加 `data-theme` 属性
- 切换按钮:MainLayout.vue 右上角,月亮/太阳图标 (el-icon Moon / Sunny)

**Alternatives considered**:
- ❌ 全量 ECharts darkMode:true:每个 chart 都要改 option
- ❌ VueUse `useDark` 库:额外依赖
- ✅ **CSS 变量 + localStorage**:0 新依赖,改动小

### 决策 2: 卡片视图性能

**问题**: 切到卡片视图时若有 60+ 卡片,DOM 节点会爆

**做法**:
- 卡片视图**强制 pageSize=20**(超过自动截断),与表格分页器复用 `filters.pageSize`
- 卡片用 `el-col :span="6"` (xl) / `:span="8"` (md) / `:span="12"` (sm) 响应式栅格
- 卡片本身是 el-card,无虚拟滚动(20 张足够,再多滚去下一页)

### 决策 3: 排序实现

Element Plus 表格列加 `sortable="custom"` 触发 `sort-change` 事件,前端**不重排序**(因为后端有 ORDER BY),而是**把 sortField + sortOrder 传给后端**。

**做法**:
- Rankings.vue 监听 `@sort-change`,参数传给 `listRankings({ sortField, sortOrder })`
- `frontend/src/api/rankings.ts` 的 `listRankings` 接受可选 `sortField / sortOrder` 参数
- 后端是否支持? — **RangkingRecordMapper.xml 已支持 ORDER BY rank**,新加 ORDER BY view_count 时需要改 mapper

**简化**: 本次 change 只在**前端 UI 切换**,不真传后端。后端排序由 URL 改 → 加 mapper 支持分两步:
- 任务 T1(本 change):前端加 UI + 类型 + 默认按 rank
- 任务 T2(可选后端任务):mapper 加 ORDER BY 动态

> 为不引入后端依赖,本 change 排序只切换"默认排序"或"前端 sort 按钮触发后端请求",后端暂只支持 rank(viewCount/recCount 排序留 v2)。

### 决策 4: 趋势页 top 5 自动填入

**做法**:
```ts
onMounted(async () => {
  topListData.value = await topList({ limit: 10, by: 'viewCount' })
  // 自动填前 5 个 id 到输入框
  novelIdsInput.value = topListData.value.slice(0, 5).map(n => n.novelId).join(',')
  await onCompare()  // 立即对比
})
```

**注意**: `topList` 之前没 `novelId` 字段 — 需确认;若没有,先从 rankings API 拉或加 `novelId` 字段(后端已在返回的 Map 里,可能没显式列)。

### 决策 5: description / tags 缺失优雅降级

**做法**:
```vue
<el-card v-if="novel.description">
  <h3>简介</h3>
  <p class="desc">{{ novel.description }}</p>
</el-card>
```

`novel.description === null` 或 `''` 时**不渲染该卡片**,不显示"暂无简介"。

tags 同样:`v-if="novel.tags"` 才渲染 chips,内部按 `,` split + filter(Boolean)。

### 决策 6: 任务页运行中高亮

**做法**:
```ts
const rowClass = (row) => row.status === 'running' ? 'running-row' : ''
```
el-table `:row-class-name="rowClass"`,CSS:
```css
.el-table .running-row { background: #fdf6ec; }
[data-theme="dark"] .el-table .running-row { background: #2d2a22; }
```

**自动滚到底**: log-stream ref 监听 `logs.length` 变化,新日志来时 `el.scrollTop = el.scrollHeight`。

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| Element Plus 暗黑模式下部分组件颜色不自动切换 | 查 EP 文档加 `--el-bg-color` `--el-text-color-primary` 等覆盖 |
| 卡片视图 60 张图同时加载 | 强制 pageSize=20;`el-image` lazy 加载 |
| 排序传后端但后端不支持 → 看起来"点了无反应" | 本次先在前端 sort 状态切换,日志说明;后端排序 v2 |
| description 字段首次为空(rich-crawler-data 还没跑) | UI 优雅降级,不显示区段 |
| tags 字段首次为空(同上) | 同上 |
| 暗黑模式切换时 ECharts 图表颜色不变 | 在 chart option 加 `textStyle.color` 根据 `useDarkModeStore().isDark` 切换 |
| Tasks.vue 日志自动滚到用户正在看的位置 | 加 "新消息" 提示按钮,用户主动决定跳不跳(避免打扰) |
| 表格排序 sort change 事件名变 | 固定用 Element Plus 文档约定的 `prop` + `sortable="custom"` |
| 大量 el-image 请求阻塞 | 给 coverUrl 缺省 placeholder `/logo.png` |

## Migration Plan

**纯前端**,无后端 / DB 改动。

1. 改 `frontend/src/api/novels.ts` 加 `description` / `tags` 字段(类型层) — 不影响运行
2. 改 `frontend/src/api/rankings.ts` 加 `sortField / sortOrder` 可选参数
3. 改 Rankings.vue / NovelDetail.vue / Trends.vue / Tasks.vue / MainLayout.vue
4. 新建 `frontend/src/styles/dark.css` + `frontend/src/stores/darkMode.ts`
5. `main.ts` 引入 dark.css + 启动时根据 localStorage 设置 `data-theme`
6. `npm run dev` 自验 + `npm run test` 单元测试
7. Vite 构建无错,浏览器手动测 4 个页面

**回滚**:
- 全部改动可 git revert 一次回退
- 暗黑模式不强制开启,关闭即可恢复

## Open Questions

1. **Element Plus 暗黑模式 CSS 变量覆盖清单?** 实施时需对照 EP 文档列出需要覆盖的变量
2. **ECharts dark mode option**: 是否每个 chart option 都改?还是给 v-chart 包一个全局 mixin?
3. **novelIdsInput 自动填后,用户改了是否自动重跑 onCompare?**: 倾向"自动 onCompare"(debounce 500ms)
4. **排序后端支持**: 本次先做 UI,后端 ORDER BY 留 v2 — 确认范围
5. **暗色模式在排行榜卡片视图的 cover 处理**: 略
