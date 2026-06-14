package com.novel.rank.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.novel.rank.entity.Novel;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.Map;

@Mapper
public interface NovelMapper extends BaseMapper<Novel> {
    Map<String, Object> selectNovelDetail(@Param("id") long id);
}
