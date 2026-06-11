package com.creditsense.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.concurrent.TimeUnit;

/**
 * Wraps Redis operations for caching credit assessment results.
 * Cache TTL = 30 minutes (NFR requirement for fast repeated lookups).
 *
 * If Redis is down, all methods fail gracefully (cache miss behavior)
 * so the application keeps working — Redis is an optimization, not
 * a hard dependency.
 */
@Service
public class CacheService {

    private static final Logger log = LoggerFactory.getLogger(CacheService.class);
    private static final String PREFIX = "credit_score:";
    private static final long TTL_MINUTES = 30;

    private final RedisTemplate<String, Object> redisTemplate;

    public CacheService(RedisTemplate<String, Object> redisTemplate) {
        this.redisTemplate = redisTemplate;
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> get(String applicationId) {
        try {
            Object cached = redisTemplate.opsForValue().get(PREFIX + applicationId);
            if (cached != null) {
                log.info("Cache HIT for application {}", applicationId);
                return (Map<String, Object>) cached;
            }
            log.info("Cache MISS for application {}", applicationId);
            return null;
        } catch (Exception e) {
            log.warn("Redis unavailable on GET, falling back to DB: {}", e.getMessage());
            return null;
        }
    }

    public void put(String applicationId, Map<String, Object> data) {
        try {
            redisTemplate.opsForValue().set(
                    PREFIX + applicationId, data, TTL_MINUTES, TimeUnit.MINUTES);
            log.info("Cached result for application {} (TTL={}min)",
                    applicationId, TTL_MINUTES);
        } catch (Exception e) {
            log.warn("Redis unavailable on SET, skipping cache: {}", e.getMessage());
        }
    }

    public void evict(String applicationId) {
        try {
            redisTemplate.delete(PREFIX + applicationId);
        } catch (Exception e) {
            log.warn("Redis unavailable on DELETE: {}", e.getMessage());
        }
    }
}