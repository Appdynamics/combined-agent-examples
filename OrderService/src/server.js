/**
 * OrderService - Node.js Service
 * Instrumented with AppDynamics + Splunk O11y (Dual Mode or Splunk-only)
 */

const isDualMode = process.env.agent_deployment_mode === 'dual' && process.env.APPD_CONTROLLER_HOST;

if (isDualMode) {
  // Dual mode: only start AppDynamics; it will call Splunk OTel start() internally.
  // Do NOT call @splunk/otel start() here or you get "Splunk APM already started".
  try {
    const appdynamics = require('appdynamics');
    appdynamics.profile({
      controllerHostName: process.env.APPD_CONTROLLER_HOST,
      controllerPort: parseInt(process.env.APPD_CONTROLLER_PORT) || 443,
      controllerSslEnabled: process.env.APPD_CONTROLLER_SSL === 'true',
      accountName: process.env.APPD_ACCOUNT_NAME,
      accountAccessKey: process.env.APPD_ACCOUNT_ACCESS_KEY,
      applicationName: process.env.APPD_APP_NAME,
      tierName: process.env.APPD_TIER_NAME || 'OrderService',
      nodeName: process.env.APPD_NODE_NAME || 'OrderNode',
    });
    console.log('[OrderService] AppDynamics agent initialized (dual mode, Splunk OTel started by AppD)');
  } catch (err) {
    console.warn('[OrderService] AppDynamics dual mode could not be started:', err.message);
  }
} else {
  // Splunk-only: start Splunk OTel directly
  try {
    const { start } = require('@splunk/otel');
    start({
      serviceName: process.env.SERVICE_NAME || 'OrderService',
      accessToken: process.env.SPLUNK_ACCESS_TOKEN,
      logLevel: process.env.SPLUNK_LOG_LEVEL || 'debug',
    });
    console.log('[OrderService] Splunk OTel initialized');
  } catch (err) {
    console.warn('[OrderService] Splunk OTel could not be initialized:', err.message);
  }
}

const express = require('express');
const { v4: uuidv4 } = require('uuid');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json());

// In-memory storage for orders
const orders = new Map();

// Note: Request logging is handled by AppDynamics and Splunk OTel instrumentation
// No need for manual request logging middleware to avoid duplicate logs

// GET /health - Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    service: 'OrderService',
    uptime: process.uptime()
  });
});

// GET /orders - Get all orders
app.get('/orders', (req, res) => {
  try {
    const allOrders = Array.from(orders.values());
    
    // Optional filtering by status
    const { status, customerId } = req.query;
    let filteredOrders = allOrders;

    if (status) {
      filteredOrders = filteredOrders.filter(order => order.status === status);
    }

    if (customerId) {
      filteredOrders = filteredOrders.filter(order => order.customerId === customerId);
    }

    res.status(200).json({
      total: filteredOrders.length,
      orders: filteredOrders
    });
  } catch (error) {
    console.error('Error fetching orders:', error);
    res.status(500).json({ 
      error: 'Internal server error', 
      message: 'Failed to fetch orders' 
    });
  }
});

// POST /orders - Create a new order
app.post('/orders', (req, res) => {
  try {
    const { items, customerId, totalAmount } = req.body;

    // Validate request
    if (!items || !Array.isArray(items) || items.length === 0) {
      return res.status(400).json({ 
        error: 'Invalid request', 
        message: 'items array is required and must not be empty' 
      });
    }

    if (!customerId) {
      return res.status(400).json({ 
        error: 'Invalid request', 
        message: 'customerId is required' 
      });
    }

    // Create order
    const orderId = uuidv4();
    const order = {
      orderId,
      customerId,
      items,
      totalAmount: totalAmount || calculateTotal(items),
      status: 'pending',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    orders.set(orderId, order);

    console.log(`Order created: ${orderId}`);
    res.status(201).json(order);
  } catch (error) {
    console.error('Error creating order:', error);
    res.status(500).json({ 
      error: 'Internal server error', 
      message: 'Failed to create order' 
    });
  }
});

// GET /orders/:orderId - Get order by ID
app.get('/orders/:orderId', (req, res) => {
  try {
    const { orderId } = req.params;

    const order = orders.get(orderId);
    if (!order) {
      return res.status(404).json({ 
        error: 'Not found', 
        message: `Order ${orderId} not found` 
      });
    }

    res.status(200).json(order);
  } catch (error) {
    console.error('Error fetching order:', error);
    res.status(500).json({ 
      error: 'Internal server error', 
      message: 'Failed to fetch order' 
    });
  }
});

// POST /orders/:orderId/pay - Process payment for an order
app.post('/orders/:orderId/pay', (req, res) => {
  try {
    const { orderId } = req.params;
    const { paymentMethod, paymentDetails } = req.body;

    const order = orders.get(orderId);
    if (!order) {
      return res.status(404).json({ 
        error: 'Not found', 
        message: `Order ${orderId} not found` 
      });
    }

    if (order.status === 'paid') {
      return res.status(400).json({ 
        error: 'Invalid operation', 
        message: 'Order has already been paid' 
      });
    }

    if (order.status === 'failed') {
      return res.status(400).json({ 
        error: 'Invalid operation', 
        message: 'Cannot pay for a failed order' 
      });
    }

    // Simulate payment processing delay
    const processingTime = Math.random() * 1000 + 500; // 500-1500ms
    setTimeout(() => {
      order.status = 'paid';
      order.paymentMethod = paymentMethod || 'credit_card';
      order.paidAt = new Date().toISOString();
      order.updatedAt = new Date().toISOString();
      orders.set(orderId, order);
    }, processingTime);

    console.log(`Payment processing for order: ${orderId}`);
    res.status(200).json({ 
      message: 'Payment processed successfully',
      orderId,
      status: 'paid',
      processingTime: `${processingTime.toFixed(0)}ms`
    });
  } catch (error) {
    console.error('Error processing payment:', error);
    res.status(500).json({ 
      error: 'Internal server error', 
      message: 'Failed to process payment' 
    });
  }
});

// POST /orders/:orderId/fail - Simulate order failure
app.post('/orders/:orderId/fail', (req, res) => {
  try {
    const { orderId } = req.params;
    const { reason } = req.body;

    const order = orders.get(orderId);
    if (!order) {
      return res.status(404).json({ 
        error: 'Not found', 
        message: `Order ${orderId} not found` 
      });
    }

    // Simulate different types of failures
    const failureType = req.query.type || 'normal';

    switch (failureType) {
      case 'timeout':
        // Simulate timeout - delay response
        setTimeout(() => {
          res.status(500).json({ 
            error: 'Timeout', 
            message: 'Order processing timed out' 
          });
        }, 5000);
        break;

      case 'exception':
        // Throw an exception
        throw new Error('Simulated exception for order processing');

      case 'memory':
        // Simulate memory-intensive operation
        const largeArray = new Array(10000000).fill('data');
        res.status(500).json({ 
          error: 'Resource exhaustion', 
          message: 'Out of memory error',
          arraySize: largeArray.length 
        });
        break;

      default:
        // Normal failure
        order.status = 'failed';
        order.failureReason = reason || 'Simulated failure for testing';
        order.failedAt = new Date().toISOString();
        order.updatedAt = new Date().toISOString();
        orders.set(orderId, order);

        console.log(`Order failed: ${orderId} - ${order.failureReason}`);
        res.status(500).json({ 
          error: 'Order failed', 
          message: order.failureReason,
          orderId,
          status: 'failed'
        });
    }
  } catch (error) {
    console.error('Error during failure simulation:', error);
    res.status(500).json({ 
      error: 'Internal server error', 
      message: error.message 
    });
  }
});

// Helper function to calculate total
function calculateTotal(items) {
  return items.reduce((sum, item) => {
    return sum + (item.price * item.quantity);
  }, 0);
}

// 404 handler
app.use((req, res) => {
  res.status(404).json({ 
    error: 'Not found', 
    message: `Route ${req.method} ${req.path} not found` 
  });
});

// Error handler
app.use((err, req, res, next) => {
  console.error('Unhandled error:', err);
  res.status(500).json({ 
    error: 'Internal server error', 
    message: err.message 
  });
});

// Start server
app.listen(PORT, () => {
  console.log('==============================================');
  console.log(`OrderService started on port ${PORT}`);
  console.log('==============================================');
  console.log(`AppD Application: ${process.env.APPD_APP_NAME || process.env.APPD_APPLICATION_NAME || 'N/A'}`);
  console.log(`AppD Tier: ${process.env.APPD_TIER_NAME || process.env.SERVICE_NAME || 'OrderService'}`);
  console.log(`OTel Endpoint: ${process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://otel-collector:4318'}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
  console.log('==============================================');
});

module.exports = app;

