package com.novel.rank.security;

import java.util.List;

/**
     * 公开访问路径白名单 - 集中维护 SecurityConfig 与 JwtAuthenticationFilter 共用的路径
     *
     * 为什么需要这个类
     * ----------------
     * 1. <b>避免漂移</b>：SecurityConfig 与 JwtAuthenticationFilter 都曾独立维护
     *    公开路径列表，两处一旦不同步，会出现"Filter 放过但 Security 拦截"或反向的不一致。
     * 2. <b>前缀精确匹配</b>：用 {@code startWith("/api/novels/")} 等简单前缀判断
     *    会误命中同前缀的子路径（如 /api/admin/novels），所以这里额外提供
     *    {@link #isPublic(String)} 进行更严格的判断。
     *
     * 调用方
     * ------
     * - SecurityConfig：声明 permitAll（用 {@link #SECURITY_PATTERNS}，Ant 风格）
     * - JwtAuthenticationFilter：跳过 token 校验（用 {@link #PREFIXES}，startsWith 风格）
     */
    public final class PublicPaths {

    private PublicPaths() {}

    /**
     * 公开路径前缀列表（按声明顺序匹配，用于 Filter 的 startsWith 快速判断）
     *
     * 注意：每个前缀必须以斜杠结尾或为完整路径，避免 {@code /api/novels}
     * 误匹配 {@code /api/novels-extra} 这种边界情况。
     */
    public static final List<String> PREFIXES = List.of(
            // 鉴权自身：登录/注册/登出/me
            "/api/auth/login",
            "/api/auth/register",
            "/api/auth/logout",
            "/api/auth/me",
            // 站点/榜单/小说/趋势/分类字典 - 公开数据
            "/api/sites",
            "/api/rankings",
            "/api/meta/",
            // 注意：/api/novels/ 用精确匹配（见 isPublic），避免误命中 /api/admin/novels
            "/api/trends/",
            // API 文档 & 错误页
            "/v3/api-docs",
            "/swagger-ui",
            "/doc.html",
            "/webjars",
            "/error"
    );

    /**
     * 供 SecurityConfig 使用的 Ant 风格路径模式。
     *
     * <b>关键差异</b>：Spring Security 6 的 {@code requestMatchers(String...)} 使用
     * {@link org.springframework.security.web.util.matcher.AntPathRequestMatcher}，
     * 对 {@code /api/meta/} 这种带尾斜杠的路径做<b>精确匹配</b>——不会匹配
     * {@code /api/meta/ranking-types}。需要用 {@code /api/meta/**} 才能匹配其下所有子路径。
     *
     * 而 Filter 中的 {@code path.startsWith(p)} 是简单前缀匹配，{@code /api/meta/}
     * 会正确匹配 {@code /api/meta/ranking-types}。所以两个消费者使用不同的常量。
     */
    public static final List<String> SECURITY_PATTERNS = List.of(
            // 鉴权自身：登录/注册/登出/me
            "/api/auth/login",
            "/api/auth/register",
            "/api/auth/logout",
            "/api/auth/me",
            // 站点/榜单 - 公开数据（无子路径，精确匹配即可）
            "/api/sites",
            "/api/rankings",
            // 分类字典/趋势 - 必须用 ** 才能匹配子路径！
            "/api/meta/**",
            "/api/trends/**",
            // API 文档 & 错误页
            "/v3/api-docs/**",
            "/swagger-ui/**",
            "/doc.html",
            "/webjars/**",
            "/error"
    );

    /**
     * /api/novels/ 下的公开接口子路径
     * （/api/admin/novels/** 不在此列 - 走 admin 鉴权）
     */
    private static final List<String> NOVEL_SUB_PATHS = List.of(
            "/api/novels/search"   // 公开搜索接口
    );

    /**
     * 判断给定路径是否公开访问
     *
     * @param path 请求 URI（不含 context-path）
     * @return true 表示无需 token
     */
    public static boolean isPublic(String path) {
        if (path == null) return true;

        // 1. 前缀匹配
        for (String p : PREFIXES) {
            if (path.startsWith(p)) return true;
        }

        // 2. /api/novels/{id} 与 /api/novels/{id}/records、/api/novels/{id}/trend 视为公开
        if (path.startsWith("/api/novels/")) {
            // 子路径白名单
            for (String sub : NOVEL_SUB_PATHS) {
                if (path.startsWith(sub)) return true;
            }
            // /api/novels/{数字}/...   详情/records/trend
            String rest = path.substring("/api/novels/".length());
            int slash = rest.indexOf('/');
            String head = slash >= 0 ? rest.substring(0, slash) : rest;
            if (head.matches("\\d+")) return true;
        }

        return false;
    }
}