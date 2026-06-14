package com.novel.rank.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.novel.rank.common.BusinessException;
import com.novel.rank.common.ErrorCode;
import com.novel.rank.common.PageResult;
import com.novel.rank.entity.Novel;
import com.novel.rank.entity.RankingRecord;
import com.novel.rank.entity.Site;
import com.novel.rank.mapper.NovelMapper;
import com.novel.rank.mapper.RankingRecordMapper;
import com.novel.rank.mapper.SiteMapper;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class SiteService {

    private final SiteMapper siteMapper;
    private final NovelMapper novelMapper;
    private final RankingRecordMapper rankingRecordMapper;

    public SiteService(SiteMapper siteMapper, NovelMapper novelMapper, RankingRecordMapper rankingRecordMapper) {
        this.siteMapper = siteMapper;
        this.novelMapper = novelMapper;
        this.rankingRecordMapper = rankingRecordMapper;
    }

    public List<Site> listEnabled() {
        return siteMapper.selectList(
                new LambdaQueryWrapper<Site>().eq(Site::getEnabled, true)
                        .orderByAsc(Site::getSortOrder).orderByAsc(Site::getId)
        );
    }

    public List<Site> listAll() {
        return siteMapper.selectList(
                new LambdaQueryWrapper<Site>().orderByAsc(Site::getSortOrder).orderByAsc(Site::getId)
        );
    }

    public PageResult<Site> page(int pageNum, int pageSize) {
        Page<Site> p = Page.of(pageNum, pageSize);
        Page<Site> res = siteMapper.selectPage(p, null);
        return PageResult.of(res);
    }

    public Site getById(long id) {
        Site s = siteMapper.selectById(id);
        if (s == null) throw new BusinessException(ErrorCode.NOT_FOUND, "site not found");
        return s;
    }

    public Site getByCode(String code) {
        Site s = siteMapper.selectOne(new LambdaQueryWrapper<Site>().eq(Site::getCode, code));
        if (s == null) throw new BusinessException(ErrorCode.NOT_FOUND, "site not found");
        return s;
    }

    public Site create(Site s) {
        Site exist = siteMapper.selectOne(new LambdaQueryWrapper<Site>().eq(Site::getCode, s.getCode()));
        if (exist != null) {
            throw new BusinessException(ErrorCode.BAD_REQUEST, "code already exists");
        }
        s.setId(null);
        siteMapper.insert(s);
        return s;
    }

    public Site update(long id, Site s) {
        Site exist = getById(id);
        if (s.getName() != null) exist.setName(s.getName());
        if (s.getBaseUrl() != null) exist.setBaseUrl(s.getBaseUrl());
        if (s.getSpiderClass() != null) exist.setSpiderClass(s.getSpiderClass());
        if (s.getColor() != null) exist.setColor(s.getColor());
        if (s.getEnabled() != null) exist.setEnabled(s.getEnabled());
        if (s.getSortOrder() != null) exist.setSortOrder(s.getSortOrder());
        siteMapper.updateById(exist);
        return exist;
    }

    public void delete(long id) {
        Site exist = getById(id);
        Long novelCount = novelMapper.selectCount(
                new LambdaQueryWrapper<Novel>().eq(Novel::getSiteId, id));
        if (novelCount > 0) {
            throw new BusinessException(ErrorCode.BAD_REQUEST, "has related data, cannot delete");
        }
        Long recordCount = rankingRecordMapper.selectCount(
                new LambdaQueryWrapper<RankingRecord>().eq(RankingRecord::getSiteId, id));
        if (recordCount > 0) {
            throw new BusinessException(ErrorCode.BAD_REQUEST, "has related data, cannot delete");
        }
        siteMapper.deleteById(exist.getId());
    }
}
