package com.novel.rank.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import java.time.LocalDateTime;

@TableName("ranking_record")
public class RankingRecord {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long novelId;
    private Long siteId;
    private String rankingType;
    private String category;
    @TableField("`rank`")
    private Integer rank;
    private Long viewCount;
    private Integer recCount;
    private LocalDateTime crawlTime;
    private Long crawlTaskId;
    private LocalDateTime createdAt;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Long getNovelId() { return novelId; }
    public void setNovelId(Long novelId) { this.novelId = novelId; }
    public Long getSiteId() { return siteId; }
    public void setSiteId(Long siteId) { this.siteId = siteId; }
    public String getRankingType() { return rankingType; }
    public void setRankingType(String rankingType) { this.rankingType = rankingType; }
    public String getCategory() { return category; }
    public void setCategory(String category) { this.category = category; }
    public Integer getRank() { return rank; }
    public void setRank(Integer rank) { this.rank = rank; }
    public Long getViewCount() { return viewCount; }
    public void setViewCount(Long viewCount) { this.viewCount = viewCount; }
    public Integer getRecCount() { return recCount; }
    public void setRecCount(Integer recCount) { this.recCount = recCount; }
    public LocalDateTime getCrawlTime() { return crawlTime; }
    public void setCrawlTime(LocalDateTime crawlTime) { this.crawlTime = crawlTime; }
    public Long getCrawlTaskId() { return crawlTaskId; }
    public void setCrawlTaskId(Long crawlTaskId) { this.crawlTaskId = crawlTaskId; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}
