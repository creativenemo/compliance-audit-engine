"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, CheckCircle, XCircle, AlertTriangle, MinusCircle } from "lucide-react";
import { clsx } from "clsx";
import type { ReportSection, SectionStatus } from "@/lib/types";

interface Props {
  section: ReportSection;
}

const STATUS_CONFIG: Record<
  SectionStatus,
  { label: string; icon: React.ReactNode; headerClass: string; badgeClass: string }
> = {
  PASS: {
    label: "Pass",
    icon: <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />,
    headerClass: "border-l-4 border-green-500",
    badgeClass: "bg-green-100 text-green-800 ring-green-200",
  },
  FAIL: {
    label: "Fail",
    icon: <XCircle className="w-5 h-5 text-red-600 flex-shrink-0" />,
    headerClass: "border-l-4 border-red-500",
    badgeClass: "bg-red-100 text-red-800 ring-red-200",
  },
  WARNING: {
    label: "Warning",
    icon: <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0" />,
    headerClass: "border-l-4 border-amber-400",
    badgeClass: "bg-amber-100 text-amber-800 ring-amber-200",
  },
  NOT_CHECKED: {
    label: "Not Checked",
    icon: <MinusCircle className="w-5 h-5 text-gray-400 flex-shrink-0" />,
    headerClass: "border-l-4 border-gray-300",
    badgeClass: "bg-gray-100 text-gray-600 ring-gray-200",
  },
};

function defaultOpen(status: SectionStatus): boolean {
  return status === "FAIL" || status === "WARNING";
}

export function SectionCard({ section }: Props) {
  const config = STATUS_CONFIG[section.status] ?? STATUS_CONFIG.NOT_CHECKED;
  const [open, setOpen] = useState(() => defaultOpen(section.status));

  return (
    <div
      className={clsx(
        "bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden",
        config.headerClass
      )}
    >
      {/* Header — always visible */}
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between gap-3 px-5 py-4 text-left hover:bg-gray-50 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-blue-500"
        aria-expanded={open}
      >
        <span className="flex items-center gap-3 min-w-0">
          {config.icon}
          <span className="font-semibold text-gray-900 text-sm sm:text-base truncate">
            {section.title}
          </span>
        </span>
        <span className="flex items-center gap-2 flex-shrink-0">
          <span
            className={clsx(
              "hidden sm:inline-flex items-center text-xs font-semibold px-2.5 py-0.5 rounded-full ring-1",
              config.badgeClass
            )}
          >
            {config.label}
          </span>
          {open ? (
            <ChevronUp className="w-4 h-4 text-gray-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-gray-400" />
          )}
        </span>
      </button>

      {/* Expandable body */}
      {open && (
        <div className="px-5 pb-5 pt-1 border-t border-gray-100 space-y-4">
          {/* Findings */}
          {section.findings.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
                Findings
              </h4>
              <ul className="space-y-2">
                {section.findings.map((f, i) => (
                  <li key={i} className="flex gap-2 text-sm text-gray-700">
                    <span className="mt-1 w-1.5 h-1.5 rounded-full bg-gray-400 flex-shrink-0" />
                    <span>
                      {f.finding}
                      {f.source_name && (
                        <span className="ml-1 text-xs text-gray-400">
                          — {f.source_name}
                        </span>
                      )}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Recommendations */}
          {section.recommendations.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
                Recommendations
              </h4>
              <ul className="space-y-1.5">
                {section.recommendations.map((rec, i) => (
                  <li key={i} className="flex gap-2 text-sm text-gray-700">
                    <span className="mt-1 w-1.5 h-1.5 rounded-full bg-blue-400 flex-shrink-0" />
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Sources */}
          {section.sources.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1">
                Sources
              </h4>
              <p className="text-xs text-gray-400 leading-relaxed">
                {section.sources.join(" · ")}
              </p>
            </div>
          )}

          {/* Empty state */}
          {section.findings.length === 0 &&
            section.recommendations.length === 0 && (
              <p className="text-sm text-gray-400 italic">No details available.</p>
            )}
        </div>
      )}
    </div>
  );
}
