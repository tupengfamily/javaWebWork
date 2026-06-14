package com.novel.rank.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.novel.rank.common.Result;
import com.novel.rank.entity.Category;
import com.novel.rank.entity.RankingType;
import com.novel.rank.mapper.CategoryMapper;
import com.novel.rank.mapper.RankingTypeMapper;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/meta")
public class MetaController {

    private final RankingTypeMapper rankingTypeMapper;
    private final CategoryMapper categoryMapper;

    public MetaController(RankingTypeMapper rankingTypeMapper, CategoryMapper categoryMapper) {
        this.rankingTypeMapper = rankingTypeMapper;
        this.categoryMapper = categoryMapper;
    }

    @GetMapping("/ranking-types")
    public Result<List<RankingType>> rankingTypes() {
        return Result.success(rankingTypeMapper.selectList(
                new LambdaQueryWrapper<RankingType>().orderByAsc(RankingType::getId)
        ));
    }

    @GetMapping("/categories")
    public Result<List<String>> categories() {
        List<Category> cats = categoryMapper.selectList(
                new QueryWrapper<Category>().orderByAsc("sort_order")
        );
        return Result.success(cats.stream().map(Category::getName).toList());
    }
}
