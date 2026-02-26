#!/usr/bin/env node
/**
 * AXCTL License Validation API
 * Handles Stripe webhooks, license activation, and validation
 */

const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const crypto = require('crypto');
const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json());

// CORS - Allow requests from axctl.dev
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  // Handle preflight
  if (req.method === 'OPTIONS') {
    return res.sendStatus(200);
  }
  
  next();
});

// Database setup
const db = new sqlite3.Database(process.env.DATABASE_PATH || './licenses.db');

// Initialize database tables
db.serialize(() => {
  db.run(`
    CREATE TABLE IF NOT EXISTS licenses (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      license_key TEXT UNIQUE NOT NULL,
      stripe_customer_id TEXT NOT NULL,
      stripe_subscription_id TEXT,
      plan TEXT NOT NULL,
      status TEXT DEFAULT 'active',
      created_at INTEGER NOT NULL,
      expires_at INTEGER,
      last_validated INTEGER
    )
  `);
  
  db.run(`
    CREATE TABLE IF NOT EXISTS machines (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      license_id INTEGER NOT NULL,
      machine_id TEXT NOT NULL,
      activated_at INTEGER NOT NULL,
      last_seen INTEGER NOT NULL,
      FOREIGN KEY (license_id) REFERENCES licenses(id),
      UNIQUE(license_id, machine_id)
    )
  `);
});

// Helper: Generate license key
function generateLicenseKey(customerId) {
  const randomHash = crypto.randomBytes(4).toString('hex');
  return `${process.env.LICENSE_KEY_PREFIX}-${customerId}-${randomHash}`;
}

// Helper: Get max machines for plan
function getMaxMachines(plan) {
  const limits = {
    monthly: parseInt(process.env.MAX_MACHINES_MONTHLY) || 1,
    annual: parseInt(process.env.MAX_MACHINES_ANNUAL) || 3,
    lifetime: parseInt(process.env.MAX_MACHINES_LIFETIME) || 5,
  };
  return limits[plan] || 1;
}

// Helper: Calculate expiry
function calculateExpiry(plan) {
  if (plan === 'lifetime') return null;
  const now = Date.now();
  const duration = plan === 'annual' ? 365 : 30; // days
  return now + (duration * 24 * 60 * 60 * 1000);
}

// POST /activate - Activate license on a machine
app.post('/activate', (req, res) => {
  const { license_key, machine_id } = req.body;
  
  if (!license_key || !machine_id) {
    return res.status(400).json({ error: 'Missing license_key or machine_id' });
  }
  
  // Verify license exists and is active
  db.get('SELECT * FROM licenses WHERE license_key = ? AND status = ?', 
    [license_key, 'active'], 
    (err, license) => {
      if (err) {
        console.error('Database error:', err);
        return res.status(500).json({ error: 'Database error' });
      }
      
      if (!license) {
        return res.status(404).json({ error: 'Invalid or inactive license' });
      }
      
      // Check if license has expired
      if (license.expires_at && license.expires_at < Date.now()) {
        return res.status(403).json({ error: 'License expired' });
      }
      
      // Count existing machines
      db.get('SELECT COUNT(*) as count FROM machines WHERE license_id = ?', 
        [license.id], 
        (err, result) => {
          if (err) {
            console.error('Database error:', err);
            return res.status(500).json({ error: 'Database error' });
          }
          
          const maxMachines = getMaxMachines(license.plan);
          
          // Check if machine already registered
          db.get('SELECT * FROM machines WHERE license_id = ? AND machine_id = ?',
            [license.id, machine_id],
            (err, existingMachine) => {
              if (err) {
                console.error('Database error:', err);
                return res.status(500).json({ error: 'Database error' });
              }
              
              const now = Date.now();
              
              if (existingMachine) {
                // Update last_seen
                db.run('UPDATE machines SET last_seen = ? WHERE id = ?',
                  [now, existingMachine.id],
                  (err) => {
                    if (err) {
                      console.error('Database error:', err);
                      return res.status(500).json({ error: 'Database error' });
                    }
                    
                    return res.json({
                      valid: true,
                      plan: license.plan,
                      expires: license.expires_at,
                      max_machines: maxMachines,
                      message: 'Machine already activated'
                    });
                  });
              } else {
                // New machine - check limit
                if (result.count >= maxMachines) {
                  return res.status(403).json({ 
                    error: 'Machine limit reached',
                    max_machines: maxMachines,
                    current_machines: result.count
                  });
                }
                
                // Register new machine
                db.run('INSERT INTO machines (license_id, machine_id, activated_at, last_seen) VALUES (?, ?, ?, ?)',
                  [license.id, machine_id, now, now],
                  (err) => {
                    if (err) {
                      console.error('Database error:', err);
                      return res.status(500).json({ error: 'Database error' });
                    }
                    
                    return res.json({
                      valid: true,
                      plan: license.plan,
                      expires: license.expires_at,
                      max_machines: maxMachines,
                      message: 'Machine activated successfully'
                    });
                  });
              }
            });
        });
    });
});

// POST /validate - Check if license is still valid
app.post('/validate', (req, res) => {
  const { license_key, machine_id } = req.body;
  
  if (!license_key || !machine_id) {
    return res.status(400).json({ error: 'Missing license_key or machine_id' });
  }
  
  db.get('SELECT * FROM licenses WHERE license_key = ?', [license_key], (err, license) => {
    if (err) {
      console.error('Database error:', err);
      return res.status(500).json({ error: 'Database error' });
    }
    
    if (!license) {
      return res.json({ valid: false, reason: 'License not found' });
    }
    
    if (license.status !== 'active') {
      return res.json({ valid: false, reason: 'License inactive' });
    }
    
    // Check expiry with grace period
    if (license.expires_at) {
      const gracePeriod = parseInt(process.env.OFFLINE_GRACE_PERIOD) || 30;
      const graceMs = gracePeriod * 24 * 60 * 60 * 1000;
      const now = Date.now();
      
      if (license.expires_at < (now - graceMs)) {
        return res.json({ valid: false, reason: 'License expired' });
      }
    }
    
    // Verify machine is registered
    db.get('SELECT * FROM machines WHERE license_id = ? AND machine_id = ?',
      [license.id, machine_id],
      (err, machine) => {
        if (err) {
          console.error('Database error:', err);
          return res.status(500).json({ error: 'Database error' });
        }
        
        if (!machine) {
          return res.json({ valid: false, reason: 'Machine not registered' });
        }
        
        // Update last_validated and last_seen
        const now = Date.now();
        db.run('UPDATE licenses SET last_validated = ? WHERE id = ?', [now, license.id]);
        db.run('UPDATE machines SET last_seen = ? WHERE id = ?', [now, machine.id]);
        
        return res.json({
          valid: true,
          plan: license.plan,
          expires: license.expires_at,
          status: license.status
        });
      });
  });
});

// POST /webhook/stripe - Handle Stripe webhook events
app.post('/webhook/stripe', express.raw({type: 'application/json'}), async (req, res) => {
  const sig = req.headers['stripe-signature'];
  
  let event;
  try {
    event = stripe.webhooks.constructEvent(req.body, sig, process.env.STRIPE_WEBHOOK_SECRET);
  } catch (err) {
    console.error('Webhook signature verification failed:', err.message);
    return res.status(400).send(`Webhook Error: ${err.message}`);
  }
  
  // Handle event
  switch (event.type) {
    case 'checkout.session.completed': {
      const session = event.data.object;
      const customerId = session.customer;
      const subscriptionId = session.subscription;
      
      // Determine plan type
      let plan = 'monthly';
      if (session.mode === 'payment') {
        plan = 'lifetime';
      } else if (session.subscription) {
        // Fetch subscription to check interval
        const subscription = await stripe.subscriptions.retrieve(subscriptionId);
        plan = subscription.items.data[0].price.recurring.interval === 'year' ? 'annual' : 'monthly';
      }
      
      // Generate license key
      const licenseKey = generateLicenseKey(customerId);
      const now = Date.now();
      const expiresAt = calculateExpiry(plan);
      
      // Insert into database
      db.run(`
        INSERT INTO licenses 
        (license_key, stripe_customer_id, stripe_subscription_id, plan, created_at, expires_at, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
      `, [licenseKey, customerId, subscriptionId, plan, now, expiresAt, 'active'], (err) => {
        if (err) {
          console.error('Failed to create license:', err);
        } else {
          console.log(`License created: ${licenseKey} (${plan})`);
          
          // TODO: Send email with license key to customer
        }
      });
      
      break;
    }
    
    case 'customer.subscription.deleted': {
      const subscription = event.data.object;
      const subscriptionId = subscription.id;
      
      // Deactivate license
      db.run('UPDATE licenses SET status = ? WHERE stripe_subscription_id = ?',
        ['canceled', subscriptionId],
        (err) => {
          if (err) {
            console.error('Failed to cancel license:', err);
          } else {
            console.log(`License canceled for subscription: ${subscriptionId}`);
          }
        });
      
      break;
    }
    
    case 'invoice.payment_succeeded': {
      const invoice = event.data.object;
      const subscriptionId = invoice.subscription;
      
      // Extend expiry for subscription
      db.get('SELECT * FROM licenses WHERE stripe_subscription_id = ?',
        [subscriptionId],
        (err, license) => {
          if (err || !license) return;
          
          const newExpiry = calculateExpiry(license.plan);
          db.run('UPDATE licenses SET expires_at = ?, status = ? WHERE id = ?',
            [newExpiry, 'active', license.id],
            (err) => {
              if (err) {
                console.error('Failed to extend license:', err);
              } else {
                console.log(`License extended: ${license.license_key}`);
              }
            });
        });
      
      break;
    }
    
    case 'invoice.payment_failed': {
      const invoice = event.data.object;
      const subscriptionId = invoice.subscription;
      
      // Mark as payment_failed (don't cancel yet, Stripe will retry)
      db.run('UPDATE licenses SET status = ? WHERE stripe_subscription_id = ?',
        ['payment_failed', subscriptionId],
        (err) => {
          if (err) {
            console.error('Failed to mark license as payment_failed:', err);
          } else {
            console.log(`Payment failed for subscription: ${subscriptionId}`);
          }
        });
      
      break;
    }
  }
  
  res.json({received: true});
});

// POST /create-checkout - Create Stripe Checkout session
app.post('/create-checkout', async (req, res) => {
  const { plan } = req.body;
  
  if (!plan || !['monthly', 'annual', 'lifetime'].includes(plan)) {
    return res.status(400).json({ error: 'Invalid plan' });
  }
  
  // Get price ID for plan
  const priceIds = {
    monthly: process.env.STRIPE_PRICE_MONTHLY,
    annual: process.env.STRIPE_PRICE_ANNUAL,
    lifetime: process.env.STRIPE_PRICE_LIFETIME,
  };
  
  try {
    const session = await stripe.checkout.sessions.create({
      mode: plan === 'lifetime' ? 'payment' : 'subscription',
      payment_method_types: ['card'],
      line_items: [{
        price: priceIds[plan],
        quantity: 1,
      }],
      success_url: `${req.headers.origin || 'https://axctl.dev'}/success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${req.headers.origin || 'https://axctl.dev'}/#pricing`,
      metadata: { plan },
    });
    
    res.json({ sessionId: session.id });
  } catch (error) {
    console.error('Checkout error:', error);
    res.status(500).json({ error: 'Failed to create checkout session' });
  }
});

// GET /health - Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: Date.now() });
});

// Start server
app.listen(PORT, () => {
  console.log(`AXCTL License API running on port ${PORT}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, closing database...');
  db.close(() => {
    process.exit(0);
  });
});
