"use client";

// Real-time HIBP breach watch tile.
// Renders inside the main dashboard grid using the same card styling as
// the surrounding Ransom / Governance / Director Liability tiles
// (bg-gray-900 / border-gray-800 / rounded-2xl). Click anywhere on the
// header to expand the last 5 alerts.

import { useState } from "react";

type Watch = {
  domain: string;
  last_checked_at: string | null;
};

type Alert = {
  breach_name: string;
  breach_date: string | null;
  pwn_count: number | null;
  affected_emails: number;
  alert_sent_at: string;
};

type BreachWatchPayload = {
  watches?: Watch[];
  alerts_30d?: number;
  recent_alerts?: Alert[];
};

function relativeTime(iso: string | null | undefined): string {
  if (!iso) return "never";
  const t = Date.parse(iso);
  if (Number.isNaN(t)) return "never";
  const secs = Math.max(0, Math.round((Date.now() - t) / 1000));
  if (secs < 60) return "just now";
  if (secs < 3600) {
    const m = Math.max(1, Math.round(secs / 60));
    return `${m} minute${m === 1 ? "" : "s"} ago`;
  }
  if (secs < 86_400) {
    const h = Math.round(secs / 3600);
    return `${h} hour${h === 1 ? "" : "s"} ago`;
  }
  const d = Math.round(secs / 86_400);
  return `${d} day${d === 1 ? "" : "s"} ago`;
}

function formatBreachDate(iso: string | null): string {
  if (!iso) return "Unknown date";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString();
}

function formatPwnCount(n: number | null): string {
  if (typeof n !== "number" || !Number.isFinite(n)) return "—";
  return n.toLocaleString();
}


export default function BreachWatchTile({
  data,
}: {
  data?: BreachWatchPayload | null;
}) {
  const [expanded, setExpanded] = useState(false);
  const watches = data?.watches ?? [];
  const recentAlerts = data?.recent_alerts ?? [];
  const alerts30d = data?.alerts_30d ?? 0;

  const monitoringSummary = (() => {
    if (watches.length === 0) return null;
    if (watches.length === 1) return watches[0].domain;
    return `${watches.length} domains`;
  })();

  // Most recent last_checked_at across all watches — the user wants one
  // freshness signal, not one per row.
  const lastCheckedAt: string | null = watches
    .map((w) => w.last_checked_at)
    .filter((v): v is string => !!v)
    .sort()
    .pop() ?? null;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
      <button
        type="button"
        onClick={() => setExpanded((e) => !e)}
        className="w-full flex items-start justify-between gap-3 text-left"
        aria-expanded={expanded}
      >
        <div>
          <h3 className="text-white font-semibold text-sm">Real-time breach watch</h3>
          <p className="text-gray-500 text-xs mt-1">
            Powered by Have I Been Pwned. Checks every 5 minutes.
          </p>
        </div>
        <span className="text-gray-500 text-xs">{expanded ? "Hide" : "View alerts"}</span>
      </button>

      <div className="mt-4 space-y-3">
        {monitoringSummary ? (
          <div className="flex items-center gap-2">
            <span
              className="inline-block w-2.5 h-2.5 rounded-full bg-green-400"
              aria-hidden
            />
            <span className="text-white text-sm">
              Active — monitoring{" "}
              <span className="text-green-300 font-medium">{monitoringSummary}</span>
            </span>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <span
              className="inline-block w-2.5 h-2.5 rounded-full bg-gray-600"
              aria-hidden
            />
            <span className="text-gray-400 text-sm">
              Verify a domain to enable real-time breach detection.
            </span>
          </div>
        )}

        {monitoringSummary && (
          <p className="text-gray-500 text-xs">
            Last checked: {relativeTime(lastCheckedAt)}
          </p>
        )}

        <p className="text-gray-400 text-sm">
          <span
            className={
              alerts30d > 0 ? "text-red-400 font-semibold" : "text-gray-300 font-medium"
            }
          >
            {alerts30d}
          </span>{" "}
          alert{alerts30d === 1 ? "" : "s"} in the last 30 days
        </p>
      </div>

      {expanded && (
        <div className="mt-5 pt-4 border-t border-gray-800">
          {recentAlerts.length === 0 ? (
            <p className="text-gray-500 text-xs">
              No alerts yet. We&apos;ll notify the director within minutes if a
              new breach affects a watched domain.
            </p>
          ) : (
            <ul className="space-y-3">
              {recentAlerts.map((a, i) => (
                <li
                  key={`${a.breach_name}-${i}`}
                  className="flex items-start justify-between gap-3"
                >
                  <div className="min-w-0">
                    <p className="text-white text-sm font-medium truncate">
                      {a.breach_name}
                    </p>
                    <p className="text-gray-500 text-xs mt-0.5">
                      Breached {formatBreachDate(a.breach_date)} —{" "}
                      {a.affected_emails} of your address
                      {a.affected_emails === 1 ? "" : "es"} affected
                    </p>
                  </div>
                  <span className="flex-shrink-0 text-xs text-gray-500 whitespace-nowrap">
                    {relativeTime(a.alert_sent_at)}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
