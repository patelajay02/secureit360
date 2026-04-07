"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { authFetch, getToken } from "../../lib/auth";

const PRICING = {
  NZ:  { currency: "NZD", symbol: "$", starter: 250,    pro: 500,    enterprise: 840    },
  AU:  { currency: "AUD", symbol: "$", starter: 299,    pro: 599,    enterprise: 999    },
  IN:  { currency: "INR", symbol: "₹", starter: 12500,  pro: 25000,  enterprise: 42000  },
  UAE: { currency: "AED", symbol: "AED", starter: 549,  pro: 1099,   enterprise: 1849   },
  OTHER: { currency: "USD", symbol: "$", starter: 149,  pro: 299,    enterprise: 499    },
};

const FEATURES = {
  starter: [
    "1 domain scanned daily",
    "6 security scan engines",
    "Ransom Risk Score",
    "Governance Score",
    "Regulatory compliance mapping",
    "Director personal liability score",
    "Weekly director email report",
    "Plain English findings - no jargon",
    "Auto-fix simple issues",
    "3 users",
  ],
  pro: [
    "3 domains scanned daily",
    "6 security scan engines",
    "Ransom Risk Score",
    "Governance Score",
    "Regulatory compliance mapping",
    "Director personal liability score",
    "Weekly director email report",
    "Plain English findings - no jargon",
    "Auto-fix simple issues",
    "Voice-guided fix walkthroughs",
    "Compliance gap report",
    "Director evidence report",
    "10 users",
  ],
  enterprise: [
    "10 domains scanned daily",
    "6 security scan engines",
    "Ransom Risk Score",
    "Governance Score",
    "Regulatory compliance mapping",
    "Director personal liability score",
    "Weekly director email report",
    "Plain English findings - no jargon",
    "Auto-fix simple issues",
    "Voice-guided fix walkthroughs",
    "Full compliance gap report",
    "Director evidence report",
    "ISO 27001 readiness report",
    "Essential Eight maturity report",
    "Priority specialist access",
    "Unlimited users",
  ],
};

export default function PricingPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(null);
  const [error, setError] = useState("");
  const [pricing, setPricing] = useState(PRICING.NZ);
  const [country, setCountry] = useState("NZ");

  useEffect(() => {
    const token = getToken();
    if (!token) { router.push("/"); return; }
    const c = localStorage.getItem("country") || "NZ";
    setCountry(c);
    setPricing(PRICING[c] || PRICING.OTHER);
  }, []);

  const handleSubscribe = async (planKey) => {
    setLoading(planKey);
    setError("");
    try {
      const res = await authFetch(`/billing/checkout/${planKey}`, {
        method: "POST",
        body: JSON.stringify({
          plan: planKey,
          success_url: "https://app.secureit360.co/dashboard?subscribed=true",
          cancel_url: "https://app.secureit360.co/pricing",
        }),
      });
      const data = await res.json();
      if (!res.ok) { setError(data.detail || "Could not start checkout. Please try again."); return; }
      window.location.href = data.url;
    } catch (e) {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(null);
    }
  };

  const plans = [
    { key: "starter", name: "Starter", price: pricing.starter, description: "Perfect for small businesses getting started with cyber security", features: FEATURES.starter },
    { key: "pro", name: "Pro", price: pricing.pro, description: "For growing businesses that need deeper protection and reporting", features: FEATURES.pro, popular: true },
    { key: "enterprise", name: "Enterprise", price: pricing.enterprise, description: "Complete cyber security for larger businesses with multiple domains", features: FEATURES.enterprise },
  ];

  return (
    <main className="min-h-screen bg-gray-950 text-white">
      <nav className="bg-gray-900 border-b border-gray-800 px-6 py-4 flex justify-between items-center">
        <h1 className="text-xl font-bold">SecureIT<span className="text-red-500">360</span></h1>
        <a href="/dashboard" className="text-gray-400 hover:text-white text-sm">Back to Dashboard</a>
      </nav>

      <div className="max-w-6xl mx-auto px-6 py-12">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-white mb-4">Choose your plan</h2>
          <p className="text-gray-400 text-lg">All plans include a 7-day free trial. Cancel anytime.</p>
          <p className="text-gray-500 text-sm mt-2">Prices shown in {pricing.currency} + GST</p>
        </div>

        {error && (
          <div className="bg-red-900/30 border border-red-700 text-red-300 rounded-lg p-4 mb-8 text-center">{error}</div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {plans.map((plan) => (
            <div key={plan.key} className={`bg-gray-900 rounded-2xl p-8 border ${plan.popular ? "border-red-500 relative" : "border-gray-800"}`}>
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                  <span className="bg-red-600 text-white text-xs font-bold px-4 py-1 rounded-full">MOST POPULAR</span>
                </div>
              )}
              <div className="mb-6">
                <h3 className="text-xl font-bold text-white mb-2">{plan.name}</h3>
                <p className="text-gray-400 text-sm">{plan.description}</p>
              </div>
              <div className="mb-6">
                <span className="text-4xl font-bold text-white">{pricing.symbol}{plan.price.toLocaleString()}</span>
                <span className="text-gray-400 text-sm"> {pricing.currency}/month + GST</span>
              </div>
              <ul className="space-y-3 mb-8">
                {plan.features.map((feature, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <span className="text-green-400 mt-0.5 flex-shrink-0">&#10003;</span>
                    <span className="text-gray-300">{feature}</span>
                  </li>
                ))}
              </ul>
              <button
                onClick={() => handleSubscribe(plan.key)}
                disabled={loading === plan.key}
                className={`w-full py-3 rounded-lg font-semibold text-sm transition ${plan.popular ? "bg-red-600 hover:bg-red-700 text-white" : "bg-gray-800 hover:bg-gray-700 text-white"} disabled:opacity-50`}
              >
                {loading === plan.key ? "Redirecting..." : "Start 7-day free trial"}
              </button>
            </div>
          ))}
        </div>

        <div className="mt-12 text-center">
          <p className="text-gray-500 text-sm">
            Not sure which plan is right for you?{" "}
            <a href="mailto:governance@secureit360.co" className="text-gray-400 hover:text-white underline">
              Email us at governance@secureit360.co
            </a>{" "}
            and we will help you choose.
          </p>
        </div>
      </div>
    </main>
  );
}
