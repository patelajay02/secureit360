"use client";

type Severity = "critical" | "high" | "medium" | "low" | "info" | string;

const STYLES: Record<string, { bg: string; text: string; label: string }> = {
  critical: { bg: "bg-red-900/50", text: "text-red-300", label: "Critical" },
  high: { bg: "bg-orange-900/50", text: "text-orange-300", label: "High" },
  medium: { bg: "bg-amber-900/50", text: "text-amber-300", label: "Medium" },
  low: { bg: "bg-blue-900/40", text: "text-blue-300", label: "Low" },
  info: { bg: "bg-gray-700", text: "text-gray-300", label: "Info" },
};

export default function SeverityBadge({ severity }: { severity: Severity }) {
  const style = STYLES[severity] ?? STYLES.info;
  return (
    <span
      className={`inline-flex items-center text-xs px-2 py-0.5 rounded font-medium ${style.bg} ${style.text}`}
    >
      {style.label}
    </span>
  );
}
