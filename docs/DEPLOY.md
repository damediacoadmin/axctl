# AXCTL Deployment Guide

## Prerequisites

- Node.js 18+ installed
- Stripe account (test mode to start)
- Domain name (axctl.dev)
- Hosting for API server (Railway, Fly.io, or VPS)
- Cloudflare Pages or Vercel for landing page

---

## Step 1: Set Up Stripe (15 minutes)

### Create Products

1. Go to https://dashboard.stripe.com/products
2. Click "Add product"

**Product 1: AXCTL Pro (Monthly)**
- Name: AXCTL Pro
- Description: macOS automation toolkit - Monthly subscription
- Pricing: $9/month, recurring
- Copy the price ID (starts with `price_...`)

**Product 2: AXCTL Pro (Annual)**
- Same product as above, add new price
- Pricing: $69/year, recurring
- Copy the price ID

**Product 3: AXCTL Pro Lifetime**
- Name: AXCTL Pro Lifetime
- Description: macOS automation toolkit - Lifetime license
- Pricing: $179, one-time payment
- Copy the price ID

### Set Up Webhook

1. Go to https://dashboard.stripe.com/webhooks
2. Click "Add endpoint"
3. Endpoint URL: `https://api.axctl.dev/webhook/stripe`
4. Events to send:
   - `checkout.session.completed`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
5. Copy the webhook signing secret (starts with `whsec_...`)

---

## Step 2: Deploy API Server (30 minutes)

### Option A: Railway (Recommended - Easiest)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Create project
cd ~/clawd/axctl/api
railway init

# Set environment variables
railway variables set STRIPE_SECRET_KEY=sk_live_...
railway variables set STRIPE_WEBHOOK_SECRET=whsec_...
railway variables set STRIPE_PRICE_MONTHLY=price_...
railway variables set STRIPE_PRICE_ANNUAL=price_...
railway variables set STRIPE_PRICE_LIFETIME=price_...

# Deploy
railway up
```

### Option B: Fly.io

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Create app
cd ~/clawd/axctl/api
fly launch --name axctl-api

# Set secrets
fly secrets set STRIPE_SECRET_KEY=sk_live_...
fly secrets set STRIPE_WEBHOOK_SECRET=whsec_...
fly secrets set STRIPE_PRICE_MONTHLY=price_...
fly secrets set STRIPE_PRICE_ANNUAL=price_...
fly secrets set STRIPE_PRICE_LIFETIME=price_...

# Deploy
fly deploy
```

### Option C: VPS (DigitalOcean, AWS, etc.)

```bash
# SSH into server
ssh user@your-server.com

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Clone repo (or upload files)
git clone https://github.com/davidmiller/axctl-api.git
cd axctl-api

# Install dependencies
npm install

# Create .env file
cp .env.example .env
nano .env  # Edit with your values

# Install PM2 for process management
npm install -g pm2

# Start server
pm2 start server.js --name axctl-api
pm2 save
pm2 startup

# Set up Nginx reverse proxy
sudo apt install nginx
sudo nano /etc/nginx/sites-available/axctl-api

# Add this config:
# server {
#   listen 80;
#   server_name api.axctl.dev;
#   location / {
#     proxy_pass http://localhost:3000;
#     proxy_http_version 1.1;
#     proxy_set_header Upgrade $http_upgrade;
#     proxy_set_header Connection 'upgrade';
#     proxy_set_header Host $host;
#     proxy_cache_bypass $http_upgrade;
#   }
# }

sudo ln -s /etc/nginx/sites-available/axctl-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Install SSL certificate
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d api.axctl.dev
```

### Verify API is Running

```bash
curl https://api.axctl.dev/health
# Should return: {"status":"ok","timestamp":1709234567890}
```

---

## Step 3: Deploy Landing Page (15 minutes)

### Option A: Cloudflare Pages (Recommended)

1. Go to https://dash.cloudflare.com
2. Pages → Create a project
3. Connect Git repository (or upload files)
4. Build settings:
   - Framework preset: None
   - Build command: (leave empty)
   - Build output directory: `landing`
5. Deploy
6. Add custom domain: axctl.dev

### Option B: Vercel

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd ~/clawd/axctl/landing
vercel

# Add domain
vercel domains add axctl.dev
```

### Option C: Netlify

1. Go to https://app.netlify.com
2. Drag & drop the `landing/` folder
3. Add custom domain: axctl.dev

### Update Landing Page

Before deploying, update `landing/index.html`:

```javascript
// Line ~1234 - Replace with your actual Stripe publishable key
const stripe = Stripe('pk_live_YOUR_PUBLISHABLE_KEY');
```

---

## Step 4: Configure DNS (5 minutes)

Add these DNS records to your domain:

```
A     @              76.76.21.21    # Cloudflare Pages IP (or your hosting provider)
CNAME api            your-api-host  # Points to Railway/Fly.io/VPS
CNAME www            @              # Redirect www to root
```

---

## Step 5: Test End-to-End (10 minutes)

### Test Free Tier
1. Visit https://axctl.dev
2. Click "Download Free"
3. Should redirect to GitHub

### Test Pro Tier Checkout
1. Visit https://axctl.dev#pricing
2. Click "Start Annual Plan"
3. Should open Stripe Checkout
4. Use test card: `4242 4242 4242 4242`
5. Complete checkout
6. Check API logs for license generation

### Test Webhook
```bash
# On your local machine
stripe listen --forward-to https://api.axctl.dev/webhook/stripe

# In another terminal
stripe trigger checkout.session.completed

# Check API logs
tail -f logs/api.log  # or check Railway/Fly logs
```

---

## Step 6: Go Live Checklist

Before announcing publicly:

- [ ] API server is deployed and accessible
- [ ] Landing page is deployed to axctl.dev
- [ ] Stripe is in **live mode** (not test mode)
- [ ] All 3 Stripe products created
- [ ] Webhook is receiving events
- [ ] Test checkout flow works end-to-end
- [ ] License activation works
- [ ] 30-day money-back guarantee policy written
- [ ] Privacy policy published
- [ ] Terms of service published
- [ ] Support email (support@axctl.dev) set up
- [ ] GitHub repo created (for free tier)
- [ ] npm package published (@axctl/core)

---

## Monitoring & Maintenance

### Check API Health
```bash
# Set up uptime monitoring
curl https://uptimerobot.com
# Add monitor: https://api.axctl.dev/health
```

### View Logs
```bash
# Railway
railway logs

# Fly.io
fly logs

# VPS
pm2 logs axctl-api
```

### Database Backups
```bash
# Set up daily backups of licenses.db
# Railway: Automatic
# Fly.io: fly volumes snapshots create
# VPS: Add cron job
0 2 * * * cp /path/to/licenses.db /backups/licenses-$(date +\%Y\%m\%d).db
```

---

## Troubleshooting

### Webhook not receiving events
- Check Stripe dashboard → Webhooks → Endpoint status
- Verify endpoint URL is correct
- Check API logs for errors
- Test with Stripe CLI: `stripe trigger checkout.session.completed`

### License activation failing
- Check machine limit not exceeded
- Verify license is in `active` status
- Check expiry date hasn't passed
- Look for errors in API logs

### Checkout not working
- Verify Stripe publishable key in HTML
- Check browser console for errors
- Ensure Stripe.js is loaded
- Test in incognito mode (clear cache)

---

## Cost Estimate

**Monthly costs for 100 paying customers:**

| Service | Cost | Notes |
|---------|------|-------|
| Railway/Fly.io | $5-10 | API hosting |
| Cloudflare Pages | $0 | Landing page (free tier) |
| Stripe | $225 | 2.9% + $0.30 per transaction |
| Email (SendGrid) | $15 | For license delivery |
| **Total** | **~$245** | |

**Revenue:** 100 customers × $69/year = $6,900/year  
**Profit:** $6,900 - ($245 × 12) = **$3,960/year**

---

## Security Checklist

- [ ] HTTPS enabled on all domains
- [ ] Environment variables not committed to Git
- [ ] Webhook signature verification enabled
- [ ] SQL injection prevention (using prepared statements)
- [ ] Rate limiting on API endpoints
- [ ] CORS configured correctly
- [ ] Stripe keys stored securely
- [ ] Database backups automated

---

**Need help? Email [hello@axctl.dev](mailto:hello@axctl.dev)**
