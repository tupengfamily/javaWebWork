## ADDED Requirements

### Requirement: init-db 子命令按优先级获取 root 密码并自动建库
`init-db` MUST 按 `MYSQL_ROOT_PASSWORD(.env) → ~/.my.cnf → 交互式 prompt` 顺序获取 root 密码,执行 `CREATE DATABASE IF NOT EXISTS novel_rank` + `CREATE USER 'novel'@'localhost' IDENTIFIED BY 'novel123'` + `GRANT ALL` + `SOURCE db/init.sql`,最后用 `SELECT COUNT(*) FROM novel` 验证。

#### Scenario: .env 有 root 密码
- **WHEN** `.env` 含 `MYSQL_ROOT_PASSWORD=xxx`
- **THEN** 直接用该密码连接 root,执行全套 init 流程,不询问

#### Scenario: 无密码且非交互
- **WHEN** `.env` 缺 root 密码 + 传 `--non-interactive`
- **THEN** 打印 "请设置 MYSQL_ROOT_PASSWORD 后重试" + 手动修复命令 + 退出码 1

#### Scenario: 无密码但可交互
- **WHEN** `.env` 缺 root 密码 + 无 --non-interactive
- **THEN** 提示 "请输入 MySQL root 密码:" (隐藏输入) → 立即使用 → 不写回 .env

#### Scenario: 库已建好
- **WHEN** novel_rank 已存在 + sys_user 有数据
- **THEN** 跳过 CREATE / GRANT,直接 SOURCE init.sql(用 INSERT IGNORE 兼容已存在记录),打印 "DB ready"

#### Scenario: init.sql 执行失败
- **WHEN** root 密码错误 / MySQL 未启动
- **THEN** 打印 mysql 错误原文 + 退出码 1,不重试

### Requirement: MySQL 端口探测优先级
init-db MUST 按 `MYSQL_PORT(.env) > --mysql-port 参数 > 自动探测 3306→3307→33060` 决定连接端口;自动探测 MUST 用 `mysqladmin ping` 试,命中即停。

#### Scenario: 显式指定端口
- **WHEN** `--mysql-port=3307`
- **THEN** 用 3307,跳过探测

#### Scenario: 自动探测命中 3307
- **WHEN** 3306 不通、3307 通
- **THEN** 用 3307 + 打印 "[dev] detected MySQL on port 3307"

#### Scenario: 全部不通
- **WHEN** 3306 / 3307 / 33060 都不通
- **THEN** 打印 "MySQL 不可达" + 启动指引 + 退出码 1
