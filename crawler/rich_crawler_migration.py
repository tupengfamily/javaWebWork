"""rich-crawler-data 数据库 migration 入口

用法:
    cd crawler && python rich_crawler_migration.py

内容:
    1) ALTER TABLE novel ADD COLUMN tags
    2) UPDATE schedule_config.main (taskTimeoutMinutes / crawlAllRankingTypes)
    3) 验证 DESC novel 与 schedule_config
"""
import sys

from sqlalchemy import create_engine, text

from config import CFG


def main() -> int:
    engine = create_engine(CFG.db_url, pool_pre_ping=True, pool_recycle=3600)

    # 1) 加 tags 列(IF NOT EXISTS 在 MySQL 8.0+ ALTER TABLE 不支持,需先判断)
    with engine.begin() as conn:
        exists = conn.execute(text("""
            SELECT COUNT(*) FROM information_schema.columns
            WHERE table_schema = DATABASE()
              AND table_name = 'novel'
              AND column_name = 'tags'
        """)).scalar()
        if exists:
            print("[migration] novel.tags 已存在,跳过 ALTER")
        else:
            print("[migration] ALTER TABLE novel ADD COLUMN tags ...")
            conn.execute(text("""
                ALTER TABLE novel
                    ADD COLUMN tags VARCHAR(1024) DEFAULT NULL
                        COMMENT '逗号分隔标签(2-8 个,详情页抽取)'
                        AFTER description
            """))
            print("[migration]   → OK")

    # 2) 更新 schedule_config.main
    with engine.begin() as conn:
        row = conn.execute(text("""
            SELECT value FROM schedule_config WHERE `key` = 'main'
        """)).fetchone()
        if not row:
            print("[migration] schedule_config.main 不存在,INSERT 默认值")
            conn.execute(text("""
                INSERT INTO schedule_config (`key`, `value`, description) VALUES
                ('main', JSON_OBJECT(
                    'dailyCrawlTimes', JSON_ARRAY('08:00','14:00','20:00'),
                    'maxConcurrentTasks', 2,
                    'taskTimeoutMinutes', 60,
                    'crawlAllRankingTypes', JSON_ARRAY('daily','monthly','total','yuepiao','newbook','finish')
                ), '调度主配置')
            """))
        else:
            print("[migration] UPDATE schedule_config.main ...")
            conn.execute(text("""
                UPDATE schedule_config
                SET value = JSON_SET(
                    value,
                    '$.taskTimeoutMinutes', 60,
                    '$.crawlAllRankingTypes',
                        JSON_ARRAY('daily','monthly','total','yuepiao','newbook','finish')
                )
                WHERE `key` = 'main'
            """))
            print("[migration]   → OK")

    # 3) 验证
    print("\n[verify] ==== DESC novel ====")
    with engine.connect() as conn:
        rows = conn.execute(text("DESC novel")).fetchall()
        for r in rows:
            print(f"  {r[0]:24s}  {r[1]}")

    print("\n[verify] ==== schedule_config.main ====")
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT JSON_PRETTY(value) FROM schedule_config WHERE `key` = 'main'
        """)).fetchone()
        if row:
            print(row[0])

    print("\n[migration] DONE.")
    engine.dispose()
    return 0


if __name__ == "__main__":
    sys.exit(main())
