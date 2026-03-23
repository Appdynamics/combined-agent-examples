package com.olly.paymentservice.controller;

import com.olly.paymentservice.model.CapturePaymentRequest;
import com.olly.paymentservice.model.CreatePaymentRequest;
import com.olly.paymentservice.model.Payment;
import com.olly.paymentservice.service.PaymentStore;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.ThreadLocalRandom;

@RestController
@RequestMapping("/payments")
public class PaymentController {

    private static final Logger log = LoggerFactory.getLogger(PaymentController.class);

    private final PaymentStore paymentStore;

    public PaymentController(PaymentStore paymentStore) {
        this.paymentStore = paymentStore;
    }

    @GetMapping
    public ResponseEntity<?> listPayments(
            @RequestParam(required = false) String status,
            @RequestParam(required = false) String customerId) {

        List<Payment> payments;
        if (status != null && !status.isBlank() && customerId != null && !customerId.isBlank()) {
            payments = paymentStore.findByStatusAndCustomerId(status.trim(), customerId.trim());
        } else if (status != null && !status.isBlank()) {
            payments = paymentStore.findByStatus(status.trim());
        } else if (customerId != null && !customerId.isBlank()) {
            payments = paymentStore.findByCustomerId(customerId.trim());
        } else {
            payments = paymentStore.findAll();
        }

        return ResponseEntity.ok(Map.of(
                "total", payments.size(),
                "payments", payments
        ));
    }

    @PostMapping
    public ResponseEntity<?> createPayment(@Valid @RequestBody CreatePaymentRequest request) {
        String paymentId = UUID.randomUUID().toString();
        Instant now = Instant.now();

        Payment payment = new Payment();
        payment.setPaymentId(paymentId);
        payment.setOrderId(request.getOrderId());
        payment.setCustomerId(request.getCustomerId());
        payment.setAmount(request.getAmount());
        payment.setCurrency(request.getCurrency() != null ? request.getCurrency() : "USD");
        payment.setStatus("pending");
        payment.setPaymentMethod(request.getPaymentMethod() != null ? request.getPaymentMethod() : "credit_card");
        payment.setCreatedAt(now);
        payment.setUpdatedAt(now);

        paymentStore.save(payment);
        log.info("Payment created: {}", paymentId);
        return ResponseEntity.status(HttpStatus.CREATED).body(payment);
    }

    @GetMapping("/{paymentId}")
    public ResponseEntity<?> getPayment(@PathVariable String paymentId) {
        Optional<Payment> payment = paymentStore.findById(paymentId);
        if (payment.isEmpty()) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of(
                    "error", "Not found",
                    "message", "Payment " + paymentId + " not found"
            ));
        }
        return ResponseEntity.ok(payment.get());
    }

    @PostMapping("/{paymentId}/capture")
    public ResponseEntity<?> capturePayment(
            @PathVariable String paymentId,
            @RequestBody(required = false) CapturePaymentRequest request) {

        Optional<Payment> opt = paymentStore.findById(paymentId);
        if (opt.isEmpty()) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of(
                    "error", "Not found",
                    "message", "Payment " + paymentId + " not found"
            ));
        }

        Payment payment = opt.get();
        if ("completed".equals(payment.getStatus())) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of(
                    "error", "Invalid operation",
                    "message", "Payment has already been completed"
            ));
        }
        if ("failed".equals(payment.getStatus())) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of(
                    "error", "Invalid operation",
                    "message", "Cannot capture a failed payment"
            ));
        }

        // Simulate processing delay (500–1500 ms)
        long processingTimeMs = 500 + ThreadLocalRandom.current().nextLong(1000);
        try {
            Thread.sleep(processingTimeMs);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of(
                    "error", "Internal server error",
                    "message", "Payment processing interrupted"
            ));
        }

        Instant now = Instant.now();
        payment.setStatus("completed");
        payment.setCompletedAt(now);
        payment.setUpdatedAt(now);
        if (request != null && request.getPaymentDetails() != null) {
            payment.setPaymentMethod(String.valueOf(request.getPaymentDetails().getOrDefault("method", payment.getPaymentMethod())));
        }
        paymentStore.save(payment);

        log.info("Payment captured: {}", paymentId);
        return ResponseEntity.ok(Map.of(
                "message", "Payment captured successfully",
                "paymentId", paymentId,
                "status", "completed",
                "processingTime", processingTimeMs + "ms"
        ));
    }

    @PostMapping("/{paymentId}/fail")
    public ResponseEntity<?> failPayment(
            @PathVariable String paymentId,
            @RequestParam(defaultValue = "normal") String type,
            @RequestBody(required = false) Map<String, String> body) {

        Optional<Payment> opt = paymentStore.findById(paymentId);
        if (opt.isEmpty()) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of(
                    "error", "Not found",
                    "message", "Payment " + paymentId + " not found"
            ));
        }

        String reason = body != null && body.containsKey("reason") ? body.get("reason") : "Simulated failure for testing";

        switch (type) {
            case "timeout":
                try {
                    Thread.sleep(5000);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of(
                        "error", "Timeout",
                        "message", "Payment processing timed out"
                ));

            case "exception":
                throw new RuntimeException("Simulated exception for payment processing");

            case "memory":
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of(
                        "error", "Resource exhaustion",
                        "message", "Out of memory error (simulated)"
                ));

            default:
                Payment payment = opt.get();
                Instant now = Instant.now();
                payment.setStatus("failed");
                payment.setFailureReason(reason);
                payment.setFailedAt(now);
                payment.setUpdatedAt(now);
                paymentStore.save(payment);
                log.info("Payment failed: {} - {}", paymentId, reason);
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of(
                        "error", "Payment failed",
                        "message", reason,
                        "paymentId", paymentId,
                        "status", "failed"
                ));
        }
    }
}
