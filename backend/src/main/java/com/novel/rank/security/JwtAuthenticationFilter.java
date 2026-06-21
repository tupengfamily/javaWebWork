package com.novel.rank.security;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.novel.rank.common.ErrorCode;
import com.novel.rank.common.Result;
import io.jsonwebtoken.Claims;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.List;

/**
 * JWT 认证过滤器 - 从请求头解析 Token 并注入 Spring Security 上下文
 *
 * 调用链
 * ------
 * 1. 请求进入 -> 判断是否公开路径（见 {@link PublicPaths}），是则直接放行
 * 2. 提取 Authorization 头，要求以 "Bearer " 开头
 * 3. 调用 {@link JwtUtil#parse(String)} 解析 token
 * 4. 解析成功 -> 构造 {@link AuthenticatedUser} 并设置到 SecurityContext
 * 5. 解析失败 -> 直接返回 401 + 标准 JSON（不再走后续过滤器）
 *
 * 关键设计点
 * ----------
 * - <b>短路公开路径</b>：避免对静态/数据接口做无谓的 JWT 解析
 * - <b>失败立即返回</b>：token 缺失/无效时直接写响应，不抛异常，
 *   防止 Spring Security 默认走 Basic Auth 弹窗
 * - <b>单一真相</b>：公开路径判定逻辑下沉到 {@link PublicPaths}，
 *   与 SecurityConfig 共用同一份白名单
 */
@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private final JwtUtil jwtUtil;
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Value("${jwt.header:Authorization}")
    private String header;

    @Value("${jwt.prefix:Bearer }")
    private String prefix;

    public JwtAuthenticationFilter(JwtUtil jwtUtil) {
        this.jwtUtil = jwtUtil;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest req,
                                    HttpServletResponse resp,
                                    FilterChain chain) throws ServletException, IOException {
        String path = req.getRequestURI();
        // 公开接口无需 token
        if (PublicPaths.isPublic(path)) {
            chain.doFilter(req, resp);
            return;
        }

        // 校验 Authorization 头
        String auth = req.getHeader(header);
        if (auth == null || !auth.startsWith(prefix)) {
            writeError(resp, ErrorCode.UNAUTHORIZED.getCode(), "missing Authorization header");
            return;
        }

        // 解析 token（JwtUtil 内部已捕获 ExpiredJwt/JwtException，统一返回 null）
        String token = auth.substring(prefix.length()).trim();
        Claims claims = jwtUtil.parse(token);
        if (claims == null) {
            writeError(resp, ErrorCode.TOKEN_EXPIRED.getCode(), "token invalid or expired");
            return;
        }

        // 构造认证信息并写入 SecurityContext
        Long userId = Long.valueOf(claims.getSubject());
        String username = claims.get("username", String.class);
        String role = claims.get("role", String.class);

        AuthenticatedUser principal = new AuthenticatedUser(userId, username, role);
        UsernamePasswordAuthenticationToken authentication = new UsernamePasswordAuthenticationToken(
                principal, null,
                // role 转大写后加 ROLE_ 前缀，匹配 Spring Security 的 hasRole() 约定
                List.of(new SimpleGrantedAuthority("ROLE_" + (role == null ? "USER" : role.toUpperCase())))
        );
        authentication.setDetails(new WebAuthenticationDetailsSource().buildDetails(req));
        SecurityContextHolder.getContext().setAuthentication(authentication);

        chain.doFilter(req, resp);
    }

    /**
     * 输出统一格式的 401 错误响应
     *
     * 注意：这里固定返回 HTTP 401（不再跟随 ErrorCode code），保证前端 axios 拦截器
     * 能统一处理"未授权"分支。
     */
    private void writeError(HttpServletResponse resp, int code, String message) throws IOException {
        resp.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        resp.setContentType(MediaType.APPLICATION_JSON_VALUE);
        resp.setCharacterEncoding("UTF-8");
        resp.getWriter().write(objectMapper.writeValueAsString(Result.error(code, message)));
    }
}