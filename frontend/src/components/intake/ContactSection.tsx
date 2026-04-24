"use client";

import type { IntakeForm } from "@/lib/types";

interface Props {
  values: Partial<IntakeForm>;
  errors: Partial<Record<keyof IntakeForm, string>>;
  onChange: (field: keyof IntakeForm, value: unknown) => void;
  onBlur: (field: keyof IntakeForm) => void;
}

export function ContactSection({ values, errors, onChange, onBlur }: Props) {
  return (
    <section>
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Contact Information</h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Field
          label="First Name"
          required
          value={values.first_name ?? ""}
          error={errors.first_name}
          onChange={(v) => onChange("first_name", v)}
          onBlur={() => onBlur("first_name")}
        />
        <Field
          label="Last Name"
          required
          value={values.last_name ?? ""}
          error={errors.last_name}
          onChange={(v) => onChange("last_name", v)}
          onBlur={() => onBlur("last_name")}
        />
        <Field
          label="Business Email"
          type="email"
          required
          className="sm:col-span-2"
          value={values.business_email ?? ""}
          error={errors.business_email}
          onChange={(v) => onChange("business_email", v)}
          onBlur={() => onBlur("business_email")}
          tooltip="Used to deliver your compliance report"
        />
      </div>
    </section>
  );
}

interface FieldProps {
  label: string;
  type?: string;
  required?: boolean;
  value: string;
  error?: string;
  className?: string;
  tooltip?: string;
  onChange: (value: string) => void;
  onBlur: () => void;
}

function Field({ label, type = "text", required, value, error, className, tooltip, onChange, onBlur }: FieldProps) {
  return (
    <div className={className}>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
        {tooltip && (
          <span className="ml-1 text-xs text-gray-400 cursor-help" title={tooltip}>(?)</span>
        )}
      </label>
      <input
        type={type}
        value={value}
        className={`w-full px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
          error ? "border-red-500" : "border-gray-300"
        }`}
        onChange={(e) => onChange(e.target.value)}
        onBlur={onBlur}
      />
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  );
}
