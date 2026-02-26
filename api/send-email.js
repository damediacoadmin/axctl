/**
 * Send welcome email with license key via Resend
 */

const { Resend } = require('resend');

async function sendLicenseEmail(customerEmail, licenseKey, plan) {
  const planDetails = {
    monthly: { price: '$9/month', machines: 1 },
    annual: { price: '$69/year', machines: 3 },
    lifetime: { price: '$179 one-time', machines: 5 }
  };
  
  const details = planDetails[plan] || planDetails.annual;
  
  const emailBody = `
Hi there,

Thanks for purchasing AXCTL! Your license is ready to go.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR LICENSE KEY

${licenseKey}

⚠️ Save this key! You'll need it to activate AXCTL.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

QUICK START (3 steps)

1. Install AXCTL
   npm install -g @axctl/core

2. Activate Your License
   axctl activate ${licenseKey}

3. Start Automating!
   # Desktop automation
   ax-helper query Safari
   
   # iOS automation
   xcode-archive --project MyApp.xcodeproj

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR PLAN: ${plan.toUpperCase()}

Price: ${details.price}
Machine limit: ${details.machines} machine(s)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHAT YOU GET

✅ Desktop automation (control any Mac app)
✅ Xcode automation (build, archive, export)
✅ TestFlight uploads
✅ App Store Connect API
✅ 98% token savings vs Vision AI
✅ Save 30+ hours/year

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DOCUMENTATION

Installation: https://github.com/damediacoadmin/axctl/blob/main/INSTALL.md
Examples: https://github.com/damediacoadmin/axctl/tree/main/examples
Support: support@axctl.dev

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Thanks for choosing AXCTL! 🦾

David Miller
Founder, AXCTL
https://axctl.dev
  `.trim();
  
  try {
    // Initialize Resend
    const resend = new Resend(process.env.RESEND_API_KEY);
    
    // Send email
    const { data, error } = await resend.emails.send({
      from: 'AXCTL <hello@axctl.dev>',
      to: customerEmail,
      subject: 'Your AXCTL License Key + Installation Guide 🚀',
      text: emailBody,
      replyTo: 'hello@axctl.dev'
    });
    
    if (error) {
      console.error('Resend API error:', error);
      return false;
    }
    
    console.log('Email sent successfully:', data.id);
    return true;
  } catch (error) {
    console.error('Email send failed:', error);
    return false;
  }
}

module.exports = { sendLicenseEmail };
