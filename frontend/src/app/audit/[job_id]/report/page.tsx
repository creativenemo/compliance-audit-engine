"use client";

import { use } from "react";
import Link from "next/link";
import { Loader2, AlertCircle, ClipboardList } from "lucide-react";
import { useAuditReport } from "@/lib/queries";
import { ReportHeader } from "@/components/report/ReportHeader";
import { ScoreGauge } from "@/components/report/ScoreGauge";
import { SectionCard } from "@/components/report/SectionCard";
import { ActionItemList } from "@/components/report/ActionItemList";
import { DataSourcesTable } from "@/components/report/DataSourcesTable";
import type { ReportSchema, ScoreBreakdown } from "@/lib/types";

// ─── Scoring weights ───────────────────────────────────────────────────────────

const SCORE_WEIGHTS: Array<{
  key: keyof ScoreBreakdown;
  label: string;
  weight: number; // fractional (sums to 1)
  display: string;
}> = [
  { key: "entity_status",       label: "Entity Status",        weight: 0.25, display: "25%" },
  { key: "federal_compliance",  label: "Federal Compliance",   weight: 0.25, display: "25%" },
  { key: "sanctions_watchlists",label: "Sanctions & Watchlists",weight: 0.20, display: "20%" },
  { key: "tax_exposure",        label: "Tax Exposure",         weight: 0.20, display: "20%" },
  { key: "license_status",      label: "License Status",       weight: 0.10, display: "10%" },
];

function computeOverallScore(breakdown: ScoreBreakdown): number {
  const raw = SCORE_WEIGHTS.reduce(
    (sum, w) => sum + breakdown[w.key] * w.weight,
    0
  );
  return Math.round(raw);
}

// ─── Props ─────────────────────────────────────────────────────────────────────

interface Props {
  params: Promise<{ job_id: string }>;
}

// ─── Loading skeleton ──────────────────────────────────────────────────────────

function LoadingSkeleton() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="h-36 bg-white border-b border-gray-200 shadow-sm" />
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-6 animate-pulse">
        <div className="h-24 bg-gray-200 rounded-lg" />
        <div className="grid grid-cols-5 gap-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-28 bg-gray-200 rounded-lg" />
          ))}
        </div>
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-16 bg-gray-200 rounded-lg" />
        ))}
      </div>
    </div>
  );
}

// ─── Error / not-ready states ─────────────────────────────────────────────────

function ErrorState({ jobId, message }: { jobId: string; message: string }) {
  const isNotReady =
    message.toLowerCase().includes("not found") ||
    message.toLowerCase().includes("not complete") ||
    message.toLowerCase().includes("404") ||
    message.toLowerCase().includes("running");

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-8 max-w-md w-full text-center space-y-4">
        {isNotReady ? (
          <>
            <ClipboardList className="w-10 h-10 text-amber-500 mx-auto" />
            <h2 className="text-lg font-semibold text-gray-900">
              Report Not Ready Yet
            </h2>
            <p className="text-sm text-gray-600">
              The audit is still running. Check back once it completes.
            </p>
            <Link
              href={`/audit/${jobId}/loading`}
              className="inline-block mt-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
            >
              View Audit Progress
            </Link>
          </>
        ) : (
          <>
            <AlertCircle className="w-10 h-10 text-red-500 mx-auto" />
            <h2 className="text-lg font-semibold text-gray-900">
              Could Not Load Report
            </h2>
            <p className="text-sm text-gray-600">{message}</p>
            <Link
              href={`/audit/${jobId}/loading`}
              className="inline-block mt-2 px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50 transition-colors"
            >
              Back to Audit Status
            </Link>
          </>
        )}
      </div>
    </div>
  );
}

// ─── Full report ──────────────────────────────────────────────────────────────

function FullReport({ jobId, report }: { jobId: string; report: ReportSchema }) {
  const overallScore = computeOverallScore(report.score_breakdown);

  // Derive entity name: check executive_summary for a quoted name, fallback to jobId
  const entityNameMatch = report.executive_summary?.match(/^([^.,:–—]+)/);
  const entityName = entityNameMatch ? entityNameMatch[1].trim() : `Audit ${jobId}`;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* ── Sticky header ── */}
      <ReportHeader
        jobId={jobId}
        entityName={entityName}
        overallScore={overallScore}
        riskLevel={report.overall_risk_score}
        generatedAt={report.generated_at}
      />

      {/* ── Main content ── */}
      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-8">

        {/* 1. Executive Summary */}
        {report.executive_summary && (
          <section aria-label="Executive Summary">
            <div className="bg-gray-100 border border-gray-200 rounded-xl px-6 py-5">
              <h2 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
                Executive Summary
              </h2>
              <p className="text-sm text-gray-700 italic leading-relaxed">
                {report.executive_summary}
              </p>
            </div>
          </section>
        )}

        {/* 2. Score breakdown */}
        <section aria-label="Score Breakdown">
          <h2 className="text-base font-semibold text-gray-900 mb-4">Score Breakdown</h2>
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm px-4 py-6">
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-6 justify-items-center">
              {SCORE_WEIGHTS.map((w) => (
                <ScoreGauge
                  key={w.key}
                  score={report.score_breakdown[w.key]}
                  label={w.label}
                  weight={w.display}
                />
              ))}
            </div>
            <div className="mt-6 pt-5 border-t border-gray-100 text-center">
              <p className="text-xs text-gray-500">
                Overall score is the weighted average of the five dimensions above.
              </p>
            </div>
          </div>
        </section>

        {/* 3. Action items */}
        {report.top_action_items?.length > 0 && (
          <section aria-label="Action Items">
            <ActionItemList items={report.top_action_items} />
          </section>
        )}

        {/* 4. Report sections */}
        {report.sections?.length > 0 && (
          <section aria-label="Detailed Sections">
            <h2 className="text-base font-semibold text-gray-900 mb-4">
              Detailed Findings
            </h2>
            <div className="space-y-3">
              {report.sections.map((section) => (
                <SectionCard key={section.section_id} section={section} />
              ))}
            </div>
          </section>
        )}

        {/* 5. Data sources */}
        {report.data_sources_checked?.length > 0 && (
          <section aria-label="Data Sources">
            <DataSourcesTable sources={report.data_sources_checked} />
          </section>
        )}

        {/* 6. Disclaimer */}
        {report.disclaimer && (
          <footer className="pb-8">
            <p className="text-xs text-gray-400 leading-relaxed border-t border-gray-200 pt-6">
              {report.disclaimer}
            </p>
          </footer>
        )}
      </main>
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function ReportPage({ params }: Props) {
  const { job_id } = use(params);
  const { data, isLoading, isError, error } = useAuditReport(job_id);

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (isError || !data) {
    const msg =
      error instanceof Error ? error.message : "Report could not be loaded.";
    return <ErrorState jobId={job_id} message={msg} />;
  }

  return <FullReport jobId={job_id} report={data} />;
}
