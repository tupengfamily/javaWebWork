## ADDED Requirements

### Requirement: 任务表格行按状态着色,运行中行高亮
Tasks.vue MUST 在 `<el-table :row-class-name="rowClass">` 上加 rowClass 函数,`running` 状态行加 `running-row` class;CSS 加 `[data-theme] .running-row { background: var(--running-bg) }`。

#### Scenario: 任务在 running 状态
- **WHEN** 某行 status='running'
- **THEN** 整行背景变为浅黄(running-row),el-tag type='warning' 标签

#### Scenario: 任务完成
- **WHEN** 任务 status 改为 'success' / 'failed' / 'cancelled'
- **THEN** running-row class 移除,行背景恢复

#### Scenario: 暗色模式
- **WHEN** 暗黑模式开启 + 任务 running
- **THEN** running-row 背景为暗黄(深色适配),不刺眼

### Requirement: 实时日志流自动滚到底部 + 新消息提示
Tasks.vue MUST 在日志流 `<div class="log-stream" ref="logStreamRef">` 监听 logs 数组长度变化,自动滚到底(scrollTop = scrollHeight);若用户已经滚到中部查看历史,显示"新消息"浮动按钮,点击跳到底部。

#### Scenario: 新日志来
- **WHEN** 5s timer 拉取 logs 新增 5 条
- **THEN** logStream 自动滚到底,scrollTop === scrollHeight

#### Scenario: 用户向上滚动
- **WHEN** 用户手动滚到 logStream 中部
- **THEN** "新消息" 按钮出现在右下角,点击后再次滚到底;若已到底,按钮自动隐藏

#### Scenario: 用户停留底部
- **WHEN** scrollTop + clientHeight >= scrollHeight - 20
- **THEN** "新消息" 按钮不显示,新日志继续自动滚
