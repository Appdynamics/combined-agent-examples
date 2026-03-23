#!/usr/bin/env python3
"""
OrderService Data Ingestion Script

This script generates traffic to the OrderService API to demonstrate
AppDynamics monitoring capabilities.

Usage:
    python ingest.py [options]

Examples:
    # Basic ingestion with 10 orders
    python ingest.py --count 10

    # Continuous ingestion for 5 minutes
    python ingest.py --duration 300

    # Include failure scenarios
    python ingest.py --count 20 --failures

    # Custom base URL
    python ingest.py --url http://localhost:3000 --count 50
"""

import argparse
import json
import random
import requests
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional


class OrderServiceIngester:
    def __init__(self, base_url: str = "http://localhost:3000", verbose: bool = True):
        self.base_url = base_url.rstrip('/')
        self.verbose = verbose
        self.orders_created = []
        self.stats = {
            'orders_created': 0,
            'orders_retrieved': 0,
            'payments_processed': 0,
            'failures_simulated': 0,
            'errors': 0
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

    def create_order(self, customer_id: Optional[str] = None) -> Optional[Dict]:
        """Create a new order"""
        customer_id = customer_id or f"customer-{random.randint(1000, 9999)}"
        
        # Generate random items
        products = [
            {"productId": "prod-1", "name": "Laptop", "price": 999.99},
            {"productId": "prod-2", "name": "Mouse", "price": 29.99},
            {"productId": "prod-3", "name": "Keyboard", "price": 79.99},
            {"productId": "prod-4", "name": "Monitor", "price": 299.99},
            {"productId": "prod-5", "name": "Webcam", "price": 49.99},
            {"productId": "prod-6", "name": "Headphones", "price": 149.99},
        ]
        
        num_items = random.randint(1, 4)
        items = random.sample(products, num_items)
        items = [
            {
                "productId": item["productId"],
                "name": item["name"],
                "price": item["price"],
                "quantity": random.randint(1, 3)
            }
            for item in items
        ]
        
        total_amount = sum(item["price"] * item["quantity"] for item in items)
        
        payload = {
            "customerId": customer_id,
            "items": items,
            "totalAmount": round(total_amount, 2)
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/orders",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 201:
                order = response.json()
                self.orders_created.append(order['orderId'])
                self.stats['orders_created'] += 1
                self.log(f"✓ Created order: {order['orderId']} (${order['totalAmount']:.2f})")
                return order
            else:
                self.log(f"✗ Failed to create order: {response.status_code} - {response.text}")
                self.stats['errors'] += 1
                return None
        except Exception as e:
            self.log(f"✗ Error creating order: {e}")
            self.stats['errors'] += 1
            return None

    def get_order(self, order_id: str) -> Optional[Dict]:
        """Retrieve an order by ID"""
        try:
            response = requests.get(f"{self.base_url}/orders/{order_id}", timeout=5)
            if response.status_code == 200:
                self.stats['orders_retrieved'] += 1
                return response.json()
            else:
                self.log(f"✗ Failed to get order {order_id}: {response.status_code}")
                self.stats['errors'] += 1
                return None
        except Exception as e:
            self.log(f"✗ Error getting order: {e}")
            self.stats['errors'] += 1
            return None

    def get_all_orders(self, status: Optional[str] = None) -> List[Dict]:
        """Get all orders, optionally filtered by status"""
        try:
            url = f"{self.base_url}/orders"
            if status:
                url += f"?status={status}"
            
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get('orders', [])
            else:
                self.log(f"✗ Failed to get orders: {response.status_code}")
                self.stats['errors'] += 1
                return []
        except Exception as e:
            self.log(f"✗ Error getting orders: {e}")
            self.stats['errors'] += 1
            return []

    def pay_order(self, order_id: str) -> bool:
        """Process payment for an order"""
        payment_methods = ["credit_card", "debit_card", "paypal", "bank_transfer"]
        payload = {
            "paymentMethod": random.choice(payment_methods),
            "paymentDetails": {
                "last4": f"{random.randint(1000, 9999)}"
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/orders/{order_id}/pay",
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                self.stats['payments_processed'] += 1
                self.log(f"✓ Payment processed for order: {order_id}")
                return True
            else:
                self.log(f"✗ Payment failed for {order_id}: {response.status_code} - {response.text}")
                self.stats['errors'] += 1
                return False
        except Exception as e:
            self.log(f"✗ Error processing payment: {e}")
            self.stats['errors'] += 1
            return False

    def fail_order(self, order_id: str, failure_type: str = "normal") -> bool:
        """Simulate order failure"""
        payload = {
            "reason": f"Simulated {failure_type} failure for testing"
        }
        
        try:
            url = f"{self.base_url}/orders/{order_id}/fail"
            if failure_type != "normal":
                url += f"?type={failure_type}"
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 500:
                self.stats['failures_simulated'] += 1
                self.log(f"✓ Simulated {failure_type} failure for order: {order_id}")
                return True
            else:
                self.log(f"✗ Failed to simulate failure: {response.status_code}")
                self.stats['errors'] += 1
                return False
        except Exception as e:
            self.log(f"✗ Error simulating failure: {e}")
            self.stats['errors'] += 1
            return False

    def run_workflow(self, count: int, include_failures: bool = False, delay: float = 0.5):
        """Run a complete workflow: create, retrieve, and pay for orders"""
        self.log(f"Starting ingestion workflow: {count} orders")
        
        if not self.check_health():
            self.log("Service is not healthy. Exiting.")
            return
        
        created_orders = []
        
        # Create orders
        for i in range(count):
            order = self.create_order()
            if order:
                created_orders.append(order)
            time.sleep(delay)
        
        if not created_orders:
            self.log("No orders were created. Exiting.")
            return
        
        # Retrieve some orders
        self.log("Retrieving orders...")
        for order in random.sample(created_orders, min(5, len(created_orders))):
            self.get_order(order['orderId'])
            time.sleep(delay * 0.5)
        
        # Process payments for some orders
        self.log("Processing payments...")
        orders_to_pay = random.sample(created_orders, min(len(created_orders) // 2, len(created_orders)))
        for order in orders_to_pay:
            self.pay_order(order['orderId'])
            time.sleep(delay)
        
        # Simulate failures if requested
        if include_failures and created_orders:
            self.log("Simulating failures...")
            failure_types = ["normal", "timeout", "exception", "memory"]
            orders_to_fail = random.sample(created_orders, min(3, len(created_orders)))
            for order in orders_to_fail:
                failure_type = random.choice(failure_types)
                self.fail_order(order['orderId'], failure_type)
                time.sleep(delay)
        
        # Get all orders summary
        self.log("Fetching all orders summary...")
        all_orders = self.get_all_orders()
        self.log(f"Total orders in system: {len(all_orders)}")
        
        self.print_stats()

    def run_continuous(self, duration: int, delay: float = 1.0, include_failures: bool = False):
        """Run continuous ingestion for a specified duration"""
        self.log(f"Starting continuous ingestion for {duration} seconds")
        
        if not self.check_health():
            self.log("Service is not healthy. Exiting.")
            return
        
        start_time = time.time()
        end_time = start_time + duration
        
        while time.time() < end_time:
            # Create an order
            order = self.create_order()
            
            if order:
                # Sometimes retrieve it
                if random.random() < 0.3:
                    self.get_order(order['orderId'])
                    time.sleep(delay * 0.3)
                
                # Sometimes pay for it
                if random.random() < 0.5:
                    time.sleep(delay * 0.5)
                    self.pay_order(order['orderId'])
                
                # Sometimes simulate failure
                if include_failures and random.random() < 0.1:
                    time.sleep(delay * 0.5)
                    failure_type = random.choice(["normal", "timeout", "exception"])
                    self.fail_order(order['orderId'], failure_type)
            
            time.sleep(delay)
        
        self.print_stats()

    def print_stats(self):
        """Print ingestion statistics"""
        print("\n" + "="*50)
        print("INGESTION STATISTICS")
        print("="*50)
        print(f"Orders Created:     {self.stats['orders_created']}")
        print(f"Orders Retrieved:    {self.stats['orders_retrieved']}")
        print(f"Payments Processed:  {self.stats['payments_processed']}")
        print(f"Failures Simulated:  {self.stats['failures_simulated']}")
        print(f"Errors:              {self.stats['errors']}")
        print("="*50)


def main():
    parser = argparse.ArgumentParser(
        description="Generate traffic to OrderService for AppDynamics demonstration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--url',
        default='http://localhost:3000',
        help='Base URL of the OrderService (default: http://localhost:3000)'
    )
    
    parser.add_argument(
        '--count',
        type=int,
        default=10,
        help='Number of orders to create (default: 10)'
    )
    
    parser.add_argument(
        '--duration',
        type=int,
        help='Run continuous ingestion for N seconds (overrides --count)'
    )
    
    parser.add_argument(
        '--failures',
        action='store_true',
        help='Include failure simulation scenarios'
    )
    
    parser.add_argument(
        '--delay',
        type=float,
        default=0.5,
        help='Delay between requests in seconds (default: 0.5)'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress verbose output'
    )
    
    args = parser.parse_args()
    
    ingester = OrderServiceIngester(base_url=args.url, verbose=not args.quiet)
    
    try:
        if args.duration:
            ingester.run_continuous(
                duration=args.duration,
                delay=args.delay,
                include_failures=args.failures
            )
        else:
            ingester.run_workflow(
                count=args.count,
                include_failures=args.failures,
                delay=args.delay
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


