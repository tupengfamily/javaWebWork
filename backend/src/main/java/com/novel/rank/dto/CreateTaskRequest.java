package com.novel.rank.dto;

import jakarta.validation.constraints.NotBlank;

public class CreateTaskRequest {
    @NotBlank(message = "siteCode 必填")
    private String siteCode;

    @NotBlank(message = "rankingType 必填")
    private String rankingType;

    private String category;

    public String getSiteCode() { return siteCode; }
    public void setSiteCode(String siteCode) { this.siteCode = siteCode; }
    public String getRankingType() { return rankingType; }
    public void setRankingType(String rankingType) { this.rankingType = rankingType; }
    public String getCategory() { return category; }
    public void setCategory(String category) { this.category = category; }
}
