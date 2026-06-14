package com.novel.rank.controller;

import com.novel.rank.common.Result;
import com.novel.rank.service.ScheduleService;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/admin/schedule")
public class ScheduleController {

    private final ScheduleService scheduleService;

    public ScheduleController(ScheduleService scheduleService) {
        this.scheduleService = scheduleService;
    }

    @GetMapping
    public Result<Map<String, Object>> get() {
        return Result.success(scheduleService.get());
    }

    @PutMapping
    public Result<Void> update(@RequestBody Map<String, Object> body) {
        scheduleService.update(body);
        return Result.success();
    }
}
