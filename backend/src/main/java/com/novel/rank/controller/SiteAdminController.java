package com.novel.rank.controller;

import com.novel.rank.common.PageResult;
import com.novel.rank.common.Result;
import com.novel.rank.entity.Site;
import com.novel.rank.service.SiteService;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/admin/sites")
public class SiteAdminController {

    private final SiteService siteService;

    public SiteAdminController(SiteService siteService) {
        this.siteService = siteService;
    }

    @GetMapping
    public Result<PageResult<Site>> page(@RequestParam(defaultValue = "1") int pageNum,
                                         @RequestParam(defaultValue = "20") int pageSize) {
        return Result.success(siteService.page(pageNum, pageSize));
    }

    @PostMapping
    public Result<Site> create(@RequestBody Site s) {
        return Result.success(siteService.create(s));
    }

    @PutMapping("/{id}")
    public Result<Site> update(@PathVariable long id, @RequestBody Site s) {
        return Result.success(siteService.update(id, s));
    }

    @DeleteMapping("/{id}")
    public Result<Void> delete(@PathVariable long id) {
        siteService.delete(id);
        return Result.success();
    }
}
