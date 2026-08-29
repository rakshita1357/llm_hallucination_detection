import React from 'react';
import type { AnalysisReport } from '@/types';
import { ClaimCard } from '@/components/analysis/ClaimCard';
import { AlertCircle, CheckCircle, ShieldCheck } from 'lucide-react';

type Props = {
  analysis: AnalysisReport | null;
  isLoading: boolean;
};

export const AnalysisPanel: React.FC<Props> = ({ analysis, isLoading }) => {
  const riskColor =
    analysis?.riskLevel === 'HIGH'
      ? 'bg-red-700 text-red-100'
      : analysis?.riskLevel === 'MEDIUM'
      ? 'bg-yellow-700 text-yellow-100'
      : 'bg-green-700 text-green-100';

  return (
    <aside className="flex flex-col overflow-y-auto p-4 bg-white dark:bg-gray-900 border-l border-gray-300 dark:border-gray-800">
      <h2 className="text-lg font-semibold mb-4 text-gray-200">Analysis Report</h2>
      {isLoading && (
        <div className="flex items-center justify-center h-full">
          <p className="text-gray-400">Generating analysis…</p>
        </div>
      )}
      {analysis && (
        <div className="space-y-4">
          <div className={`p-3 rounded ${riskColor} shadow-md`}> {/* Risk indicator */}
            <div className="flex items-center space-x-2">
              <AlertCircle size={20} />
              <span className="font-medium">Overall Risk: {analysis.riskLevel}</span>
            </div>
            <p className="mt-1 text-sm">Risk Score: {analysis.riskScore}%</p>
          </div>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="p-2 bg-gray-800 rounded">
              <p className="text-gray-400">Claims</p>
              <p className="font-medium text-gray-200">{analysis.totalClaims}</p>
            </div>
            <div className="p-2 bg-gray-800 rounded">
              <p className="text-gray-400">Supported</p>
              <p className="font-medium text-gray-200">{analysis.supportedClaims}</p>
            </div>
            <div className="p-2 bg-gray-800 rounded">
              <p className="text-gray-400">Uncertain</p>
              <p className="font-medium text-gray-200">{analysis.uncertainClaims}</p>
            </div>
            <div className="p-2 bg-gray-800 rounded">
              <p className="text-gray-400">Contradicted</p>
              <p className="font-medium text-gray-200">{analysis.contradictedClaims}</p>
            </div>
          </div>
          <div>
            <h3 className="text-md font-medium mb-2 text-gray-300">Claims</h3>
            {analysis.claims.map((claim) => (
              <ClaimCard key={claim.id} claim={claim} />
            ))}
          </div>
        </div>
      )}
      {!analysis && !isLoading && (
        <p className="text-gray-500 text-center mt-8">No analysis yet – send a message to see results.</p>
      )}
    </aside>
  );
};
