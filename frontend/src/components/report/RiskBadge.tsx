"use client";

import { clsx } from "clsx";

interface Props {
  level: string;
  size?: "sm" | "lg";
}

const STYLES: Record<string, string> = {
  LOW: "bg-green-100 text-green-800 ring-green-200",
  MEDIUM: "bg-amber-100 text-amber-800 ring-amber-200",
  HIGH: "bg-red-100 text-red-800 ring-red-200",
  CRITICAL: "bg-red-950 text-red-100 ring-red-900",
};

export function RiskBadge({ level, size = "sm" }: Props) {
  const normalized = level.toUpperCase();
  const colorClasses = STYLES[normalized] ?? "bg-gray-100 text-gray-700 ring-gray-200";

  return (
    <span
      className={clsx(
        "inline-flex items-center font-semibold tracking-wide rounded-full ring-1",
        colorClasses,
        size === "lg"
          ? "px-4 py-1.5 text-sm"
          : "px-2.5 py-0.5 text-xs"
      )}
    >
      {normalized}
    </span>
  );
}
