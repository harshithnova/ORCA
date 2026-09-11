/**
 * RecommendationCard Component
 * Premium card displaying recommendation with scores, status, and key factors
 */

import React from 'react';
import { ReasonResponse, StatusType } from '@/types';
import {
  getSuitabilityLevel,
  getRiskLevel,
  formatConfidence,
  formatTimeWindow,
} from '@/utils/scoring';

interface RecommendationCardProps {
  response: ReasonResponse;
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({ response }) => {
  const { status, recommendation, location, requested_time } = response;

  const getStatusConfig = (status: StatusType) => {
    const configs: Record<StatusType, { icon: string; label: string; color: string; bg: string }> = {
      'SAFE': { icon: '✓', label: 'Safe to Proceed', color: 'from-green-400 to-emerald-600', bg: 'bg-green-500/10' },
      'CAUTION': { icon: '⚠', label: 'Proceed with Caution', color: 'from-amber-400 to-orange-600', bg: 'bg-amber-500/10' },
      'BLOCK': { icon: '✕', label: 'Do Not Proceed', color: 'from-red-400 to-red-600', bg: 'bg-red-500/10' },
      'NO_SAFE_RECOMMENDATION': { icon: '?', label: 'Insufficient Data', color: 'from-gray-400 to-gray-600', bg: 'bg-gray-500/10' },
    };
    return configs[status];
  };

  const statusConfig = getStatusConfig(status);
  const suitabilityLevel = getSuitabilityLevel(recommendation.suitability_score);
  const riskLevel = getRiskLevel(recommendation.risk_score);

  return (
    <div className="premium-card zone-analysis-card">
      {/* Header with Status */}
      <div className="card-header">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h2 className="text-4xl font-bold text-white mb-1">{location.name}</h2>
            <p className="text-cyan-300 text-sm">
              {location.latitude.toFixed(2)}° N, {location.longitude.toFixed(2)}° E
            </p>
          </div>
          <div className={`status-badge ${statusConfig.bg}`}>
            <div className={`bg-gradient-to-r ${statusConfig.color} text-white px-4 py-3 rounded-full font-bold text-lg`}>
              {statusConfig.icon}
            </div>
            <p className={`text-sm font-semibold text-white mt-2`}>{statusConfig.label}</p>
          </div>
        </div>

        {/* Zone Info */}
        <div className="grid grid-cols-3 gap-4 pb-6 border-b border-white/10">
          <div>
            <p className="text-cyan-300 text-xs uppercase tracking-widest mb-1">Zone ID</p>
            <p className="text-white text-lg font-bold">{recommendation.zone_id}</p>
          </div>
          <div>
            <p className="text-cyan-300 text-xs uppercase tracking-widest mb-1">Time Window</p>
            <p className="text-white text-sm">{formatTimeWindow(requested_time.valid_from, requested_time.valid_to)}</p>
          </div>
          <div>
            <p className="text-cyan-300 text-xs uppercase tracking-widest mb-1">Data Confidence</p>
            <p className="text-white text-lg font-bold">{formatConfidence(recommendation.confidence_score)}</p>
          </div>
        </div>
      </div>

      {/* Score Section */}
      <div className="card-scores">
        {/* Suitability Score */}
        <div className="score-item">
          <div className="flex items-baseline justify-between mb-3">
            <label className="text-cyan-300 font-semibold">Suitability for Fishing</label>
            <div className="flex items-baseline gap-2">
              <span className="text-4xl font-bold text-green-400">{recommendation.suitability_score}</span>
              <span className="text-sm text-white">/100</span>
            </div>
          </div>
          <div className="score-bar">
            <div 
              className="score-fill bg-gradient-to-r from-green-400 to-emerald-600"
              style={{ width: `${recommendation.suitability_score}%` }}
            />
          </div>
          <p className="text-xs text-blue-300 mt-2">{suitabilityLevel} – Production potential is strong</p>
        </div>

        {/* Risk Score */}
        <div className="score-item">
          <div className="flex items-baseline justify-between mb-3">
            <label className="text-cyan-300 font-semibold">Safety Risk Level</label>
            <div className="flex items-baseline gap-2">
              <span className="text-4xl font-bold text-red-400">{recommendation.risk_score}</span>
              <span className="text-sm text-white">/100</span>
            </div>
          </div>
          <div className="score-bar">
            <div 
              className="score-fill bg-gradient-to-r from-red-500 to-red-600"
              style={{ width: `${recommendation.risk_score}%` }}
            />
          </div>
          <p className="text-xs text-blue-300 mt-2">{riskLevel} – {recommendation.risk_score < 40 ? 'Safe conditions' : recommendation.risk_score < 70 ? 'Monitor conditions' : 'High risk'}</p>
        </div>
      </div>

      {/* Why This Zone Section */}
      <div className="card-why-this mt-6 pt-6 border-t border-white/10">
        <h3 className="text-cyan-300 font-bold text-sm uppercase tracking-widest mb-3">Why This Zone?</h3>
        <p className="text-white leading-relaxed">{recommendation.reason}</p>
      </div>

      {/* Key Factors */}
      <div className="card-factors mt-6 pt-6 border-t border-white/10">
        <h3 className="text-cyan-300 font-bold text-sm uppercase tracking-widest mb-4">Key Factors</h3>
        <div className="grid grid-cols-2 gap-3">
          <div className="factor-badge">
            <span className="text-cyan-400">🌊</span>
            <span className="text-white text-sm">Optimal Wave Conditions</span>
          </div>
          <div className="factor-badge">
            <span className="text-cyan-400">☀️</span>
            <span className="text-white text-sm">Favorable Weather</span>
          </div>
          <div className="factor-badge">
            <span className="text-cyan-400">🎣</span>
            <span className="text-white text-sm">High Fish Activity</span>
          </div>
          <div className="factor-badge">
            <span className="text-cyan-400">🛡️</span>
            <span className="text-white text-sm">Safe Depth & Current</span>
          </div>
        </div>
      </div>
    </div>
  );
};
