package com.novel.rank.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.novel.rank.entity.CrawlLog;
import com.novel.rank.mapper.CrawlLogMapper;
import com.novel.rank.mapper.CrawlTaskMapper;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.*;

@Service
public class DashboardService {

    private final CrawlLogMapper logMapper;
    private final CrawlTaskMapper taskMapper;

    public DashboardService(CrawlLogMapper logMapper, CrawlTaskMapper taskMapper) {
        this.logMapper = logMapper;
        this.taskMapper = taskMapper;
    }

    public Map<String, Object> listLogs(String level, String siteCode, int limit, LocalDateTime before) {
        if (limit < 1 || limit > 500) limit = 100;
        LambdaQueryWrapper<CrawlLog> q = new LambdaQueryWrapper<CrawlLog>()
                .orderByDesc(CrawlLog::getLogTime)
                .last("LIMIT " + limit);
        if (level != null && !level.isBlank()) q.eq(CrawlLog::getLevel, level);
        if (before != null) q.lt(CrawlLog::getLogTime, before);
        List<CrawlLog> logs = logMapper.selectList(q);
        LocalDateTime nextBefore = logs.isEmpty() ? null : logs.get(logs.size() - 1).getLogTime();
        Map<String, Object> out = new HashMap<>();
        out.put("records", logs);
        out.put("nextBefore", nextBefore);
        return out;
    }

    public List<Map<String, Object>> siteStatus() {
        List<Map<String, Object>> sites = taskMapper.selectLatestTaskPerSite();
        Map<Long, Long> failureMap = new HashMap<>();
        for (Map<String, Object> f : taskMapper.countRecentFailures()) {
            failureMap.put(((Number) f.get("siteId")).longValue(),
                           ((Number) f.get("failureCount")).longValue());
        }
        for (Map<String, Object> s : sites) {
            Object siteIdObj = s.get("siteId");
            if (siteIdObj == null) continue;
            Long siteId = ((Number) siteIdObj).longValue();
            s.put("recentFailureCount", failureMap.getOrDefault(siteId, 0L));
            if (s.get("lastTaskId") != null) {
                Map<String, Object> lt = new HashMap<>();
                lt.put("id", s.remove("lastTaskId"));
                lt.put("status", s.remove("lastTaskStatus"));
                lt.put("finishedAt", s.remove("lastTaskFinishedAt"));
                lt.put("fetchedCount", s.remove("lastTaskFetchedCount"));
                s.put("lastTask", lt);
            } else {
                s.remove("lastTaskId");
                s.remove("lastTaskStatus");
                s.remove("lastTaskFinishedAt");
                s.remove("lastTaskFetchedCount");
                s.put("lastTask", null);
            }
        }
        return sites;
    }
}
