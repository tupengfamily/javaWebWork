package com.novel.rank.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.novel.rank.common.PageResult;
import com.novel.rank.common.Result;
import com.novel.rank.entity.Novel;
import com.novel.rank.entity.RankingRecord;
import com.novel.rank.mapper.NovelMapper;
import com.novel.rank.mapper.RankingRecordMapper;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.io.PrintWriter;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/admin/novels")
public class AdminNovelController {

    private final NovelMapper novelMapper;
    private final RankingRecordMapper rankingRecordMapper;

    public AdminNovelController(NovelMapper novelMapper, RankingRecordMapper rankingRecordMapper) {
        this.novelMapper = novelMapper;
        this.rankingRecordMapper = rankingRecordMapper;
    }

    /** 分页查询小说列表（管理员视角，支持高级筛选） */
    @GetMapping
    public Result<PageResult<Novel>> page(@RequestParam(defaultValue = "1") int pageNum,
                                          @RequestParam(defaultValue = "20") int pageSize,
                                          @RequestParam(required = false) String keyword,
                                          @RequestParam(required = false) Long siteId,
                                          @RequestParam(required = false) Boolean hasCover,
                                          @RequestParam(required = false) Boolean hasDescription,
                                          @RequestParam(required = false) Boolean hasAuthor,
                                          @RequestParam(required = false) Integer updatedDays) {
        LambdaQueryWrapper<Novel> q = new LambdaQueryWrapper<Novel>()
                .orderByDesc(Novel::getLastCrawlTime)
                .orderByDesc(Novel::getId);
        if (keyword != null && !keyword.isBlank()) {
            q.and(w -> w.like(Novel::getTitle, keyword).or().like(Novel::getAuthor, keyword));
        }
        if (siteId != null) {
            q.eq(Novel::getSiteId, siteId);
        }
        if (hasCover != null) {
            if (hasCover) q.and(w -> w.isNotNull(Novel::getCoverUrl).ne(Novel::getCoverUrl, ""));
            else q.and(w -> w.isNull(Novel::getCoverUrl).or().eq(Novel::getCoverUrl, ""));
        }
        if (hasDescription != null) {
            if (hasDescription) q.and(w -> w.isNotNull(Novel::getDescription).ne(Novel::getDescription, ""));
            else q.and(w -> w.isNull(Novel::getDescription).or().eq(Novel::getDescription, ""));
        }
        if (hasAuthor != null) {
            if (hasAuthor) q.and(w -> w.isNotNull(Novel::getAuthor).ne(Novel::getAuthor, "").ne(Novel::getAuthor, "未知"));
            else q.and(w -> w.isNull(Novel::getAuthor).or().eq(Novel::getAuthor, "").or().eq(Novel::getAuthor, "未知"));
        }
        if (updatedDays != null && updatedDays > 0) {
            q.ge(Novel::getLastCrawlTime, LocalDateTime.now().minusDays(updatedDays));
        }
        Page<Novel> p = Page.of(pageNum, pageSize);
        return Result.success(PageResult.of(novelMapper.selectPage(p, q)));
    }

    /** 删除单本小说及其关联排行记录 */
    @DeleteMapping("/{id}")
    @Transactional
    public Result<Void> delete(@PathVariable long id) {
        rankingRecordMapper.delete(new LambdaQueryWrapper<RankingRecord>().eq(RankingRecord::getNovelId, id));
        novelMapper.deleteById(id);
        return Result.success();
    }

    /** 批量删除小说及其关联排行记录 */
    @DeleteMapping("/batch")
    @Transactional
    public Result<Map<String, Integer>> deleteBatch(@RequestBody List<Long> ids) {
        int novelCnt = 0, recordCnt = 0;
        for (Long id : ids) {
            int rc = rankingRecordMapper.delete(new LambdaQueryWrapper<RankingRecord>().eq(RankingRecord::getNovelId, id));
            recordCnt += rc;
            novelCnt += novelMapper.deleteById(id);
        }
        return Result.success(Map.of("deletedNovels", novelCnt, "deletedRecords", recordCnt));
    }

    /** 删除排行榜记录（按 novelId） */
    @DeleteMapping("/{novelId}/records")
    public Result<Integer> deleteRecords(@PathVariable long novelId) {
        int cnt = rankingRecordMapper.delete(new LambdaQueryWrapper<RankingRecord>().eq(RankingRecord::getNovelId, novelId));
        return Result.success(cnt);
    }

    /** 删除指定排行榜单条记录 */
    @DeleteMapping("/records/{recordId}")
    public Result<Void> deleteRecord(@PathVariable long recordId) {
        rankingRecordMapper.deleteById(recordId);
        return Result.success();
    }

    /** 分页查询排行榜记录（管理员视角） */
    @GetMapping("/records")
    public Result<PageResult<Map<String, Object>>> listRecords(@RequestParam(defaultValue = "1") int pageNum,
                                                                @RequestParam(defaultValue = "20") int pageSize,
                                                                @RequestParam(required = false) Long novelId,
                                                                @RequestParam(required = false) Long siteId,
                                                                @RequestParam(required = false) String keyword) {
        Page<RankingRecord> p = Page.of(pageNum, pageSize);
        LambdaQueryWrapper<RankingRecord> q = new LambdaQueryWrapper<RankingRecord>()
                .orderByDesc(RankingRecord::getCrawlTime);
        if (novelId != null) q.eq(RankingRecord::getNovelId, novelId);
        if (siteId != null) q.eq(RankingRecord::getSiteId, siteId);
        // keyword 按小说 title/author 过滤（需要先用 novelId 集合限定,避免分页错乱）
        if (keyword != null && !keyword.isBlank()) {
            List<Long> novelIds = novelMapper.selectList(
                    new com.baomidou.mybatisplus.core.conditions.query.QueryWrapper<Novel>()
                            .select("id")
                            .like("title", keyword)
                            .or().like("author", keyword)
            ).stream().map(Novel::getId).toList();
            if (novelIds.isEmpty()) {
                PageResult<Map<String, Object>> empty = new PageResult<>();
                empty.setRecords(java.util.Collections.emptyList());
                empty.setTotal(0);
                empty.setPageNum(pageNum);
                empty.setPageSize(pageSize);
                empty.setPages(0);
                return Result.success(empty);
            }
            q.in(RankingRecord::getNovelId, novelIds);
        }
        Page<RankingRecord> res = rankingRecordMapper.selectPage(p, q);
        PageResult<RankingRecord> pr = PageResult.of(res);

        PageResult<Map<String, Object>> out = new PageResult<>();
        List<Map<String, Object>> list = pr.getRecords().stream().map(r -> {
            Map<String, Object> m = new java.util.HashMap<>();
            m.put("id", r.getId());
            m.put("novelId", r.getNovelId());
            m.put("siteId", r.getSiteId());
            m.put("rankingType", r.getRankingType());
            m.put("category", r.getCategory());
            m.put("rank", r.getRank());
            m.put("viewCount", r.getViewCount());
            m.put("recCount", r.getRecCount());
            m.put("crawlTime", r.getCrawlTime());
            m.put("crawlTaskId", r.getCrawlTaskId());
            return m;
        }).toList();
        out.setRecords(list);
        out.setTotal(pr.getTotal());
        out.setPageNum(pr.getPageNum());
        out.setPageSize(pr.getPageSize());
        out.setPages(pr.getPages());
        return Result.success(out);
    }
}
