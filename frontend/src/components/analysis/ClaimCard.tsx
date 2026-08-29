import React, { useState } from 'react';
import type { Claim } from '@/types';
import { ChevronDown, ChevronUp, Slash } from 'lucide-react';

type ClaimCardProps = {
  claim: Claim;
};

export const ClaimCard: React.FC<ClaimCardProps> = ({ claim }) => {
  const [expanded, setExpanded] = useState(false);
  const toggle = () => setExpanded((prev) => !prev);

  const confidenceColor =
    claim.confidenceScore >= 0.75
      ? 'text-green-400'
      : claim.confidenceScore >= 0.5
      ? 'text-yellow-400'
      : 'text-red-400';

  return (
    <div className="border border-gray-700 rounded-md mb-2 bg-gray-800/60">
      <button
        onClick={toggle}
        className="w-full flex items-center justify-between p-3 focus:outline-none"
      >
        <div className="flex items-center space-x-2">
          <span className={`font-medium ${confidenceColor}`}>Confidence: {(claim.confidenceScore * 100).toFixed(0)}%</span>
          <span className="text-sm text-gray-300">{claim.text}</span>
        </div>
        {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </button>
      {expanded && (
        <div className="p-3 border-t border-gray-700">
          {claim.evidence.length === 0 ? (
            <p className="text-xs text-gray-500 flex items-center">
              <Slash size={12} className="mr-1" /> No evidence found
            </p>
          ) : (
            <ul className="space-y-2">
              {claim.evidence.map((ev) => (
                <li key={ev.id} className="text-xs border border-gray-600 rounded p-2">
                  <a href={ev.url} target="_blank" rel="noopener noreferrer" className="underline text-accentBlue">
                    {ev.title}
                  </a>
                  <p className="text-gray-400 mt-1">{ev.snippet}</p>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
};
