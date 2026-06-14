"""诊断脚本:检查 novel 表中 description / tags 字段值"""
import sys

from sqlalchemy import create_engine, text

from config import CFG


def main() -> int:
    engine = create_engine(CFG.db_url, pool_pre_ping=True, pool_recycle=3600)
    with engine.connect() as conn:
        # 1) 看列是否存在
        cols = conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = DATABASE() AND table_name = 'novel'
            ORDER BY ordinal_position
        """)).fetchall()
        print("=== novel columns ===")
        for c in cols:
            print(f"  {c[0]:20s}  {c[1]:20s}  nullable={c[2]}")

        # 2) 看 id=1 的真实数据
        row = conn.execute(text("""
            SELECT id, title, description, tags FROM novel WHERE id = 1
        """)).fetchone()
        print(f"\n=== novel id=1 ===")
        print(f"  id: {row[0]}")
        print(f"  title: {row[1]}")
        print(f"  description: {repr(row[2])}")
        print(f"  tags: {repr(row[3])}")

        # 3) 统计 description / tags 命中率
        stats = conn.execute(text("""
            SELECT
                COUNT(*) AS total,
                SUM(description IS NOT NULL AND description != '') AS with_desc,
                SUM(tags IS NOT NULL AND tags != '') AS with_tags
            FROM novel
        """)).fetchone()
        print(f"\n=== novel stats ===")
        print(f"  total: {stats[0]}")
        print(f"  with description: {stats[1]}")
        print(f"  with tags: {stats[2]}")

    engine.dispose()
    return 0


if __name__ == "__main__":
    sys.exit(main())
