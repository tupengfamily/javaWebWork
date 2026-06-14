package com.novel.rank.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.novel.rank.entity.CrawlTask;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Mapper
public interface CrawlTaskMapper extends BaseMapper<CrawlTask> {

    List<Map<String, Object>> selectTaskPage(@Param("status") String status,
                                             @Param("siteCode") String siteCode,
                                             @Param("triggerType") String triggerType,
                                             @Param("startTime") LocalDateTime startTime,
                                             @Param("endTime") LocalDateTime endTime,
                                             @Param("offset") long offset,
                                             @Param("size") long size);

    long countTaskPage(@Param("status") String status,
                       @Param("siteCode") String siteCode,
                       @Param("triggerType") String triggerType,
                       @Param("startTime") LocalDateTime startTime,
                       @Param("endTime") LocalDateTime endTime);

    List<Map<String, Object>> selectLatestTaskPerSite();

    List<Map<String, Object>> countRecentFailures();
}
