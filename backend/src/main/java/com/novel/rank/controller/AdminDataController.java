package com.novel.rank.controller;

import com.novel.rank.common.Result;
import com.novel.rank.entity.Site;
import com.novel.rank.mapper.NovelMapper;
import com.novel.rank.mapper.RankingRecordMapper;
import com.novel.rank.service.SiteService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/admin/data")
public class AdminDataController {

    private final NovelMapper novelMapper;
    private final RankingRecordMapper rankingRecordMapper;
    private final SiteService siteService;

    public AdminDataController(NovelMapper novelMapper, RankingRecordMapper rankingRecordMapper, SiteService siteService) {
        this.novelMapper = novelMapper;
        this.rankingRecordMapper = rankingRecordMapper;
        this.siteService = siteService;
    }

    /** 数据质量仪表盘 — 各站点数据完整性统计 */
    @GetMapping("/quality")
    public Result<List<Map<String, Object>>> quality() {
        List<Site> sites = siteService.listEnabled();
        List<Map<String, Object>> result = new ArrayList<>();

        for (Site site : sites) {
            Map<String, Object> row = new LinkedHashMap<>();
            long siteId = site.getId();

            // 基础计数
            long total = novelMapper.selectCount(
                    new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<com.novel.rank.entity.Novel>()
                            .eq(com.novel.rank.entity.Novel::getSiteId, siteId));
            long noCover = novelMapper.selectCount(
                    new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<com.novel.rank.entity.Novel>()
                            .eq(com.novel.rank.entity.Novel::getSiteId, siteId)
                            .and(w -> w.isNull(com.novel.rank.entity.Novel::getCoverUrl).or()
                                    .eq(com.novel.rank.entity.Novel::getCoverUrl, "")));
            long noDescription = novelMapper.selectCount(
                    new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<com.novel.rank.entity.Novel>()
                            .eq(com.novel.rank.entity.Novel::getSiteId, siteId)
                            .and(w -> w.isNull(com.novel.rank.entity.Novel::getDescription).or()
                                    .eq(com.novel.rank.entity.Novel::getDescription, "")));
            long noAuthor = novelMapper.selectCount(
                    new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<com.novel.rank.entity.Novel>()
                            .eq(com.novel.rank.entity.Novel::getSiteId, siteId)
                            .and(w -> w.isNull(com.novel.rank.entity.Novel::getAuthor).or()
                                    .eq(com.novel.rank.entity.Novel::getAuthor, "")
                                    .or().eq(com.novel.rank.entity.Novel::getAuthor, "未知")));
            long recordCount = rankingRecordMapper.selectCount(
                    new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<com.novel.rank.entity.RankingRecord>()
                            .eq(com.novel.rank.entity.RankingRecord::getSiteId, siteId));

            // 完整率 = 4项都有的小说占比
            long fullCount = total - noCover - noDescription - noAuthor;
            if (fullCount < 0) fullCount = 0;
            double completeness = total > 0 ? Math.round(fullCount * 10000.0 / total) / 100.0 : 0;

            row.put("siteId", siteId);
            row.put("siteCode", site.getCode());
            row.put("siteName", site.getName());
            row.put("color", site.getColor());
            row.put("total", total);
            row.put("noCover", noCover);
            row.put("noDescription", noDescription);
            row.put("noAuthor", noAuthor);
            row.put("recordCount", recordCount);
            row.put("completeness", completeness);
            result.add(row);
        }

        return Result.success(result);
    }
}
