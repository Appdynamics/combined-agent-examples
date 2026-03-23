package com.olly.paymentservice.service;

import com.olly.paymentservice.model.Payment;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;

@Component
public class PaymentStore {

    private final Map<String, Payment> payments = new ConcurrentHashMap<>();

    public Payment save(Payment payment) {
        payments.put(payment.getPaymentId(), payment);
        return payment;
    }

    public Optional<Payment> findById(String paymentId) {
        return Optional.ofNullable(payments.get(paymentId));
    }

    public List<Payment> findAll() {
        return List.copyOf(payments.values());
    }

    public List<Payment> findByStatus(String status) {
        return payments.values().stream()
                .filter(p -> status.equals(p.getStatus()))
                .collect(Collectors.toList());
    }

    public List<Payment> findByCustomerId(String customerId) {
        return payments.values().stream()
                .filter(p -> customerId.equals(p.getCustomerId()))
                .collect(Collectors.toList());
    }

    public List<Payment> findByStatusAndCustomerId(String status, String customerId) {
        return payments.values().stream()
                .filter(p -> status.equals(p.getStatus()) && customerId.equals(p.getCustomerId()))
                .collect(Collectors.toList());
    }
}
