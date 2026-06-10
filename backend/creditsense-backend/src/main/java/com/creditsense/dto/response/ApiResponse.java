package com.creditsense.dto.response;

public class ApiResponse<T> {
    private boolean success;
    private String message;
    private T data;

    public ApiResponse() {}

    public ApiResponse(boolean success, String message, T data) {
        this.success = success;
        this.message = message;
        this.data    = data;
    }

    public boolean isSuccess() { return success; }
    public String getMessage() { return message; }
    public T getData()         { return data; }

    public void setSuccess(boolean v) { this.success = v; }
    public void setMessage(String v)  { this.message = v; }
    public void setData(T v)          { this.data = v; }

    public static <T> ApiResponse<T> ok(String message, T data) {
        return new ApiResponse<>(true, message, data);
    }

    public static <T> ApiResponse<T> error(String message) {
        return new ApiResponse<>(false, message, null);
    }

    public static <T> Builder<T> builder() { return new Builder<>(); }

    public static class Builder<T> {
        private boolean success;
        private String message;
        private T data;
        public Builder<T> success(boolean v) { this.success = v; return this; }
        public Builder<T> message(String v)  { this.message = v; return this; }
        public Builder<T> data(T v)          { this.data = v; return this; }
        public ApiResponse<T> build() {
            return new ApiResponse<>(success, message, data);
        }
    }
}