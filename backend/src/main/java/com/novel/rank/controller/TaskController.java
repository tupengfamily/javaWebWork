package com.novel.rank.controller;

import com.novel.rank.common.PageResult;
import com.novel.rank.common.Result;
import com.novel.rank.dto.CreateTaskRequest;
import com.novel.rank.security.AuthenticatedUser;
import com.novel.rank.service.TaskService;
import jakarta.validation.Valid;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/admin/tasks")
public class TaskController {

    private final TaskService taskService;

    public TaskController(TaskService taskService) {
        this.taskService = taskService;
    }

    @GetMapping
    public Result<PageResult<Map<String, Object>>> list(
            @RequestParam(required = false) String status,
            @RequestParam(required = false) String site,
            @RequestParam(required = false) String triggerType,
            @RequestParam(required = false)
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime startTime,
            @RequestParam(required = false)
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime endTime,
            @RequestParam(defaultValue = "1") int pageNum,
            @RequestParam(defaultValue = "20") int pageSize) {
        return Result.success(taskService.listTasks(status, site, triggerType,
                startTime, endTime, pageNum, pageSize));
    }

    @PostMapping
    public Result<Map<String, Object>> create(@RequestBody @Valid CreateTaskRequest req,
                                               @AuthenticationPrincipal AuthenticatedUser principal) {
        Long id = taskService.createTask(req, principal == null ? null : principal.getUsername());
        Map<String, Object> out = new HashMap<>();
        out.put("taskId", id);
        return Result.success(out);
    }

    @PostMapping("/{id}/cancel")
    public Result<Void> cancel(@PathVariable long id) {
        taskService.cancel(id);
        return Result.success();
    }

    @PostMapping("/{id}/retry")
    public Result<Map<String, Object>> retry(@PathVariable long id) {
        Long newId = taskService.retry(id);
        Map<String, Object> out = new HashMap<>();
        out.put("taskId", newId);
        return Result.success(out);
    }

    @GetMapping("/{id}/log")
    public Result<Map<String, Object>> log(@PathVariable long id) {
        return Result.success(taskService.getLog(id));
    }
}
