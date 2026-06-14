package com.novel.rank.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import java.time.LocalDateTime;

@TableName("crawl_log")
public class CrawlLog {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long crawlTaskId;
    private Long siteId;
    private String level;
    private String message;
    private LocalDateTime logTime;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Long getCrawlTaskId() { return crawlTaskId; }
    public void setCrawlTaskId(Long crawlTaskId) { this.crawlTaskId = crawlTaskId; }
    public Long getSiteId() { return siteId; }
    public void setSiteId(Long siteId) { this.siteId = siteId; }
    public String getLevel() { return level; }
    public void setLevel(String level) { this.level = level; }
    public String getMessage() { return message; }
    public void setMessage(String message) { this.message = message; }
    public LocalDateTime getLogTime() { return logTime; }
    public void setLogTime(LocalDateTime logTime) { this.logTime = logTime; }
}
