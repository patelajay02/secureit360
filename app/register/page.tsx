'use client'

import { useState, useRef } from 'react'
import ReCAPTCHA from 'react-google-recaptcha'

const COUNTRIES = [
  { code: 'NZ', name: 'New Zealand' },
  { code: 'AU', name: 'Australia' },
  { code: 'GB', name: 'United Kingdom' },
  { code: 'US', name: 'United States' },
  { code: 'CA', name: 'Canada' },
  { code: 'SG', name: 'Singapore' },
  { code: 'IN', name: 'India' },
  { code: 'AE', name: 'United Arab Emirates' },
  { code: 'ZA', name: 'South Africa' },
]

export default function RegisterPage() {
  const recaptchaRef = useRef<ReCAPTCHA>(null)
  const [formData, setFormData] = useState({
    company_name: '',
    domain: '',
    email: '',
    password: '',
    country: '',
    mobile: ''
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)

  const handleRegister = async () => {
    setError('')

    if (!formData.company_name) { setError('Please enter your business name.'); return }
    if (!formData.country) { setError('Please select your country.'); return }
    if (!formData.domain) { setError('Please enter your company domain.'); return }
    if (!formData.email) { setError('Please enter your email address.'); return }
    
    if (!formData.password) { setError('Please choose a password.'); return }

    const emailDomain = formData.email.split('@')[1]?.toLowerCase()
    const companyDomain = formData.domain.toLowerCase().replace(/^www\./, '')
    if (emailDomain !== companyDomain) {
      setError(`Your email must match your company domain. Expected @${companyDomain}`)
      return
    }

    const token = recaptchaRef.current?.getValue()
    if (!token) {
      setError('Please tick the reCAPTCHA box before continuing.')
      return
    }

    setLoading(true)

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...formData, recaptcha_token: token })
      })

      const data = await response.json()

      if (!response.ok) {
        setError(typeof data.detail === 'string' ? data.detail : 'Something went wrong. Please try again.')
        recaptchaRef.current?.reset()
        return
      }

      setSuccess(true)

    } catch (err) {
      setError('Something went wrong. Please try again.')
      recaptchaRef.current?.reset()
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <main className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-white mb-2">
              SecureIT<span className="text-red-500">360</span>
            </h1>
          </div>
          <div className="bg-gray-900 rounded-2xl p-8 border border-gray-800 text-center">
            <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-white mb-3">Registration Successful!</h2>
            <p className="text-gray-400 mb-2">We have sent a verification email to:</p>
            <p className="text-red-400 font-semibold mb-4">{formData.email}</p>
            <p className="text-gray-400 text-sm mb-6">
              Please click the link in your email to verify your account before signing in.
              Check your spam folder if you do not see it within a few minutes.
            </p>
            <a href="/" className="block w-full bg-red-600 hover:bg-red-700 text-white font-semibold rounded-lg py-3 transition text-center">
              Go to Sign In
            </a>
          </div>
          <p className="text-center text-gray-600 text-xs mt-6">
            © 2026 Global Cyber Assurance All rights reserved.
          </p>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-gray-950 flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-md">
        <div className="text-center mb-10">
          <h1 className="text-4xl font-bold text-white mb-2">
            SecureIT<span className="text-red-500">360</span>
          </h1>
          <p className="text-gray-400">Start your free 7-day trial</p>
        </div>
        <div className="bg-gray-900 rounded-2xl p-8 border border-gray-800">
          <h2 className="text-xl font-semibold text-white mb-6">Create your account</h2>
          {error && (
            <div className="bg-red-900/30 border border-red-700 text-red-300 rounded-lg p-3 mb-4 text-sm">
              {error}
            </div>
          )}
          <div className="mb-4">
            <label className="block text-gray-400 text-sm mb-2">Your business name</label>
            <input type="text" value={formData.company_name}
              onChange={(e) => setFormData({...formData, company_name: e.target.value})}
              className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-3 focus:outline-none focus:border-red-500" />
          </div>
          <div className="mb-4">
            <label className="block text-gray-400 text-sm mb-2">Where is your business based?</label>
            <select value={formData.country}
              onChange={(e) => setFormData({...formData, country: e.target.value})}
              className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-3 focus:outline-none focus:border-red-500">
              <option value="">Select your country</option>
              {COUNTRIES.map((c) => (
                <option key={c.code} value={c.code}>{c.name}</option>
              ))}
            </select>
          </div>
          <div className="mb-4">
            <label className="block text-gray-400 text-sm mb-2">Company domain</label>
            <input type="text" value={formData.domain}
              onChange={(e) => setFormData({...formData, domain: e.target.value})}
              className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-3 focus:outline-none focus:border-red-500" />
            <p className="text-gray-500 text-xs mt-1">Without https:// e.g. yourcompany.com</p>
          </div>
          <div className="mb-4">
            <label className="block text-gray-400 text-sm mb-2">Business email</label>
            <input type="email" value={formData.email}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
              className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-3 focus:outline-none focus:border-red-500" />
            <p className="text-gray-500 text-xs mt-1">Must match your company domain</p>
          </div>
          <div className="mb-4">
            <label className="block text-gray-400 text-sm mb-2">Mobile number</label>
            <input type="tel" value={formData.mobile}
              onChange={(e) => setFormData({...formData, mobile: e.target.value})}
              className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-3 focus:outline-none focus:border-red-500" />
          </div>
          <div className="mb-6">
            <label className="block text-gray-400 text-sm mb-2">Choose a password</label>
            <input type="password" value={formData.password}
              onChange={(e) => setFormData({...formData, password: e.target.value})}
              className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-3 focus:outline-none focus:border-red-500" />
          </div>
          <div className="mb-6">
            <ReCAPTCHA
              ref={recaptchaRef}
              sitekey={process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY!}
              theme="dark"
              onExpired={() => recaptchaRef.current?.reset()}
            />
          </div>
          <button onClick={handleRegister} disabled={loading}
            className="w-full bg-red-600 hover:bg-red-700 text-white font-semibold rounded-lg py-3 transition disabled:opacity-50">
            {loading ? 'Creating your account...' : 'Start free trial'}
          </button>
          <p className="text-center text-gray-500 text-sm mt-6">
            Already have an account?{' '}
            <a href="/" className="text-red-400 hover:text-red-300">Sign in</a>
          </p>
        </div>
        <div className="text-center mt-6 text-gray-600 text-xs">
          <p>7-day free trial. No credit card required.</p>
          <p className="mt-1">© 2026 Global Cyber Assurance All rights reserved.</p>
        </div>
      </div>
    </main>
  )
}