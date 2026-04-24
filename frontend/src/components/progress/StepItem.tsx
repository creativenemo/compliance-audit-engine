"use client";

import type { StepProgress } from "@/lib/types";

interface Props {
  step: StepProgress;
}

export function StepItem({ step }: Props) {
  return (
    <div className="flex items-center gap-3 py-2">
      <div className="flex-shrink-0 w-6 h-6 flex items-center justify-center">
        {step.status === "complete" || step.status === "skipped" ? (
          <CheckIcon />
        ) : step.status === "running" ? (
          <Spinner />
        ) : step.status === "failed" ? (
          <WarningIcon />
        ) : (
          <PendingDot />
        )}
      </div>
      <span
        className={`text-sm ${
          step.status === "complete" || step.status === "skipped"
            ? "text-gray-400"
            : step.status === "running"
            ? "text-gray-900 font-semibold"
            : step.status === "failed"
            ? "text-amber-700"
            : "text-gray-400"
        }`}
      >
        {step.name}
      </span>
    </div>
  );
}

function CheckIcon() {
  return (
    <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
    </svg>
  );
}

function Spinner() {
  return (
    <svg className="w-5 h-5 text-blue-500 animate-spin" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  );
}

function WarningIcon() {
  return (
    <svg className="w-5 h-5 text-amber-500" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
    </svg>
  );
}

function PendingDot() {
  return <div className="w-3 h-3 rounded-full bg-gray-300 mx-auto" />;
}
