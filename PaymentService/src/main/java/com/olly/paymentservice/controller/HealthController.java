package com.olly.paymentservice.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.Instant;
import java.util.Map;

@RestController
public class HealthController {

    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        return ResponseEntity.ok(Map.of(
                "status", "healthy",
                "timestamp", Instant.now().toString(),
                "service", "PaymentService",
                "uptime", getUptimeSeconds()
        ));
    }

    private static long getUptimeSeconds() {
        return ManagementHolder.getUptimeSeconds();
    }

    /**
     * Holder for uptime to avoid direct dependency on ManagementFactory in controller.
     */
    static final class ManagementHolder {
        private static final long START = System.currentTimeMillis();

        static long getUptimeSeconds() {
            return (System.currentTimeMillis() - START) / 1000;
        }
    }
}
