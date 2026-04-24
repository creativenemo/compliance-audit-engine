"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuditStatus as useQuery } from "@/lib/queries";

export function useAuditStatus(jobId: string) {
  const router = useRouter();
  const query = useQuery(jobId);

  useEffect(() => {
    if (query.data?.status === "complete") {
      router.push(`/audit/${jobId}/report`);
    }
  }, [query.data?.status, jobId, router]);

  return query;
}
