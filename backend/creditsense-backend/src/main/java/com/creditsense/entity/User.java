package com.creditsense.entity;

import jakarta.persistence.*;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "users")
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(name = "user_id", updatable = false, nullable = false)
    private UUID userId;

    @Column(nullable = false, length = 150)
    private String name;

    @Column(nullable = false, unique = true, length = 255)
    private String email;

    @Column(name = "password_hash", nullable = false, length = 255)
    private String passwordHash;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private Role role = Role.APPLICANT;

    @Column(name = "is_active", nullable = false)
    private Boolean isActive = true;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    public enum Role { APPLICANT, OFFICER, ADMIN }

    public User() {}

    // Getters
    public UUID getUserId()          { return userId; }
    public String getName()          { return name; }
    public String getEmail()         { return email; }
    public String getPasswordHash()  { return passwordHash; }
    public Role getRole()            { return role; }
    public Boolean getIsActive()     { return isActive; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public LocalDateTime getUpdatedAt() { return updatedAt; }

    // Setters
    public void setUserId(UUID userId)             { this.userId = userId; }
    public void setName(String name)               { this.name = name; }
    public void setEmail(String email)             { this.email = email; }
    public void setPasswordHash(String hash)       { this.passwordHash = hash; }
    public void setRole(Role role)                 { this.role = role; }
    public void setIsActive(Boolean isActive)      { this.isActive = isActive; }
    public void setCreatedAt(LocalDateTime t)      { this.createdAt = t; }
    public void setUpdatedAt(LocalDateTime t)      { this.updatedAt = t; }

    // Builder
    public static Builder builder() { return new Builder(); }

    public static class Builder {
        private final User user = new User();
        public Builder name(String v)         { user.name = v; return this; }
        public Builder email(String v)        { user.email = v; return this; }
        public Builder passwordHash(String v) { user.passwordHash = v; return this; }
        public Builder role(Role v)           { user.role = v; return this; }
        public Builder isActive(Boolean v)    { user.isActive = v; return this; }
        public User build()                   { return user; }
    }
}