# Tasks — frontend-polish

## 1. 类型层扩展 (frontend/src/api)

- [ ] 1.1 `frontend/src/api/novels.ts` `NovelVO` 接口加 `description: string` / `tags: string` 字段
- [ ] 1.2 `frontend/src/api/rankings.ts` `listRankings` 参数加 `sortField?: 'rank'|'viewCount'|'recCount'` / `sortOrder?: 'asc'|'desc'`
- [ ] 1.3 `frontend/src/api/sites.ts` `SiteVO` 加 `color: string`(后端已返回,只补类型)
- [ ] 1.4 `frontend/src/api/rankings.ts` `topList` 参数加 `by?: 'viewCount'|'recCount'|'rank'`(已存在,确认)
- [ ] 1.5 验证:TypeScript 编译 `npm run type-check` 0 错

## 2. 全局暗黑模式 (基础设施)

- [ ] 2.1 新建 `frontend/src/styles/dark.css`,定义 `:root` 与 `[data-theme="dark"]` 下的 CSS 变量(bg/card/border/text/hover/running/warn 等)
- [ ] 2.2 覆盖 Element Plus 关键变量:`--el-bg-color` / `--el-bg-color-page` / `--el-text-color-primary` / `--el-border-color`
- [ ] 2.3 新建 `frontend/src/stores/darkMode.ts` Pinia store:`isDark: boolean`、`toggle()`、`init()`;`init()` 读 localStorage + 监听 storage 事件
- [ ] 2.4 `frontend/src/main.ts`:import dark.css,`app.use(pinia)` 后立即 `darkModeStore.init()`,根据 `isDark` 给 `<html>` 加 `data-theme="dark"`
- [ ] 2.5 `MainLayout.vue` user-area 加 el-button (Sunny / Moon 图标),点击 `darkModeStore.toggle()`
- [ ] 2.6 验证:刷新页面后保持上次主题;两个 tab 同步切换

## 3. 排行榜 Rankings.vue 改造 (6 项)

- [ ] 3.1 el-table 加封面列(width=80,el-image 60×80 lazy,缺省 placeholder)
- [ ] 3.2 el-table 加站点色 tag 列(用 site.color,effect="dark")
- [ ] 3.3 el-table 顶部右侧加 `<el-radio-button v-model="viewMode" size="small">` 列表/卡片切换
- [ ] 3.4 filters.pageSize 默认 50,el-pagination layout 加 `sizes` 与 `page-sizes=[20,50,100]`
- [ ] 3.5 rank / viewCount / recCount 三列加 `sortable="custom"`,监听 `@sort-change`,写入 filters.sortField / sortOrder
- [ ] 3.6 filter-bar 下方加分类 chip 行(el-tag,点击切换 filters.category)
- [ ] 3.7 卡片视图模板(el-row + el-col + el-card,强制 pageSize=20,卡片点击进详情)
- [ ] 3.8 验证:浏览器查看排行榜页,封面/站点/排序/chip/卡片视图全部正常;暗色模式下文字不刺眼

## 4. 详情页 NovelDetail.vue 改造 (2 项)

- [ ] 4.1 在 info-card 下方加 el-card "简介" 区段,`v-if="novel.description"`,超 500 字折叠(展开/收起按钮)
- [ ] 4.2 meta 区在"跳转原文"上方加 tags chips 区段,`v-if="novel.tags"`,按 `,` split 后用 el-tag effect="plain" 循环 5 色
- [ ] 4.3 验证:浏览器访问 /novels/1,description + tags 正常显示;数据空时不渲染(不显示空状态)

## 5. 趋势页 Trends.vue 改造 (3 项)

- [ ] 5.1 onMounted:先调 `topList({by:'viewCount',limit:10})` 取 top 5 自动填入 novelIdsInput,立即 onCompare
- [ ] 5.2 filter-bar 加站点 + 分类两个 el-select,绑定 topListParams.site / topListParams.category
- [ ] 5.3 "跨站 TOP 10" 包成 el-tabs,三个 tab label 分别为 "浏览量" / "推荐数" / "排名",tab 切换调 topList({by})
- [ ] 5.4 tab 切换 + 站点/分类变化时 fetchTop 自动重跑
- [ ] 5.5 验证:页面加载立即有 5 条对比曲线;切 tab 立刻刷新;暗色模式图表清晰

## 6. 任务页 Tasks.vue 改造 (1 项)

- [ ] 6.1 el-table 加 `:row-class-name="rowClass"`,running 状态返回 'running-row'
- [ ] 6.2 CSS:深浅两套 running-row 背景(用 CSS 变量)
- [ ] 6.3 log-stream ref + watch(logs.length),自动 scrollTop = scrollHeight
- [ ] 6.4 检测用户是否在底部(scrollTop + clientHeight >= scrollHeight - 20),否则显示"新消息"按钮
- [ ] 6.5 "新消息" el-button 浮动在 log-stream 右下角,点击触发滚动到底
- [ ] 6.6 验证:触发爬虫后日志流自动滚;手动滚到中部后"新消息"按钮出现;切暗色背景不变

## 7. 视觉验证 (必做)

- [ ] 7.1 浅色模式 4 个页面整体走查,无白底黑字/暗底亮字错误
- [ ] 7.2 切到暗色模式,4 个页面整体走查,文字对比度足够(el-text vs bg)
- [ ] 7.3 暗色模式下两张 ECharts 图表清晰可读
- [ ] 7.4 移动端模拟(Chrome DevTools 375px):卡片视图可读,表格横向滚动不破版
- [ ] 7.5 `npm run test` 全部通过
- [ ] 7.6 `npm run build` 0 警告 0 错误
