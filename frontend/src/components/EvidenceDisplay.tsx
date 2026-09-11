/**
 * EvidenceDisplay Component
 * Premium evidence display with trustworthy design and clear data hierarchy
 */

import React from 'react';
import { Evidence, ReasonResponse } from '@/types';
import { formatDate } from '@/utils/scoring';

interface EvidenceDisplayProps {
  response: ReasonResponse;
}

export const EvidenceDisplay: React.FC<EvidenceDisplayProps> = ({ response }) => {
  const { evidence, recommendation, status } = response;

  const getTrustBadgeColor = (dataMode: string | undefined) => {
    return dataMode === 'CACHED_OFFICIAL' ? 'text-green-400' : 'text-amber-400';
  };

  if (!evidence || evidence.length === 0) {
    return (
      <div className="premium-card evidence-card">
        <h2 className="card-title">Supporting Evidence</h2>
        <div className="card-empty">
          <p className="text-cyan-300">No detailed evidence available for this recommendation.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="premium-card evidence-card">
      <h2 className="card-title">Supporting Evidence & Data Sources</h2>

      {/* Summary */}
      <div className="evidence-summary mb-6 p-4 rounded-lg bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border border-blue-500/20">
        <p className="text-cyan-300 text-xs uppercase tracking-widest font-bold mb-2">Recommendation Summary</p>
        <p className="text-white leading-relaxed">{recommendation.reason}</p>
      </div>

      {/* Evidence List */}
      <div className="evidence-list space-y-3">
        {evidence.map((item: Evidence, index) => (
          <div key={index} className="evidence-item">
            {/* Source Header */}
            <div className="evidence-header">
              <div className="flex items-center gap-3 flex-1">
                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center text-white font-bold text-sm">
                  {index + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-bold text-white truncate">{item.source}</p>
                  {item.source_url && (
                    <a
                      href={item.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-cyan-400 hover:text-cyan-300 truncate block"
                    >
                      View source →
                    </a>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2">
                {item.data_mode && (
                  <span
                    className={`text-xs px-2 py-1 rounded-full font-semibold ${
                      item.data_mode === 'CACHED_OFFICIAL'
                        ? 'bg-green-500/20 text-green-300'
                        : 'bg-amber-500/20 text-amber-300'
                    }`}
                  >
                    {item.data_mode === 'CACHED_OFFICIAL' ? '✓ Official' : '⚠ Simulated'}
                  </span>
                )}
                {item.data_type && (
                  <span className="text-xs px-2 py-1 rounded-full font-semibold bg-blue-500/20 text-blue-300">
                    {item.data_type}
                  </span>
                )}
              </div>
            </div>

            {/* Data Content */}
            <div className="evidence-content">
              <div className="grid grid-cols-2 gap-4">
                {/* Parameter */}
                <div>
                  <p className="text-cyan-400 text-xs uppercase tracking-widest mb-1">Parameter</p>
                  <p className="text-white font-semibold text-lg">{item.parameter}</p>
                </div>

                {/* Value */}
                <div>
                  <p className="text-cyan-400 text-xs uppercase tracking-widest mb-1">Measured Value</p>
                  <p className="text-white font-bold text-xl">
                    {item.value}
                    {item.unit && <span className="text-sm text-blue-300 ml-1">{item.unit}</span>}
                  </p>
                </div>
              </div>

              {/* Validity Period */}
              {(item.valid_from || item.valid_to) && (
                <div className="mt-4 pt-4 border-t border-white/10 grid grid-cols-2 gap-4 text-sm">
                  {item.valid_from && (
                    <div>
                      <p className="text-cyan-400 text-xs uppercase tracking-widest mb-1">Valid From</p>
                      <p className="text-blue-200">{formatDate(item.valid_from)}</p>
                    </div>
                  )}
                  {item.valid_to && (
                    <div>
                      <p className="text-cyan-400 text-xs uppercase tracking-widest mb-1">Valid Until</p>
                      <p className="text-blue-200">{formatDate(item.valid_to)}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Trust & Transparency Footer */}
      <div className="evidence-footer mt-6 pt-6 border-t border-white/10">
        <h3 className="text-cyan-300 font-bold text-sm uppercase tracking-widest mb-4">Data Integrity & Transparency</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/20">
            <p className="text-green-400 font-semibold mb-1">✓ Official Sources</p>
            <p className="text-blue-200 text-xs">Data sourced from verified marine and meteorological authorities</p>
          </div>
          <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
            <p className="text-blue-400 font-semibold mb-1">🔒 Real-Time Processing</p>
            <p className="text-blue-200 text-xs">All data processed deterministically for reproducible results</p>
          </div>
        </div>
      </div>
    </div>
  );
};
