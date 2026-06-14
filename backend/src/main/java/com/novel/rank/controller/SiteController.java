package com.novel.rank.controller;

import com.novel.rank.common.Result;
import com.novel.rank.entity.Site;
import com.novel.rank.service.SiteService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/sites")
public class SiteController {

    private final SiteService siteService;

    public SiteController(SiteService siteService) {
        this.siteService = siteService;
    }

    @GetMapping
    public Result<List<Site>> list() {
        return Result.success(siteService.listEnabled());
    }
}
