"use client";

import type { AuditStatusResponse } from "@/lib/types";
import { StepItem } from "./StepItem";

interface Props {
  status: AuditStatusResponse;
}

export function ProgressLoader({ status }: Props) {
  const eta = status.eta_seconds;

  return (
    <div className="max-w-md mx-auto">
      <div className="mb-6">
        <div className="flex justify-between text-sm text-gray-600 mb-2">
          <span>Running compliance checks…</span>
          {eta != null && eta > 0 && (
            <span>~{eta}s remaining</span>
          )}
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-500"
            style={{ width: `${status.progress_pct}%` }}
          />
        </div>
      </div>

      <div className="divide-y divide-gray-100">
        {status.steps.map((step) => (
          <StepItem key={step.id} step={step} />
        ))}
      </div>

      {status.status === "failed" && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
          Audit failed. Some checks could not complete. Partial report may be available.
        </div>
      )}
    </div>
  );
}
