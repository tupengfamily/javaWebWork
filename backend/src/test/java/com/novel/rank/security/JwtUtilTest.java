package com.novel.rank.security;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;

import javax.crypto.SecretKey;
import java.util.Date;

import static org.junit.jupiter.api.Assertions.*;

class JwtUtilTest {

    private JwtUtil jwtUtil;
    private static final String SECRET = "test-secret-key-that-is-at-least-32-bytes-long!";
    private static final long EXPIRE_HOURS = 24;

    @BeforeEach
    void setUp() {
        jwtUtil = new JwtUtil();
        ReflectionTestUtils.setField(jwtUtil, "secret", SECRET);
        ReflectionTestUtils.setField(jwtUtil, "expireHours", EXPIRE_HOURS);
        jwtUtil.init();
    }

    @Test
    void generate_validInput_returnsToken() {
        // Given
        Long userId = 1L;
        String username = "testuser";
        String role = "USER";

        // When
        String token = jwtUtil.generate(userId, username, role);

        // Then
        assertNotNull(token);
        assertFalse(token.isEmpty());
    }

    @Test
    void parse_validToken_returnsClaims() {
        // Given
        Long userId = 1L;
        String username = "testuser";
        String role = "USER";
        String token = jwtUtil.generate(userId, username, role);

        // When
        Claims claims = jwtUtil.parse(token);

        // Then
        assertNotNull(claims);
        assertEquals("1", claims.getSubject());
        assertEquals(username, claims.get("username", String.class));
        assertEquals(role, claims.get("role", String.class));
    }

    @Test
    void parse_expiredToken_returnsNull() {
        // Given - create expired token
        SecretKey key = Keys.hmacShaKeyFor(SECRET.getBytes());
        long expiredTime = System.currentTimeMillis() - 3600000; // 1 hour ago
        String expiredToken = Jwts.builder()
                .subject("1")
                .claim("username", "testuser")
                .claim("role", "USER")
                .expiration(new Date(expiredTime))
                .signWith(key)
                .compact();

        // When
        Claims claims = jwtUtil.parse(expiredToken);

        // Then - parse() returns null for expired token
        assertNull(claims);
    }

    @Test
    void parse_invalidToken_returnsNull() {
        // Given
        String invalidToken = "invalid.token.string";

        // When
        Claims claims = jwtUtil.parse(invalidToken);

        // Then
        assertNull(claims);
    }

    @Test
    void parse_tamperedToken_returnsNull() {
        // Given
        String token = jwtUtil.generate(1L, "testuser", "USER");
        String tamperedToken = token + "tampered";

        // When
        Claims claims = jwtUtil.parse(tamperedToken);

        // Then
        assertNull(claims);
    }
}