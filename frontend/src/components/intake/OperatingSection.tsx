"use client";

import type { CustomerType, IntakeForm } from "@/lib/types";

interface Props {
  values: Partial<IntakeForm>;
  errors: Partial<Record<keyof IntakeForm, string>>;
  onChange: (field: keyof IntakeForm, value: unknown) => void;
}

const CUSTOMER_TYPES: { value: CustomerType; label: string; description: string }[] = [
  { value: "B2B", label: "Business (B2B)", description: "Sell to other businesses" },
  { value: "B2C", label: "Consumer (B2C)", description: "Sell directly to consumers" },
  { value: "Government", label: "Government", description: "Sell to government agencies" },
];

export function OperatingSection({ values, errors, onChange }: Props) {
  const toggleCustomerType = (type: CustomerType) => {
    const current = (values.customer_types ?? []) as CustomerType[];
    const next = current.includes(type) ? current.filter((t) => t !== type) : [...current, type];
    onChange("customer_types", next);
  };

  return (
    <section>
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Operating Profile</h2>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Customer Types <span className="text-red-500">*</span>
          </label>
          <div className="flex flex-wrap gap-3">
            {CUSTOMER_TYPES.map((ct) => (
              <button
                key={ct.value}
                type="button"
                onClick={() => toggleCustomerType(ct.value)}
                className={`px-4 py-2 rounded-lg border text-sm transition-colors ${
                  (values.customer_types ?? []).includes(ct.value)
                    ? "bg-blue-600 text-white border-blue-600"
                    : "bg-white text-gray-700 border-gray-300 hover:border-blue-400"
                }`}
                title={ct.description}
              >
                {ct.label}
              </button>
            ))}
          </div>
          {errors.customer_types && <p className="mt-1 text-xs text-red-600">{errors.customer_types}</p>}
        </div>

        <div className="flex items-start gap-3">
          <input
            type="checkbox"
            id="ecommerce"
            checked={values.ecommerce_marketplace ?? false}
            onChange={(e) => onChange("ecommerce_marketplace", e.target.checked)}
            className="mt-1 h-4 w-4 text-blue-600 border-gray-300 rounded"
          />
          <label htmlFor="ecommerce" className="text-sm text-gray-700">
            <span className="font-medium">E-commerce marketplace</span>
            <span className="block text-gray-500 text-xs">Sell products through an online marketplace (Amazon, Etsy, Shopify, etc.)</span>
          </label>
        </div>
      </div>
    </section>
  );
}
