/**
 * ORCA Frontend Types
 * Matches API_CONTRACT.md and DATA_CONTRACT.md
 */

export type StatusType = 'SAFE' | 'CAUTION' | 'BLOCK' | 'NO_SAFE_RECOMMENDATION';
export type DataMode = 'CACHED_OFFICIAL' | 'SIMULATED_MVP';
export type DataType = 'OBSERVATION' | 'FORECAST' | 'WARNING' | 'REFERENCE';
export type RiskLevel = 'LOW' | 'MODERATE' | 'ELEVATED' | 'HIGH' | 'SEVERE';
export type SuitabilityLevel = 'POOR' | 'FAIR' | 'GOOD' | 'VERY GOOD' | 'EXCELLENT';

export interface Location {
  name: string;
  latitude: number;
  longitude: number;
}

export interface TimeWindow {
  valid_from: string;
  valid_to: string;
}

export interface Recommendation {
  zone_id: string;
  suitability_score: number;
  risk_score: number;
  confidence_score: number;
  reason: string;
}

export interface Evidence {
  source: string;
  source_url?: string;
  parameter: string;
  value: string | number;
  unit?: string;
  valid_from?: string;
  valid_to?: string;
  data_type?: DataType;
  data_mode?: DataMode;
}

export interface MapData {
  geojson?: any;
}

export interface ReasonResponse {
  status: StatusType;
  query: string;
  location: Location;
  requested_time: TimeWindow;
  recommendation: Recommendation;
  evidence: Evidence[];
  map: MapData;
}

export interface CandidateZone {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  geometry?: any;
  region: string;
  active: boolean;
  suitability_score?: number;
  risk_score?: number;
  confidence_score?: number;
}

export interface MarineRecord {
  latitude: number;
  longitude: number;
  issued_at: string;
  valid_from: string;
  valid_to: string;
  wave_height_m?: number;
  wave_period_s?: number;
  wind_speed_ms?: number;
  wind_direction_deg?: number;
  current_speed_ms?: number;
  current_direction_deg?: number;
  sst_c?: number;
  chlorophyll_mg_m3?: number;
  source: string;
  data_mode: DataMode;
  data_type: DataType;
}

export interface WeatherRecord {
  latitude: number;
  longitude: number;
  issued_at: string;
  valid_from: string;
  valid_to: string;
  wind_speed_ms?: number;
  wind_direction_deg?: number;
  rainfall_mm?: number;
  visibility_km?: number;
  weather_condition?: string;
  warning_level?: string;
  source: string;
  data_mode: DataMode;
  data_type: DataType;
}

export interface UIState {
  selectedZoneId?: string;
  loading: boolean;
  error?: string;
  response?: ReasonResponse;
}
