## ADDED Requirements

### Requirement: dev.sh reset 清库并重建
`dev.sh reset` MUST 先 `DROP DATABASE IF EXISTS novel_rank` 再重新 init-db;MUST 提示 "将丢失所有数据" + 默认必须 `--yes` 才执行。

#### Scenario: 无 --yes 拒绝执行
- **WHEN** `dev.sh reset` (无 --yes)
- **THEN** 打印 "⚠ 将删除 novel_rank,所有数据丢失。重跑加 --yes 确认" + 退出码 0(不报错)

#### Scenario: --yes 真的删
- **WHEN** `dev.sh reset --yes`
- **THEN** DROP DATABASE → CREATE → init-db 全套

#### Scenario: 库不存在
- **WHEN** `dev.sh reset --yes` 但 novel_rank 不存在
- **THEN** DROP 用 IF EXISTS 跳过错误,继续 CREATE

### Requirement: start.sh reset 销毁 Docker 卷
`start.sh reset` MUST 等价于 `docker compose down -v`,MUST 列出将被清空的卷(db_data / crawler_logs);默认必须 `--yes` 才执行。

#### Scenario: 无 --yes
- **WHEN** `start.sh reset` (无 --yes)
- **THEN** 打印卷列表 + "重跑加 --yes 确认" + 退出码 0

#### Scenario: --yes 真删
- **WHEN** `start.sh reset --yes`
- **THEN** `docker compose down -v` 执行,卷被清

#### Scenario: 容器没起也能 reset
- **WHEN** 容器已停,`start.sh reset --yes`
- **THEN** down -v 正常执行(只清卷不报错)
