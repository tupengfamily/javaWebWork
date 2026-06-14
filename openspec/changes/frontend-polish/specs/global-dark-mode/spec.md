## ADDED Requirements

### Requirement: 全局暗黑模式 toggle + localStorage 持久化
MainLayout.vue MUST 在 user-area 加一个 el-button (月亮/太阳图标,el-icon Moon / Sunny),点击切换 `data-theme` 属性;Pinia store `useDarkModeStore` 持久化到 localStorage;main.ts 启动时根据值设置 `<html data-theme="...">`。

#### Scenario: 默认浅色
- **WHEN** 用户首次访问
- **THEN** localStorage.theme 为空,默认 light,`<html>` 无 data-theme 属性

#### Scenario: 切换暗黑
- **WHEN** 用户点太阳图标
- **THEN** `<html data-theme="dark">`,localStorage.theme='dark',icon 变月亮

#### Scenario: 持久化
- **WHEN** 用户刷新页面
- **THEN** main.ts 读 localStorage.theme 还原 `<html data-theme>`,保持上次模式

#### Scenario: 跨 tab 同步
- **WHEN** 用户在 tab A 切换模式
- **THEN** tab B 通过 `storage` 事件同步切换(B 页面无须刷新)

### Requirement: CSS 变量定义 dark/light 两套主题
`frontend/src/styles/dark.css` MUST 定义 `[data-theme="dark"]` 与 `:root`(默认)下的 CSS 变量;Element Plus 暗色 tokens 通过覆盖 `--el-bg-color` `--el-text-color-primary` 等实现。

#### Scenario: 暗黑背景色
- **WHEN** `[data-theme="dark"]`
- **THEN** `--bg-primary: #1f1f1f`、`--bg-card: #262626`、`--text-primary: #e5e5e5` 生效

#### Scenario: 浅色背景色
- **WHEN** `:root`(默认)
- **THEN** `--bg-primary: #f5f7fa`、`--bg-card: #fff`、`--text-primary: #303133` 生效

#### Scenario: ECharts 暗黑适配
- **WHEN** 暗黑模式 + 趋势图/详情图
- **THEN** ECharts option 读 store.isDark 决定 `textStyle.color` 与 axisLine / splitLine 颜色

### Requirement: Tasks.vue 站点卡片适配暗色
Tasks.vue 站点卡片 MUST 用 CSS 变量(而不是写死 #f56c6c 等),确保暗色模式下 warn 文字色与暗背景对比度足够。

#### Scenario: warn 文案暗色
- **WHEN** 暗黑模式 + 显示 "近 7 天失败 N 次"
- **THEN** 文字色为 #f56c6c(亮红)与暗背景对比清晰

### Requirement: 排行榜表格 + 详情页 + 趋势页的 layout 配色随主题变化
4 个页面的 el-card、el-table、el-empty、el-tag、el-tag chips MUST 全部用 CSS 变量控制背景/边框/文字色,避免硬编码。

#### Scenario: el-card 暗色
- **WHEN** 暗黑模式
- **THEN** el-card 背景 = var(--bg-card),border = var(--border-color)

#### Scenario: 表格行 hover
- **WHEN** 暗黑模式 + 鼠标 hover
- **THEN** hover 背景 = var(--hover-bg),不刺眼
