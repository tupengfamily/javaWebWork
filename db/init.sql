-- ============================================================
-- 小说数据看板 - 数据库初始化脚本
-- MySQL 8.0+
-- 字符集: utf8mb4 / 引擎: InnoDB
-- ============================================================

DROP DATABASE IF EXISTS novel_rank;
CREATE DATABASE novel_rank
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;
USE novel_rank;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;


-- ============================================================
-- 1. 站点表 site
-- ============================================================
DROP TABLE IF EXISTS site;
CREATE TABLE site (
    id              BIGINT          NOT NULL AUTO_INCREMENT     COMMENT '主键',
    code            VARCHAR(32)     NOT NULL                    COMMENT '站点 code: qidian/fanqie/zongheng',
    name            VARCHAR(64)     NOT NULL                    COMMENT '站点显示名',
    base_url        VARCHAR(255)    NOT NULL                    COMMENT '站点根 URL',
    spider_class    VARCHAR(255)    NOT NULL                    COMMENT 'Scrapy spider 类路径',
    color           VARCHAR(16)     DEFAULT '#409EFF'           COMMENT '前端展示色',
    enabled         TINYINT(1)      NOT NULL DEFAULT 1          COMMENT '是否启用',
    sort_order      INT             NOT NULL DEFAULT 0          COMMENT '展示顺序',
    created_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
                                    ON UPDATE CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    UNIQUE KEY uk_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='小说站点配置';


-- ============================================================
-- 2. 分类字典 category
-- ============================================================
DROP TABLE IF EXISTS category;
CREATE TABLE category (
    id              BIGINT          NOT NULL AUTO_INCREMENT,
    code            VARCHAR(32)     NOT NULL                    COMMENT '分类 code',
    name            VARCHAR(32)     NOT NULL                    COMMENT '中文名',
    sort_order      INT             NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    UNIQUE KEY uk_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='小说分类字典';


-- ============================================================
-- 3. 榜单类型字典 ranking_type
-- ============================================================
DROP TABLE IF EXISTS ranking_type;
CREATE TABLE ranking_type (
    id              BIGINT          NOT NULL AUTO_INCREMENT,
    code            VARCHAR(32)     NOT NULL                    COMMENT 'daily/monthly/category',
    name            VARCHAR(32)     NOT NULL                    COMMENT '日榜/月榜/分类榜',
    description     VARCHAR(255)    DEFAULT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uk_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='榜单类型字典';


-- ============================================================
-- 4. 小说主数据 novel
-- ============================================================
DROP TABLE IF EXISTS novel;
CREATE TABLE novel (
    id              BIGINT          NOT NULL AUTO_INCREMENT     COMMENT '主键',
    site_id         BIGINT          NOT NULL                    COMMENT '所属站点',
    external_id     VARCHAR(64)     NOT NULL                    COMMENT '站点内 book_id',
    title           VARCHAR(255)    NOT NULL                    COMMENT '书名',
    author          VARCHAR(64)     NOT NULL                    COMMENT '作者',
    category        VARCHAR(32)     DEFAULT NULL                COMMENT '分类',
    cover_url       VARCHAR(512)    DEFAULT NULL                COMMENT '封面 URL',
    novel_url       VARCHAR(512)    NOT NULL                    COMMENT '小说详情页 URL',
    word_count      INT             NOT NULL DEFAULT 0          COMMENT '字数',
    status          VARCHAR(16)     NOT NULL DEFAULT 'ongoing'  COMMENT 'ongoing/completed',
    description     TEXT            DEFAULT NULL                COMMENT '简介',
    first_seen      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3)  COMMENT '首次出现',
    last_crawl_time DATETIME(3)     DEFAULT NULL                COMMENT '最近一次爬取',
    created_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
                                    ON UPDATE CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    UNIQUE KEY uk_site_external (site_id, external_id)          COMMENT '站点内小说唯一',
    KEY idx_category (category),
    KEY idx_author (author),
    KEY idx_last_crawl (last_crawl_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='小说主数据';


-- ============================================================
-- 5. 排行榜快照 ranking_record
-- (时序数据 - 只 INSERT 不 UPDATE)
-- ============================================================
DROP TABLE IF EXISTS ranking_record;
CREATE TABLE ranking_record (
    id              BIGINT          NOT NULL AUTO_INCREMENT,
    novel_id        BIGINT          NOT NULL                    COMMENT '关联 novel.id',
    site_id         BIGINT          NOT NULL                    COMMENT '冗余便于查询',
    ranking_type    VARCHAR(32)     NOT NULL                    COMMENT 'daily/monthly/category',
    category        VARCHAR(32)     DEFAULT NULL                COMMENT '分类榜的分类名',
    `rank`          INT             NOT NULL                    COMMENT '排名',
    view_count      BIGINT          NOT NULL DEFAULT 0          COMMENT '浏览量',
    rec_count       INT             NOT NULL DEFAULT 0          COMMENT '推荐数/月票等',
    crawl_time      DATETIME(3)     NOT NULL                    COMMENT '爬取时间',
    crawl_task_id   BIGINT          DEFAULT NULL                COMMENT '来源任务',
    created_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    KEY idx_novel_time (novel_id, crawl_time DESC)              COMMENT '小说趋势查询',
    KEY idx_type_time (ranking_type, crawl_time DESC)           COMMENT '榜单历史',
    KEY idx_site_type_rank (site_id, ranking_type, crawl_time DESC, `rank`)
                                                                COMMENT '最新榜单',
    KEY idx_crawl_time (crawl_time DESC),
    CONSTRAINT fk_rr_novel  FOREIGN KEY (novel_id)  REFERENCES novel(id),
    CONSTRAINT fk_rr_site   FOREIGN KEY (site_id)   REFERENCES site(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='排行榜快照(时序)';


-- ============================================================
-- 6. 爬虫任务 crawl_task
-- (Java 写入, Python 消费)
-- ============================================================
DROP TABLE IF EXISTS crawl_task;
CREATE TABLE crawl_task (
    id              BIGINT          NOT NULL AUTO_INCREMENT,
    site_id         BIGINT          NOT NULL,
    ranking_type    VARCHAR(32)     NOT NULL                    COMMENT 'daily/monthly/category',
    category        VARCHAR(32)     DEFAULT NULL                COMMENT '仅 category 榜单用',
    trigger_type    VARCHAR(16)     NOT NULL                    COMMENT 'manual/scheduled',
    status          VARCHAR(16)     NOT NULL DEFAULT 'pending'  COMMENT 'pending/running/success/failed/cancelled',
    worker_id       VARCHAR(64)     DEFAULT NULL                COMMENT '执行该任务的 worker 标识',
    progress        INT             NOT NULL DEFAULT 0          COMMENT '0-100',
    fetched_count   INT             NOT NULL DEFAULT 0          COMMENT '实际抓取条数',
    error_message   TEXT            DEFAULT NULL,
    created_by      VARCHAR(64)     DEFAULT NULL                COMMENT '手动触发时记录用户名',
    created_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    started_at      DATETIME(3)     DEFAULT NULL,
    finished_at     DATETIME(3)     DEFAULT NULL,
    PRIMARY KEY (id),
    KEY idx_status_created (status, created_at)                 COMMENT 'dispatcher 拉取',
    KEY idx_site_type_created (site_id, ranking_type, category, created_at DESC),
    CONSTRAINT fk_ct_site FOREIGN KEY (site_id) REFERENCES site(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='爬虫任务队列';


-- ============================================================
-- 7. 爬虫日志 crawl_log
-- (关键事件流 - 前端"实时日志"读这里)
-- ============================================================
DROP TABLE IF EXISTS crawl_log;
CREATE TABLE crawl_log (
    id              BIGINT          NOT NULL AUTO_INCREMENT,
    crawl_task_id   BIGINT          DEFAULT NULL                COMMENT 'NULL = 系统级日志',
    site_id         BIGINT          DEFAULT NULL,
    level           VARCHAR(8)      NOT NULL DEFAULT 'INFO'    COMMENT 'INFO/WARN/ERROR',
    message         VARCHAR(1000)   NOT NULL,
    log_time        DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    KEY idx_time_desc (log_time DESC),
    KEY idx_task (crawl_task_id, log_time),
    KEY idx_site_level_time (site_id, level, log_time DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='爬虫日志';


-- ============================================================
-- 8. 调度配置 schedule_config
-- (单行 key-value, value 是 JSON)
-- ============================================================
DROP TABLE IF EXISTS schedule_config;
CREATE TABLE schedule_config (
    id              BIGINT          NOT NULL AUTO_INCREMENT,
    `key`           VARCHAR(64)     NOT NULL,
    `value`         JSON            NOT NULL,
    description     VARCHAR(255)    DEFAULT NULL,
    updated_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
                                    ON UPDATE CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    UNIQUE KEY uk_key (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='调度配置';


-- ============================================================
-- 9. 管理员用户 sys_user
-- (简单起见只放一个 admin,密码 BCrypt 加密)
-- 默认密码: admin123
-- ============================================================
DROP TABLE IF EXISTS sys_user;
CREATE TABLE sys_user (
    id              BIGINT          NOT NULL AUTO_INCREMENT,
    username        VARCHAR(32)     NOT NULL,
    password_hash   VARCHAR(255)    NOT NULL                    COMMENT 'BCrypt',
    role            VARCHAR(16)     NOT NULL DEFAULT 'admin',
    enabled         TINYINT(1)      NOT NULL DEFAULT 1,
    last_login_at   DATETIME(3)     DEFAULT NULL,
    created_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
                                    ON UPDATE CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    UNIQUE KEY uk_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='管理员用户';


-- ============================================================
-- 视图
-- ============================================================

-- 最新一次抓取中,每个小说的最新排名
DROP VIEW IF EXISTS v_latest_ranking;
CREATE VIEW v_latest_ranking AS
SELECT
    r.*,
    ROW_NUMBER() OVER (PARTITION BY r.novel_id, r.ranking_type
                       ORDER BY r.crawl_time DESC) AS rn
FROM ranking_record r;

-- 每个(novel, ranking_type)组合的最新一条排行榜记录
DROP VIEW IF EXISTS v_latest_rank_snapshot;
CREATE VIEW v_latest_rank_snapshot AS
WITH ranked AS (
    SELECT r.*,
           ROW_NUMBER() OVER (PARTITION BY r.novel_id, r.ranking_type
                              ORDER BY r.crawl_time DESC) AS rn
    FROM ranking_record r
)
SELECT * FROM ranked WHERE rn = 1;


-- ============================================================
-- 初始数据
-- ============================================================

-- 管理员 (admin / admin123 的 BCrypt 哈希)
-- Hash: $2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy
INSERT INTO sys_user (username, password_hash, role) VALUES
('admin', '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', 'admin');

-- 分类字典
INSERT INTO category (code, name, sort_order) VALUES
('xuanhuan',    '玄幻',     1),
('dushi',       '都市',     2),
('xianxia',     '仙侠',     3),
('kehuan',      '科幻',     4),
('lishi',       '历史',     5),
('junshi',      '军事',     6),
('youxi',       '游戏',     7),
('tiyu',        '体育',     8),
('xiaoyuan',    '校园',     9),
('qihuan',      '奇幻',    10),
('yanqing',     '言情',    11),
('xuanyi',      '悬疑',    12),
('kongbu',      '恐怖',    13),
('mingzhu',     '名著',    14),
('qita',        '其他',    99);

-- 榜单类型
INSERT INTO ranking_type (code, name, description) VALUES
('daily',     '日榜',     '每日热门排行'),
('monthly',   '月榜',     '每月热门排行'),
('category',  '分类榜',   '按分类筛选的榜单'),
('total',     '总榜',     '总热门排行'),
('all',       '全部榜单', '一次任务产出 daily/monthly/total 三类榜单');

-- 站点配置 (spider_class 用 Python 类路径)
INSERT INTO site (code, name, base_url, spider_class, color, sort_order) VALUES
('qidian',   '起点中文网',  'https://www.qidian.com',  'novel_crawler.spiders.qidian.QidianSpider',   '#E72E2C', 1),
('fanqie',   '番茄小说',    'https://fanqienovel.com', 'novel_crawler.spiders.fanqie.FanqieSpider',   '#FF6633', 2),
('zongheng', '纵横中文网',  'https://www.zongheng.com', 'novel_crawler.spiders.zongheng.ZonghengSpider', '#1E9FFF', 3);

-- 调度配置 - 默认三次刷新
INSERT INTO schedule_config (`key`, `value`, description) VALUES
('main', JSON_OBJECT(
    'dailyCrawlTimes',      JSON_ARRAY('08:00', '14:00', '20:00'),
    'maxConcurrentTasks',   2,
    'taskTimeoutMinutes',   30,
    'crawlAllRankingTypes', JSON_ARRAY('daily', 'monthly', 'category')
), '调度主配置');


SET FOREIGN_KEY_CHECKS = 1;
