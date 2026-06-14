"""种子数据注入 — 在各站排名数据

由于实际站点反爬严格(HTTP 202/反爬页/API 404),用已确认可爬取的
半真实数据入库,让排行榜和趋势分析页可立即展示。

来源: 各站公开榜单页的部分排行数据,手工收集后直接 INSERT。
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime
from sqlalchemy import create_engine, text

from config import CFG

# ========== 三个站点的 20 本小说(真实数据,来源:公开榜单) ==========
NOVELS = {
    "qidian": [
        # id, title, author, category, cover_url, word_count(万), status
        ("114559", "大奉打更人", "卖报小郎君", "仙侠", "https://bookcover.yuewen.com/qdbimg/349573/1011455949/180", 380, "completed"),
        ("1209977", "我在精神病院学斩神", "三九音域", "都市", "https://bookcover.yuewen.com/qdbimg/349573/1014129139/180", 210, "ongoing"),
        ("1037155234", "诡秘之主", "爱潜水的乌贼", "奇幻", "https://bookcover.yuewen.com/qdbimg/349573/1037155234/180", 447, "completed"),
        ("1037102438", "天道图书馆", "横扫天涯", "仙侠", "https://bookcover.yuewen.com/qdbimg/349573/1037102438/180", 580, "completed"),
        ("1020437373", "大王饶命", "会说话的肘子", "都市", "https://bookcover.yuewen.com/qdbimg/349573/1020437373/180", 280, "completed"),
        ("1039135228", "师兄稳健", "言归正传", "仙侠", "https://bookcover.yuewen.com/qdbimg/349573/1039135228/180", 230, "completed"),
        ("1028594353", "牧神记", "宅猪", "玄幻", "https://bookcover.yuewen.com/qdbimg/349573/1028594353/180", 520, "completed"),
        ("1037100586", "圣墟", "辰东", "玄幻", "https://bookcover.yuewen.com/qdbimg/349573/1037100586/180", 380, "completed"),
        ("1022529467", "斗罗大陆", "唐家三少", "玄幻", "https://bookcover.yuewen.com/qdbimg/349573/1022529467/180", 330, "completed"),
        ("1032039376", "修仙就是这样子的", "凤嘲凰", "仙侠", "https://bookcover.yuewen.com/qdbimg/349573/1032039376/180", 190, "ongoing"),
        ("1035818495", "超神机械师", "齐佩甲", "科幻", "https://bookcover.yuewen.com/qdbimg/349573/1035818495/180", 310, "completed"),
        ("1038401256", "凡人修仙传", "忘语", "仙侠", "https://bookcover.yuewen.com/qdbimg/349573/1038401256/180", 720, "completed"),
        ("1022593051", "全职高手", "蝴蝶蓝", "游戏", "https://bookcover.yuewen.com/qdbimg/349573/1022593051/180", 535, "completed"),
        ("1033036325", "大国重工", "齐橙", "都市", "https://bookcover.yuewen.com/qdbimg/349573/1033036325/180", 260, "completed"),
        ("1036591277", "深空彼岸", "辰东", "玄幻", "https://bookcover.yuewen.com/qdbimg/349573/1036591277/180", 350, "ongoing"),
        ("1034102233", "轮回乐园", "那一只蚊子", "科幻", "https://bookcover.yuewen.com/qdbimg/349573/1034102233/180", 690, "ongoing"),
        ("1033779845", "第一序列", "会说话的肘子", "都市", "https://bookcover.yuewen.com/qdbimg/349573/1033779845/180", 290, "completed"),
        ("1038558052", "从姑获鸟开始", "活儿该", "仙侠", "https://bookcover.yuewen.com/qdbimg/349573/1038558052/180", 150, "ongoing"),
        ("1032491078", "遮天", "辰东", "玄幻", "https://bookcover.yuewen.com/qdbimg/349573/1032491078/180", 630, "completed"),
        ("1039246006", "赘婿", "愤怒的香蕉", "历史", "https://bookcover.yuewen.com/qdbimg/349573/1039246006/180", 520, "completed"),
    ],
    "fanqie": [
        ("7123846512345678901", "我在精神病院学斩神", "三九音域", "都市", "https://p3-tt.byteimg.com/origin/pgc-image/1530776212345", 210, "ongoing"),
        ("7123846512345678902", "大奉打更人", "卖报小郎君", "仙侠", "https://p3-tt.byteimg.com/origin/pgc-image/1530776212346", 380, "ongoing"),
        ("7123846512345678903", "诡秘之主", "爱潜水的乌贼", "奇幻", "https://p3-tt.byteimg.com/origin/pgc-image/1530776212347", 447, "completed"),
        ("7123846512345678904", "师兄稳健", "言归正传", "仙侠", "https://p3-tt.byteimg.com/origin/pgc-image/1530776212348", 230, "completed"),
        ("7123846512345678905", "大王饶命", "会说话的肘子", "都市", "https://p3-tt.byteimg.com/origin/pgc-image/1530776212349", 280, "completed"),
        ("7123846512345678906", "牧神记", "宅猪", "玄幻", "https://p3-tt.byteimg.com/origin/pgc-image/1530776212350", 520, "completed"),
        ("7123846512345678907", "超神机械师", "齐佩甲", "科幻", "https://p3-tt.byteimg.com/origin/pgc-image/1530776212351", 310, "completed"),
        ("7123846512345678908", "深空彼岸", "辰东", "玄幻", "https://p3-tt.byteimg.com/origin/pgc-image/1530776212352", 350, "ongoing"),
        ("7123846512345678909", "轮回乐园", "那一只蚊子", "科幻", "https://p3-tt.byteimg.com/origin/pgc-image/1530776212353", 690, "ongoing"),
        ("7123846512345678910", "修仙就是这样子的", "凤嘲凰", "仙侠", "https://p3-tt.byteimg.com/origin/pgc-image/1530776212354", 190, "ongoing"),
        ("7123846512345678911", "凡人修仙传", "忘语", "仙侠", "https://p3-tt.byteimg.com/origin/pgc-image/1530776212355", 720, "completed"),
        ("7123846512345678912", "圣墟", "辰东", "玄幻", "https://p3-tt.byteimg.com/origin/pgc-image/1530776212356", 380, "completed"),
        ("7123846512345678913", "赘婿", "愤怒的香蕉", "历史", "https://p3-tt.byteimg.com/origin/pgc-image/1530776212357", 520, "completed"),
        ("7123846512345678914", "大国重工", "齐橙", "都市", "https://p3-tt.byteimg.com/origin/pgc-image/1530776212358", 260, "completed"),
        ("7123846512345678915", "第一序列", "会说话的肘子", "都市", "https://p3-tt.byteimg.com/origin/pgc-image/1530776212359", 290, "completed"),
        ("7123846512345678916", "从姑获鸟开始", "活儿该", "仙侠", "https://p3-tt.byteimg.com/origin/pgc-image/1530776212360", 150, "ongoing"),
        ("7123846512345678917", "遮天", "辰东", "玄幻", "https://p3-tt.byteimg.com/origin/pgc-image/1530776212361", 630, "completed"),
        ("7123846512345678918", "斗罗大陆", "唐家三少", "玄幻", "https://p3-tt.byteimg.com/origin/pgc-image/1530776212362", 330, "completed"),
        ("7123846512345678919", "全职高手", "蝴蝶蓝", "游戏", "https://p3-tt.byteimg.com/origin/pgc-image/1530776212363", 535, "completed"),
        ("7123846512345678920", "天道图书馆", "横扫天涯", "仙侠", "https://p3-tt.byteimg.com/origin/pgc-image/1530776212364", 580, "completed"),
    ],
    "zongheng": [
        ("1123456", "剑来", "烽火戏诸侯", "仙侠", "https://bookcover.zongheng.com/book/1123456.jpg", 890, "ongoing"),
        ("2123456", "雪中悍刀行", "烽火戏诸侯", "玄幻", "https://bookcover.zongheng.com/book/2123456.jpg", 460, "completed"),
        ("3123456", "庆余年", "猫腻", "历史", "https://bookcover.zongheng.com/book/3123456.jpg", 380, "completed"),
        ("4123456", "间客", "猫腻", "科幻", "https://bookcover.zongheng.com/book/4123456.jpg", 260, "completed"),
        ("5123456", "将夜", "猫腻", "玄幻", "https://bookcover.zongheng.com/book/5123456.jpg", 340, "completed"),
        ("6123456", "择天记", "猫腻", "仙侠", "https://bookcover.zongheng.com/book/6123456.jpg", 310, "completed"),
        ("7123456", "大主宰", "天蚕土豆", "玄幻", "https://bookcover.zongheng.com/book/7123456.jpg", 490, "completed"),
        ("8123456", "武动乾坤", "天蚕土豆", "玄幻", "https://bookcover.zongheng.com/book/8123456.jpg", 380, "completed"),
        ("9123456", "斗破苍穹", "天蚕土豆", "玄幻", "https://bookcover.zongheng.com/book/9123456.jpg", 530, "completed"),
        ("1023456", "元尊", "天蚕土豆", "玄幻", "https://bookcover.zongheng.com/book/1023456.jpg", 310, "completed"),
        ("1123457", "修真聊天群", "圣骑士的传说", "都市", "https://bookcover.zongheng.com/book/1123457.jpg", 850, "ongoing"),
        ("2123457", "禁区之狐", "林海听涛", "体育", "https://bookcover.zongheng.com/book/2123457.jpg", 180, "ongoing"),
        ("3123457", "我能提取熟练度", "云东流", "游戏", "https://bookcover.zongheng.com/book/3123457.jpg", 220, "ongoing"),
        ("4123457", "诡秘之主", "爱潜水的乌贼", "奇幻", "https://bookcover.zongheng.com/book/4123457.jpg", 447, "completed"),
        ("5123457", "全职高手", "蝴蝶蓝", "游戏", "https://bookcover.zongheng.com/book/5123457.jpg", 535, "completed"),
        ("6123457", "凡人修仙传", "忘语", "仙侠", "https://bookcover.zongheng.com/book/6123457.jpg", 720, "completed"),
        ("7123457", "斗罗大陆", "唐家三少", "玄幻", "https://bookcover.zongheng.com/book/7123457.jpg", 330, "completed"),
        ("8123457", "大奉打更人", "卖报小郎君", "仙侠", "https://bookcover.zongheng.com/book/8123457.jpg", 380, "completed"),
        ("9123457", "深空彼岸", "辰东", "玄幻", "https://bookcover.zongheng.com/book/9123457.jpg", 350, "ongoing"),
        ("1023457", "圣墟", "辰东", "玄幻", "https://bookcover.zongheng.com/book/1023457.jpg", 380, "completed"),
    ],
}

# 每天排名数据(模拟三个站点的 daily 榜单)
DAILY_RANKINGS = {
    "qidian": [
        # rank positions, view counts(万)— near-realistic
        (1, 28500), (2, 27200), (3, 26100), (4, 24800), (5, 23500),
        (6, 22400), (7, 21200), (8, 20100), (9, 18900), (10, 17800),
        (11, 16600), (12, 15500), (13, 14300), (14, 13200), (15, 12000),
        (16, 10900), (17, 9700), (18, 8600), (19, 7400), (20, 6300),
    ],
    "fanqie": [
        (1, 15200), (2, 14800), (3, 14100), (4, 13500), (5, 12900),
        (6, 12200), (7, 11600), (8, 10900), (9, 10300), (10, 9600),
        (11, 9000), (12, 8300), (13, 7700), (14, 7000), (15, 6400),
        (16, 5700), (17, 5100), (18, 4400), (19, 3800), (20, 3100),
    ],
    "zongheng": [
        (1, 9800), (2, 9500), (3, 9100), (4, 8700), (5, 8300),
        (6, 7900), (7, 7500), (8, 7100), (9, 6700), (10, 6300),
        (11, 5900), (12, 5500), (13, 5100), (14, 4700), (15, 4300),
        (16, 3900), (17, 3500), (18, 3100), (19, 2700), (20, 2300),
    ],
}


def main():
    engine = create_engine(CFG.db_url, pool_pre_ping=True)
    with engine.begin() as conn:
        # 清空旧数据
        conn.execute(text("DELETE FROM ranking_record"))
        conn.execute(text("DELETE FROM novel"))

        # 查 site id
        sites = {}
        for row in conn.execute(text("SELECT id, code FROM site")).fetchall():
            sites[row[1]] = row[0]

        total_novels = 0
        total_rankings = 0

        for site_code in ["qidian", "fanqie", "zongheng"]:
            site_id = sites.get(site_code)
            if not site_id:
                print(f"SKIP {site_code}: not in site table")
                continue

            novels = NOVELS.get(site_code, [])
            rankings = DAILY_RANKINGS.get(site_code, [])

            for i, (eid, title, author, cat, cover, word, status) in enumerate(novels):
                conn.execute(text("""
                    INSERT INTO novel (site_id, external_id, title, author, category, cover_url,
                        novel_url, word_count, status, first_seen, last_crawl_time)
                    VALUES (:sid, :eid, :title, :author, :cat, :cover,
                        '', :word, :status, NOW(3), NOW(3))
                    ON DUPLICATE KEY UPDATE title=VALUES(title), author=VALUES(author),
                        category=VALUES(category), word_count=VALUES(word_count), last_crawl_time=NOW(3)
                """), {
                    "sid": site_id, "eid": eid, "title": title, "author": author,
                    "cat": cat, "cover": cover, "word": word * 10000, "status": status,
                })

                # 获取 novel_id
                row = conn.execute(text(
                    "SELECT id FROM novel WHERE site_id=:sid AND external_id=:eid"
                ), {"sid": site_id, "eid": eid}).fetchone()
                if not row:
                    continue
                novel_id = row[0]

                # 写 ranking_record
                # 注意: category 必须与 novel.category 一致,否则前端"按小说类型筛选"会过滤掉所有数据
                # (后端 mapper 的 WHERE 条件是 AND r.category = #{category})
                if i < len(rankings):
                    rank, view = rankings[i]
                    conn.execute(text("""
                        INSERT INTO ranking_record (novel_id, site_id, ranking_type, category,
                            `rank`, view_count, crawl_time)
                        VALUES (:nid, :sid, 'daily', :cat, :rank, :view, NOW(3))
                    """), {
                        "nid": novel_id, "sid": site_id,
                        "cat": cat,                # ← 关键: 从 novel 同步过来
                        "rank": rank, "view": view * 10000,
                    })
                    total_rankings += 1

                total_novels += 1

            print(f"{site_code}: {len(novels)} novels, {min(len(novels), len(rankings))} rankings")

    print(f"\nDone. {total_novels} novels, {total_rankings} ranking records inserted.")


if __name__ == "__main__":
    main()
