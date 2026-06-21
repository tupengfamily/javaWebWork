package com.novel.rank.security;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.novel.rank.common.ErrorCode;
import com.novel.rank.common.Result;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.MediaType;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.filter.CorsFilter;

/**
 * Spring Security 主配置
 *
 * 设计要点
 * --------
 * 1. <b>无状态会话</b>：使用 JWT，禁用 HttpSession 与 CSRF。
 * 2. <b>公开路径集中维护</b>：公开接口以 {@link PublicPaths#PREFIXES} 为单一来源，
 *    避免 SecurityConfig 与 JwtAuthenticationFilter 各自维护导致漂移。
 * 3. <b>Admin 强制 ROLE</b>：{@code /api/admin/**} 要求 ROLE_ADMIN，
 *    失败时通过 {@link #writeJson} 输出统一的 {@link Result} 错误体。
 * 4. <b>异常处理</b>：未登录 401、无权限 403 均返回 JSON 而非默认 HTML，
 *    便于前端拦截器统一处理。
 */
@Configuration
public class SecurityConfig {

    private final JwtAuthenticationFilter jwtFilter;
    private final CorsFilter corsFilter;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public SecurityConfig(JwtAuthenticationFilter jwtFilter, CorsFilter corsFilter) {
        this.jwtFilter = jwtFilter;
        this.corsFilter = corsFilter;
    }

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
                .csrf(AbstractHttpConfigurer::disable)
                .cors(AbstractHttpConfigurer::disable)
                .formLogin(AbstractHttpConfigurer::disable)
                .httpBasic(AbstractHttpConfigurer::disable)
                .sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                .authorizeHttpRequests(auth -> auth
                        // 公开路径 - Ant 风格见 PublicPaths.SECURITY_PATTERNS（** 必须）
                        .requestMatchers(PublicPaths.SECURITY_PATTERNS.toArray(new String[0])).permitAll()
                        // /api/novels/{id}、/api/novels/search 等也属公开 - 见 PublicPaths.isPublic
                        .requestMatchers("/api/novels/search").permitAll()
                        .requestMatchers(org.springframework.http.HttpMethod.GET, "/api/novels/*").permitAll()
                        .requestMatchers(org.springframework.http.HttpMethod.GET, "/api/novels/*/records").permitAll()
                        .requestMatchers(org.springframework.http.HttpMethod.GET, "/api/novels/*/trend").permitAll()
                        // Admin 接口 - 必须 ROLE_ADMIN
                        .requestMatchers("/api/admin/**").hasRole("ADMIN")
                        // 其它任何路径需登录
                        .anyRequest().authenticated()
                )
                .exceptionHandling(eh -> eh
                        // 未登录：返回 JSON { code: 401, ... } 而非默认 HTML
                        .authenticationEntryPoint((req, resp, ex) -> writeJson(resp, ErrorCode.UNAUTHORIZED.getCode(), "not logged in"))
                        // 无权限：返回 JSON { code: 403, ... }
                        .accessDeniedHandler((req, resp, ex) -> writeJson(resp, ErrorCode.FORBIDDEN.getCode(), "no permission"))
                )
                // 过滤器链：CorsFilter -> JwtAuthenticationFilter -> UsernamePasswordAuthenticationFilter
                .addFilterBefore(corsFilter, UsernamePasswordAuthenticationFilter.class)
                .addFilterBefore(jwtFilter, UsernamePasswordAuthenticationFilter.class);
        return http.build();
    }

    /**
     * 密码编码器 - 使用 BCrypt（强哈希 + 自带盐）
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * 将错误以统一的 {@link Result} JSON 形式写入响应
     *
     * 关键点：
     * - HTTP 状态码跟随业务 code（401/403）变化，保证与前端 axios 拦截器期望一致
     * - 其他 code 回落为 200，因为前端拦截器优先读 body.code 判断业务结果
     */
    private void writeJson(HttpServletResponse resp, int code, String message) throws java.io.IOException {
        resp.setStatus(code == 401 ? HttpServletResponse.SC_UNAUTHORIZED
                : code == 403 ? HttpServletResponse.SC_FORBIDDEN : HttpServletResponse.SC_OK);
        resp.setContentType(MediaType.APPLICATION_JSON_VALUE);
        resp.setCharacterEncoding("UTF-8");
        resp.getWriter().write(objectMapper.writeValueAsString(Result.error(code, message)));
    }
}