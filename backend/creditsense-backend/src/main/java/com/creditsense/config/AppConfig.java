package com.creditsense.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.WebClient;

/**
 * Configures WebClient instances for calling Flask ML services.
 * WebClient is Spring's non-blocking HTTP client.
 * We create one bean per Flask service — each pre-configured with base URL.
 */
@Configuration
public class AppConfig {

    @Value("${ml-service.url}")
    private String mlServiceUrl;

    @Value("${fraud-service.url}")
    private String fraudServiceUrl;

    @Bean(name = "mlWebClient")
    public WebClient mlWebClient() {
        return WebClient.builder()
                .baseUrl(mlServiceUrl)
                .defaultHeader("Content-Type", "application/json")
                .build();
    }

    @Bean(name = "fraudWebClient")
    public WebClient fraudWebClient() {
        return WebClient.builder()
                .baseUrl(fraudServiceUrl)
                .defaultHeader("Content-Type", "application/json")
                .build();
    }
}