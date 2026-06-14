"""fix_category.py — 修复历史 ranking_record 缺 category 的问题

问题: 早期版本的 seed_data.py INSERT ranking_record 时没有写 category 字段,
导致前端"小说类型"筛选全部返回空数据。

修复: 把 novel.category 同步到对应的 ranking_record.category
(每个 (site_id, novel_id) 组合的所有 ranking_record 一致更新)。

使用:
    cd crawler
    python fix_category.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine, text

from config import CFG


def main():
    engine = create_engine(CFG.db_url, pool_pre_ping=True)
    with engine.begin() as conn:
        # 1. 看现状
        before_null = conn.execute(text("""
            SELECT COUNT(*) FROM ranking_record WHERE category IS NULL OR category = ''
        """)).scalar()
        before_total = conn.execute(text("""
            SELECT COUNT(*) FROM ranking_record
        """)).scalar()
        print(f"[fix_category] 修复前: 共 {before_total} 条,category 为空的 {before_null} 条")

        if before_null == 0:
            print("[fix_category] 无需修复,所有 ranking_record.category 已正确填写")
            return

        # 2. 从 novel 表同步 category 到 ranking_record
        #    (ranking_record.novel_id 与 novel.id 对应,novel.category 是权威)
        result = conn.execute(text("""
            UPDATE ranking_record r
            JOIN novel n ON r.novel_id = n.id
            SET r.category = n.category
            WHERE r.category IS NULL OR r.category = ''
        """))
        print(f"[fix_category] 已修复 {result.rowcount} 条 ranking_record")

        # 3. 验证
        after_null = conn.execute(text("""
            SELECT COUNT(*) FROM ranking_record WHERE category IS NULL OR category = ''
        """)).scalar()
        print(f"[fix_category] 修复后: category 仍为空的 {after_null} 条")
        print("[fix_category] DONE. 现在可以按小说类型筛选榜单了")


if __name__ == "__main__":
    main()