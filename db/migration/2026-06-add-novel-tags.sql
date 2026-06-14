-- ============================================================
-- Migration: 2026-06 - rich-crawler-data
-- 1) novel 表新增 tags 列(逗号分隔标签,最多 1024 字符)
-- 2) schedule_config 更新默认 taskTimeoutMinutes / crawlAllRankingTypes
-- ============================================================

USE novel_rank;

-- 1) novel.tags(可空,旧数据保持 NULL)
ALTER TABLE novel
    ADD COLUMN tags VARCHAR(1024) DEFAULT NULL
        COMMENT '逗号分隔标签(2-8 个,详情页抽取)'
        AFTER description;

-- 2) schedule_config (只更新不重建,保留用户现有值)
-- 思路: JSON_SET 在 `value` JSON 对象上按 path 替换字段
-- 若用户没配 main key,INSERT 默认值(用 INSERT IGNORE 兜底)
INSERT IGNORE INTO schedule_config (`key`, `value`, description) VALUES
('main', JSON_OBJECT(
    'dailyCrawlTimes',      JSON_ARRAY('08:00', '14:00', '20:00'),
    'maxConcurrentTasks',   2,
    'taskTimeoutMinutes',   60,
    'crawlAllRankingTypes', JSON_ARRAY('daily', 'monthly', 'total', 'yuepiao', 'newbook', 'finish')
), '调度主配置');

-- 已有 main key 的,只更新 2 个字段
UPDATE schedule_config
SET `value` = JSON_SET(
    `value`,
    '$.taskTimeoutMinutes', 60,
    '$.crawlAllRankingTypes', JSON_ARRAY('daily','monthly','total','yuepiao','newbook','finish')
)
WHERE `key` = 'main';

-- 验证
SELECT 'after migration:' AS phase;
DESC novel;
SELECT JSON_PRETTY(`value`) AS schedule_main
FROM schedule_config WHERE `key` = 'main';
