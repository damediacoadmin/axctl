# AXCTL Stripe Setup Guide

## Products to Create

### 1. AXCTL Pro Monthly
- **Product Name:** AXCTL Pro
- **Price:** $9/month
- **Type:** Recurring subscription
- **Billing Period:** Monthly
- **Price ID:** Save as `STRIPE_PRICE_MONTHLY` in `.env`

### 2. AXCTL Pro Annual
- **Product Name:** AXCTL Pro (same product as monthly)
- **Price:** $69/year
- **Type:** Recurring subscription
- **Billing Period:** Yearly
- **Price ID:** Save as `STRIPE_PRICE_ANNUAL` in `.env`

### 3. AXCTL Pro Lifetime
- **Product Name:** AXCTL Pro Lifetime
- **Price:** $179
- **Type:** One-time payment
- **Price ID:** Save as `STRIPE_PRICE_LIFETIME` in `.env`

---

## Webhook Configuration

### Endpoint URL:
```
https://api.axctl.dev/webhook/stripe
```

### Events to Listen For:
- `checkout.session.completed` - New purchase
- `customer.subscription.created` - Subscription started
- `customer.subscription.deleted` - Subscription canceled
- `customer.subscription.updated` - Plan changed
- `invoice.payment_succeeded` - Recurring payment
- `invoice.payment_failed` - Payment failed

### Webhook Secret:
Save as `STRIPE_WEBHOOK_SECRET` in `.env`

---

## Environment Variables

Create `~/clawd/axctl/api/.env`:

```env
# Stripe Keys
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Price IDs
STRIPE_PRICE_MONTHLY=price_...
STRIPE_PRICE_ANNUAL=price_...
STRIPE_PRICE_LIFETIME=price_...

# API Config
PORT=3000
DATABASE_PATH=./licenses.db
LICENSE_KEY_PREFIX=AXCTL-PRO

# Machine Limits
MAX_MACHINES_MONTHLY=1
MAX_MACHINES_ANNUAL=3
MAX_MACHINES_LIFETIME=5

# Grace Period (days)
OFFLINE_GRACE_PERIOD=30
```

---

## Checkout Session Creation

### Example Code:

```javascript
const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);

async function createCheckout(priceId, email) {
  const session = await stripe.checkout.sessions.create({
    mode: priceId === process.env.STRIPE_PRICE_LIFETIME ? 'payment' : 'subscription',
    line_items: [{
      price: priceId,
      quantity: 1,
    }],
    customer_email: email,
    success_url: 'https://axctl.dev/success?session_id={CHECKOUT_SESSION_ID}',
    cancel_url: 'https://axctl.dev/pricing',
    metadata: {
      product: 'axctl-pro',
    },
  });
  
  return session.url;
}
```

---

## License Key Generation

Format: `AXCTL-PRO-{STRIPE_CUSTOMER_ID}-{RANDOM_HASH}`

Example: `AXCTL-PRO-cus_ABC123xyz-9f8e7d6c`

**Why this format:**
- `AXCTL-PRO` - Product identifier
- `{STRIPE_CUSTOMER_ID}` - Links to Stripe customer
- `{RANDOM_HASH}` - Prevents guessing

---

## Testing

### Test Mode Setup:
1. Use Stripe test keys (sk_test_...)
2. Test card: `4242 4242 4242 4242`
3. Any future expiry date
4. Any CVC

### Verify:
- Checkout flow works
- Webhook receives events
- License key generated
- Database updated

---

## Go Live Checklist

- [ ] Switch to live Stripe keys
- [ ] Update webhook URL to production
- [ ] Test live checkout (small amount)
- [ ] Verify webhook signature validation
- [ ] Set up monitoring/alerts
- [ ] Document refund process
