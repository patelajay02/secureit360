"use client";

import { useMemo, useState } from "react";

/**
 * A wizard recipe is a JSON doc shaped like:
 *
 * {
 *   "app_slug": "example",
 *   "app_name": "Example",
 *   "steps": [
 *     {
 *       "title": "Open your Example admin page",
 *       "instruction": "Sign in to Example and click the gear icon.",
 *       "screenshot_url": "https://...",           // optional
 *       "input": {                                  // optional
 *         "name": "api_key",
 *         "label": "Paste your API key here",
 *         "type": "text" | "password" | "select",
 *         "options": [...],                         // for select
 *         "required": true
 *       }
 *     },
 *     ...
 *   ]
 * }
 */

export type WizardInput = {
  name: string;
  label: string;
  type?: "text" | "password" | "select" | "url";
  placeholder?: string;
  required?: boolean;
  options?: { value: string; label: string }[];
  help?: string;
};

export type WizardStep = {
  title: string;
  instruction: string;
  screenshot_url?: string | null;
  input?: WizardInput | null;
};

export type WizardRecipe = {
  app_slug: string;
  app_name: string;
  steps: WizardStep[];
};

type Props = {
  recipe: WizardRecipe;
  onCancel?: () => void;
  onSubmit: (values: Record<string, string>) => Promise<void> | void;
  submitting?: boolean;
};

export default function GuidedWizard({
  recipe,
  onCancel,
  onSubmit,
  submitting,
}: Props) {
  const [index, setIndex] = useState(0);
  const [values, setValues] = useState<Record<string, string>>({});
  const [error, setError] = useState<string>("");

  const steps = recipe.steps || [];
  const total = steps.length;
  const step = steps[index];
  const isLast = index === total - 1;
  const progress = useMemo(
    () => (total === 0 ? 0 : Math.round(((index + 1) / total) * 100)),
    [index, total]
  );

  if (!step) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8 text-center">
        <p className="text-white font-semibold">This wizard has no steps yet.</p>
      </div>
    );
  }

  const validateAndAdvance = async () => {
    setError("");
    const input = step.input;
    if (input?.required && !values[input.name]) {
      setError(`Please fill in: ${input.label}`);
      return;
    }
    if (!isLast) {
      setIndex(index + 1);
      return;
    }
    try {
      await onSubmit(values);
    } catch (e: any) {
      setError(e?.message || "Something went wrong. Please try again.");
    }
  };

  const renderInput = (input: WizardInput) => {
    const shared =
      "w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-3 focus:outline-none focus:border-indigo-500";
    const value = values[input.name] || "";
    const update = (v: string) =>
      setValues({ ...values, [input.name]: v });

    if (input.type === "select") {
      return (
        <select
          className={shared}
          value={value}
          onChange={(e) => update(e.target.value)}
        >
          <option value="">Select an option</option>
          {(input.options || []).map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      );
    }

    return (
      <input
        type={input.type === "password" ? "password" : "text"}
        value={value}
        onChange={(e) => update(e.target.value)}
        placeholder={input.placeholder}
        className={shared}
      />
    );
  };

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 sm:p-8">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-white font-semibold">
          Connecting {recipe.app_name}
        </h2>
        <span className="text-gray-500 text-xs">
          Step {index + 1} of {total}
        </span>
      </div>
      <div className="w-full bg-gray-800 rounded-full h-1.5 mb-8 overflow-hidden">
        <div
          className="bg-indigo-500 h-full rounded-full transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="space-y-5">
        <div>
          <p className="text-white text-lg font-semibold mb-1">{step.title}</p>
          <p className="text-gray-300 text-sm leading-relaxed">
            {step.instruction}
          </p>
        </div>

        {step.screenshot_url && (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={step.screenshot_url}
            alt=""
            className="w-full rounded-xl border border-gray-800"
          />
        )}

        {step.input && (
          <div>
            <label className="block text-white text-sm font-medium mb-2">
              {step.input.label}
              {step.input.required && (
                <span className="text-red-400 ml-1">*</span>
              )}
            </label>
            {renderInput(step.input)}
            {step.input.help && (
              <p className="text-gray-500 text-xs mt-2">{step.input.help}</p>
            )}
          </div>
        )}
      </div>

      {error && (
        <p className="mt-4 text-red-400 text-sm" role="alert">
          {error}
        </p>
      )}

      <div className="mt-8 flex items-center justify-between gap-3">
        <button
          onClick={() => (index === 0 ? onCancel?.() : setIndex(index - 1))}
          disabled={submitting}
          className="text-sm px-4 py-2.5 rounded-lg bg-gray-800 hover:bg-gray-700 disabled:bg-gray-900 border border-gray-700 text-gray-200 font-medium"
        >
          {index === 0 ? "Cancel" : "Back"}
        </button>
        <button
          onClick={validateAndAdvance}
          disabled={submitting}
          className="text-sm px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-700 text-white font-semibold"
        >
          {submitting ? "Connecting…" : isLast ? "Connect" : "Next"}
        </button>
      </div>
    </div>
  );
}
