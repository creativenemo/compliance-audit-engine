import type { AuditStatusResponse, AuditSubmitResponse, IntakeForm, ReportSchema } from "./types";

const API_KEY = process.env.NEXT_PUBLIC_API_KEY ?? "dev-key-001";
const BASE = "";  // rewrites proxy /api/* to backend

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": API_KEY,
      ...init?.headers,
    },
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail ?? `HTTP ${res.status}`);
  }

  return res.json() as Promise<T>;
}

export async function submitAudit(form: IntakeForm): Promise<AuditSubmitResponse> {
  return request<AuditSubmitResponse>(`${BASE}/api/v1/audit`, {
    method: "POST",
    body: JSON.stringify(form),
  });
}

export async function getAuditStatus(jobId: string): Promise<AuditStatusResponse> {
  return request<AuditStatusResponse>(`${BASE}/api/v1/audit/${jobId}/status`);
}

export async function getAuditReport(jobId: string): Promise<ReportSchema> {
  return request<ReportSchema>(`${BASE}/api/v1/audit/${jobId}/report`);
}

export async function getReportPdf(jobId: string): Promise<Blob> {
  const API_KEY_VAL = process.env.NEXT_PUBLIC_API_KEY ?? "dev-key-001";
  const res = await fetch(`${BASE}/api/v1/audit/${jobId}/pdf`, {
    headers: { "X-API-Key": API_KEY_VAL },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.blob();
}

export async function getShareUrl(jobId: string): Promise<{ share_url: string }> {
  return request<{ share_url: string }>(`${BASE}/api/v1/audit/${jobId}/share`);
}
