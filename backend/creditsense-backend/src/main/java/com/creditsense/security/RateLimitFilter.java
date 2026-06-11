package com.creditsense.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Simple in-memory rate limiter: 100 requests/minute per IP.
 * NFR-020: API Rate Limiting requirement.
 *
 * For production scale, this would use Redis with a sliding window.
 * For our scope (BCA project, single instance), in-memory is sufficient
 * and avoids adding Redis as a hard dependency for this feature.
 */
@Component
@Order(1)
public class RateLimitFilter extends OncePerRequestFilter {

    private static final int MAX_REQUESTS_PER_MINUTE = 100;
    private static final long WINDOW_MS = 60_000;

    private final ConcurrentHashMap<String, RequestCounter> requestCounts =
            new ConcurrentHashMap<>();

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain)
            throws ServletException, IOException {

        // Don't rate-limit Swagger docs
        String path = request.getRequestURI();
        if (path.startsWith("/swagger-ui") || path.startsWith("/api-docs")) {
            filterChain.doFilter(request, response);
            return;
        }

        String clientIp = getClientIp(request);
        RequestCounter counter = requestCounts.computeIfAbsent(
                clientIp, k -> new RequestCounter());

        long now = System.currentTimeMillis();

        synchronized (counter) {
            if (now - counter.windowStart > WINDOW_MS) {
                counter.windowStart = now;
                counter.count.set(0);
            }

            if (counter.count.incrementAndGet() > MAX_REQUESTS_PER_MINUTE) {
                response.setStatus(429);
                response.setContentType("application/json");
                response.getWriter().write(
                    "{\"success\":false,\"message\":\"Rate limit exceeded — " +
                    "max " + MAX_REQUESTS_PER_MINUTE + " requests per minute\",\"data\":null}"
                );
                return;
            }
        }

        filterChain.doFilter(request, response);
    }

    private String getClientIp(HttpServletRequest request) {
        String xff = request.getHeader("X-Forwarded-For");
        if (xff != null && !xff.isEmpty()) {
            return xff.split(",")[0].trim();
        }
        return request.getRemoteAddr();
    }

    private static class RequestCounter {
        volatile long windowStart = System.currentTimeMillis();
        AtomicInteger count = new AtomicInteger(0);
    }
}