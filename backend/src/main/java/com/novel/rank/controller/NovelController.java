package com.novel.rank.controller;

import com.novel.rank.common.BusinessException;
import com.novel.rank.common.ErrorCode;
import com.novel.rank.common.PageResult;
import com.novel.rank.common.Result;
import com.novel.rank.service.NovelService;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/novels")
public class NovelController {

    private final NovelService novelService;

    public NovelController(NovelService novelService) {
        this.novelService = novelService;
    }

    @GetMapping("/{id}")
    public Result<Map<String, Object>> detail(@PathVariable long id) {
        return Result.success(novelService.getDetail(id));
    }

    @GetMapping("/{id}/records")
    public Result<PageResult<Map<String, Object>>> records(@PathVariable long id,
                                                           @RequestParam(required = false) String type,
                                                           @RequestParam(required = false) String startTime,
                                                           @RequestParam(required = false) String endTime,
                                                           @RequestParam(defaultValue = "1") int pageNum,
                                                           @RequestParam(defaultValue = "20") int pageSize) {
        return Result.success(novelService.getRecords(id, type, startTime, endTime, pageNum, pageSize));
    }

    @GetMapping("/{id}/trend")
    public Result<Map<String, List<Map<String, Object>>>> trend(@PathVariable long id,
                                                                @RequestParam(required = false, defaultValue = "daily") String type,
                                                                @RequestParam(defaultValue = "30") int days) {
        if (days < 1 || days > 365) {
            throw new BusinessException(ErrorCode.BAD_REQUEST, "days out of range");
        }
        return Result.success(novelService.getTrend(id, type, days));
    }

    /** 搜索小说（公开，按书名/作者） */
    @GetMapping("/search")
    public Result<List<Map<String, Object>>> search(@RequestParam String keyword,
                                                     @RequestParam(defaultValue = "20") int limit) {
        return Result.success(novelService.search(keyword, limit));
    }
}
