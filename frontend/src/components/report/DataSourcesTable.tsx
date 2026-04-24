"use client";

import { useState } from "react";
import { CheckCircle, XCircle, MinusCircle, ChevronDown, ChevronUp } from "lucide-react";
import { clsx } from "clsx";
import type { ReportSource, SourceStatus } from "@/lib/types";

interface Props {
  sources: ReportSource[];
}

const STATUS_ICON: Record<SourceStatus, React.ReactNode> = {
  checked: <CheckCircle className="w-4 h-4 text-green-600" />,
  failed: <XCircle className="w-4 h-4 text-red-500" />,
  skipped: <MinusCircle className="w-4 h-4 text-gray-400" />,
};

const STATUS_LABEL: Record<SourceStatus, string> = {
  checked: "Checked",
  failed: "Failed",
  skipped: "Skipped",
};

function formatTs(ts: string | null): string {
  if (!ts) return "—";
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(ts));
  } catch {
    return ts;
  }
}

export function DataSourcesTable({ sources }: Props) {
  const [open, setOpen] = useState(false);

  const checkedCount = sources.filter((s) => s.status === "checked").length;
  const failedCount = sources.filter((s) => s.status === "failed").length;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* Toggle header */}
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-gray-50 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-blue-500"
        aria-expanded={open}
      >
        <div>
          <h2 className="text-base font-semibold text-gray-900">Data Sources Checked</h2>
          <p className="text-xs text-gray-500 mt-0.5">
            {sources.length} source{sources.length !== 1 ? "s" : ""} queried
            {checkedCount > 0 && (
              <span className="ml-2 text-green-600">{checkedCount} ok</span>
            )}
            {failedCount > 0 && (
              <span className="ml-2 text-red-600">{failedCount} failed</span>
            )}
          </p>
        </div>
        {open ? (
          <ChevronUp className="w-4 h-4 text-gray-400 flex-shrink-0" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-400 flex-shrink-0" />
        )}
      </button>

      {open && (
        <div className="border-t border-gray-100">
          {/* Mobile: stacked list */}
          <ul className="sm:hidden divide-y divide-gray-100">
            {sources.map((src, i) => (
              <li key={i} className="flex items-center gap-3 px-5 py-3">
                {STATUS_ICON[src.status] ?? <MinusCircle className="w-4 h-4 text-gray-400" />}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-800 truncate">{src.name}</p>
                  <p className="text-xs text-gray-400">{formatTs(src.checked_at)}</p>
                </div>
                <span
                  className={clsx(
                    "text-xs flex-shrink-0",
                    src.status === "checked" && "text-green-600",
                    src.status === "failed" && "text-red-600",
                    src.status === "skipped" && "text-gray-400"
                  )}
                >
                  {STATUS_LABEL[src.status]}
                </span>
              </li>
            ))}
          </ul>

          {/* Desktop: table */}
          <div className="hidden sm:block overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-100">
                  <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                    Source
                  </th>
                  <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 w-28">
                    Status
                  </th>
                  <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 w-44">
                    Checked At
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {sources.map((src, i) => (
                  <tr key={i} className="hover:bg-gray-50 transition-colors">
                    <td className="px-5 py-3 font-medium text-gray-800">{src.name}</td>
                    <td className="px-5 py-3">
                      <span className="flex items-center gap-1.5">
                        {STATUS_ICON[src.status] ?? (
                          <MinusCircle className="w-4 h-4 text-gray-400" />
                        )}
                        <span
                          className={clsx(
                            "text-xs font-medium",
                            src.status === "checked" && "text-green-700",
                            src.status === "failed" && "text-red-600",
                            src.status === "skipped" && "text-gray-400"
                          )}
                        >
                          {STATUS_LABEL[src.status]}
                        </span>
                      </span>
                    </td>
                    <td className="px-5 py-3 text-gray-500 text-xs">
                      {formatTs(src.checked_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
