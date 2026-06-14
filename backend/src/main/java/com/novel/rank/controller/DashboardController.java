package com.novel.rank.controller;

import com.novel.rank.common.Result;
import com.novel.rank.service.DashboardService;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/admin/dashboard")
public class DashboardController {

    private final DashboardService dashboardService;

    public DashboardController(DashboardService dashboardService) {
        this.dashboardService = dashboardService;
    }

    @GetMapping("/logs")
    public Result<Map<String, Object>> logs(@RequestParam(required = false) String level,
                                            @RequestParam(required = false) String site,
                                            @RequestParam(defaultValue = "100") int limit,
                                            @RequestParam(required = false)
                                            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime before) {
        return Result.success(dashboardService.listLogs(level, site, limit, before));
    }

    @GetMapping("/sites")
    public Result<List<Map<String, Object>>> sites() {
        return Result.success(dashboardService.siteStatus());
    }
}
