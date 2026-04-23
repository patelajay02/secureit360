"use client";

// Per-SaaS-finding action block. Renders the shared FindingActionsBar
// (Auto Fix / Voice Guide / Connect to Expert) plus a lightweight voice
// modal that reads governance_statement + recommended_action via the
// Web Speech API. SaaS findings do not have hand-crafted VOICE_GUIDE_STEPS
// transcripts the way the main dashboard findings do.

import { useEffect, useState } from "react";

import FindingActionsBar from "../findings/FindingActionsBar";
import { authFetch } from "../../lib/auth";

type Finding = {
  id: string;
  check_id: string;
  severity: string;
  governance_statement: string;
  recommended_action: string;
  technical_detail?: string | null;
  app_name?: string;
  auto_fixable?: boolean;
};

type Props = {
  finding: Finding;
  onChanged?: () => void | Promise<void>;
  onToast?: (message: string, type?: "success" | "error" | "info") => void;
};

export default function FindingActions({ finding, onChanged, onToast }: Props) {
  const [voiceOpen, setVoiceOpen] = useState(false);
  const [fixing, setFixing] = useState(false);

  const handleAutoFix = async () => {
    setFixing(true);
    try {
      const resp = await authFetch(`/saas/findings/${finding.id}/auto-fix`, {
        method: "POST",
      });
      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        throw new Error(data.detail || "Could not fix this finding");
      }
      const data = await resp.json();
      onToast?.(data.message || "Fixed.", "success");
      await onChanged?.();
    } catch (e: any) {
      onToast?.(e?.message || "Could not fix this finding", "error");
    } finally {
      setFixing(false);
    }
  };

  return (
    <>
      <FindingActionsBar
        autoFixable={!!finding.auto_fixable}
        autoFixBusy={fixing}
        onAutoFix={handleAutoFix}
        onVoiceGuide={() => setVoiceOpen(true)}
        expertSubject={`Expert help: ${finding.app_name || "SaaS"} — ${finding.check_id}`}
        expertBody={finding.governance_statement}
      />
      {voiceOpen && (
        <VoiceGuideModal finding={finding} onClose={() => setVoiceOpen(false)} />
      )}
    </>
  );
}


function VoiceGuideModal({
  finding,
  onClose,
}: {
  finding: Finding;
  onClose: () => void;
}) {
  const [speaking, setSpeaking] = useState(false);

  useEffect(() => {
    return () => {
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const speak = (text: string) => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(text);
    utter.rate = 0.95;
    utter.onend = () => setSpeaking(false);
    utter.onerror = () => setSpeaking(false);
    setSpeaking(true);
    window.speechSynthesis.speak(utter);
  };

  const stop = () => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    setSpeaking(false);
  };

  const script =
    `${finding.governance_statement} ` +
    `Here is the recommended next step. ${finding.recommended_action}`;

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 px-4">
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 max-w-lg w-full">
        <div className="flex items-start justify-between gap-3 mb-3">
          <h3 className="text-white font-semibold text-lg">Voice guide</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white"
            aria-label="Close"
          >
            ✕
          </button>
        </div>
        <p className="text-gray-300 text-sm leading-relaxed mb-3">
          {finding.governance_statement}
        </p>
        <div className="rounded-lg border border-indigo-900/60 bg-indigo-900/20 px-4 py-3 mb-4">
          <p className="text-indigo-200 text-xs uppercase tracking-wide font-semibold mb-1">
            Recommended next step
          </p>
          <p className="text-indigo-100 text-sm">{finding.recommended_action}</p>
        </div>
        <div className="flex items-center gap-2">
          {speaking ? (
            <button
              onClick={stop}
              className="text-xs px-3 py-2 rounded-lg bg-amber-900/60 hover:bg-amber-900 text-amber-100 font-medium"
            >
              Stop
            </button>
          ) : (
            <button
              onClick={() => speak(script)}
              className="text-xs px-3 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-medium"
            >
              Read it aloud
            </button>
          )}
          <button
            onClick={onClose}
            className="text-xs px-3 py-2 rounded-lg bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-200 font-medium"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
