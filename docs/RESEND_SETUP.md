# Resend Email Setup Guide

## 1. Create Resend Account

1. Go to: https://resend.com/signup
2. Sign up with your email
3. Verify your account

## 2. Add Domain (axctl.dev)

1. In Resend dashboard: **Domains** → **Add Domain**
2. Enter: `axctl.dev`
3. Click **Add Domain**

## 3. Add DNS Records to Cloudflare

Resend will show you 3 DNS records to add. Copy them to Cloudflare:

### Go to Cloudflare
https://dash.cloudflare.com → Select `axctl.dev` → **DNS** → **Records**

### Add These Records

**TXT Record (for verification):**
- Type: `TXT`
- Name: `@` or `axctl.dev`
- Content: `resend-verification=abc123...` (copy from Resend)
- TTL: Auto
- Proxy: Off (DNS only)

**MX Records (for sending):**

Record 1:
- Type: `MX`
- Name: `@` or `axctl.dev`
- Mail server: `feedback-smtp.us-east-1.amazonses.com`
- Priority: `10`
- TTL: Auto

Record 2:
- Type: `MX`
- Name: `@` or `axctl.dev`
- Mail server: `feedback-smtp.eu-west-1.amazonses.com`
- Priority: `10`
- TTL: Auto

**CNAME Records (for DKIM):**

You'll get 3 CNAME records from Resend that look like:
- `resend._domainkey.axctl.dev` → `...resend.dev`
- `resend2._domainkey.axctl.dev` → `...resend.dev`
- `resend3._domainkey.axctl.dev` → `...resend.dev`

Add all 3 as CNAME records with:
- Proxy: Off (DNS only)
- TTL: Auto

## 4. Verify Domain

1. After adding DNS records, wait 5-10 minutes
2. Go back to Resend → **Domains**
3. Click **Verify** next to `axctl.dev`
4. Status should change to ✅ **Verified**

## 5. Create API Key

1. In Resend: **Settings** → **API Keys**
2. Click **Create API Key**
3. Name: `AXCTL Production`
4. Permissions: **Full Access**
5. Click **Create**
6. **Copy the key** (starts with `re_...`)

⚠️ Save this key! You won't see it again.

## 6. Add to Railway

1. Go to Railway project: https://railway.app/project/c811587e-29e9-422b-a753-b71c0f6d0160
2. Click your service → **Variables**
3. Click **+ New Variable**
4. Name: `RESEND_API_KEY`
5. Value: `re_...` (paste your key)
6. Click **Add**
7. Service will redeploy automatically

## 7. Test Email

Once Railway redeploys, test the email system:

```bash
curl -X POST https://agile-enjoyment-production-82c8.up.railway.app/test-email \
  -H "Content-Type: application/json" \
  -d '{"to":"your-email@gmail.com"}'
```

You should receive a test email from `hello@axctl.dev`!

## Troubleshooting

### Domain verification stuck?
- Wait 15-30 minutes for DNS propagation
- Check DNS records with: `dig axctl.dev TXT`
- Make sure CNAME records have **Proxy: Off**

### Emails not sending?
- Check Railway logs for errors
- Verify RESEND_API_KEY is set in Railway
- Check Resend dashboard → **Logs** for delivery status

### "Domain not verified" error?
- Domain must be verified before sending emails
- Check Resend dashboard → **Domains** → `axctl.dev` status

## Free Tier Limits

- **3,000 emails/month** free
- After that: $1 per 1,000 emails
- More than enough for AXCTL's launch phase

## Support

If you need help:
- Resend Docs: https://resend.com/docs
- Resend Support: support@resend.com
