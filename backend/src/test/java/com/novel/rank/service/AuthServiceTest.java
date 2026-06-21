package com.novel.rank.service;

import com.novel.rank.common.BusinessException;
import com.novel.rank.common.ErrorCode;
import com.novel.rank.dto.LoginRequest;
import com.novel.rank.entity.SysUser;
import com.novel.rank.mapper.SysUserMapper;
import com.novel.rank.security.JwtUtil;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.password.PasswordEncoder;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class AuthServiceTest {

    @Mock
    private SysUserMapper userMapper;

    @Mock
    private PasswordEncoder passwordEncoder;

    @Mock
    private JwtUtil jwtUtil;

    @InjectMocks
    private AuthService authService;

    private SysUser testUser;

    @BeforeEach
    void setUp() {
        testUser = new SysUser();
        testUser.setId(1L);
        testUser.setUsername("testuser");
        testUser.setPasswordHash("hashedpassword");
        testUser.setEnabled(true);
        testUser.setRole("USER");
    }

    @Test
    void login_success_returnsToken() {
        // Given
        LoginRequest req = new LoginRequest();
        req.setUsername("testuser");
        req.setPassword("password");

        when(userMapper.selectOne(any())).thenReturn(testUser);
        when(passwordEncoder.matches("password", "hashedpassword")).thenReturn(true);
        when(jwtUtil.generate(any(), any(), anyString())).thenReturn("test-token");

        // When
        var result = authService.login(req);

        // Then
        assertNotNull(result);
        assertEquals("test-token", result.getToken());
        assertNotNull(result.getUser());
        assertEquals("testuser", result.getUser().getUsername());
    }

    @Test
    void login_invalidUsername_throwsException() {
        // Given
        LoginRequest req = new LoginRequest();
        req.setUsername("nonexistent");
        req.setPassword("password");

        when(userMapper.selectOne(any())).thenReturn(null);

        // When/Then
        var ex = assertThrows(BusinessException.class, () -> authService.login(req));
        assertEquals(ErrorCode.INVALID_CREDENTIALS.getCode(), ex.getCode());
    }

    @Test
    void login_wrongPassword_throwsException() {
        // Given
        LoginRequest req = new LoginRequest();
        req.setUsername("testuser");
        req.setPassword("wrongpassword");

        when(userMapper.selectOne(any())).thenReturn(testUser);
        when(passwordEncoder.matches("wrongpassword", "hashedpassword")).thenReturn(false);

        // When/Then
        var ex = assertThrows(BusinessException.class, () -> authService.login(req));
        assertEquals(ErrorCode.INVALID_CREDENTIALS.getCode(), ex.getCode());
    }

    @Test
    void login_disabledUser_throwsException() {
        // Given - AuthService checks enabled field
        testUser.setEnabled(false);
        LoginRequest req = new LoginRequest();
        req.setUsername("testuser");
        req.setPassword("password");

        // Only stub what's needed for this test path
        when(userMapper.selectOne(any())).thenReturn(testUser);

        // When/Then - service should reject disabled user
        var ex = assertThrows(BusinessException.class, () -> authService.login(req));
        assertEquals(ErrorCode.INVALID_CREDENTIALS.getCode(), ex.getCode());
    }
}