"use client";

import { US_STATES, type EntityType, type IntakeForm } from "@/lib/types";

interface Props {
  values: Partial<IntakeForm>;
  errors: Partial<Record<keyof IntakeForm, string>>;
  onChange: (field: keyof IntakeForm, value: unknown) => void;
  onBlur: (field: keyof IntakeForm) => void;
}

const ENTITY_TYPES: { value: EntityType; label: string }[] = [
  { value: "LLC", label: "LLC" },
  { value: "Corp", label: "Corporation" },
  { value: "LP", label: "Limited Partnership" },
  { value: "LLP", label: "LLP" },
  { value: "SoleProp", label: "Sole Proprietorship" },
  { value: "Nonprofit", label: "Nonprofit" },
  { value: "Other", label: "Other" },
];

export function EntitySection({ values, errors, onChange, onBlur }: Props) {
  const handleStateToggle = (field: "employee_states" | "product_service_location", code: string) => {
    const current = (values[field] as string[]) ?? [];
    const next = current.includes(code) ? current.filter((s) => s !== code) : [...current, code];
    onChange(field, next);
  };

  return (
    <section>
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Entity Details</h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Legal Entity Name <span className="text-red-500">*</span>
            <span className="ml-1 text-xs text-gray-400 cursor-help" title="Full legal name as registered with the state">(?)</span>
          </label>
          <input
            type="text"
            value={values.legal_name ?? ""}
            className={`w-full px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${errors.legal_name ? "border-red-500" : "border-gray-300"}`}
            onChange={(e) => onChange("legal_name", e.target.value)}
            onBlur={() => onBlur("legal_name")}
          />
          {errors.legal_name && <p className="mt-1 text-xs text-red-600">{errors.legal_name}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Entity Type <span className="text-red-500">*</span>
          </label>
          <select
            value={values.entity_type ?? ""}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            onChange={(e) => onChange("entity_type", e.target.value)}
            onBlur={() => onBlur("entity_type")}
          >
            <option value="">Select type…</option>
            {ENTITY_TYPES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Domicile State <span className="text-red-500">*</span>
            <span className="ml-1 text-xs text-gray-400 cursor-help" title="State where entity was formed/incorporated">(?)</span>
          </label>
          <select
            value={values.domicile_state ?? ""}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            onChange={(e) => onChange("domicile_state", e.target.value)}
            onBlur={() => onBlur("domicile_state")}
          >
            <option value="">Select state…</option>
            {US_STATES.map((s) => (
              <option key={s.code} value={s.code}>{s.name}</option>
            ))}
          </select>
        </div>

        <div className="sm:col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Nature of Business <span className="text-red-500">*</span>
          </label>
          <textarea
            value={values.business_nature ?? ""}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Describe what your business does (e.g., 'Professional aviation consulting and maintenance services')"
            onChange={(e) => onChange("business_nature", e.target.value)}
            onBlur={() => onBlur("business_nature")}
          />
        </div>

        <div className="sm:col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            States with Employees
            <span className="ml-1 text-xs text-gray-400 cursor-help" title="States where you have employees, offices, or significant operations">(?)</span>
          </label>
          <div className="grid grid-cols-6 gap-1 sm:grid-cols-9">
            {US_STATES.map((s) => (
              <button
                key={s.code}
                type="button"
                onClick={() => handleStateToggle("employee_states", s.code)}
                className={`px-2 py-1 text-xs rounded border transition-colors ${
                  (values.employee_states ?? []).includes(s.code)
                    ? "bg-blue-600 text-white border-blue-600"
                    : "bg-white text-gray-600 border-gray-300 hover:border-blue-400"
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
