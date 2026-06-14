## ADDED Requirements

### Requirement: 榜单类型字典
系统 MUST 提供 `GET /api/meta/ranking-types` 公开接口,返回 ranking_type 表的所有条目。

#### Scenario: 正常返回
- **WHEN** 客户端调用此接口
- **THEN** 系统返回 `[ { code, name, description } ]`,按 id 升序

### Requirement: 分类字典
系统 MUST 提供 `GET /api/meta/categories` 公开接口,返回 category 表的所有分类名(字符串数组)。

#### Scenario: 正常返回
- **WHEN** 客户端调用此接口
- **THEN** 系统返回 `["玄幻", "都市", "仙侠", ...]`,按 sort_order 升序

### Requirement: 字典缓存(可选)
前端 MUST 在应用启动时一次性加载这两个字典,缓存到 Pinia store,后续组件不重复请求。

#### Scenario: 避免重复请求
- **WHEN** 多个页面使用榜单类型字典
- **THEN** 整个会话只发一次 `GET /api/meta/ranking-types`
