/**
 * CandidateZonesPanel Component
 * Displays alternative candidate zones
 */

import React from 'react';
import { CandidateZone } from '@/types';
import {
  getSuitabilityLevel,
  getRiskLevel,
  getSuitabilityColor,
  getRiskColor,
} from '@/utils/scoring';

interface CandidateZonesPanelProps {
  candidates: CandidateZone[];
  selectedZoneId?: string;
  onZoneSelect: (zoneId: string) => void;
  loading?: boolean;
}

export const CandidateZonesPanel: React.FC<CandidateZonesPanelProps> = ({
  candidates,
  selectedZoneId,
  onZoneSelect,
  loading = false,
}) => {
  if (candidates.length === 0) {
    return null;
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">
        Alternative Zones ({candidates.length})
      </h2>

      <div className="space-y-3 max-h-96 overflow-y-auto">
        {candidates.map((zone) => {
          const isSelected = selectedZoneId === zone.id;
          const suitColor =
            zone.suitability_score !== undefined
              ? getSuitabilityColor(zone.suitability_score)
              : '#9ca3af';
          const riskColor =
            zone.risk_score !== undefined
              ? getRiskColor(zone.risk_score)
              : '#9ca3af';

          return (
            <div
              key={zone.id}
              onClick={() => !loading && onZoneSelect(zone.id)}
              className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                isSelected
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 bg-white hover:border-gray-300'
              } ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <div className="flex justify-between items-start mb-2">
                <div>
                  <p className="font-bold text-gray-900">{zone.name}</p>
                  <p className="text-sm text-gray-600">{zone.region}</p>
                </div>
                {zone.active && (
                  <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">
                    Active
                  </span>
                )}
              </div>

              <div className="grid grid-cols-3 gap-2 text-sm mb-2">
                <div>
                  <p className="text-gray-600">Location</p>
                  <p className="font-semibold text-gray-900 text-xs">
                    {zone.latitude.toFixed(2)}°, {zone.longitude.toFixed(2)}°
                  </p>
                </div>
                {zone.suitability_score !== undefined && (
                  <div>
                    <p className="text-gray-600">Suitability</p>
                    <div className="flex items-center gap-1">
                      <span
                        style={{ color: suitColor }}
                        className="font-bold"
                      >
                        {zone.suitability_score}%
                      </span>
                      <span
                        style={{ backgroundColor: suitColor, color: 'white' }}
                        className="text-xs px-1 py-0.5 rounded"
                      >
                        {getSuitabilityLevel(zone.suitability_score)}
                      </span>
                    </div>
                  </div>
                )}
                {zone.risk_score !== undefined && (
                  <div>
                    <p className="text-gray-600">Risk</p>
                    <div className="flex items-center gap-1">
                      <span
                        style={{ color: riskColor }}
                        className="font-bold"
                      >
                        {zone.risk_score}%
                      </span>
                      <span
                        style={{ backgroundColor: riskColor, color: 'white' }}
                        className="text-xs px-1 py-0.5 rounded"
                      >
                        {getRiskLevel(zone.risk_score)}
                      </span>
                    </div>
                  </div>
                )}
              </div>

              {zone.confidence_score !== undefined && (
                <div className="text-xs text-gray-600">
                  Confidence: {(zone.confidence_score * 100).toFixed(1)}%
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
