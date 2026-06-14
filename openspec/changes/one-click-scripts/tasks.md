# Tasks — one-click-scripts

## 1. 共享库(_lib.sh / _lib.bat)

- [ ] 1.1 创建 `scripts/_lib.sh`,实现 `log_info / log_warn / log_err` 彩色输出与 `[dev]/[start]` 前缀
- [ ] 1.2 在 `_lib.sh` 实现 `load_env` 函数(解析 `.env` 为 shell 变量,缺字段有默认值)
- [ ] 1.3 在 `_lib.sh` 实现 `check_java / check_python / check_node`(返回 0/非 0)
- [ ] 1.4 在 `_lib.sh` 实现 `wait_for_url URL TIMEOUT` HTTP 探活(curl + 重试)
- [ ] 1.5 在 `_lib.sh` 实现 `port_listening PORT` 端口占用检查
- [ ] 1.6 创建 `scripts/_lib.bat`,逐函数对应 .sh 实现(用 `where` / `powershell -Command`)
- [ ] 1.7 验证:在干净 PowerShell 与 bash 下分别 `source` / `call` 共享库,无报错

## 2. MySQL Bootstrap(init-db / seed / reset — 本地模式)

- [ ] 2.1 扩展 `crawler/seed_data.py` 加 `--emit-sql <file>` 参数(输出 INSERT SQL 到文件,不改默认行为)
- [ ] 2.2 在 `dev.sh` 实现 `init-db` 子命令:按 `.env → ~/.my.cnf → 交互 prompt` 取 root 密码
- [ ] 2.3 `init-db` 内:探测 MySQL 端口(3306 → 3307 → 33060),命中即停
- [ ] 2.4 `init-db` 内:执行 CREATE DATABASE / USER / GRANT,失败打印 mysql 错误原文后退出 1
- [ ] 2.5 `init-db` 内:`Get-Content db\init.sql | mysql ...` / `mysql ... < db/init.sql` 灌 schema,`SELECT COUNT(*) FROM novel` 验证
- [ ] 2.6 在 `dev.sh` 实现 `seed` 子命令:跑 `python crawler/seed_data.py`(默认行为,直接 INSERT)
- [ ] 2.7 `seed` 支持 `--clean`(TRUNCATE 后再灌)与 `--no-clean`(默认跳过若已有 >= 5 本)
- [ ] 2.8 在 `dev.sh` 实现 `reset` 子命令:必须 `--yes` 才 DROP DATABASE;无参数时只 WARN 提示
- [ ] 2.9 在 `dev.bat` 镜像实现 2.1-2.8 的所有子命令(PowerShell 调 mysql / python,跨平台等价)
- [ ] 2.10 验证:在干净 MySQL 上 `dev.sh init-db` → `dev.sh seed` → `SELECT COUNT(*)` = 60

## 3. 环境预检(check)

- [ ] 3.1 在 `dev.sh` 实现 `check` 子命令:依次检测 JDK 17+ / Python 3.11+ / Node 18+ / MySQL / 端口 8080+5173 空闲
- [ ] 3.2 `check` 任一失败:打印 "✗ 失败项 — 修复方法" 列表,退出码 = 失败项数
- [ ] 3.3 Node 版本 < 18 视为 WARN(允许试运行)而非 error
- [ ] 3.4 在 `dev.bat` 镜像实现 3.1-3.3(用 `where java` / `python --version` / `node --version` 探测)
- [ ] 3.5 在 `start.sh` 实现 `check` 子命令:检测 `docker` / `docker compose` / `docker info` 三项
- [ ] 3.6 在 `start.bat` 镜像实现 3.5
- [ ] 3.7 验证:`dev.sh check` 在缺 JDK 环境退出非 0,在齐备环境退出 0

## 4. dev.sh / dev.bat start 流程增强

- [ ] 4.1 在 `dev.sh` 修改 `start` 子命令:增加 4 个阶段(`check → init-db → seed → 启三件套`),可 `--no-seed / --reset / --non-interactive / --mysql-port=N` 控制
- [ ] 4.2 `start` 内启动 backend / crawler 前 MUST `export MYSQL_*` / `DB_*`,从 `.env` 读
- [ ] 4.3 `start` 内并行启三件套:用 `start /B`(Windows)或 `nohup ... &`(Linux)拉后台,写 `.pids/{name}.pid`
- [ ] 4.4 `start` 内等 backend 30s 内 `curl /api/meta/categories` 200,失败打印 logs/backend.log 最后 30 行
- [ ] 4.5 `start` 成功完成打印 "Frontend http://localhost:5173 / Backend http://localhost:8080/api / Swagger /doc.html / admin/admin123"
- [ ] 4.6 在 `dev.bat` 镜像实现 4.1-4.5(用 PowerShell 启动 java/python/npm 的后台进程)
- [ ] 4.7 `dev.sh stop` / `status` / `restart` 行为不变,仍读 `.pids/*.pid`
- [ ] 4.8 验证:空 MySQL 跑 `dev.sh start` → 30-60s 内三件套全起来 + 列表有 60 本数据

## 5. start.sh / start.bat up 流程增强

- [ ] 5.1 在 `start.sh` 修改 `up` 子命令:增加 3 个阶段(`check → docker compose up -d → 等所有 healthcheck 通过`)
- [ ] 5.2 `up` 支持 `--build / --no-build / --seed / --reset / --yes` 五个 flag
- [ ] 5.3 `up --seed` 在 mysql 容器 healthy 后调 `seed` 子命令
- [ ] 5.4 `up --reset` 必须 `--yes` 才 `docker compose down -v`,无参数只 WARN
- [ ] 5.5 healthcheck 超时(backend 60s / mysql 90s):打印 `docker compose ps` + 失败服务日志
- [ ] 5.6 在 `start.sh` 实现 `seed` 子命令:`docker compose exec mysql mysql -unovel -pnovel123 novel_rank` 灌 SQL
- [ ] 5.7 `seed` 默认行为:库已有 >= 5 本则跳过;`--clean` 先 TRUNCATE
- [ ] 5.8 在 `start.bat` 镜像实现 5.1-5.7
- [ ] 5.9 现有 `down` / `logs [service]` / `status` 行为不变
- [ ] 5.10 验证:无镜像环境 `start.sh up --build --seed` → 60-120s 内 + 列表有数据

## 6. 配置 & 文档

- [ ] 6.1 更新 `.env.example`:补 `MYSQL_ROOT_PASSWORD=` 占位 + 注释说明自动 init-db 用
- [ ] 6.2 更新 `scripts/README.md`:列出全部子命令(dev.sh 9 个 + start.sh 7 个)+ 用法示例
- [ ] 6.3 更新根 `README.md` "快速开始"段落:`./scripts/dev.sh start` 与 `./scripts/start.sh up --build --seed`
- [ ] 6.4 更新 `docs/quickstart.md`:同步替换手工命令为脚本调用
- [ ] 6.5 在 `docs/troubleshooting.md` 新增章节:"dev.sh start 常见失败"+ "start.sh up 常见失败"
- [ ] 6.6 验证:按照更新后的 README,新人在干净环境照着 5 步内能起来

## 7. 端到端验证(必做)

- [ ] 7.1 Windows PowerShell:`dev.bat start`(空 MySQL)→ 三件套起来 + 列表有数据
- [ ] 7.2 Windows PowerShell:`dev.bat start --no-seed` → 三件套起来 + 列表空白
- [ ] 7.3 Windows PowerShell:`dev.bat start --reset` → 库清空 + 重建 + 有数据
- [ ] 7.4 Windows PowerShell:`dev.bat stop` / `start` / `status` → PID 文件正确写入/读取
- [ ] 7.5 Linux bash:`dev.sh start` 同上四步
- [ ] 7.6 Linux bash:`start.sh up --build --seed` → 容器起来 + 列表有数据
- [ ] 7.7 Linux bash:`start.sh reset --yes` → db_data 卷被清
- [ ] 7.8 跨平台一致性:同一 README 在 Windows 与 Linux 各跑一次,输出格式/退出码/日志路径一致
