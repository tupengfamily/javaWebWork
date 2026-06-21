package com.novel.rank.common;

public enum ErrorCode {

    SUCCESS(0, "ok"),
    BAD_REQUEST(400, "参数错误"),
    UNAUTHORIZED(401, "未登录"),
    FORBIDDEN(403, "无权限"),
    NOT_FOUND(404, "资源不存在"),
    INTERNAL_ERROR(500, "服务器异常"),
    INVALID_CREDENTIALS(1001, "用户名或密码错误"),
    TOKEN_EXPIRED(1002, "token 已过期"),
    DUPLICATE_USERNAME(1003, "用户名已存在"),
    DUPLICATE_TASK(2001, "该任务已在队列中"),
    INVALID_SCHEDULE_TIME(2002, "时间格式错误");

    private final int code;
    private final String message;

    ErrorCode(int code, String message) {
        this.code = code;
        this.message = message;
    }

    public int getCode() { return code; }
    public String getMessage() { return message; }
}
