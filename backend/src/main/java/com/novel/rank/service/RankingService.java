package com.novel.rank.service;

import com.novel.rank.common.BusinessException;
import com.novel.rank.common.ErrorCode;
import com.novel.rank.common.PageResult;
import com.novel.rank.mapper.RankingRecordMapper;
import org.springframework.stereotype.Service;

import java.util.*;

@Service
public class RankingService {

    private final RankingRecordMapper rankingMapper;

    public RankingService(RankingRecordMapper rankingMapper) {
        this.rankingMapper = rankingMapper;
    }

    public PageResult<Map<String, Object>> listLatest(String siteCode, String rankingType,
                                                      String category, String keyword,
                                                      int pageNum, int pageSize) {
        if (siteCode == null || siteCode.isBlank()) {
            throw new BusinessException(ErrorCode.BAD_REQUEST, "site required");
        }
        if (rankingType == null || rankingType.isBlank()) {
            throw new BusinessException(ErrorCode.BAD_REQUEST, "type required");
        }
        if ("category".equals(rankingType) && (category == null || category.isBlank())) {
            throw new BusinessException(ErrorCode.BAD_REQUEST, "category required when type=category");
        }
        if (pageNum < 1) pageNum = 1;
        if (pageSize < 1 || pageSize > 100) pageSize = 20;

        long offset = (pageNum - 1) * pageSize;
        long total = rankingMapper.countLatestRanking(siteCode, rankingType, category, keyword);
        List<Map<String, Object>> records = total == 0
                ? Collections.emptyList()
                : rankingMapper.selectLatestRanking(siteCode, rankingType, category, keyword, offset, pageSize);

        PageResult<Map<String, Object>> pr = new PageResult<>();
        pr.setRecords(records);
        pr.setTotal(total);
        pr.setPageNum(pageNum);
        pr.setPageSize(pageSize);
        pr.setPages((total + pageSize - 1) / pageSize);
        return pr;
    }

    public Map<String, Object> compareTrend(List<Long> novelIds, String metric, int days) {
        if (novelIds == null || novelIds.isEmpty()) {
            throw new BusinessException(ErrorCode.BAD_REQUEST, "novelIds required");
        }
        if (novelIds.size() > 5) {
            throw new BusinessException(ErrorCode.BAD_REQUEST, "max 5 novels");
        }
        if (days < 1 || days > 90) days = 7;

        List<Map<String, Object>> rows = rankingMapper.selectMultiNovelTrend(novelIds, metric, days);

        Map<Long, Map<String, Object>> seriesMap = new LinkedHashMap<>();
        for (Long nid : novelIds) {
            Map<String, Object> s = new HashMap<>();
            s.put("novelId", nid);
            s.put("title", "");
            s.put("siteCode", "");
            s.put("color", "#409EFF");
            s.put("points", new ArrayList<Map<String, Object>>());
            seriesMap.put(nid, s);
        }
        for (Map<String, Object> r : rows) {
            Long nid = ((Number) r.get("novelId")).longValue();
            Map<String, Object> s = seriesMap.get(nid);
            if (s == null) continue;
            s.put("title", r.get("title"));
            s.put("siteCode", r.get("siteCode"));
            s.put("color", r.get("color"));
            Map<String, Object> pt = new HashMap<>();
            pt.put("time", r.get("time"));
            pt.put("value", r.get("value"));
            @SuppressWarnings("unchecked")
            List<Map<String, Object>> points = (List<Map<String, Object>>) s.get("points");
            points.add(pt);
        }
        Map<String, Object> out = new HashMap<>();
        out.put("metric", metric);
        out.put("series", new ArrayList<>(seriesMap.values()));
        return out;
    }

    public List<Map<String, Object>> topList(int limit, String by, String category) {
        if (limit < 1 || limit > 50) limit = 10;
        return rankingMapper.selectCrossSiteTop(limit, category);
    }
}
