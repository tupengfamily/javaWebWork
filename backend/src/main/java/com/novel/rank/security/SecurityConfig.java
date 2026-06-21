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
                        .requestMatchers(
                                "/api/auth/register",
                                "/api/auth/login",
                                "/api/auth/logout",
                                "/api/auth/me",
                                "/api/sites",
                                "/api/sites/**",
                                "/api/rankings",
                                "/api/rankings/**",
                                "/api/novels/**",
                                "/api/trends/**",
                                "/api/meta/**",
                                "/v3/api-docs/**",
                                "/swagger-ui/**",
                                "/doc.html",
                                "/webjars/**",
                                "/actuator/**",
                                "/error"
                        ).permitAll()
                        .requestMatchers("/api/admin/**").hasRole("ADMIN")
                        .anyRequest().authenticated()
                )
                .exceptionHandling(eh -> eh
                        .authenticationEntryPoint((req, resp, ex) -> writeJson(resp, ErrorCode.UNAUTHORIZED.getCode(), "not logged in"))
                        .accessDeniedHandler((req, resp, ex) -> writeJson(resp, ErrorCode.FORBIDDEN.getCode(), "no permission"))
                )
                .addFilterBefore(corsFilter, UsernamePasswordAuthenticationFilter.class)
                .addFilterBefore(jwtFilter, UsernamePasswordAuthenticationFilter.class);
        return http.build();
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    private void writeJson(HttpServletResponse resp, int code, String message) throws java.io.IOException {
        resp.setStatus(code == 401 ? HttpServletResponse.SC_UNAUTHORIZED
                : code == 403 ? HttpServletResponse.SC_FORBIDDEN : HttpServletResponse.SC_OK);
        resp.setContentType(MediaType.APPLICATION_JSON_VALUE);
        resp.setCharacterEncoding("UTF-8");
        resp.getWriter().write(objectMapper.writeValueAsString(Result.error(code, message)));
    }
}
