"use client";

import { useState } from "react";
import { Download, Share2, Loader2 } from "lucide-react";
import { ScoreGauge } from "./ScoreGauge";
import { RiskBadge } from "./RiskBadge";
import { getReportPdf, getShareUrl } from "@/lib/api-client";
import type { RiskLevel } from "@/lib/types";

interface Props {
  jobId: string;
  entityName: string;
  overallScore: number;
  riskLevel: RiskLevel;
  generatedAt: string;
}

function formatGeneratedAt(iso: string): string {
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "long",
      timeStyle: "short",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

export function ReportHeader({
  jobId,
  entityName,
  overallScore,
  riskLevel,
  generatedAt,
}: Props) {
  const [pdfLoading, setPdfLoading] = useState(false);
  const [shareLoading, setShareLoading] = useState(false);
  const [shareMsg, setShareMsg] = useState<string | null>(null);

  async function handleDownloadPdf() {
    setPdfLoading(true);
    try {
      const blob = await getReportPdf(jobId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `compliance-report-${jobId}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      // Stub — backend may not be implemented yet
      alert("PDF download is not available for this report.");
    } finally {
      setPdfLoading(false);
    }
  }

  async function handleShare() {
    setShareLoading(true);
    setShareMsg(null);
    try {
      const { share_url } = await getShareUrl(jobId);
      await navigator.clipboard.writeText(share_url);
      setShareMsg("Link copied!");
    } catch {
      // Stub — copy current URL as fallback
      try {
        await navigator.clipboard.writeText(window.location.href);
        setShareMsg("URL copied!");
      } catch {
        setShareMsg("Could not copy link.");
      }
    } finally {
      setShareLoading(false);
      setTimeout(() => setShareMsg(null), 3000);
    }
  }

  return (
    <header className="sticky top-0 z-30 bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-3">
        {/* Top row: entity name + action buttons */}
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div className="min-w-0">
            <p className="text-xs text-gray-400 uppercase tracking-wider font-medium">
              Compliance Report
            </p>
            <h1 className="text-lg sm:text-xl font-bold text-gray-900 truncate max-w-xs sm:max-w-md">
              {entityName}
            </h1>
            <p className="text-xs text-gray-400 mt-0.5">
              Generated {formatGeneratedAt(generatedAt)}
            </p>
          </div>

          <div className="flex items-center gap-2 flex-shrink-0 pt-1">
            {/* Download PDF */}
            <button
              type="button"
              onClick={handleDownloadPdf}
              disabled={pdfLoading}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-60 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
              title="Download PDF"
            >
              {pdfLoading ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Download className="w-3.5 h-3.5" />
              )}
              <span className="hidden sm:inline">Download PDF</span>
            </button>

            {/* Share */}
            <button
              type="button"
              onClick={handleShare}
              disabled={shareLoading}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-60 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
              title="Share report"
            >
              {shareLoading ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Share2 className="w-3.5 h-3.5" />
              )}
              <span className="hidden sm:inline">
                {shareMsg ?? "Share Report"}
              </span>
              {shareMsg && (
                <span className="sm:hidden text-green-600">{shareMsg}</span>
              )}
            </button>
          </div>
        </div>

        {/* Score row */}
        <div className="flex items-center gap-4 mt-3 pb-1">
          <ScoreGauge score={overallScore} label="Overall Score" />
          <div className="flex flex-col gap-1">
            <RiskBadge level={riskLevel} size="lg" />
            <p className="text-xs text-gray-400">Risk Level</p>
          </div>
        </div>
      </div>
    </header>
  );
}
