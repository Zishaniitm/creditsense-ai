package com.creditsense.security;

import io.jsonwebtoken.*;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;

/**
 * Handles all JWT operations:
 *  - generateToken: creates a signed JWT for an authenticated user
 *  - validateToken: verifies signature + expiry
 *  - extractEmail:  reads the subject (user email) from token
 *
 * JWT structure: Header.Payload.Signature
 *  Header   → algorithm (HS256)
 *  Payload  → subject (email), role, issued-at, expiry
 *  Signature→ HMAC-SHA256(header + payload, secretKey)
 */
@Component
public class JwtUtil {

    @Value("${jwt.secret}")
    private String secret;

    @Value("${jwt.expiration-ms}")
    private long expirationMs;

    private SecretKey getSigningKey() {
        return Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
    }

    /**
     * Generate JWT token for authenticated user.
     * Embeds email as subject and role as a custom claim.
     */
    public String generateToken(UserDetails userDetails, String role) {
        Map<String, Object> claims = new HashMap<>();
        claims.put("role", role);

        return Jwts.builder()
                .claims(claims)
                .subject(userDetails.getUsername())
                .issuedAt(new Date())
                .expiration(new Date(System.currentTimeMillis() + expirationMs))
                .signWith(getSigningKey())
                .compact();
    }

    /** Extract email (subject) from token. */
    public String extractEmail(String token) {
        return parseClaims(token).getSubject();
    }

    /** Extract role from token claims. */
    public String extractRole(String token) {
        return (String) parseClaims(token).get("role");
    }

    /** Check if token is valid for this user and not expired. */
    public boolean validateToken(String token, UserDetails userDetails) {
        try {
            String email = extractEmail(token);
            return email.equals(userDetails.getUsername()) && !isTokenExpired(token);
        } catch (JwtException | IllegalArgumentException e) {
            return false;
        }
    }

    private boolean isTokenExpired(String token) {
        return parseClaims(token).getExpiration().before(new Date());
    }

    private Claims parseClaims(String token) {
        return Jwts.parser()
                .verifyWith(getSigningKey())
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }
}