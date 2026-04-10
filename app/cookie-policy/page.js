// app/cookie-policy/page.js
// SecureIT360 - Cookie Policy

export default function CookiePolicyPage() {
  return (
    <div className="min-h-screen bg-white text-gray-900">
      <div className="max-w-4xl mx-auto px-6 py-12">
        <div className="mb-8">
          <a href="/" className="text-red-600 hover:text-red-700 text-sm font-medium">Back to SecureIT360</a>
        </div>
        <h1 style={{fontSize:'26px', fontFamily:'Arial', color:'#000', marginBottom:'8px'}}>COOKIE POLICY</h1>
        <p style={{color:'#595959', fontSize:'14px', marginBottom:'32px'}}><strong>Last updated April 10, 2026</strong></p>

        <div style={{fontFamily:'Arial', fontSize:'14px', color:'#595959', lineHeight:'1.8'}}>

          <h2 style={{fontSize:'19px', color:'#000', marginTop:'32px', marginBottom:'12px'}}>1. WHAT ARE COOKIES?</h2>
          <p>Cookies are small data files placed on your device when you visit a website. They are widely used to make websites work efficiently and to provide information to website owners.</p>

          <h2 style={{fontSize:'19px', color:'#000', marginTop:'32px', marginBottom:'12px'}}>2. HOW WE USE COOKIES</h2>
          <p>SecureIT360 uses cookies and similar technologies for the following purposes:</p>
          <ul style={{marginLeft:'20px', marginBottom:'12px'}}>
            <li><strong>Essential cookies</strong> — Required for the platform to function. These include session authentication tokens that keep you logged in securely.</li>
            <li><strong>Security cookies</strong> — Used to detect and prevent security threats including reCAPTCHA for bot prevention.</li>
            <li><strong>Preference cookies</strong> — Remember your settings and preferences such as your country and plan selection.</li>
          </ul>

          <h2 style={{fontSize:'19px', color:'#000', marginTop:'32px', marginBottom:'12px'}}>3. THIRD PARTY COOKIES</h2>
          <p>We use the following third party services that may set cookies:</p>
          <ul style={{marginLeft:'20px', marginBottom:'12px'}}>
            <li><strong>Google reCAPTCHA</strong> — Used on our registration page to prevent automated abuse</li>
            <li><strong>Stripe</strong> — Used during payment processing for fraud prevention</li>
          </ul>

          <h2 style={{fontSize:'19px', color:'#000', marginTop:'32px', marginBottom:'12px'}}>4. MANAGING COOKIES</h2>
          <p>Most web browsers allow you to control cookies through browser settings. You can choose to block or delete cookies. Please note that blocking essential cookies may prevent you from logging in to the platform.</p>

          <h2 style={{fontSize:'19px', color:'#000', marginTop:'32px', marginBottom:'12px'}}>5. LOCAL STORAGE</h2>
          <p>In addition to cookies, SecureIT360 uses browser local storage to store your session token, company name, country, and plan information. This data remains on your device and is cleared when you sign out.</p>

          <h2 style={{fontSize:'19px', color:'#000', marginTop:'32px', marginBottom:'12px'}}>6. CONTACT US</h2>
          <p>For questions about our cookie use, contact us at <a href="mailto:governance@secureit360.co" style={{color:'#dc2626'}}>governance@secureit360.co</a></p>

        </div>
      </div>
    </div>
  )
}
