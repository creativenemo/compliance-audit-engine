"use client";

import { US_STATES, type IntakeForm, type RevenueRange, type TransactionRange } from "@/lib/types";

interface Props {
  values: Partial<IntakeForm>;
  errors: Partial<Record<keyof IntakeForm, string>>;
  onChange: (field: keyof IntakeForm, value: unknown) => void;
  onBlur: (field: keyof IntakeForm) => void;
}

const REVENUE_RANGES: { value: RevenueRange; label: string }[] = [
  { value: "under_100k", label: "Under $100K" },
  { value: "100k_500k", label: "$100K – $500K" },
  { value: "500k_1m", label: "$500K – $1M" },
  { value: "1m_5m", label: "$1M – $5M" },
  { value: "5m_25m", label: "$5M – $25M" },
  { value: "over_25m", label: "Over $25M" },
];

const TRANSACTION_RANGES: { value: TransactionRange; label: string }[] = [
  { value: "under_200", label: "Under 200" },
  { value: "200_1k", label: "200 – 1,000" },
  { value: "1k_10k", label: "1,000 – 10,000" },
  { value: "10k_100k", label: "10,000 – 100,000" },
  { value: "over_100k", label: "Over 100,000" },
];

export function RevenueSection({ values, errors, onChange, onBlur }: Props) {
  const handleSalesTaxToggle = (code: string) => {
    const current = (values.states_registered_sales_tax ?? []) as string[];
    const next = current.includes(code) ? current.filter((s) => s !== code) : [...current, code];
    onChange("states_registered_sales_tax", next);
  };

  return (
    <section>
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Revenue & Tax</h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Annual Revenue <span className="text-red-500">*</span>
            <span className="ml-1 text-xs text-gray-400 cursor-help" title="Used to determine sales tax nexus thresholds">(?)</span>
          </label>
          <select
            value={values.annual_revenue ?? ""}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            onChange={(e) => onChange("annual_revenue", e.target.value)}
            onBlur={() => onBlur("annual_revenue")}
          >
            <option value="">Select range…</option>
            {REVENUE_RANGES.map((r) => (
              <option key={r.value} value={r.value}>{r.label}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Annual Transactions <span className="text-red-500">*</span>
            <span className="ml-1 text-xs text-gray-400 cursor-help" title="Number of sales transactions per year across all states">(?)</span>
          </label>
          <select
            value={values.annual_transactions ?? ""}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            onChange={(e) => onChange("annual_transactions", e.target.value)}
            onBlur={() => onBlur("annual_transactions")}
          >
            <option value="">Select range…</option>
            {TRANSACTION_RANGES.map((r) => (
              <option key={r.value} value={r.value}>{r.label}</option>
            ))}
          </select>
        </div>

        <div className="sm:col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            States Registered for Sales Tax
            <span className="ml-1 text-xs text-gray-400 cursor-help" title="States where you are already registered to collect sales tax">(?)</span>
          </label>
          <div className="grid grid-cols-6 gap-1 sm:grid-cols-9">
            {US_STATES.map((s) => (
              <button
                key={s.code}
                type="button"
                onClick={() => handleSalesTaxToggle(s.code)}
                className={`px-2 py-1 text-xs rounded border transition-colors ${
                  (values.states_registered_sales_tax ?? []).includes(s.code)
                    ? "bg-green-600 text-white border-green-600"
                    : "bg-white text-gray-600 border-gray-300 hover:border-green-400"
                }`}
                title={s.name}
              >
                {s.code}
              </button>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
