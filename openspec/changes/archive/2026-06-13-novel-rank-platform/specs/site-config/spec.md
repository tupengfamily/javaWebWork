## ADDED Requirements

### Requirement: 公开站点列表
系统 MUST 提供 `GET /api/sites` 公开接口,返回所有 `enabled = true` 的站点配置,不含后端字段(spider_class 等)。

#### Scenario: 查询启用站点
- **WHEN** 任意客户端调用此接口
- **THEN** 系统返回 `[ { id, code, name, color, sortOrder } ]` 列表,按 `sortOrder ASC, id ASC` 排序

#### Scenario: 无启用站点
- **WHEN** 数据库中没有任何 enabled 站点
- **THEN** 系统返回空数组 `[]`,HTTP 200

### Requirement: 管理员站点管理
系统 MUST 提供管理员对 `site` 表的完整 CRUD,通过 `/api/admin/sites/**` 路径。

#### Scenario: 列出全部站点
- **WHEN** 管理员调用 `GET /api/admin/sites`
- **THEN** 系统返回全部站点(含禁用的),分页结构

#### Scenario: 新增站点
- **WHEN** 管理员提交 `POST /api/admin/sites` 含 `code, name, baseUrl, spiderClass, color?, sortOrder?`
- **THEN** 系统插入记录并返回新站点;code 已存在时返回 HTTP 400 错误码 `400`

#### Scenario: 更新站点
- **WHEN** 管理员调用 `PUT /api/admin/sites/{id}` 提交部分字段
- **THEN** 系统只更新提供的字段,`updated_at` 自动刷新

#### Scenario: 切换启用
- **WHEN** 管理员将某站点的 `enabled` 从 true 改为 false
- **THEN** 该站点从下次调度起不再自动生成 task,公开列表中也不出现;已有历史数据保留

#### Scenario: 删除站点
- **WHEN** 管理员删除某站点
- **THEN** 若该站点已有 `novel` 或 `ranking_record` 关联数据,系统 MUST 拒绝并返回错误码 `400` 与消息"存在关联数据,无法删除"

### Requirement: 站点字典与爬虫绑定
系统 MUST 将站点的 `spider_class`(Python 类路径)与爬虫层注册表保持一致,新增/修改站点时填写正确路径,爬虫层启动时据此动态加载。

#### Scenario: 爬虫加载
- **WHEN** Python 启动并加载 site 表
- **THEN** 通过 `importlib.import_module` 按 `spider_class` 路径动态导入 Spider 类,失败的站点 MUST 写 ERROR 日志并跳过
