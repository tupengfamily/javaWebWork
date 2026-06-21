## ADDED Requirements

### Requirement: 小说列表 CSV 导出

系统 SHALL 支持将当前筛选条件下的小说列表导出为 CSV 文件，包含站点、书名、作者、分类、字数、状态、封面 URL、简介、最近爬取时间。

#### Scenario: 导出当前筛选结果
- **WHEN** 管理员点击「导出小说」按钮
- **THEN** 系统下载 CSV 文件，包含当前筛选条件下的所有小说数据

#### Scenario: 导出上限保护
- **WHEN** 筛选结果超过 10000 条
- **THEN** 系统导出前 10000 条并在 CSV 首行注释说明截断

### Requirement: 排行记录 CSV 导出

系统 SHALL 支持将指定小说的排行记录导出为 CSV 文件。

#### Scenario: 导出排行记录
- **WHEN** 管理员在排行记录弹窗中点击「导出记录」
- **THEN** 系统下载 CSV 文件，包含该小说的所有历史排行记录（排名、浏览量、推荐数、榜单类型、爬取时间）

### Requirement: CSV 格式规范

导出的 CSV 文件 SHALL 使用 UTF-8 with BOM 编码（兼容 Excel 中文显示），首行为列标题。

#### Scenario: Excel 打开中文正常
- **WHEN** 用户用 Microsoft Excel 打开导出的 CSV 文件
- **THEN** 中文内容正常显示，无乱码
