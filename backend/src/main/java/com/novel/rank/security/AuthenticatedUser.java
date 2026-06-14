package com.novel.rank.security;

import java.io.Serializable;

public class AuthenticatedUser implements Serializable {

    private final Long userId;
    private final String username;
    private final String role;

    public AuthenticatedUser(Long userId, String username, String role) {
        this.userId = userId;
        this.username = username;
        this.role = role;
    }

    public Long getUserId() { return userId; }
    public String getUsername() { return username; }
    public String getRole() { return role; }
}
