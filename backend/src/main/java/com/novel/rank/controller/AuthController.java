package com.novel.rank.controller;

import com.novel.rank.common.Result;
import com.novel.rank.dto.LoginRequest;
import com.novel.rank.dto.LoginResponse;
import com.novel.rank.dto.UserInfo;
import com.novel.rank.security.AuthenticatedUser;
import com.novel.rank.service.AuthService;
import jakarta.validation.Valid;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final AuthService authService;

    public AuthController(AuthService authService) {
        this.authService = authService;
    }

    @PostMapping("/login")
    public Result<LoginResponse> login(@RequestBody @Valid LoginRequest req) {
        return Result.success(authService.login(req));
    }

    @PostMapping("/logout")
    public Result<Void> logout() {
        return Result.success();
    }

    @GetMapping("/me")
    public Result<UserInfo> me(@AuthenticationPrincipal AuthenticatedUser principal) {
        if (principal == null) {
            return Result.success(null);
        }
        return Result.success(authService.currentUser(principal.getUserId()));
    }
}
