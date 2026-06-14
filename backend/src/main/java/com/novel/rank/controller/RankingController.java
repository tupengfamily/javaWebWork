package com.novel.rank.controller;

import com.novel.rank.common.PageResult;
import com.novel.rank.common.Result;
import com.novel.rank.service.RankingService;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
public class RankingController {

    private final RankingService rankingService;

    public RankingController(RankingService rankingService) {
        this.rankingService = rankingService;
    }

    @GetMapping("/api/rankings")
    public Result<PageResult<Map<String, Object>>> list(@RequestParam String site,
                                                        @RequestParam String type,
                                                        @RequestParam(required = false) String category,
                                                        @RequestParam(required = false) String keyword,
                                                        @RequestParam(defaultValue = "1") int pageNum,
                                                        @RequestParam(defaultValue = "20") int pageSize) {
        return Result.success(rankingService.listLatest(site, type, category, keyword, pageNum, pageSize));
    }

    @GetMapping("/api/trends/compare")
    public Result<Map<String, Object>> compare(@RequestParam String novelIds,
                                               @RequestParam String metric,
                                               @RequestParam(defaultValue = "7") int days) {
        List<Long> ids = java.util.Arrays.stream(novelIds.split(","))
                .map(String::trim).filter(s -> !s.isEmpty())
                .map(Long::parseLong).toList();
        return Result.success(rankingService.compareTrend(ids, metric, days));
    }

    @GetMapping("/api/trends/top")
    public Result<List<Map<String, Object>>> top(@RequestParam(defaultValue = "10") int limit,
                                                 @RequestParam(required = false, defaultValue = "viewCount") String by,
                                                 @RequestParam(required = false) String category) {
        return Result.success(rankingService.topList(limit, by, category));
    }
}
