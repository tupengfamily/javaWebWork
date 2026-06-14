package com.novel.rank.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.novel.rank.common.BusinessException;
import com.novel.rank.common.ErrorCode;
import com.novel.rank.common.PageResult;
import com.novel.rank.dto.CreateTaskRequest;
import com.novel.rank.entity.CrawlLog;
import com.novel.rank.entity.CrawlTask;
import com.novel.rank.entity.Site;
import com.novel.rank.mapper.CrawlLogMapper;
import com.novel.rank.mapper.CrawlTaskMapper;
import com.novel.rank.mapper.SiteMapper;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class TaskService {

    private final CrawlTaskMapper taskMapper;
    private final CrawlLogMapper logMapper;
    private final SiteMapper siteMapper;

    public TaskService(CrawlTaskMapper taskMapper, CrawlLogMapper logMapper, SiteMapper siteMapper) {
        this.taskMapper = taskMapper;
        this.logMapper = logMapper;
        this.siteMapper = siteMapper;
    }

    public PageResult<Map<String, Object>> listTasks(String status, String siteCode, String triggerType,
                                                     LocalDateTime startTime, LocalDateTime endTime,
                                                     int pageNum, int pageSize) {
        if (pageNum < 1) pageNum = 1;
        if (pageSize < 1 || pageSize > 100) pageSize = 20;
        long offset = (pageNum - 1) * pageSize;
        long total = taskMapper.countTaskPage(status, siteCode, triggerType, startTime, endTime);
        List<Map<String, Object>> records = total == 0
                ? Collections.emptyList()
                : taskMapper.selectTaskPage(status, siteCode, triggerType, startTime, endTime, offset, pageSize);
        PageResult<Map<String, Object>> pr = new PageResult<>();
        pr.setRecords(records);
        pr.setTotal(total);
        pr.setPageNum(pageNum);
        pr.setPageSize(pageSize);
        pr.setPages((total + pageSize - 1) / pageSize);
        return pr;
    }

    public Long createTask(CreateTaskRequest req, String createdBy) {
        Site site = siteMapper.selectOne(
                new LambdaQueryWrapper<Site>().eq(Site::getCode, req.getSiteCode()));
        if (site == null) {
            throw new BusinessException(ErrorCode.NOT_FOUND, "site not found");
        }
        if (Boolean.FALSE.equals(site.getEnabled())) {
            throw new BusinessException(ErrorCode.BAD_REQUEST, "site disabled");
        }

        String category = req.getCategory() == null ? "" : req.getCategory();
        Long exist = taskMapper.selectCount(new LambdaQueryWrapper<CrawlTask>()
                .eq(CrawlTask::getSiteId, site.getId())
                .eq(CrawlTask::getRankingType, req.getRankingType())
                .eq(CrawlTask::getCategory, category)
                .in(CrawlTask::getStatus, "pending", "running"));
        if (exist != null && exist > 0) {
            throw new BusinessException(ErrorCode.DUPLICATE_TASK);
        }

        CrawlTask t = new CrawlTask();
        t.setSiteId(site.getId());
        t.setRankingType(req.getRankingType());
        t.setCategory(req.getCategory());
        t.setTriggerType("manual");
        t.setStatus("pending");
        t.setCreatedBy(createdBy);
        t.setCreatedAt(LocalDateTime.now());
        taskMapper.insert(t);
        return t.getId();
    }

    public void cancel(long id) {
        CrawlTask t = taskMapper.selectById(id);
        if (t == null) throw new BusinessException(ErrorCode.NOT_FOUND, "task not found");
        if (!"pending".equals(t.getStatus())) {
            throw new BusinessException(ErrorCode.BAD_REQUEST, "cannot cancel running task");
        }
        CrawlTask upd = new CrawlTask();
        upd.setId(id);
        upd.setStatus("cancelled");
        upd.setFinishedAt(LocalDateTime.now());
        taskMapper.updateById(upd);
    }

    public Long retry(long id) {
        CrawlTask t = taskMapper.selectById(id);
        if (t == null) throw new BusinessException(ErrorCode.NOT_FOUND, "task not found");
        if (!"failed".equals(t.getStatus())) {
            throw new BusinessException(ErrorCode.BAD_REQUEST, "only failed tasks can be retried");
        }
        CrawlTask nt = new CrawlTask();
        nt.setSiteId(t.getSiteId());
        nt.setRankingType(t.getRankingType());
        nt.setCategory(t.getCategory());
        nt.setTriggerType("manual");
        nt.setStatus("pending");
        nt.setCreatedAt(LocalDateTime.now());
        taskMapper.insert(nt);
        return nt.getId();
    }

    public Map<String, Object> getLog(long id) {
        CrawlTask t = taskMapper.selectById(id);
        if (t == null) throw new BusinessException(ErrorCode.NOT_FOUND, "task not found");
        List<CrawlLog> logs = logMapper.selectList(
                new LambdaQueryWrapper<CrawlLog>()
                        .eq(CrawlLog::getCrawlTaskId, id)
                        .orderByAsc(CrawlLog::getLogTime)
        );
        Map<String, Object> out = new HashMap<>();
        out.put("task", t);
        out.put("logs", logs);
        return out;
    }
}
