import { useQuery } from "@tanstack/react-query";
import { getAuditReport, getAuditStatus } from "./api-client";
import type { ReportSchema } from "./types";

export function useAuditStatus(jobId: string, enabled = true) {
  return useQuery({
    queryKey: ["audit-status", jobId],
    queryFn: () => getAuditStatus(jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "complete" || status === "failed") return false;
      return 2000;
    },
    enabled: enabled && !!jobId,
  });
}

export function useAuditReport(jobId: string, enabled = true) {
  return useQuery<ReportSchema>({
    queryKey: ["audit-report", jobId],
    queryFn: () => getAuditReport(jobId),
    enabled: enabled && !!jobId,
    retry: false,
  });
}
