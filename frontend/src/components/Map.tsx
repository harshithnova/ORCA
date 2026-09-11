/**
 * Map Component
 * Premium Leaflet map with ocean styling, enhanced markers and animations
 */

import React, { useEffect, useRef, useState } from 'react';
import * as L from 'leaflet';
import { CandidateZone, ReasonResponse } from '@/types';
import { getRiskLevel } from '@/utils/scoring';

interface MapProps {
  response?: ReasonResponse;
  selectedZoneId?: string;
  onZoneSelect: (zoneId: string) => void;
  candidates?: CandidateZone[];
}

const getMarkerColor = (score: number): string => {
  // Green = Suitable (0-40), Amber = Moderate (41-70), Red = Unsafe (71-100)
  // This is based on risk score, so inverted for suitability
  if (score <= 30) return '#dc2626'; // Red - Unsafe
  if (score <= 60) return '#f59e0b'; // Amber - Moderate
  return '#10b981'; // Green - Suitable
};

export const Map: React.FC<MapProps> = ({ response, selectedZoneId, onZoneSelect, candidates = [] }) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<L.Map | null>(null);
  const markersRef = useRef<Map<string, L.Marker>>(new Map());

  useEffect(() => {
    if (!mapContainer.current) return;

    // Initialize map with ocean-themed styling
    if (!map.current) {
      map.current = L.map(mapContainer.current, {
        zoomControl: true,
        attributionControl: true,
      }).setView([20, 75], 4);

      // Use ocean-themed tiles (CartoDB Positron)
      L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '© OpenStreetMap, © CartoDB',
        maxZoom: 19,
        className: 'ocean-tiles',
      }).addTo(map.current);

      // Add a dark ocean overlay for evening effect
      const canvas = document.createElement('canvas');
      canvas.width = 2;
      canvas.height = 2;
      const ctx = canvas.getContext('2d')!;
      ctx.fillStyle = 'rgba(15, 23, 42, 0.05)'; // Very subtle dark overlay
      ctx.fillRect(0, 0, 2, 2);
      
      L.tileLayer(canvas.toDataURL(), {
        attribution: '',
        maxZoom: 19,
      }).addTo(map.current);
    }

    // Clear existing markers
    markersRef.current.forEach((marker) => marker.remove());
    markersRef.current.clear();

    // Add recommendation marker if available
    if (response?.recommendation && response?.location) {
      const { latitude, longitude } = response.location;
      const color = getMarkerColor(response.recommendation.risk_score);

      const markerIcon = new L.DivIcon({
        html: `
          <div class="marker-recommended">
            <div class="marker-glow" style="background-color: ${color}"></div>
            <div class="marker-core" style="background-color: ${color}; border-color: white;">
              ★
            </div>
          </div>
        `,
        iconSize: [45, 45],
        iconAnchor: [22.5, 45],
        popupAnchor: [0, -45],
        className: 'marker-custom',
      });

      const marker = L.marker([latitude, longitude], { icon: markerIcon })
        .bindPopup(`
          <div class="map-popup p-3 rounded-lg">
            <p class="font-bold text-gray-900">${response.location.name}</p>
            <p class="text-xs text-gray-600 mb-2">Recommended Zone</p>
            <div class="text-sm">
              <p class="text-gray-700"><strong>Suitability:</strong> ${response.recommendation.suitability_score}%</p>
              <p class="text-gray-700"><strong>Risk:</strong> ${response.recommendation.risk_score}%</p>
            </div>
          </div>
        `)
        .addTo(map.current!);

      markersRef.current.set(response.location.name, marker);
      map.current!.setView([latitude, longitude], 8);
    }

    // Add candidate zone markers
    candidates.forEach((zone) => {
      const color = getMarkerColor(zone.risk_score || 50);
      const isSelected = selectedZoneId === zone.id;

      const markerIcon = new L.DivIcon({
        html: `
          <div class="marker-candidate ${isSelected ? 'selected' : ''}">
            <div class="marker-glow" style="background-color: ${color}"></div>
            <div class="marker-core" style="background-color: ${color}; border-color: white;">
              ${isSelected ? '◆' : '●'}
            </div>
          </div>
        `,
        iconSize: [40, 40],
        iconAnchor: [20, 40],
        popupAnchor: [0, -40],
        className: 'marker-custom',
      });

      const marker = L.marker([zone.latitude, zone.longitude], { icon: markerIcon })
        .bindPopup(`
          <div class="map-popup p-3 rounded-lg">
            <p class="font-bold text-gray-900">${zone.name}</p>
            <p class="text-xs text-gray-600 mb-2">${zone.region}</p>
            <div class="text-sm">
              ${
                zone.suitability_score !== undefined
                  ? `<p class="text-gray-700"><strong>Suitability:</strong> ${zone.suitability_score}%</p>`
                  : ''
              }
              ${
                zone.risk_score !== undefined
                  ? `<p class="text-gray-700"><strong>Risk:</strong> ${zone.risk_score}%</p>`
                  : ''
              }
            </div>
          </div>
        `)
        .on('click', () => onZoneSelect(zone.id))
        .addTo(map.current!);

      markersRef.current.set(zone.id, marker);
    });
  }, [response, candidates, selectedZoneId, onZoneSelect]);

  return (
    <div className="premium-map-container">
      <div className="map-header">
        <h2 className="map-title">Marine Intelligence Map</h2>
        <div className="map-legend">
          <div className="legend-item">
            <div className="legend-dot" style={{ backgroundColor: '#10b981' }}></div>
            <span>Suitable</span>
          </div>
          <div className="legend-item">
            <div className="legend-dot" style={{ backgroundColor: '#f59e0b' }}></div>
            <span>Moderate</span>
          </div>
          <div className="legend-item">
            <div className="legend-dot" style={{ backgroundColor: '#dc2626' }}></div>
            <span>Unsafe</span>
          </div>
        </div>
      </div>
      <div
        ref={mapContainer}
        className="premium-map"
      />
    </div>
  );
};
