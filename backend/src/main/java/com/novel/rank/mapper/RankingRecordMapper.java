package com.novel.rank.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.novel.rank.entity.RankingRecord;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;
import java.util.Map;

@Mapper
public interface RankingRecordMapper extends BaseMapper<RankingRecord> {

    List<Map<String, Object>> selectLatestRanking(@Param("siteCode") String siteCode,
                                                  @Param("rankingType") String rankingType,
                                                  @Param("category") String category,
                                                  @Param("keyword") String keyword,
                                                  @Param("offset") long offset,
                                                  @Param("size") long size);

    long countLatestRanking(@Param("siteCode") String siteCode,
                            @Param("rankingType") String rankingType,
                            @Param("category") String category,
                            @Param("keyword") String keyword);

    List<Map<String, Object>> selectNovelTrend(@Param("novelId") long novelId,
                                               @Param("rankingType") String rankingType,
                                               @Param("days") int days);

    List<Map<String, Object>> selectMultiNovelTrend(@Param("novelIds") List<Long> novelIds,
                                                    @Param("metric") String metric,
                                                    @Param("days") int days);

    List<Map<String, Object>> selectCrossSiteTop(@Param("limit") int limit,
                                                 @Param("category") String category);
}
