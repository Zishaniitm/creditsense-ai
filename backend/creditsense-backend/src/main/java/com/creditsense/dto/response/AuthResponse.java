package com.creditsense.dto.response;

public class AuthResponse {
    private String accessToken;
    private String tokenType = "Bearer";
    private String role;
    private String email;
    private String name;
    private long expiresIn;

    public AuthResponse() {}

    // Getters
    public String getAccessToken() { return accessToken; }
    public String getTokenType()   { return tokenType; }
    public String getRole()        { return role; }
    public String getEmail()       { return email; }
    public String getName()        { return name; }
    public long getExpiresIn()     { return expiresIn; }

    // Setters
    public void setAccessToken(String v) { this.accessToken = v; }
    public void setTokenType(String v)   { this.tokenType = v; }
    public void setRole(String v)        { this.role = v; }
    public void setEmail(String v)       { this.email = v; }
    public void setName(String v)        { this.name = v; }
    public void setExpiresIn(long v)     { this.expiresIn = v; }

    public static Builder builder() { return new Builder(); }

    public static class Builder {
        private final AuthResponse r = new AuthResponse();
        public Builder accessToken(String v) { r.accessToken = v; return this; }
        public Builder tokenType(String v)   { r.tokenType = v; return this; }
        public Builder role(String v)        { r.role = v; return this; }
        public Builder email(String v)       { r.email = v; return this; }
        public Builder name(String v)        { r.name = v; return this; }
        public Builder expiresIn(long v)     { r.expiresIn = v; return this; }
        public AuthResponse build()          { return r; }
    }
}