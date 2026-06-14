package com.novel.rank.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.novel.rank.common.BusinessException;
import com.novel.rank.common.ErrorCode;
import com.novel.rank.common.PageResult;
import com.novel.rank.entity.RankingRecord;
import com.novel.rank.mapper.NovelMapper;
import com.novel.rank.mapper.RankingRecordMapper;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class NovelService {

    private final NovelMapper novelMapper;
    private final RankingRecordMapper rankingRecordMapper;

    public NovelService(NovelMapper novelMapper, RankingRecordMapper rankingRecordMapper) {
        this.novelMapper = novelMapper;
        this.rankingRecordMapper = rankingRecordMapper;
    }

    public Map<String, Object> getDetail(long id) {
        Map<String, Object> detail = novelMapper.selectNovelDetail(id);
        if (detail == null) {
            throw new BusinessException(ErrorCode.NOT_FOUND, "novel not found");
        }
        return detail;
    }

    public PageResult<Map<String, Object>> getRecords(long id, String type, String startTime, String endTime,
                                                      int pageNum, int pageSize) {
        Page<RankingRecord> p = Page.of(pageNum, pageSize);
        LambdaQueryWrapper<RankingRecord> q = new LambdaQueryWrapper<RankingRecord>()
                .eq(RankingRecord::getNovelId, id)
                .orderByDesc(RankingRecord::getCrawlTime);
        if (type != null && !type.isBlank()) q.eq(RankingRecord::getRankingType, type);
        if (startTime != null && !startTime.isBlank()) q.ge(RankingRecord::getCrawlTime, startTime);
        if (endTime != null && !endTime.isBlank()) q.le(RankingRecord::getCrawlTime, endTime);
        Page<RankingRecord> res = rankingRecordMapper.selectPage(p, q);
        PageResult<RankingRecord> pr = PageResult.of(res);
        PageResult<Map<String, Object>> out = new PageResult<>();
        List<Map<String, Object>> flatList = new ArrayList<>();
        for (RankingRecord r : pr.getRecords()) {
            Map<String, Object> item = new HashMap<>();
            item.put("id", r.getId());
            item.put("crawlTime", r.getCrawlTime());
            item.put("rankingType", r.getRankingType());
            item.put("category", r.getCategory());
            item.put("rank", r.getRank());
            item.put("viewCount", r.getViewCount());
            item.put("recCount", r.getRecCount());
            item.put("crawlTaskId", r.getCrawlTaskId());
            flatList.add(item);
        }
        out.setRecords(flatList);
        out.setTotal(pr.getTotal());
        out.setPageNum(pr.getPageNum());
        out.setPageSize(pr.getPageSize());
        out.setPages(pr.getPages());
        return out;
    }

    public Map<String, List<Map<String, Object>>> getTrend(long id, String type, int days) {
        List<Map<String, Object>> rows = rankingRecordMapper.selectNovelTrend(id, type, days);
        List<Map<String, Object>> ranking = new ArrayList<>();
        List<Map<String, Object>> view = new ArrayList<>();
        List<Map<String, Object>> rec = new ArrayList<>();
        for (Map<String, Object> r : rows) {
            String t = String.valueOf(r.get("time"));
            ranking.add(point(t, ((Number) r.get("rank")).intValue()));
            view.add(point(t, ((Number) r.get("viewCount")).longValue()));
            rec.add(point(t, ((Number) r.get("recCount")).intValue()));
        }
        Map<String, List<Map<String, Object>>> out = new HashMap<>();
        out.put("ranking", ranking);
        out.put("viewCount", view);
        out.put("recCount", rec);
        return out;
    }

    private static Map<String, Object> point(String t, Object v) {
        Map<String, Object> m = new HashMap<>();
        m.put("time", t);
        m.put("value", v);
        return m;
    }
}
