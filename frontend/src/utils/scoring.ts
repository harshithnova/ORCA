/**
 * ORCA Utility Functions
 * Helper functions for scoring, colors, and data transformation
 */

import { RiskLevel, SuitabilityLevel, StatusType } from '@/types';

/**
 * Get suitability level from score (0-100)
 */
export function getSuitabilityLevel(score: number): SuitabilityLevel {
  if (score <= 20) return 'POOR';
  if (score <= 40) return 'FAIR';
  if (score <= 60) return 'GOOD';
  if (score <= 80) return 'VERY GOOD';
  return 'EXCELLENT';
}

/**
 * Get risk level from score (0-100)
 */
export function getRiskLevel(score: number): RiskLevel {
  if (score <= 20) return 'LOW';
  if (score <= 40) return 'MODERATE';
  if (score <= 60) return 'ELEVATED';
  if (score <= 80) return 'HIGH';
  return 'SEVERE';
}

/**
 * Get color for suitability score
 */
export function getSuitabilityColor(score: number): string {
  const level = getSuitabilityLevel(score);
  const colors: Record<SuitabilityLevel, string> = {
    'POOR': '#dc2626', // red
    'FAIR': '#f97316', // orange
    'GOOD': '#eab308', // yellow
    'VERY GOOD': '#84cc16', // lime
    'EXCELLENT': '#22c55e', // green
  };
  return colors[level];
}

/**
 * Get color for risk score
 */
export function getRiskColor(score: number): string {
  const level = getRiskLevel(score);
  const colors: Record<RiskLevel, string> = {
    'LOW': '#22c55e', // green
    'MODERATE': '#84cc16', // lime
    'ELEVATED': '#eab308', // yellow
    'HIGH': '#f97316', // orange
    'SEVERE': '#dc2626', // red
  };
  return colors[level];
}

/**
 * Get color for status
 */
export function getStatusColor(status: StatusType): string {
  const colors: Record<StatusType, string> = {
    'SAFE': '#22c55e', // green
    'CAUTION': '#f97316', // orange
    'BLOCK': '#dc2626', // red
    'NO_SAFE_RECOMMENDATION': '#6b7280', // gray
  };
  return colors[status];
}

/**
 * Get icon for marker based on suitability
 */
export function getMarkerIcon(score: number) {
  const color = getSuitabilityColor(score);
  return `
    <svg width="32" height="40" viewBox="0 0 32 40" fill="none">
      <path d="M16 0C7.16 0 0 7.16 0 16c0 10 16 24 16 24s16-14 16-24c0-8.84-7.16-16-16-16z" fill="${color}"/>
    </svg>
  `;
}

/**
 * Format confidence as percentage
 */
export function formatConfidence(confidence: number): string {
  return `${(confidence * 100).toFixed(1)}%`;
}

/**
 * Format date to readable string
 */
export function formatDate(date: string): string {
  return new Date(date).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Format time window
 */
export function formatTimeWindow(from: string, to: string): string {
  const fromDate = new Date(from);
  const toDate = new Date(to);
  const fromTime = fromDate.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  const toTime = toDate.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  return `${fromTime} - ${toTime}`;
}

/**
 * Calculate distance between two coordinates (km)
 */
export function calculateDistance(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
): number {
  const R = 6371; // Earth's radius in km
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}
