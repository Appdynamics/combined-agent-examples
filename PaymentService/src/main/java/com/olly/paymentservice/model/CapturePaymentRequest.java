package com.olly.paymentservice.model;

import java.util.Map;

public class CapturePaymentRequest {

    private Map<String, Object> paymentDetails;

    public Map<String, Object> getPaymentDetails() {
        return paymentDetails;
    }

    public void setPaymentDetails(Map<String, Object> paymentDetails) {
        this.paymentDetails = paymentDetails;
    }
}
