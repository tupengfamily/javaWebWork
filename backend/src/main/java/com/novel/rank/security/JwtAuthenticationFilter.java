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
        if (isPublicPath(path)) {
            chain.doFilter(req, resp);
            return;
        }

        String auth = req.getHeader(header);
        if (auth == null || !auth.startsWith(prefix)) {
            writeError(resp, ErrorCode.UNAUTHORIZED.getCode(), "missing Authorization header");
            return;
        }

        String token = auth.substring(prefix.length()).trim();
        Claims claims = jwtUtil.parse(token);
        if (claims == null) {
            writeError(resp, ErrorCode.TOKEN_EXPIRED.getCode(), "token invalid or expired");
            return;
        }

        Long userId = Long.valueOf(claims.getSubject());
        String username = claims.get("username", String.class);
        String role = claims.get("role", String.class);

        AuthenticatedUser principal = new AuthenticatedUser(userId, username, role);
        UsernamePasswordAuthenticationToken authentication = new UsernamePasswordAuthenticationToken(
                principal, null,
                List.of(new SimpleGrantedAuthority("ROLE_" + (role == null ? "USER" : role.toUpperCase())))
        );
        authentication.setDetails(new WebAuthenticationDetailsSource().buildDetails(req));
        SecurityContextHolder.getContext().setAuthentication(authentication);

        chain.doFilter(req, resp);
    }

    private boolean isPublicPath(String path) {
        if (path == null) return true;
        return path.startsWith("/api/auth/login")
                || path.startsWith("/api/auth/register")
                || path.startsWith("/api/auth/logout")
                || path.startsWith("/api/sites")
                || path.startsWith("/api/rankings")
                || path.startsWith("/api/novels/")
                || path.startsWith("/api/trends/")
                || path.startsWith("/api/meta/")
                || path.startsWith("/v3/api-docs")
                || path.startsWith("/swagger-ui")
                || path.startsWith("/doc.html")
                || path.startsWith("/webjars")
                || path.startsWith("/actuator")
                || path.startsWith("/error");
    }

    private void writeError(HttpServletResponse resp, int code, String message) throws IOException {
        resp.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        resp.setContentType(MediaType.APPLICATION_JSON_VALUE);
        resp.setCharacterEncoding("UTF-8");
        resp.getWriter().write(objectMapper.writeValueAsString(Result.error(code, message)));
    }
}
