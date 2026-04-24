"use client";

import { use } from "react";
import { useAuditReport } from "@/lib/queries";

interface Props {
  params: Promise<{ job_id: string }>;
}

export default function ReportPage({ params }: Props) {
  const { job_id } = use(params);
  const { data, isLoading, isError } = useAuditReport(job_id);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-500">Loading report…</p>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-red-600">Report not available. The audit may still be running.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Compliance Report</h1>
        <p className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded px-3 py-2 mb-6">
          Sprint 1 stub — full report UI implemented in Sprint 3.
        </p>
        <pre className="bg-white border border-gray-200 rounded-lg p-4 text-xs overflow-auto">
          {JSON.stringify(data, null, 2)}
        </pre>
      </div>
    </div>
  );
}
