package com.novel.rank.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.novel.rank.common.BusinessException;
import com.novel.rank.common.ErrorCode;
import com.novel.rank.entity.ScheduleConfig;
import com.novel.rank.mapper.ScheduleConfigMapper;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class ScheduleService {

    private final ScheduleConfigMapper configMapper;
    private final ObjectMapper objectMapper = new ObjectMapper();

    private static final String KEY = "main";

    public ScheduleService(ScheduleConfigMapper configMapper) {
        this.configMapper = configMapper;
    }

    public Map<String, Object> get() {
        ScheduleConfig c = configMapper.selectOne(
                new LambdaQueryWrapper<ScheduleConfig>().eq(ScheduleConfig::getKey, KEY));
        if (c == null) {
            throw new BusinessException(ErrorCode.NOT_FOUND, "schedule config not found");
        }
        return parse(c);
    }

    public void update(Map<String, Object> body) {
        @SuppressWarnings("unchecked")
        List<String> times = (List<String>) body.get("dailyCrawlTimes");
        if (times == null) {
            throw new BusinessException(ErrorCode.BAD_REQUEST, "dailyCrawlTimes required");
        }
        if (times.size() < 1 || times.size() > 5) {
            throw new BusinessException(ErrorCode.BAD_REQUEST, "1-5 time points allowed");
        }
        for (String t : times) {
            if (t == null || !t.matches("^([01]\\d|2[0-3]):[0-5]\\d$")) {
                throw new BusinessException(ErrorCode.INVALID_SCHEDULE_TIME);
            }
        }
        List<Integer> mins = times.stream()
                .map(t -> Integer.parseInt(t.split(":")[0]) * 60 + Integer.parseInt(t.split(":")[1]))
                .sorted()
                .toList();
        for (int i = 1; i < mins.size(); i++) {
            if (mins.get(i) - mins.get(i - 1) < 30) {
                throw new BusinessException(ErrorCode.BAD_REQUEST, "interval must be >= 30 minutes");
            }
        }

        Integer maxConc = (Integer) body.get("maxConcurrentTasks");
        if (maxConc == null || maxConc < 1 || maxConc > 10) {
            throw new BusinessException(ErrorCode.BAD_REQUEST, "maxConcurrentTasks must be 1-10");
        }
        Integer timeout = (Integer) body.get("taskTimeoutMinutes");
        if (timeout == null || timeout < 5 || timeout > 240) {
            throw new BusinessException(ErrorCode.BAD_REQUEST, "taskTimeoutMinutes must be 5-240");
        }

        Map<String, Object> value = new HashMap<>();
        value.put("dailyCrawlTimes", times);
        value.put("maxConcurrentTasks", maxConc);
        value.put("taskTimeoutMinutes", timeout);
        @SuppressWarnings("unchecked")
        List<String> types = (List<String>) body.get("crawlAllRankingTypes");
        if (types == null || types.isEmpty()) types = List.of("daily", "monthly", "category");
        value.put("crawlAllRankingTypes", types);

        String json;
        try {
            json = objectMapper.writeValueAsString(value);
        } catch (Exception e) {
            throw new BusinessException(ErrorCode.INTERNAL_ERROR, "serialize failed");
        }

        ScheduleConfig c = configMapper.selectOne(
                new LambdaQueryWrapper<ScheduleConfig>().eq(ScheduleConfig::getKey, KEY));
        if (c == null) {
            c = new ScheduleConfig();
            c.setKey(KEY);
            c.setValue(json);
            c.setDescription("main schedule config");
            c.setUpdatedAt(LocalDateTime.now());
            configMapper.insert(c);
        } else {
            c.setValue(json);
            c.setUpdatedAt(LocalDateTime.now());
            configMapper.updateById(c);
        }
    }

    private Map<String, Object> parse(ScheduleConfig c) {
        try {
            Map<String, Object> value = objectMapper.readValue(c.getValue(), new TypeReference<>() {});
            value.put("updatedAt", c.getUpdatedAt());
            return value;
        } catch (Exception e) {
            throw new BusinessException(ErrorCode.INTERNAL_ERROR, "parse failed");
        }
    }
}
