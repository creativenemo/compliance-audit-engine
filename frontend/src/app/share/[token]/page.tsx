"use client";

import { use } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { AlertCircle, Loader2 } from "lucide-react";
import { ScoreGauge } from "@/components/report/ScoreGauge";
import { RiskBadge } from "@/components/report/RiskBadge";
import { SectionCard } from "@/components/report/SectionCard";
import { ActionItemList } from "@/components/report/ActionItemList";
import { DataSourcesTable } from "@/components/report/DataSourcesTable";
import type { ReportSchema, ScoreBreakdown } from "@/lib/types";

// ─── Scoring weights (mirrors full report page) ───────────────────────────────

const SCORE_WEIGHTS: Array<{
  key: keyof ScoreBreakdown;
  label: string;
  weight: number;
  display: string;
}> = [
  { key: "entity_status",        label: "Entity Status",         weight: 0.25, display: "25%" },
  { key: "federal_compliance",   label: "Federal Compliance",    weight: 0.25, display: "25%" },
  { key: "sanctions_watchlists", label: "Sanctions & Watchlists",weight: 0.20, display: "20%" },
  { key: "tax_exposure",         label: "Tax Exposure",          weight: 0.20, display: "20%" },
  { key: "license_status",       label: "License Status",        weight: 0.10, display: "10%" },
];

function computeOverallScore(breakdown: ScoreBreakdown): number {
  const raw = SCORE_WEIGHTS.reduce(
    (sum, w) => sum + breakdown[w.key] * w.weight,
    0,
  );
  return Math.round(raw);
}

// ─── Props ────────────────────────────────────────────────────────────────────

interface Props {
  params: Promise<{ token: string }>;
}

// ─── Shared banner ────────────────────────────────────────────────────────────

function SharedBanner() {
  return (
    <div className="w-full bg-amber-50 border-b border-amber-200 px-4 py-2.5">
      <p className="text-center text-xs font-medium text-amber-800">
        Read-only shared view. Link expires 7 days from creation.
      </p>
    </div>
  );
}

// ─── Loading skeleton ─────────────────────────────────────────────────────────

function LoadingSkeleton() {
  return (
    <div className="min-h-screen bg-gray-50">
      <SharedBanner />
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

// ─── Error state ──────────────────────────────────────────────────────────────

function ErrorState({ isExpired }: { isExpired: boolean }) {
  return (
    <div className="min-h-screen bg-gray-50">
      <SharedBanner />
      <div className="flex items-center justify-center p-4 mt-16">
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-8 max-w-md w-full text-center space-y-4">
          <AlertCircle className="w-10 h-10 text-red-500 mx-auto" />
          <h2 className="text-lg font-semibold text-gray-900">
            {isExpired ? "Link Expired" : "Report Not Found"}
          </h2>
          <p className="text-sm text-gray-600">
            {isExpired
              ? "This share link has expired or is invalid."
              : "The shared report could not be loaded. The link may have expired or been revoked."}
          </p>
          <Link
            href="/"
            className="inline-block mt-2 px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50 transition-colors"
          >
            Go to Home
          </Link>
        </div>
      </div>
    </div>
  );
}

// ─── Shared report header (no action buttons) ─────────────────────────────────

function SharedReportHeader({
  entityName,
  overallScore,
  riskLevel,
  generatedAt,
}: {
  entityName: string;
  overallScore: number;
  riskLevel: string;
  generatedAt: string;
}) {
  let formattedDate = generatedAt;
  try {
    formattedDate = new Intl.DateTimeFormat(undefined, {
      dateStyle: "long",
      timeStyle: "short",
    }).format(new Date(generatedAt));
  } catch {
    // keep raw string
  }

  return (
    <header className="sticky top-0 z-30 bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-3">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div className="min-w-0">
            <p className="text-xs text-gray-400 uppercase tracking-wider font-medium">
              Shared Compliance Report
            </p>
            <h1 className="text-lg sm:text-xl font-bold text-gray-900 truncate max-w-xs sm:max-w-md">
              {entityName}
            </h1>
            <p className="text-xs text-gray-400 mt-0.5">
              Generated {formattedDate}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4 mt-3 pb-1">
          <ScoreGauge score={overallScore} label="Overall Score" />
          <div className="flex flex-col gap-1">
            <RiskBadge level={riskLevel as import("@/lib/types").RiskLevel} size="lg" />
            <p className="text-xs text-gray-400">Risk Level</p>
          </div>
        </div>
      </div>
    </header>
  );
}

// ─── Full shared report ───────────────────────────────────────────────────────

function SharedReport({ report }: { report: ReportSchema }) {
  const overallScore = computeOverallScore(report.score_breakdown);
  const entityNameMatch = report.executive_summary?.match(/^([^.,:–—]+)/);
  const entityName = entityNameMatch ? entityNameMatch[1].trim() : "Shared Audit";

  return (
    <div className="min-h-screen bg-gray-50">
      <SharedBanner />
      <SharedReportHeader
        entityName={entityName}
        overallScore={overallScore}
        riskLevel={report.overall_risk_score}
        generatedAt={report.generated_at}
      />

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

export default function SharePage({ params }: Props) {
  const { token } = use(params);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["shared-report", token],
    queryFn: () =>
      fetch(`/api/v1/share/${token}`).then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json() as Promise<ReportSchema>;
      }),
    retry: false,
  });

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (isError || !data) {
    const status =
      error instanceof Error && error.message.includes("404") ? 404 : 0;
    return <ErrorState isExpired={status === 404} />;
  }

  return <SharedReport report={data} />;
}
