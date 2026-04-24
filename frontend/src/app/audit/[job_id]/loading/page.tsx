"use client";

import { use } from "react";
import { ProgressLoader } from "@/components/progress/ProgressLoader";
import { useAuditStatus } from "@/hooks/useAuditStatus";

interface Props {
  params: Promise<{ job_id: string }>;
}

export default function LoadingPage({ params }: Props) {
  const { job_id } = use(params);
  const { data, isLoading, isError } = useAuditStatus(job_id);

  if (isLoading || !data) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-500">Initializing audit…</p>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-red-600">Failed to load audit status. Please refresh.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-8 w-full max-w-lg">
        <h1 className="text-xl font-bold text-gray-900 mb-6">Running Your Compliance Audit</h1>
        <ProgressLoader status={data} />
      </div>
    </div>
  );
}
