#!/usr/bin/env python3
"""
PaymentService Data Ingestion Script

This script generates traffic to the PaymentService API to demonstrate
AppDynamics / observability monitoring capabilities.

Usage:
    python ingest.py [options]

Examples:
    # Basic ingestion with 10 payments
    python ingest.py --count 10

    # Continuous ingestion for 5 minutes
    python ingest.py --duration 300

    # Include failure scenarios
    python ingest.py --count 20 --failures

    # Custom base URL
    python ingest.py --url http://localhost:8080 --count 50
"""

import argparse
import random
import requests
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional


class PaymentServiceIngester:
    def __init__(self, base_url: str = "http://localhost:8080", verbose: bool = True):
        self.base_url = base_url.rstrip("/")
        self.verbose = verbose
        self.payments_created: List[str] = []
        self.stats = {
            "payments_created": 0,
            "payments_retrieved": 0,
            "payments_captured": 0,
            "failures_simulated": 0,
            "errors": 0,
        }

    def log(self, message: str):
        """Print log message with timestamp"""
        if self.verbose:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] {message}")

    def check_health(self) -> bool:
        """Check if the service is healthy"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log(f"✓ Service is healthy: {data.get('status')}")
                return True
            else:
                self.log(f"✗ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"✗ Health check error: {e}")
            return False

    def create_payment(self, customer_id: Optional[str] = None, order_id: Optional[str] = None) -> Optional[Dict]:
        """Create a new payment"""
        customer_id = customer_id or f"customer-{random.randint(1000, 9999)}"
        order_id = order_id or f"order-{random.randint(10000, 99999)}"

        amount = round(random.uniform(9.99, 499.99), 2)
        payment_methods = ["credit_card", "debit_card", "paypal", "bank_transfer"]
        currencies = ["USD", "EUR", "GBP"]

        payload = {
            "orderId": order_id,
            "customerId": customer_id,
            "amount": amount,
            "currency": random.choice(currencies),
            "paymentMethod": random.choice(payment_methods),
        }

        try:
            response = requests.post(
                f"{self.base_url}/payments",
                json=payload,
                timeout=10,
            )

            if response.status_code == 201:
                payment = response.json()
                self.payments_created.append(payment["paymentId"])
                self.stats["payments_created"] += 1
                self.log(
                    f"✓ Created payment: {payment['paymentId']} "
                    f"(${payment['amount']:.2f} {payment.get('currency', 'USD')})"
                )
                return payment
            else:
                self.log(f"✗ Failed to create payment: {response.status_code} - {response.text}")
                self.stats["errors"] += 1
                return None
        except Exception as e:
            self.log(f"✗ Error creating payment: {e}")
            self.stats["errors"] += 1
            return None

    def get_payment(self, payment_id: str) -> Optional[Dict]:
        """Retrieve a payment by ID"""
        try:
            response = requests.get(f"{self.base_url}/payments/{payment_id}", timeout=5)
            if response.status_code == 200:
                self.stats["payments_retrieved"] += 1
                return response.json()
            else:
                self.log(f"✗ Failed to get payment {payment_id}: {response.status_code}")
                self.stats["errors"] += 1
                return None
        except Exception as e:
            self.log(f"✗ Error getting payment: {e}")
            self.stats["errors"] += 1
            return None

    def get_all_payments(self, status: Optional[str] = None) -> List[Dict]:
        """Get all payments, optionally filtered by status"""
        try:
            url = f"{self.base_url}/payments"
            if status:
                url += f"?status={status}"

            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get("payments", [])
            else:
                self.log(f"✗ Failed to get payments: {response.status_code}")
                self.stats["errors"] += 1
                return []
        except Exception as e:
            self.log(f"✗ Error getting payments: {e}")
            self.stats["errors"] += 1
            return []

    def capture_payment(self, payment_id: str) -> bool:
        """Capture (complete) a payment"""
        payload = {
            "paymentDetails": {
                "method": random.choice(["credit_card", "debit_card", "paypal"]),
                "last4": f"{random.randint(1000, 9999)}",
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/payments/{payment_id}/capture",
                json=payload,
                timeout=20,
            )

            if response.status_code == 200:
                self.stats["payments_captured"] += 1
                self.log(f"✓ Payment captured: {payment_id}")
                return True
            else:
                self.log(f"✗ Capture failed for {payment_id}: {response.status_code} - {response.text}")
                self.stats["errors"] += 1
                return False
        except Exception as e:
            self.log(f"✗ Error capturing payment: {e}")
            self.stats["errors"] += 1
            return False

    def fail_payment(self, payment_id: str, failure_type: str = "normal") -> bool:
        """Simulate payment failure"""
        payload = {
            "reason": f"Simulated {failure_type} failure for testing",
        }

        try:
            url = f"{self.base_url}/payments/{payment_id}/fail"
            if failure_type != "normal":
                url += f"?type={failure_type}"

            response = requests.post(url, json=payload, timeout=15)

            if response.status_code == 500:
                self.stats["failures_simulated"] += 1
                self.log(f"✓ Simulated {failure_type} failure for payment: {payment_id}")
                return True
            else:
                self.log(f"✗ Failed to simulate failure: {response.status_code}")
                self.stats["errors"] += 1
                return False
        except Exception as e:
            self.log(f"✗ Error simulating failure: {e}")
            self.stats["errors"] += 1
            return False

    def run_workflow(
        self, count: int, include_failures: bool = False, delay: float = 0.5
    ):
        """Run a complete workflow: create, retrieve, and capture payments"""
        self.log(f"Starting ingestion workflow: {count} payments")

        if not self.check_health():
            self.log("Service is not healthy. Exiting.")
            return

        created_payments: List[Dict] = []

        # Create payments
        for i in range(count):
            payment = self.create_payment()
            if payment:
                created_payments.append(payment)
            time.sleep(delay)

        if not created_payments:
            self.log("No payments were created. Exiting.")
            return

        # Retrieve some payments
        self.log("Retrieving payments...")
        for payment in random.sample(created_payments, min(5, len(created_payments))):
            self.get_payment(payment["paymentId"])
            time.sleep(delay * 0.5)

        # Capture payments for a subset (only pending can be captured)
        self.log("Capturing payments...")
        to_capture = random.sample(
            created_payments, min(len(created_payments) // 2, len(created_payments))
        )
        for payment in to_capture:
            self.capture_payment(payment["paymentId"])
            time.sleep(delay)

        # Simulate failures if requested
        if include_failures and created_payments:
            self.log("Simulating failures...")
            failure_types = ["normal", "timeout", "exception", "memory"]
            to_fail = random.sample(created_payments, min(3, len(created_payments)))
            for payment in to_fail:
                failure_type = random.choice(failure_types)
                self.fail_payment(payment["paymentId"], failure_type)
                time.sleep(delay)

        # Get all payments summary
        self.log("Fetching all payments summary...")
        all_payments = self.get_all_payments()
        self.log(f"Total payments in system: {len(all_payments)}")

        self.print_stats()

    def run_continuous(
        self, duration: int, delay: float = 1.0, include_failures: bool = False
    ):
        """Run continuous ingestion for a specified duration"""
        self.log(f"Starting continuous ingestion for {duration} seconds")

        if not self.check_health():
            self.log("Service is not healthy. Exiting.")
            return

        start_time = time.time()
        end_time = start_time + duration

        while time.time() < end_time:
            payment = self.create_payment()

            if payment:
                if random.random() < 0.3:
                    self.get_payment(payment["paymentId"])
                    time.sleep(delay * 0.3)

                if random.random() < 0.5:
                    time.sleep(delay * 0.5)
                    self.capture_payment(payment["paymentId"])

                if include_failures and random.random() < 0.1:
                    time.sleep(delay * 0.5)
                    failure_type = random.choice(["normal", "timeout", "exception"])
                    self.fail_payment(payment["paymentId"], failure_type)

            time.sleep(delay)

        self.print_stats()

    def print_stats(self):
        """Print ingestion statistics"""
        print("\n" + "=" * 50)
        print("INGESTION STATISTICS")
        print("=" * 50)
        print(f"Payments Created:     {self.stats['payments_created']}")
        print(f"Payments Retrieved:   {self.stats['payments_retrieved']}")
        print(f"Payments Captured:    {self.stats['payments_captured']}")
        print(f"Failures Simulated:   {self.stats['failures_simulated']}")
        print(f"Errors:               {self.stats['errors']}")
        print("=" * 50)


def main():
    parser = argparse.ArgumentParser(
        description="Generate traffic to PaymentService for AppDynamics / observability demonstration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--url",
        default="http://localhost:8080",
        help="Base URL of the PaymentService (default: http://localhost:8080)",
    )

    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of payments to create (default: 10)",
    )

    parser.add_argument(
        "--duration",
        type=int,
        help="Run continuous ingestion for N seconds (overrides --count)",
    )

    parser.add_argument(
        "--failures",
        action="store_true",
        help="Include failure simulation scenarios",
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Delay between requests in seconds (default: 0.5)",
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose output",
    )

    args = parser.parse_args()

    ingester = PaymentServiceIngester(base_url=args.url, verbose=not args.quiet)

    try:
        if args.duration:
            ingester.run_continuous(
                duration=args.duration,
                delay=args.delay,
                include_failures=args.failures,
            )
        else:
            ingester.run_workflow(
                count=args.count,
                include_failures=args.failures,
                delay=args.delay,
            )
    except KeyboardInterrupt:
        print("\n\nIngestion interrupted by user")
        ingester.print_stats()
        sys.exit(0)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        ingester.print_stats()
        sys.exit(1)


if __name__ == "__main__":
    main()
