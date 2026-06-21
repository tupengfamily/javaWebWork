## 1. 后端 API — 数据质量统计

- [ ] 1.1 新增 `AdminDataController.java`，实现 `GET /api/admin/data/quality` 接口，返回各站点数据完整性指标（总小说数、缺封面数、缺简介数、缺作者数、完整率）
- [ ] 1.2 新增 `AdminNovelController.java` 中 `DELETE /api/admin/novels/batch` 批量删除接口，接收 ID 列表，单事务内删除小说及关联排行记录

## 2. 后端 API — 数据导出

- [ ] 2.1 新增 `GET /api/admin/novels/export` 接口，支持筛选条件导出小说列表为 CSV（UTF-8 BOM），上限 10000 条
- [ ] 2.2 新增 `GET /api/admin/novels/{id}/records/export` 接口，导出指定小说的排行记录为 CSV

## 3. 后端 API — 高级筛选

- [ ] 3.1 扩展 `AdminNovelController.page` 接口，新增 `hasCover`、`hasDescription`、`hasAuthor`、`updatedDays` 筛选参数

## 4. 前端 — API 封装

- [ ] 4.1 新增 `api/admin-data.ts`，封装数据质量统计、批量删除、导出接口

## 5. 前端 — 数据管理页面重写

- [ ] 5.1 重写 `CrawlerData.vue`，移除站点状态卡片，改为 3 个 Tab：数据质量概览、小说管理、排行记录
- [ ] 5.2 实现数据质量概览 Tab — 卡片展示各站点完整性指标，点击问题数量跳转到小说管理 Tab 并自动应用筛选
- [ ] 5.3 实现小说管理 Tab — 新增高级筛选（有/无封面、有/无简介、有/无作者、更新时间）、批量选择、批量删除、导出按钮
- [ ] 5.4 实现排行记录 Tab — 增强弹窗，增加趋势迷你图（轻量 SVG 折线图）和导出记录按钮

## 6. 构建与验证

- [ ] 6.1 重新构建后端和前端容器，手动测试数据质量 API 返回正确
- [ ] 6.2 测试批量删除功能，验证关联排行记录同步清除
- [ ] 6.3 测试 CSV 导出，验证 Excel 打开中文无乱码
- [ ] 6.4 测试高级筛选各维度组合
