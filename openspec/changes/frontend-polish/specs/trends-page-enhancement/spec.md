## ADDED Requirements

### Requirement: 趋势页加载时自动从 topList 拉前 5 个 novelId
Trends.vue MUST 在 onMounted 时调 `topList({by:'viewCount', limit:10})` 并取前 5 个 novelId 自动填入 novelIdsInput,立即触发 onCompare。

#### Scenario: 默认填充
- **WHEN** 首次进入 Trends 页
- **THEN** novelIdsInput 显示 "1,2,3,4,5" (TOP5 真实 id),对比图已渲染

#### Scenario: 用户手动清空
- **WHEN** 用户清空 novelIdsInput
- **THEN** onCompare 不调用(无 ids),对比图保留上次数据

#### Scenario: 用户修改输入
- **WHEN** 用户改 novelIdsInput 为 "1,2,3"
- **THEN** debounce 500ms 后自动 onCompare,无感刷新

### Requirement: 趋势页加站点 + 分类两个 el-select 过滤
Trends.vue MUST 在 filter-bar 加站点(从 listEnabledSites 拉取)+ 分类(从 meta store 拉取)两个 el-select;筛选作用于 topList API 的 `site` 与 `category` 参数。

#### Scenario: 选起点
- **WHEN** 选 site='qidian'
- **THEN** topList 调用加 `site=qidian` 参数,跨站 TOP 10 仅显示起点数据

#### Scenario: 选玄幻
- **WHEN** 选 category='玄幻'
- **THEN** topList 调用加 `category=玄幻` 参数,跨站 TOP 10 仅显示玄幻分类

#### Scenario: 两个都选
- **WHEN** 站点+分类都选
- **THEN** topList 同时带两个参数(后端已支持 WHERE site_id + category 过滤)

### Requirement: 跨站 TOP10 三个 tab(viewCount / recCount / rank)
Trends.vue MUST 把"跨站 TOP 10"区段包成 `<el-tabs>`,三个 tab 标签 = "浏览量" / "推荐数" / "排名",tab 切换调 `topList({by: 'viewCount'|'recCount'|'rank'})`。

#### Scenario: 浏览量 tab 默认
- **WHEN** 页面加载
- **THEN** 默认 active='viewCount',topListData 显示按 viewCount 排序

#### Scenario: 切到推荐数
- **WHEN** 用户点 "推荐数" tab
- **THEN** topListData 重新拉 `by='recCount'`,表格 viewCount 列变 recCount 列(标题/列名同步)

#### Scenario: 切到排名
- **WHEN** 用户点 "排名" tab
- **THEN** topListData 拉 `by='rank'`,表格显示按 rank 升序,排名 rank 列

#### Scenario: 数字格式化
- **WHEN** 任意 tab 显示浏览量或推荐数
- **THEN** 用 formatNum (>=1亿显示 "X.XX 亿",>=1万显示 "X.X 万")
