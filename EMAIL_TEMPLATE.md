# AXCTL Purchase Email Template

## Subject: Your AXCTL License Key + Installation Guide 🚀

---

Hi there,

Thanks for purchasing AXCTL! Your license is ready to go.

## Your License Key

```
{{LICENSE_KEY}}
```

**⚠️ Important:** Save this key somewhere safe. You'll need it to activate AXCTL on your Mac.

---

## Quick Start (3 steps)

### 1. Install AXCTL

```bash
npm install -g @axctl/core
```

Or download from GitHub: https://github.com/damediacoadmin/axctl

### 2. Activate Your License

```bash
axctl activate {{LICENSE_KEY}}
```

### 3. Start Automating!

```bash
# Desktop automation (free features work too)
ax-helper query Safari
ax-helper click "Button:OK"

# iOS automation (your paid features)
xcode-archive --project MyApp.xcodeproj --scheme MyApp
asc-api upload-build --ipa MyApp.ipa
```

---

## Your Plan: {{PLAN}}

{{#if monthly}}
- **Monthly subscription:** $9/month
- **Machine limit:** 1 machine
- **Renews:** Automatically every 30 days
{{/if}}

{{#if annual}}
- **Annual subscription:** $69/year
- **Machine limit:** 3 machines
- **Renews:** Automatically every 365 days
- **Savings:** $39/year vs monthly
{{/if}}

{{#if lifetime}}
- **Lifetime license:** $179 one-time
- **Machine limit:** 5 machines
- **Renews:** Never! Yours forever
- **Savings:** Pays for itself in 2.6 years
{{/if}}

---

## What You Get

✅ **Desktop automation** - Control any Mac app via Accessibility APIs  
✅ **Xcode automation** - Build, archive, export iOS apps  
✅ **TestFlight uploads** - Automated deployment pipeline  
✅ **App Store Connect API** - Manage apps, submissions, metadata  
✅ **Token savings** - 98% cheaper than Vision AI (150 vs 7,800 tokens/action)  
✅ **Time savings** - Save 30+ hours/year on manual tasks  

---

## Full Documentation

- **Installation Guide:** https://github.com/damediacoadmin/axctl/blob/main/INSTALL.md
- **Examples:** https://github.com/damediacoadmin/axctl/tree/main/examples
- **API Reference:** https://github.com/damediacoadmin/axctl#readme

---

## Need Help?

- **Email:** hello@axctl.dev
- **GitHub Issues:** https://github.com/damediacoadmin/axctl/issues
- **Discord:** https://discord.gg/axctl (coming soon)

---

## Manage Your Subscription

{{#if monthly}}
You can cancel anytime from your Stripe dashboard:
https://billing.stripe.com/p/login/{{CUSTOMER_ID}}
{{/if}}

{{#if annual}}
You can cancel anytime from your Stripe dashboard:
https://billing.stripe.com/p/login/{{CUSTOMER_ID}}
{{/if}}

{{#if lifetime}}
Your lifetime license never expires - no subscription to manage!
{{/if}}

---

Thanks for choosing AXCTL! 🦾

**David Miller**  
Founder, AXCTL  
https://axctl.dev

P.S. If you save thousands with AXCTL, I'd love to hear about it! Reply to this email or tweet @DisruptiveBytes.

---

*This email was sent because you purchased AXCTL. Your license key is stored securely and can only be activated on {{MACHINE_LIMIT}} machine(s).*

