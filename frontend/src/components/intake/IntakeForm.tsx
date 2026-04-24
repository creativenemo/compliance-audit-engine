"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { submitAudit } from "@/lib/api-client";
import type { IntakeForm as IntakeFormData } from "@/lib/types";
import { ContactSection } from "./ContactSection";
import { EntitySection } from "./EntitySection";
import { OperatingSection } from "./OperatingSection";
import { RevenueSection } from "./RevenueSection";

type FormValues = Partial<IntakeFormData>;
type FormErrors = Partial<Record<keyof IntakeFormData, string>>;

const REQUIRED_FIELDS: (keyof IntakeFormData)[] = [
  "first_name", "last_name", "business_email",
  "legal_name", "domicile_state", "entity_type", "business_nature",
  "annual_revenue", "annual_transactions",
];

function validate(values: FormValues, field?: keyof IntakeFormData): FormErrors {
  const errors: FormErrors = {};
  const fields = field ? [field] : REQUIRED_FIELDS;

  for (const f of fields) {
    const val = values[f];
    if (!val || (Array.isArray(val) && val.length === 0) || val === "") {
      errors[f] = "This field is required";
    }
    if (f === "business_email" && val && typeof val === "string") {
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val)) {
        errors[f] = "Enter a valid email address";
      }
    }
  }

  if (!field && (!values.customer_types || (values.customer_types as string[]).length === 0)) {
    errors.customer_types = "Select at least one customer type";
  }

  return errors;
}

function completionPct(values: FormValues): number {
  const allFields: (keyof IntakeFormData)[] = [...REQUIRED_FIELDS, "customer_types"];
  const filled = allFields.filter((f) => {
    const v = values[f];
    return v !== undefined && v !== "" && !(Array.isArray(v) && v.length === 0);
  });
  return Math.round((filled.length / allFields.length) * 100);
}

export function IntakeForm() {
  const router = useRouter();
  const [values, setValues] = useState<FormValues>({ employee_states: [], customer_types: [], states_registered_sales_tax: [] });
  const [errors, setErrors] = useState<FormErrors>({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const pct = completionPct(values);
  const allErrors = validate(values);
  const isValid = Object.keys(allErrors).length === 0;

  function handleChange(field: keyof IntakeFormData, value: unknown) {
    setValues((v) => ({ ...v, [field]: value }));
  }

  function handleBlur(field: keyof IntakeFormData) {
    const fieldErrors = validate(values, field);
    setErrors((e) => ({ ...e, [field]: fieldErrors[field] }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const allErrs = validate(values);
    if (Object.keys(allErrs).length > 0) {
      setErrors(allErrs);
      return;
    }

    setSubmitting(true);
    setSubmitError(null);
    try {
      const response = await submitAudit(values as IntakeFormData);
      router.push(`/audit/${response.job_id}/loading`);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Submission failed. Please try again.");
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sticky progress bar */}
      <div className="sticky top-0 z-10 bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-2xl mx-auto px-4 py-3 flex items-center gap-4">
          <span className="text-sm text-gray-500 whitespace-nowrap">Form complete</span>
          <div className="flex-1 bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${pct}%` }}
            />
          </div>
          <span className="text-sm font-medium text-gray-700 whitespace-nowrap">{pct}%</span>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Compliance Audit</h1>
          <p className="mt-1 text-gray-600">One form. Every compliance check. Report in under 60 seconds.</p>
        </div>

        <form onSubmit={handleSubmit} noValidate>
          <div className="space-y-8">
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <ContactSection values={values} errors={errors} onChange={handleChange} onBlur={handleBlur} />
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <EntitySection values={values} errors={errors} onChange={handleChange} onBlur={handleBlur} />
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <OperatingSection values={values} errors={errors} onChange={handleChange} />
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <RevenueSection values={values} errors={errors} onChange={handleChange} onBlur={handleBlur} />
            </div>
          </div>

          {submitError && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
              {submitError}
            </div>
          )}

          <div className="mt-6">
            <button
              type="submit"
              disabled={!isValid || submitting}
              className="w-full py-3 px-6 bg-blue-600 text-white font-semibold rounded-lg disabled:opacity-40 disabled:cursor-not-allowed hover:bg-blue-700 transition-colors"
            >
              {submitting ? "Submitting…" : "Run Compliance Audit"}
            </button>
            {!isValid && (
              <p className="mt-2 text-center text-xs text-gray-500">
                Complete all required fields to enable submission
              </p>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}
