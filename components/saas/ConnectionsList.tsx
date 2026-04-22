"use client";

import { useState } from "react";

export type Connection = {
  id: string;
  app_slug: string;
  app_name: string;
  connection_type: "oauth" | "api_key" | string;
  status: "active" | "expired" | "failed" | string;
  last_scan_at: string | null;
  created_at: string;
  logo_url?: string | null;
};

type Props = {
  connections: Connection[];
  onScan: (id: string) => Promise<void> | void;
  onDisconnect: (id: string) => Promise<void> | void;
};

const STATUS_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  active: { bg: "bg-green-900/40", text: "text-green-300", label: "Connected" },
  expired: { bg: "bg-amber-900/40", text: "text-amber-300", label: "Needs reconnecting" },
  failed: { bg: "bg-red-900/40", text: "text-red-300", label: "Not working" },
};

function StatusBadge({ status }: { status: string }) {
  const style = STATUS_STYLES[status] ?? STATUS_STYLES.active;
  return (
    <span
      className={`inline-flex items-center text-xs px-2 py-0.5 rounded-full ${style.bg} ${style.text}`}
    >
      {style.label}
    </span>
  );
}

function Initials({ name }: { name: string }) {
  const initials =
    name
      .split(/\s+/)
      .slice(0, 2)
      .map((w) => w[0])
      .join("")
      .toUpperCase() || "?";
  return (
    <div className="w-10 h-10 rounded-lg bg-gray-800 border border-gray-700 flex items-center justify-center text-gray-300 text-sm font-semibold flex-shrink-0">
      {initials}
    </div>
  );
}

function formatLastScan(value: string | null): string {
  if (!value) return "Never scanned";
  try {
    const d = new Date(value);
    return `Last scanned ${d.toLocaleString()}`;
  } catch {
    return "Never scanned";
  }
}

export default function ConnectionsList({
  connections,
  onScan,
  onDisconnect,
}: Props) {
  const [busyScan, setBusyScan] = useState<string | null>(null);
  const [busyDisconnect, setBusyDisconnect] = useState<string | null>(null);

  if (!connections || connections.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8 text-center">
        <p className="text-white font-semibold mb-2">No tools connected yet</p>
        <p className="text-gray-400 text-sm">
          Click <span className="text-white font-medium">Connect a tool</span>{" "}
          above and we&apos;ll walk you through hooking up the business apps
          you already use.
        </p>
      </div>
    );
  }

  const handleScan = async (id: string) => {
    setBusyScan(id);
    try {
      await onScan(id);
    } finally {
      setBusyScan(null);
    }
  };

  const handleDisconnect = async (id: string) => {
    if (!confirm("Disconnect this tool? Past findings will be deleted too.")) return;
    setBusyDisconnect(id);
    try {
      await onDisconnect(id);
    } finally {
      setBusyDisconnect(null);
    }
  };

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl divide-y divide-gray-800">
      {connections.map((c) => (
        <div
          key={c.id}
          className="px-5 py-4 flex flex-col md:flex-row md:items-center gap-4"
        >
          <div className="flex items-center gap-3 flex-1 min-w-0">
            {c.logo_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={c.logo_url}
                alt=""
                className="w-10 h-10 rounded-lg bg-gray-800 border border-gray-700 object-contain flex-shrink-0"
              />
            ) : (
              <Initials name={c.app_name} />
            )}
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <p className="text-white font-medium truncate">{c.app_name}</p>
                <StatusBadge status={c.status} />
              </div>
              <p className="text-gray-500 text-xs mt-0.5">
                {formatLastScan(c.last_scan_at)}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <button
              onClick={() => handleScan(c.id)}
              disabled={busyScan === c.id}
              className="text-xs px-3 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-700 text-white font-medium"
            >
              {busyScan === c.id ? "Scanning…" : "Scan now"}
            </button>
            <button
              onClick={() => handleDisconnect(c.id)}
              disabled={busyDisconnect === c.id}
              className="text-xs px-3 py-2 rounded-lg bg-gray-800 hover:bg-gray-700 disabled:bg-gray-900 border border-gray-700 text-gray-200 font-medium"
            >
              {busyDisconnect === c.id ? "Removing…" : "Disconnect"}
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
