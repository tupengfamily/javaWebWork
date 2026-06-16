## ADDED Requirements

### Requirement: 排行榜表格加封面缩略图 + 站点色 tag
Rankings.vue MUST 在 `el-table-column` 加封面列(el-image 60×80,懒加载)+ 站点色 tag(用 `site.color` 字段,style 自定义);表格可读性提升。

#### Scenario: 表格行显示封面
- **WHEN** 列表页加载完成
- **THEN** 每行第一列是 60×80 缩略图,`<el-image :src="row.coverUrl" fit="cover" lazy />`;coverUrl 缺失时显示占位 `<el-image :src="defaultCover" />`

#### Scenario: 站点色 tag
- **WHEN** 列表属于起点 / 番茄 / 纵横任一站
- **THEN** 站点列显示带站点色的 `<el-tag :color="site.color" effect="dark">{{ site.name }}</el-tag>`

#### Scenario: 封面列固定宽度
- **WHEN** 表格渲染
- **THEN** 封面列 width="80",align="center",不影响其他列宽

### Requirement: pageSize 可选 20/50/100,默认 50
Rankings.vue MUST 在 el-pagination 加 `page-sizes=[20,50,100]` 与 `layout="total, sizes, prev, pager, next, jumper"`,pageSize 默认 50。

#### Scenario: 切换到 100
- **WHEN** 用户点 pager 右侧 sizes 下拉选 100
- **THEN** `filters.pageSize = 100`,onPageSizeChange 触发 fetchData

#### Scenario: 默认 50
- **WHEN** 首次进入页面
- **THEN** filters.pageSize = 50,显示 50 条/页

### Requirement: 表格列可排序(rank / viewCount / recCount)
Rankings.vue MUST 在 rank / viewCount / recCount 三列加 `sortable="custom"`,监听 `@sort-change` 事件,sortField + sortOrder 写入 filters;后端接口参数透传。

#### Scenario: 按 viewCount 降序
- **WHEN** 用户点 viewCount 列头
- **THEN** `filters.sortField='viewCount'`,`filters.sortOrder='desc'`,fetchData 重查

#### Scenario: 取消排序
- **WHEN** 用户再次点击当前排序列
- **THEN** `sortField=''`,`sortOrder=''`,回退默认按 rank

#### Scenario: 后端未支持 sortField
- **WHEN** 后端 mapper 暂不接收 sortField / sortOrder 参数
- **THEN** 排序状态在前端切换但数据无变化(显示 "已请求排序" 状态,日志说明);此为过渡,留 v2

### Requirement: 分类快捷 chip 一键过滤
Rankings.vue MUST 在 filter-bar 下方加一行 `el-tag` chips,每个 chip 是分类名;点击 chip 等价于选中下拉并触发 onChange。

#### Scenario: 点击 "玄幻" chip
- **WHEN** 用户点 "玄幻" 标签
- **THEN** `filters.category='玄幻'`,chip 变实心(其他空心),fetchData 过滤

#### Scenario: 取消 chip
- **WHEN** 用户再次点击当前选中 chip
- **THEN** `filters.category=''`,chip 回空心

#### Scenario: chip 数量超 12
- **WHEN** meta.categories 长度 > 12
- **THEN** 多余 chip 折到 `el-popover` 折叠按钮内,避免换行难看

### Requirement: 列表/卡片视图切换
Rankings.vue MUST 在 header-row 加 `el-radio-button` 切换 `viewMode='list'|'card'`;卡片模式用 el-col 栅格 + el-card 渲染,强制 pageSize=20。

#### Scenario: 切到卡片视图
- **WHEN** viewMode = 'card'
- **THEN** el-table 隐藏,改渲染 `<el-row :gutter="16"><el-col :span="6" v-for="row in data.records">` 卡片网格,每张卡显示 cover + title + author + rank

#### Scenario: 卡片视图强制 20
- **WHEN** viewMode 切到 card
- **THEN** filters.pageSize 自动设 20,fetchData 重查;回切 list 保留用户上次的 pageSize

#### Scenario: 卡片点击进详情
- **WHEN** 卡片被点击
- **THEN** 跳 `/novels/{row.novelId}`(复用 goDetail 逻辑)
