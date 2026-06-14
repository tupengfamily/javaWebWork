package com.novel.rank.common;

public class BusinessException extends RuntimeException {

    private final int code;

    public BusinessException(ErrorCode ec) {
        super(ec.getMessage());
        this.code = ec.getCode();
    }

    public BusinessException(ErrorCode ec, String message) {
        super(message);
        this.code = ec.getCode();
    }

    public BusinessException(int code, String message) {
        super(message);
        this.code = code;
    }

    public int getCode() { return code; }
}
