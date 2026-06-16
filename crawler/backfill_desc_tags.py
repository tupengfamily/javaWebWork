"""rich-crawler-data 旧数据 backfill: 给 60 条旧 novel 写示例 description / tags

目的:
    1. 验证 SELECT IFNULL(...) 后的 API 响应能正常包含 description / tags
    2. 临时占位,等真实爬虫跑一遍后会被覆盖

注意:
    - 这只是**演示数据**,与真实小说无关
    - 真实数据由后续 `scrapy crawl qidian` 等抓取写入
"""
import sys

from sqlalchemy import create_engine, text

from config import CFG


# 6 套示例 (description, tags) 循环使用
SAMPLES = [
    (
        "这是一部正在连载的玄幻小说,讲述了主角在异世界崛起的故事。情节跌宕起伏,世界观宏大。",
        "玄幻,穿越,系统,无敌流,龙傲天"
    ),
    (
        "都市言情,讲述职场新人的成长与爱情,文笔细腻,情节引人入胜。",
        "都市,职场,言情,甜文,日常"
    ),
    (
        "仙侠修真类小说,融合了古典神话与现代想象,主角历经磨难终成大道。",
        "仙侠,修真,古典,励志,修仙"
    ),
    (
        "科幻末世题材,人类在废墟中重建文明,主线悬疑,副本精彩。",
        "科幻,末世,生存,悬疑,脑洞"
    ),
    (
        "历史穿越文,主角回到古代,运用现代知识改变历史走向。",
        "历史,穿越,权谋,军事,种田"
    ),
    (
        "游戏竞技类,电竞少年追逐梦想的热血故事,双线并叙,情感丰富。",
        "游戏,电竞,热血,青春,竞技"
    ),
]


def main() -> int:
    engine = create_engine(CFG.db_url, pool_pre_ping=True, pool_recycle=3600)

    with engine.begin() as conn:
        # 取所有 novel
        rows = conn.execute(text("""
            SELECT id FROM novel ORDER BY id
        """)).fetchall()

        print(f"[backfill] 共 {len(rows)} 条 novel")
        updated = 0
        for i, (nid,) in enumerate(rows):
            desc, tags = SAMPLES[i % len(SAMPLES)]
            conn.execute(text("""
                UPDATE novel
                SET description = :desc, tags = :tags
                WHERE id = :id
            """), {"desc": desc, "tags": tags, "id": nid})
            updated += 1

        print(f"[backfill] 已 backfill {updated} 条")

        # 验证
        stats = conn.execute(text("""
            SELECT
                COUNT(*) AS total,
                SUM(description IS NOT NULL AND description != '') AS with_desc,
                SUM(tags IS NOT NULL AND tags != '') AS with_tags
            FROM novel
        """)).fetchone()
        print(f"\n[verify] ==== after backfill ====")
        print(f"  total: {stats[0]}")
        print(f"  with description: {stats[1]}")
        print(f"  with tags: {stats[2]}")

    engine.dispose()
    return 0


if __name__ == "__main__":
    sys.exit(main())
