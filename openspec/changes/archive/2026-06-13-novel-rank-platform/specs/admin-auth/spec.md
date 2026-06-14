## ADDED Requirements

### Requirement: 管理员登录
系统 MUST 提供管理员登录接口,接收用户名与密码,验证通过后返回 JWT 与用户信息。

#### Scenario: 登录成功
- **WHEN** 客户端提交正确的用户名和密码
- **THEN** 系统返回 HTTP 200 与 `{ token, expiresIn, user: {id, username, role} }`,token 通过 BCrypt 校验后签发

#### Scenario: 凭据错误
- **WHEN** 客户端提交的用户名或密码错误
- **THEN** 系统返回 HTTP 401 与错误码 `1001` 与消息"用户名或密码错误",不暴露具体哪个字段错误

#### Scenario: 必填参数缺失
- **WHEN** 客户端未传 username 或 password
- **THEN** 系统返回 HTTP 400 与错误码 `400` 与字段级校验错误信息

### Requirement: JWT 鉴权
系统 MUST 对所有 `/api/admin/**` 接口与 `/api/auth/me` 接口强制校验 JWT,缺失/无效/过期 token 拒绝访问。

#### Scenario: 合法 token 访问
- **WHEN** 客户端携带有效 JWT 访问受保护接口
- **THEN** 系统放行并从 token 解析当前用户身份

#### Scenario: 缺失 token
- **WHEN** 客户端未携带 Authorization 头访问 `/api/admin/**`
- **THEN** 系统返回 HTTP 401 与错误码 `401` 与消息"未登录"

#### Scenario: token 过期
- **WHEN** 客户端使用的 token 已过 `exp` 声明
- **THEN** 系统返回 HTTP 401 与错误码 `1002` 与消息"token 已过期"

#### Scenario: 非 admin 角色
- **WHEN** 客户端使用有效 token 但 `role != "admin"` 访问 `/api/admin/**`
- **THEN** 系统返回 HTTP 403 与错误码 `403` 与消息"无权限"

### Requirement: 获取当前用户
系统 MUST 提供 `/api/auth/me` 接口,返回当前登录管理员的公开信息(不含密码哈希)。

#### Scenario: 已登录
- **WHEN** 已登录管理员调用此接口
- **THEN** 系统返回 `{ id, username, role }`,并更新 `sys_user.last_login_at`

### Requirement: 退出登录
系统 MUST 提供 `/api/auth/logout` 接口,前端调用后清空本地 token 即可(后端无状态,接口本身仅返回成功)。

#### Scenario: 退出
- **WHEN** 已登录管理员调用 `/api/auth/logout`
- **THEN** 系统返回 HTTP 200 与 `code: 0`,无需服务端操作
