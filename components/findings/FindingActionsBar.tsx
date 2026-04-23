"use client";

// Shared three-button action row rendered under every finding, both on
// the main dashboard (/dashboard) and on the SaaS connections page
// (/saas/connections). Keeps the visual grammar unified: disabled grey
// Auto Fix when not auto-fixable, amber Voice Guide, red Connect to
// Expert.

import type { MouseEvent } from "react";

type Props = {
  autoFixable?: boolean;
  autoFixBusy?: boolean;
  onAutoFix?: () => void | Promise<void>;
  onVoiceGuide?: () => void;
  expertSubject: string;
  expertBody: string;
};

export default function FindingActionsBar({
  autoFixable,
  autoFixBusy,
  onAutoFix,
  onVoiceGuide,
  expertSubject,
  expertBody,
}: Props) {
  const autoFixDisabled = !autoFixable || !onAutoFix || autoFixBusy;

  const stopBubbling = (e: MouseEvent) => e.stopPropagation();

  const mailto =
    `mailto:governance@secureit360.co` +
    `?subject=${encodeURIComponent(expertSubject)}` +
    `&body=${encodeURIComponent(expertBody)}`;

  return (
    <div className="mt-3 flex items-center gap-2 flex-wrap" onClick={stopBubbling}>
      <button
        type="button"
        disabled={autoFixDisabled}
        onClick={(e) => {
          stopBubbling(e);
          if (!autoFixDisabled) onAutoFix?.();
        }}
        title={
          autoFixable
            ? "Fix this automatically"
            : "Automated fixing isn't available for this finding"
        }
        className={
          autoFixDisabled
            ? "text-xs px-2 py-1 rounded font-medium bg-gray-800 text-gray-500 cursor-not-allowed border border-gray-700"
            : "text-xs px-2 py-1 rounded font-medium bg-green-700 text-white hover:bg-green-600"
        }
      >
        {autoFixBusy ? "Fixing…" : "Auto Fix"}
      </button>
      <button
        type="button"
        onClick={(e) => {
          stopBubbling(e);
          onVoiceGuide?.();
        }}
        className="text-xs px-2 py-1 rounded font-medium bg-amber-900/50 text-amber-300 hover:bg-amber-900"
      >
        Voice Guide
      </button>
      <a
        href={mailto}
        onClick={stopBubbling}
        className="text-xs px-2 py-1 rounded font-medium bg-red-900/50 text-red-300 hover:bg-red-900"
      >
        Connect to Expert
      </a>
    </div>
  );
}
