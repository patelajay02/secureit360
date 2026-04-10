// app/privacy/page.js
// SecureIT360 - Privacy Policy Page

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-white text-gray-900">
      <div className="max-w-4xl mx-auto px-6 py-12">
        <div className="mb-8">
          <a href="/" className="text-red-600 hover:text-red-700 text-sm font-medium">
            Back to SecureIT360
          </a>
        </div>
        <div className="prose max-w-none" dangerouslySetInnerHTML={{ __html: PRIVACY_HTML }} />
      </div>
    </div>
  )
}

const PRIVACY_HTML = `<style>
  [data-custom-class='body'], [data-custom-class='body'] * { background: transparent !important; }
  [data-custom-class='body_text'], [data-custom-class='body_text'] * { color: #595959 !important; font-size: 14px !important; font-family: Arial !important; }
</style>
<div data-custom-class="body">
<h1 style="font-size:26px;font-family:Arial;color:#000;">PRIVACY POLICY</h1>
<p><strong>Last updated April 09, 2026</strong></p>
<p>This Privacy Notice for Global Cyber Assurance (doing business as SecureIT360) describes how and why we might access, collect, store, use, and/or share your personal information when you use our services, including when you visit our website at <a href="https://app.secureit360.co">https://app.secureit360.co</a> or use our mobile application SecureIT360.</p>
<p><strong>Questions or concerns?</strong> Contact us at <a href="mailto:governance@secureit360.co">governance@secureit360.co</a></p>

<h2 style="font-size:19px;font-family:Arial;color:#000;margin-top:24px;">1. WHAT INFORMATION DO WE COLLECT?</h2>
<p>We collect personal information that you provide to us when you register, including: names, phone numbers, email addresses, job titles, usernames, passwords, contact preferences, and billing addresses.</p>
<p><strong>Payment Data.</strong> All payment data is handled and stored by Stripe. See their privacy policy at <a href="https://stripe.com/en-nz/privacy">https://stripe.com/en-nz/privacy</a></p>
<p>We automatically collect certain information when you visit our services, including IP address, browser type, device information, and location data.</p>

<h2 style="font-size:19px;font-family:Arial;color:#000;margin-top:24px;">2. HOW DO WE PROCESS YOUR INFORMATION?</h2>
<p>We process your information to provide our services, manage your account, respond to inquiries, send administrative information, fulfil orders, request feedback, send marketing communications, protect our services, evaluate and improve our services, identify usage trends, and comply with legal obligations.</p>

<h2 style="font-size:19px;font-family:Arial;color:#000;margin-top:24px;">3. WHEN AND WITH WHOM DO WE SHARE YOUR PERSONAL INFORMATION?</h2>
<p>We share your data with the following third parties:</p>
<ul style="margin-left:20px;">
<li><strong>Stripe</strong> - Invoice and billing</li>
<li><strong>Supabase</strong> - Cloud infrastructure and database (Sydney, Australia)</li>
<li><strong>Vercel</strong> - Frontend hosting</li>
<li><strong>Railway</strong> - Backend hosting</li>
<li><strong>SendGrid</strong> - Email communications</li>
</ul>

<h2 style="font-size:19px;font-family:Arial;color:#000;margin-top:24px;">4. DO WE USE COOKIES AND OTHER TRACKING TECHNOLOGIES?</h2>
<p>We may use cookies and similar tracking technologies. See our Cookie Policy at <a href="https://app.secureit360.co/cookie-policy">https://app.secureit360.co/cookie-policy</a></p>

<h2 style="font-size:19px;font-family:Arial;color:#000;margin-top:24px;">5. HOW LONG DO WE KEEP YOUR INFORMATION?</h2>
<p>We keep your personal information for as long as you have an account with us, unless a longer retention period is required by law.</p>

<h2 style="font-size:19px;font-family:Arial;color:#000;margin-top:24px;">6. HOW DO WE KEEP YOUR INFORMATION SAFE?</h2>
<p>We have implemented appropriate technical and organisational security measures. All data is encrypted at rest and in transit using AES-256 encryption and stored in Sydney, Australia.</p>

<h2 style="font-size:19px;font-family:Arial;color:#000;margin-top:24px;">7. DO WE COLLECT INFORMATION FROM MINORS?</h2>
<p>We do not knowingly collect data from children under 18 years of age. Contact us at <a href="mailto:governance@secureit360.co">governance@secureit360.co</a> if you become aware of any such data.</p>

<h2 style="font-size:19px;font-family:Arial;color:#000;margin-top:24px;">8. WHAT ARE YOUR PRIVACY RIGHTS?</h2>
<p>You may review, change, or terminate your account at any time by visiting <a href="https://app.secureit360.co/settings">https://app.secureit360.co/settings</a> or contacting us at <a href="mailto:governance@secureit360.co">governance@secureit360.co</a></p>

<h2 style="font-size:19px;font-family:Arial;color:#000;margin-top:24px;">9. CONTROLS FOR DO-NOT-TRACK FEATURES</h2>
<p>We do not currently respond to DNT browser signals as no uniform technology standard has been finalised.</p>

<h2 style="font-size:19px;font-family:Arial;color:#000;margin-top:24px;">10. AUSTRALIA AND NEW ZEALAND SPECIFIC PRIVACY RIGHTS</h2>
<p>We collect and process your personal information under Australia's Privacy Act 1988 and New Zealand's Privacy Act 2020.</p>
<p>To submit a complaint: <a href="https://www.oaic.gov.au/privacy/privacy-complaints/lodge-a-privacy-complaint-with-us">Office of the Australian Information Commissioner</a> or <a href="https://www.privacy.org.nz/your-rights/making-a-complaint/">Office of New Zealand Privacy Commissioner</a>.</p>

<h2 style="font-size:19px;font-family:Arial;color:#000;margin-top:24px;">11. DATA STORAGE AND SECURITY PLATFORM SPECIFIC TERMS</h2>
<p>All client data is stored on Supabase infrastructure located in Sydney, Australia (ap-southeast-2 region). By using SecureIT360 you consent to your data being stored and processed in Australia. All data is encrypted at rest and in transit using industry-standard AES-256 encryption. SecureIT360 performs automated security scanning of domains you provide. By adding a domain to the platform you confirm you own or have authority to scan that domain. Security findings generated by the platform are for awareness purposes only and do not constitute legal advice. Global Cyber Assurance Ltd is the data controller for all personal information collected through the SecureIT360 platform. For privacy enquiries contact <a href="mailto:governance@secureit360.co">governance@secureit360.co</a></p>

<h2 style="font-size:19px;font-family:Arial;color:#000;margin-top:24px;">12. DO WE MAKE UPDATES TO THIS NOTICE?</h2>
<p>We may update this Privacy Notice from time to time. We encourage you to review this Privacy Notice frequently.</p>

<h2 style="font-size:19px;font-family:Arial;color:#000;margin-top:24px;">13. HOW CAN YOU CONTACT US ABOUT THIS NOTICE?</h2>
<p>Email us at <a href="mailto:governance@secureit360.co">governance@secureit360.co</a></p>
<p>Global Cyber Assurance Ltd<br>300 Richmond Road<br>Grey Lynn<br>Auckland 1021<br>New Zealand</p>

<h2 style="font-size:19px;font-family:Arial;color:#000;margin-top:24px;">14. HOW CAN YOU REVIEW, UPDATE, OR DELETE THE DATA WE COLLECT FROM YOU?</h2>
<p>Visit <a href="https://app.secureit360.co/settings">https://app.secureit360.co/settings</a> to review, update, or delete your personal information.</p>
<br>
<p style="color:#999;font-size:12px;"><em>This Privacy Policy was created using Termly's Privacy Policy Generator</em></p>
</div>`
