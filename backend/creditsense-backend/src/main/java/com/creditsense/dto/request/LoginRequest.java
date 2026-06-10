package com.creditsense.dto.request;

import jakarta.validation.constraints.*;

public class LoginRequest {

    @NotBlank(message = "Email is required")
    @Email(message = "Must be a valid email")
    private String email;

    @NotBlank(message = "Password is required")
    private String password;

    public String getEmail()    { return email; }
    public String getPassword() { return password; }

    public void setEmail(String v)    { this.email = v; }
    public void setPassword(String v) { this.password = v; }
}