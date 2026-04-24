"use client";

import { clsx } from "clsx";
import type { ActionItem, ActionUrgency } from "@/lib/types";

interface Props {
  items: ActionItem[];
}

const URGENCY_BADGE: Record<ActionUrgency, string> = {
  critical: "bg-red-950 text-red-100 ring-red-900",
  high: "bg-red-100 text-red-800 ring-red-200",
  medium: "bg-amber-100 text-amber-800 ring-amber-200",
  low: "bg-gray-100 text-gray-700 ring-gray-200",
};

function rowClass(priority: number): string {
  if (priority <= 2) return "bg-red-50";
  if (priority === 3) return "bg-amber-50";
  return "bg-white";
}

export function ActionItemList({ items }: Props) {
  if (items.length === 0) return null;

  const sorted = [...items].sort((a, b) => a.priority - b.priority);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <div className="px-5 py-4 border-b border-gray-100">
        <h2 className="text-base font-semibold text-gray-900">Action Items</h2>
        <p className="text-xs text-gray-500 mt-0.5">
          {items.length} item{items.length !== 1 ? "s" : ""} requiring attention
        </p>
      </div>

      {/* Mobile: card list */}
      <ul className="sm:hidden divide-y divide-gray-100">
        {sorted.map((item, i) => (
          <li key={i} className={clsx("px-5 py-4", rowClass(item.priority))}>
            <div className="flex items-start justify-between gap-3 mb-1">
              <span
                className={clsx(
                  "flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold",
                  item.priority <= 2
                    ? "bg-red-600 text-white"
                    : item.priority === 3
                    ? "bg-amber-500 text-white"
                    : "bg-gray-200 text-gray-700"
                )}
              >
                {item.priority}
              </span>
              <span
                className={clsx(
                  "text-xs font-semibold px-2 py-0.5 rounded-full ring-1",
                  URGENCY_BADGE[item.urgency] ?? URGENCY_BADGE.low
                )}
              >
                {item.urgency.charAt(0).toUpperCase() + item.urgency.slice(1)}
              </span>
            </div>
            <p className="text-sm text-gray-800 mt-2">{item.action}</p>
            {item.estimated_cost && (
              <p className="text-xs text-gray-500 mt-1">
                Est. cost: {item.estimated_cost}
              </p>
            )}
          </li>
        ))}
      </ul>

      {/* Desktop: table */}
      <div className="hidden sm:block overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50 text-left">
              <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-gray-500 w-12">
                #
              </th>
              <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-gray-500">
                Action
              </th>
              <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-gray-500 w-28">
                Urgency
              </th>
              <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-gray-500 w-36 text-right">
                Est. Cost
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {sorted.map((item, i) => (
              <tr key={i} className={clsx("transition-colors", rowClass(item.priority))}>
                <td className="px-4 py-3">
                  <span
                    className={clsx(
                      "w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold mx-auto",
                      item.priority <= 2
                        ? "bg-red-600 text-white"
                        : item.priority === 3
                        ? "bg-amber-500 text-white"
                        : "bg-gray-200 text-gray-700"
                    )}
                  >
                    {item.priority}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-800">{item.action}</td>
                <td className="px-4 py-3">
                  <span
                    className={clsx(
                      "inline-flex items-center text-xs font-semibold px-2.5 py-0.5 rounded-full ring-1",
                      URGENCY_BADGE[item.urgency] ?? URGENCY_BADGE.low
                    )}
                  >
                    {item.urgency.charAt(0).toUpperCase() + item.urgency.slice(1)}
                  </span>
                </td>
                <td className="px-4 py-3 text-right text-gray-600">
                  {item.estimated_cost ?? (
                    <span className="text-gray-400">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
