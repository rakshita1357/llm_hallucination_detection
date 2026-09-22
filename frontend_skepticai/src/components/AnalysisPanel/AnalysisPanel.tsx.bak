import React, { useState } from 'react';
import { 
  ShieldCheck, 
  ShieldAlert, 
  AlertTriangle, 
  ChevronDown, 
  ChevronUp, 
  ExternalLink, 
  CheckCircle2, 
  XCircle, 
  Info, 
  Sparkles, 
  X, 
  HelpCircle,
  FileCheck,
  Search,
  Activity,
  Layers,
  BarChart2
} from 'lucide-react';
import { AnalysisReportData, AnalysisFinding, VerificationStatus } from '../../types.ts';
import { PIPELINE_STEPS } from '../../constants/models.ts';

interface AnalysisPanelProps {
  analysisData: AnalysisReportData | null;
  isLoading: boolean;
  currentStep?: number;
  onClose?: () => void;
  className?: string;
  isMobile?: boolean;
}

export const AnalysisPanel: React.FC<AnalysisPanelProps> = ({
  analysisData,
  isLoading,
  currentStep = 0,
  onClose,
  className = '',
  isMobile = false
}) => {
  const [expandedFindingId, setExpandedFindingId] = useState<string | null>(null);

  const toggleExpand = (id: string) => {
    setExpandedFindingId(prev => (prev === id ? null : id));
  };

  const getStatusMeta = (status: VerificationStatus) => {
    switch (status) {
      case 'verified':
        return {
          title: 'Verified & Sound',
          label: 'Highly Reliable',
          color: 'text-emerald-400',
          ringColor: 'text-emerald-500',
          bg: 'bg-emerald-500/10',
          border: 'border-emerald-500/30',
          icon: <ShieldCheck className="w-5 h-5 text-emerald-400" />
        };
      case 'mostly_reliable':
        return {
          title: 'Mostly Reliable',
          label: 'Minor Ambiguity',
          color: 'text-blue-400',
          ringColor: 'text-blue-500',
          bg: 'bg-blue-500/10',
          border: 'border-blue-500/30',
          icon: <ShieldCheck className="w-5 h-5 text-blue-400" />
        };
      case 'partially_reliable':
        return {
          title: 'Partially Reliable',
          label: 'Requires Caution',
          color: 'text-amber-400',
          ringColor: 'text-amber-500',
          bg: 'bg-amber-500/10',
          border: 'border-amber-500/30',
          icon: <AlertTriangle className="w-5 h-5 text-amber-400" />
        };
      case 'potential_hallucination':
        return {
          title: 'Potential Hallucination',
          label: 'Contradiction Alert',
          color: 'text-red-400',
          ringColor: 'text-red-500',
          bg: 'bg-red-500/15',
          border: 'border-red-500/40',
          icon: <ShieldAlert className="w-5 h-5 text-red-400" />
        };
      case 'analysis_unavailable':
      default:
        return {
          title: 'Analysis Unavailable',
          label: 'Unverified',
          color: 'text-gray-400',
          ringColor: 'text-gray-600',
          bg: 'bg-gray-900',
          border: 'border-gray-800',
          icon: <HelpCircle className="w-5 h-5 text-gray-400" />
        };
    }
  };

  const renderConfidenceScore = (score: number, status: VerificationStatus) => {
    const percentage = Math.round(score * 100);
    const meta = getStatusMeta(status);
    const circumference = 175.9; // 2 * PI * 28
    const strokeDashoffset = circumference - (circumference * score);

    return (
      <div className="flex items-center gap-4 bg-gray-900/50 p-4 rounded-xl border border-gray-800 shadow-sm">
        {/* Circular Progress Gauge */}
        <div className="relative w-16 h-16 flex items-center justify-center shrink-0">
          <svg className="w-full h-full transform -rotate-90">
            <circle
              cx="32"
              cy="32"
              r="28"
              stroke="currentColor"
              strokeWidth="4"
              fill="transparent"
              className="text-gray-800"
            />
            <circle
              cx="32"
              cy="32"
              r="28"
              stroke="currentColor"
              strokeWidth="4"
              fill="transparent"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              className={`${meta.ringColor} transition-all duration-700 ease-out`}
            />
          </svg>
          <span className="absolute text-lg font-bold text-white">
            {percentage}<span className="text-[10px] font-normal text-gray-400">%</span>
          </span>
        </div>

        {/* Right Info */}
        <div className="flex-1 min-w-0">
          <div className="text-xs text-gray-400 font-medium">Overall Reliability</div>
          <div className={`text-sm font-bold truncate ${meta.color}`}>
            {meta.title}
          </div>
          <div className="text-[11px] text-gray-500 mt-0.5">
            {meta.label}
          </div>
        </div>
      </div>
    );
  };

  return (
    <aside
      id="analysis-report-panel"
      className={`flex flex-col h-full bg-[#0c0c0e] border-l border-gray-800 text-gray-200 overflow-hidden ${className}`}
    >
      {/* Panel Header */}
      <div className="p-4 border-b border-gray-800 flex items-center justify-between">
        <h2 className="text-xs font-bold uppercase tracking-widest text-gray-400 flex items-center gap-1.5">
          <span>Analysis Report</span>
          {analysisData && analysisData.flaggedFindingsCount !== undefined && analysisData.flaggedFindingsCount > 0 && (
            <span className="px-1.5 py-0.2 rounded-full bg-red-600 text-[10px] font-bold text-white">
              {analysisData.flaggedFindingsCount}
            </span>
          )}
        </h2>

        {onClose && (
          <button
            type="button"
            id="close-analysis-panel-button"
            onClick={onClose}
            className="p-1 rounded text-gray-500 hover:text-gray-200 hover:bg-white/5 transition cursor-pointer"
            title="Close analysis panel"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Panel Content Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin">
        {/* Loading State: Step-based Pipeline Animation */}
        {isLoading && (
          <div id="analysis-loading-state" className="space-y-4">
            <div className="p-4 rounded-xl bg-gray-900/50 border border-gray-800 space-y-3">
              <div className="flex items-center gap-2 text-xs font-semibold text-blue-400">
                <Sparkles className="w-4 h-4 animate-spin" />
                <span>Cross-Referencing Claims...</span>
              </div>

              {/* Progress Steps */}
              <div className="space-y-2.5 pt-1">
                {PIPELINE_STEPS.map((step) => {
                  const isDone = currentStep > step.id;
                  const isCurrent = currentStep === step.id;
                  return (
                    <div
                      key={step.id}
                      className={`flex items-start gap-2.5 text-xs transition-opacity duration-200 ${
                        isCurrent ? 'text-blue-400 font-semibold' : isDone ? 'text-emerald-400' : 'text-gray-600'
                      }`}
                    >
                      <span className="mt-0.5 text-xs">
                        {isDone ? (
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                        ) : isCurrent ? (
                          <span className="inline-block w-3.5 h-3.5 rounded-full border-2 border-blue-400 border-t-transparent animate-spin" />
                        ) : (
                          <span className="inline-block w-3.5 h-3.5 rounded-full border border-gray-700 text-center text-[9px] leading-3 text-gray-600">
                            ○
                          </span>
                        )}
                      </span>
                      <div className="flex-1">
                        <div>{step.label}</div>
                        {isCurrent && (
                          <p className="text-[10px] text-gray-400 font-normal mt-0.5">
                            {step.detail}
                          </p>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Skeletons */}
            <div className="space-y-2 animate-pulse">
              <div className="h-16 rounded-xl bg-gray-900/40 border border-gray-800/60" />
              <div className="h-24 rounded-xl bg-gray-900/20 border border-gray-800/40" />
            </div>
          </div>
        )}

        {/* If Not Loading and No Data Available */}
        {!isLoading && (!analysisData || analysisData.status === 'analysis_unavailable') && (
          <div id="analysis-unavailable-state" className="p-6 rounded-xl bg-gray-900/40 border border-gray-800 text-center space-y-2 my-auto">
            <div className="p-3 rounded-full bg-gray-800 text-gray-400 w-12 h-12 mx-auto flex items-center justify-center">
              <Info className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-semibold text-gray-200">Analysis Unavailable</h3>
            <p className="text-xs text-gray-500 leading-relaxed max-w-xs mx-auto">
              Select or generate an AI response in the conversation to perform factual claim decomposition and confidence calibration.
            </p>
          </div>
        )}

        {/* Main Analysis Display when Data Exists */}
        {!isLoading && analysisData && analysisData.status !== 'analysis_unavailable' && (
          <div className="space-y-4">
            {/* Section 1: Overall Confidence Score */}
            {renderConfidenceScore(analysisData.confidence, analysisData.status)}

            {/* Summary sentence */}
            {analysisData.summary && (
              <div className="px-3 py-2 rounded-lg bg-gray-900/40 border border-gray-800 text-xs text-gray-300 leading-relaxed flex items-start gap-2">
                <Info className="w-3.5 h-3.5 text-blue-400 mt-0.5 shrink-0" />
                <span>{analysisData.summary}</span>
              </div>
            )}

            {/* Section 2: Hallucination Findings ONLY (Problematic content) */}
            {analysisData.findings && analysisData.findings.length > 0 ? (
              <div className="space-y-2.5">
                <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-wider text-gray-500 px-1">
                  <span>Flagged Findings ({analysisData.findings.length})</span>
                  <span className="text-red-400 font-normal">
                    Requires Review
                  </span>
                </div>

                <div className="space-y-2.5">
                  {analysisData.findings.map((finding) => {
                    const isExpanded = expandedFindingId === finding.id;
                    const isContradiction = finding.status === 'contradicted';
                    const isUnsupported = finding.status === 'unsupported';

                    return (
                      <div
                        key={finding.id}
                        id={`finding-card-${finding.id}`}
                        className={`rounded-xl border transition-all duration-150 overflow-hidden shadow-sm ${
                          isContradiction
                            ? 'bg-red-950/20 border-red-900/50 hover:border-red-700/60'
                            : isUnsupported
                            ? 'bg-amber-950/20 border-amber-900/50 hover:border-amber-700/60'
                            : 'bg-gray-900/60 border-gray-800 hover:border-gray-700'
                        }`}
                      >
                        {/* Header Banner */}
                        <button
                          type="button"
                          onClick={() => toggleExpand(finding.id)}
                          className="w-full text-left p-3 flex items-start justify-between gap-2.5 cursor-pointer"
                        >
                          <div className="flex items-start gap-2.5">
                            <span className="mt-0.5 shrink-0">
                              {isContradiction ? (
                                <XCircle className="w-4 h-4 text-red-500" />
                              ) : isUnsupported ? (
                                <AlertTriangle className="w-4 h-4 text-amber-500" />
                              ) : (
                                <Info className="w-4 h-4 text-blue-400" />
                              )}
                            </span>
                            <div>
                              <div className="flex items-center gap-2">
                                <span className={`text-xs font-bold ${
                                  isContradiction ? 'text-red-400' : isUnsupported ? 'text-amber-400' : 'text-blue-400'
                                }`}>
                                  {isContradiction ? 'Critical Finding' : isUnsupported ? 'Unverified Claim' : 'Low Confidence'}
                                </span>
                                <span className="text-[10px] px-1.5 py-0.2 rounded bg-black/40 border border-gray-800 text-gray-300 font-mono">
                                  {Math.round(finding.confidence * 100)}% conf
                                </span>
                              </div>
                              <p className="text-[11px] text-gray-300 mt-1 leading-snug line-clamp-2">
                                "{finding.claim}"
                              </p>
                            </div>
                          </div>

                          <span className="text-gray-500 mt-1 shrink-0">
                            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                          </span>
                        </button>

                        {/* Collapsible Expanded Details */}
                        {isExpanded && (
                          <div className="px-3 pb-3 pt-1 border-t border-red-900/30 space-y-2.5 text-xs text-gray-300 bg-black/30">
                            {/* Verification Status */}
                            <div className="flex items-center justify-between pt-1">
                              <span className="text-gray-500 text-[11px]">Verification Status:</span>
                              <span className={`font-semibold capitalize px-2 py-0.5 rounded text-[10px] ${
                                isContradiction ? 'bg-red-500/20 text-red-300 border border-red-500/30' : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                              }`}>
                                {finding.status}
                              </span>
                            </div>

                            {/* Reason */}
                            <div>
                              <span className="text-gray-500 text-[10px] font-bold uppercase tracking-wider block mb-1">
                                Reason for Flagging:
                              </span>
                              <p className="text-gray-300 bg-black/40 p-2.5 rounded border border-red-900/20 text-[11px] leading-relaxed">
                                {finding.reason}
                              </p>
                            </div>

                            {/* Evidence Snippet */}
                            {finding.evidence && (
                              <div>
                                <span className="text-gray-500 text-[10px] font-bold uppercase tracking-wider block mb-1">
                                  Retrieved Evidence:
                                </span>
                                <div className="p-2.5 rounded bg-black/40 border border-gray-800 text-gray-400 italic leading-relaxed text-[11px]">
                                  "{finding.evidence}"
                                </div>
                              </div>
                            )}

                            {/* Source Citation */}
                            {finding.source && (
                              <div className="pt-1 flex items-center justify-between border-t border-gray-800/80 text-[11px]">
                                <span className="text-gray-500">Source:</span>
                                <a
                                  href={finding.source.url}
                                  target="_blank"
                                  rel="noreferrer noopener"
                                  className="text-blue-400 hover:text-blue-300 font-semibold underline underline-offset-2 flex items-center gap-1"
                                >
                                  <span className="truncate max-w-[170px]">{finding.source.title}</span>
                                  <ExternalLink className="w-3 h-3 shrink-0" />
                                </a>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              /* Section 3: No Hallucination State (Clean, no long list of verified claims) */
              <div id="no-hallucinations-state" className="p-4 rounded-xl bg-gray-900/40 border border-emerald-500/30 text-center space-y-2">
                <div className="w-10 h-10 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 flex items-center justify-center mx-auto">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
                <h3 className="text-sm font-bold text-emerald-400">
                  No Hallucinations Detected
                </h3>
                <p className="text-xs text-gray-400 leading-relaxed max-w-xs mx-auto">
                  The analyzed claims were cross-referenced and verified against retrieved evidence.
                </p>
                <div className="pt-2 flex items-center justify-center gap-3 text-[11px] text-gray-500">
                  <span className="font-semibold text-emerald-400">Status: Highly Reliable</span>
                  <span>•</span>
                  <span>Confidence: {Math.round(analysisData.confidence * 100)}%</span>
                </div>
              </div>
            )}

            {/* Meta statistics footer */}
            <div className="pt-3 border-t border-gray-800 text-[11px] text-gray-500 space-y-1">
              <div className="flex items-center justify-between">
                <span>Evaluated model:</span>
                <span className="font-semibold text-gray-400">{analysisData.modelUsed || 'Default'}</span>
              </div>
              {analysisData.latencyMs && (
                <div className="flex items-center justify-between">
                  <span>Verification latency:</span>
                  <span className="font-mono text-gray-400">{analysisData.latencyMs}ms</span>
                </div>
              )}
              {analysisData.analyzedAt && (
                <div className="flex items-center justify-between">
                  <span>Timestamp:</span>
                  <span className="text-gray-400">{analysisData.analyzedAt}</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Footer Info */}
      <div className="p-3 text-center text-[10px] text-gray-500 border-t border-gray-900/80 shrink-0">
        Confidence scores derived from cross-reference between WebSearch, ArXiv, and Knowledge bases.
      </div>
    </aside>
  );
};
