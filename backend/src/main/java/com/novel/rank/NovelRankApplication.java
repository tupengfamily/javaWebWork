package com.novel.rank;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * 小说数据看板 - 后端启动类
 */
@SpringBootApplication
@MapperScan("com.novel.rank.mapper")
public class NovelRankApplication {

    public static void main(String[] args) {
        SpringApplication.run(NovelRankApplication.class, args);
    }
}
