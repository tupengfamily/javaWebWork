package com.novel.rank.common;

import jakarta.servlet.http.HttpServletResponse;
import jakarta.validation.ConstraintViolationException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.AuthenticationException;
import org.springframework.validation.BindException;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;

import java.util.stream.Collectors;

@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    @ExceptionHandler(BusinessException.class)
    public Result<Void> handleBusiness(BusinessException ex, HttpServletResponse resp) {
        log.warn("business error: code={}, msg={}", ex.getCode(), ex.getMessage());
        if (ex.getCode() == 401) resp.setStatus(HttpStatus.UNAUTHORIZED.value());
        else if (ex.getCode() == 403) resp.setStatus(HttpStatus.FORBIDDEN.value());
        else if (ex.getCode() == 404) resp.setStatus(HttpStatus.NOT_FOUND.value());
        return Result.error(ex.getCode(), ex.getMessage());
    }

    @ExceptionHandler({MethodArgumentNotValidException.class, BindException.class})
    public Result<Void> handleValidation(Exception ex) {
        String msg = "param error";
        if (ex instanceof MethodArgumentNotValidException manv) {
            msg = manv.getBindingResult().getFieldErrors().stream()
                    .map(this::fieldErrorToStr)
                    .collect(Collectors.joining("; "));
        } else if (ex instanceof BindException be) {
            msg = be.getBindingResult().getFieldErrors().stream()
                    .map(this::fieldErrorToStr)
                    .collect(Collectors.joining("; "));
        }
        return Result.error(ErrorCode.BAD_REQUEST.getCode(), msg);
    }

    @ExceptionHandler(ConstraintViolationException.class)
    public Result<Void> handleConstraint(ConstraintViolationException ex) {
        return Result.error(ErrorCode.BAD_REQUEST.getCode(),
                ex.getConstraintViolations().stream()
                        .map(v -> v.getPropertyPath() + " " + v.getMessage())
                        .collect(Collectors.joining("; ")));
    }

    @ExceptionHandler({MissingServletRequestParameterException.class,
            MethodArgumentTypeMismatchException.class,
            HttpMessageNotReadableException.class})
    public Result<Void> handleBadRequest(Exception ex) {
        return Result.error(ErrorCode.BAD_REQUEST.getCode(), "param error: " + ex.getMessage());
    }

    @ExceptionHandler(AuthenticationException.class)
    public Result<Void> handleAuth(AuthenticationException ex) {
        return Result.error(ErrorCode.UNAUTHORIZED.getCode(), ex.getMessage());
    }

    @ExceptionHandler(AccessDeniedException.class)
    public Result<Void> handleAccessDenied(AccessDeniedException ex) {
        return Result.error(ErrorCode.FORBIDDEN.getCode(), ex.getMessage());
    }

    @ExceptionHandler(Exception.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public Result<Void> handleAll(Exception ex) {
        log.error("unexpected error", ex);
        return Result.error(ErrorCode.INTERNAL_ERROR.getCode(), "服务器内部错误，请稍后重试");
    }

    private String fieldErrorToStr(FieldError fe) {
        return fe.getField() + " " + fe.getDefaultMessage();
    }
}
