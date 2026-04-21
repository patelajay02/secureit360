"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { authFetch, getToken } from "../../../lib/auth";

const ALL_ENGINES = [
  { key: "darkweb", label: "Dark Web Scan", description: "Checks if your business emails and passwords have been leaked in data breaches" },
  { key: "email", label: "Email Security Scan", description: "Checks if scammers can send emails pretending to be your business (DMARC, SPF, DKIM)" },
  { key: "network", label: "Network Scan", description: "Scans for open ports and exposed services" },
  { key: "website", label: "Website & SSL Scan", description: "Checks certificates and security headers" },
  { key: "devices", label: "Device Scan", description: "Looks for unpatched software and vulnerabilities" },
  { key: "cloud", label: "Cloud Storage Scan", description: "Checks for publicly exposed cloud files" },
  { key: "threat_intel", label: "Threat Intelligence Scan", description: "Checks your domain and IPs against abuse lists, typosquat registrations, and breach databases" },
];

const FREE_ENGINES = ALL_ENGINES.slice(0, 2);
const LOCKED_ENGINES = ALL_ENGINES.slice(2);

function StatusIcon({ status }) {
  if (status === "complete") return <span className="text-green-400 text-xl">&#10003;</span>;
  if (status === "running") return (
    <div className="w-5 h-5 border-2 border-red-400 border-t-transparent rounded-full animate-spin" />
  );
  return <div className="w-5 h-5 rounded-full border-2 border-gray-600" />;
}

export default function ScanningPage() {
  const router = useRouter();
  const [step, setStep] = useState("loading");
  const [domain, setDomain] = useState("");
  const [domainId, setDomainId] = useState(null);
  const [verifyToken, setVerifyToken] = useState(null);
  const [error, setError] = useState("");
  const [checking, setChecking] = useState(false);
  const [hasFullAccess, setHasFullAccess] = useState(false);
  const [activeEngines, setActiveEngines] = useState(FREE_ENGINES);
  const [statuses, setStatuses] = useState({
    darkweb: "pending", email: "pending",
    network: "pending", website: "pending", devices: "pending", cloud: "pending",
    threat_intel: "pending"
  });

  useEffect(() => {
    const token = getToken();
    if (!token) { router.push("/"); return; }
    const status = localStorage.getItem("status") || "trial";
    const fullAccess = status === "active" || status === "comped";
    setHasFullAccess(fullAccess);
    setActiveEngines(fullAccess ? ALL_ENGINES : FREE_ENGINES);
    checkExistingDomain();
  }, []);

  const checkExistingDomain = async () => {
    try {
      const res = await authFetch("/domains/");
      const data = await res.json();
      const verified = data.domains?.find(d => d.verified === true);
      if (verified) {
        setDomainId(verified.id);
        setDomain(verified.domain);
        setStep("scanning");
        runScans(verified.id);
      } else if (data.domains?.length > 0) {
        const unverified = data.domains[0];
        setDomainId(unverified.id);
        setDomain(unverified.domain);
        setVerifyToken(unverified.verify_token);
        setStep("verify");
      } else {
        setStep("add_domain");
      }
    } catch (e) {
      setStep("add_domain");
    }
  };

  const handleAddDomain = async () => {
    setError("");
    if (!domain.trim()) { setError("Please enter your domain name."); return; }
    try {
      const res = await authFetch("/domains/", { method: "POST", body: JSON.stringify({ domain: domain.trim().toLowerCase().replace(/^https?:\/\//, "") }) });
      const data = await res.json();
      if (!res.ok) { setError(data.detail || "Could not add domain."); return; }
      setDomainId(data.domain.id);
      setVerifyToken(data.verify_token);
      setStep("verify");
    } catch (e) {
      setError("Something went wrong. Please try again.");
    }
  };

  const handleCheckVerification = async () => {
    setError("");
    setChecking(true);
    try {
      const res = await authFetch("/domains/verify", { method: "POST", body: JSON.stringify({ domain_id: domainId }) });
      const data = await res.json();
      if (data.verified) {
        setStep("scanning");
        runScans(domainId);
      } else {
        setError(data.message || "TXT record not found yet. Please wait a few minutes and try again.");
      }
    } catch (e) {
      setError("Something went wrong. Please try again.");
    } finally {
      setChecking(false);
    }
  };

  const runScans = async (did) => {
    const id = did || domainId;
    const status = localStorage.getItem("status") || "trial";
    const fullAccess = status === "active" || status === "comped";
    const engines = fullAccess ? ALL_ENGINES : FREE_ENGINES;

    for (const engine of engines) {
      setStatuses(prev => ({ ...prev, [engine.key]: "running" }));
      try {
        if (engine.key === "threat_intel") {
          await authFetch(`/threat-intel/scan`, { method: "POST" });
        } else {
          await authFetch(`/scans/${engine.key}`, { method: "POST", body: JSON.stringify({ domain_id: id }) });
        }
      } catch (e) {
        console.error(`${engine.key} scan failed`, e);
      }
      setStatuses(prev => ({ ...prev, [engine.key]: "complete" }));
    }
    setTimeout(() => router.push("/dashboard"), 1500);
  };

  const enginesForDisplay = hasFullAccess ? ALL_ENGINES : FREE_ENGINES;
  const completed = enginesForDisplay.filter(e => statuses[e.key] === "complete").length;

  if (step === "loading") {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <p className="text-gray-400">Loading...</p>
      </div>
    );
  }

  if (step === "add_domain") {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
        <div className="w-full max-w-lg">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-white">SecureIT<span className="text-red-500">360</span></h1>
            <p className="text-gray-400 mt-2">Step 1 of 3 - Enter your business domain</p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8">
            <p className="text-white font-medium mb-2">What is your business domain name?</p>
            <p className="text-gray-500 text-sm mb-6">This is the web address of your business, for example: <span className="text-gray-300">qualitymark.co.nz</span></p>
            <input type="text" value={domain} onChange={e => setDomain(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleAddDomain()}
              placeholder="yourbusiness.co.nz"
              className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-3 mb-4 focus:outline-none focus:border-red-500" />
            {error && <p className="text-red-400 text-sm mb-4">{error}</p>}
            <button onClick={handleAddDomain} className="w-full bg-red-600 hover:bg-red-700 text-white font-semibold py-3 rounded-lg">Continue</button>
          </div>
        </div>
      </div>
    );
  }

  if (step === "verify") {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
        <div className="w-full max-w-lg">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-white">SecureIT<span className="text-red-500">360</span></h1>
            <p className="text-gray-400 mt-2">Step 2 of 3 - Verify you own this domain</p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8">
            <p className="text-white font-medium mb-4">Before we can scan <span className="text-red-400">{domain}</span>, we need to confirm you own it.</p>
            <div className="bg-gray-800 rounded-xl p-4 mb-6">
              <p className="text-gray-400 text-sm font-medium mb-3">Follow these steps:</p>
              <ol className="space-y-3 text-sm text-gray-300">
                <li className="flex gap-2"><span className="text-red-400 font-bold">1.</span> Log in to wherever you manage your domain name</li>
                <li className="flex gap-2"><span className="text-red-400 font-bold">2.</span> Find the DNS settings for your domain</li>
                <li className="flex gap-2"><span className="text-red-400 font-bold">3.</span> Add a new TXT record with these exact details:</li>
              </ol>
              <div className="bg-gray-900 rounded-lg p-4 mt-3 space-y-2">
                <div className="flex justify-between text-sm"><span className="text-gray-500">Type</span><span className="text-white font-mono">TXT</span></div>
                <div className="flex justify-between text-sm"><span className="text-gray-500">Name / Host</span><span className="text-white font-mono">@</span></div>
                <div className="flex flex-col text-sm gap-1"><span className="text-gray-500">Value</span><span className="text-green-400 font-mono text-xs break-all">{verifyToken}</span></div>
                <div className="flex justify-between text-sm"><span className="text-gray-500">TTL</span><span className="text-white font-mono">3600 (or Default)</span></div>
              </div>
              <p className="text-gray-500 text-xs mt-3">Not sure how to do this? Email <a href="mailto:governance@secureit360.co" className="text-gray-400 underline">governance@secureit360.co</a></p>
            </div>
            {error && <p className="text-amber-400 text-sm mb-4">{error}</p>}
            <button onClick={handleCheckVerification} disabled={checking}
              className="w-full bg-red-600 hover:bg-red-700 disabled:bg-gray-700 text-white font-semibold py-3 rounded-lg">
              {checking ? "Checking..." : "I have added the TXT record - verify now"}
            </button>
            <p className="text-gray-600 text-xs mt-3 text-center">DNS changes can take up to 30 minutes to take effect</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
      <div className="w-full max-w-lg">
        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold text-white">SecureIT<span className="text-red-500">360</span></h1>
          <p className="text-gray-400 mt-2">Scanning {domain}</p>
          <p className="text-gray-500 text-sm mt-1">This takes about 60 seconds - please do not close this page</p>
        </div>
        <div className="mb-8">
          <div className="flex justify-between text-sm text-gray-400 mb-2">
            <span>Scanning in progress</span>
            <span>{completed} of {enginesForDisplay.length} complete</span>
          </div>
          <div className="w-full bg-gray-800 rounded-full h-2">
            <div className="bg-red-500 h-2 rounded-full transition-all duration-700"
              style={{ width: `${(completed / enginesForDisplay.length) * 100}%` }} />
          </div>
        </div>
        <div className="bg-gray-900 rounded-2xl border border-gray-800 divide-y divide-gray-800 mb-4">
          {enginesForDisplay.map(engine => (
            <div key={engine.key} className="flex items-center gap-4 px-6 py-4">
              <StatusIcon status={statuses[engine.key]} />
              <div className="flex-1">
                <div className="text-white font-medium">{engine.label}</div>
                <div className="text-gray-500 text-sm">{engine.description}</div>
              </div>
              <span className="text-xs text-gray-600 capitalize">{statuses[engine.key]}</span>
            </div>
          ))}
        </div>
        {!hasFullAccess && (
          <div className="bg-gray-900 rounded-2xl border border-gray-800 divide-y divide-gray-800">
            {LOCKED_ENGINES.map(engine => (
              <div key={engine.key} className="flex items-center gap-4 px-6 py-4 opacity-50">
                <div className="w-5 h-5 rounded-full border-2 border-gray-700 flex items-center justify-center">
                  <span className="text-gray-600 text-xs">&#128274;</span>
                </div>
                <div className="flex-1">
                  <div className="text-gray-500 font-medium">{engine.label}</div>
                  <div className="text-gray-600 text-sm">{engine.description}</div>
                </div>
                <a href="/pricing" className="text-xs text-red-400 hover:text-red-300">Upgrade to unlock</a>
              </div>
            ))}
          </div>
        )}
        <p className="text-center text-gray-600 text-xs mt-6">by Global Cyber Assurance - Complete cyber protection</p>
      </div>
    </div>
  );
}
