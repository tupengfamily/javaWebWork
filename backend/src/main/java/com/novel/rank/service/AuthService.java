package com.novel.rank.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.novel.rank.common.BusinessException;
import com.novel.rank.common.ErrorCode;
import com.novel.rank.dto.LoginRequest;
import com.novel.rank.dto.LoginResponse;
import com.novel.rank.dto.RegisterRequest;
import com.novel.rank.dto.UserInfo;
import com.novel.rank.entity.SysUser;
import com.novel.rank.mapper.SysUserMapper;
import com.novel.rank.security.JwtUtil;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

@Service
public class AuthService {

    private final SysUserMapper userMapper;
    private final PasswordEncoder passwordEncoder;
    private final JwtUtil jwtUtil;

    public AuthService(SysUserMapper userMapper, PasswordEncoder passwordEncoder, JwtUtil jwtUtil) {
        this.userMapper = userMapper;
        this.passwordEncoder = passwordEncoder;
        this.jwtUtil = jwtUtil;
    }

    public LoginResponse register(RegisterRequest req) {
        Long count = userMapper.selectCount(
                new LambdaQueryWrapper<SysUser>().eq(SysUser::getUsername, req.getUsername())
        );
        if (count > 0) {
            throw new BusinessException(ErrorCode.DUPLICATE_USERNAME);
        }

        SysUser user = new SysUser();
        user.setUsername(req.getUsername());
        user.setPasswordHash(passwordEncoder.encode(req.getPassword()));
        user.setRole("user");
        user.setEnabled(true);
        user.setCreatedAt(LocalDateTime.now());
        user.setUpdatedAt(LocalDateTime.now());
        userMapper.insert(user);

        String token = jwtUtil.generate(user.getId(), user.getUsername(), user.getRole());
        return new LoginResponse(
                token,
                jwtUtil.getExpireSeconds(),
                new UserInfo(user.getId(), user.getUsername(), user.getRole())
        );
    }

    public LoginResponse login(LoginRequest req) {
        SysUser user = userMapper.selectOne(
                new LambdaQueryWrapper<SysUser>().eq(SysUser::getUsername, req.getUsername())
        );
        if (user == null
                || !Boolean.TRUE.equals(user.getEnabled())
                || !passwordEncoder.matches(req.getPassword(), user.getPasswordHash())) {
            throw new BusinessException(ErrorCode.INVALID_CREDENTIALS);
        }

        SysUser upd = new SysUser();
        upd.setId(user.getId());
        upd.setLastLoginAt(LocalDateTime.now());
        userMapper.updateById(upd);

        String token = jwtUtil.generate(user.getId(), user.getUsername(), user.getRole());
        return new LoginResponse(
                token,
                jwtUtil.getExpireSeconds(),
                new UserInfo(user.getId(), user.getUsername(), user.getRole())
        );
    }

    public UserInfo currentUser(Long userId) {
        SysUser user = userMapper.selectById(userId);
        if (user == null) {
            throw new BusinessException(ErrorCode.UNAUTHORIZED, "user not found");
        }
        return new UserInfo(user.getId(), user.getUsername(), user.getRole());
    }
}
