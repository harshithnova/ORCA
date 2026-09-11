/**
 * App Component
 * Main application component that coordinates all features
 */

import React, { useState, useCallback } from 'react';
import { ReasonResponse, CandidateZone, UIState } from '@/types';
import { LandingPage, QueryInput, Map, RecommendationCard, EvidenceDisplay, CandidateZonesPanel } from '@/components';
import orcaApi from '@/services/api';

export const App: React.FC = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [uiState, setUiState] = useState<UIState>({
    loading: false,
  });

  const [candidates, setCandidates] = useState<CandidateZone[]>([]);

  const handleLogin = useCallback(() => {
    setIsAuthenticated(true);
  }, []);

  // Handle query submission
  const handleQuerySubmit = useCallback(async (query: string) => {
    setUiState({ loading: true, error: undefined });

    try {
      const response = await orcaApi.reason(query);
      setUiState({
        loading: false,
        response,
        selectedZoneId: response.recommendation.zone_id,
      });

      // In a real scenario, the backend would return candidate zones
      // For now, we'll create a candidate from the recommendation
      const recommendedZone: CandidateZone = {
        id: response.recommendation.zone_id,
        name: response.location.name,
        latitude: response.location.latitude,
        longitude: response.location.longitude,
        region: response.location.name,
        active: true,
        suitability_score: response.recommendation.suitability_score,
        risk_score: response.recommendation.risk_score,
        confidence_score: response.recommendation.confidence_score,
      };

      setCandidates([recommendedZone]);
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Failed to get recommendation. Please try again.';
      setUiState({
        loading: false,
        error: errorMessage,
      });
    }
  }, []);

  const handleZoneSelect = useCallback((zoneId: string) => {
    setUiState((prev) => ({
      ...prev,
      selectedZoneId: zoneId,
    }));
  }, []);

  if (!isAuthenticated) {
    return <LandingPage onLogin={handleLogin} />;
  }

  return (
    <div className="dashboard-container">
      {/* Dashboard Background */}
      <div className="dashboard-background">
        <div className="background-gradient" />
        <div className="background-particles">
          {[...Array(30)].map((_, i) => (
            <div
              key={i}
              className="particle"
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
                animationDelay: `${i * 0.1}s`,
                animationDuration: `${5 + Math.random() * 5}s`,
              }}
            />
          ))}
        </div>
      </div>

      {/* Header */}
      <header className="dashboard-header">
        <div className="header-content max-w-7xl mx-auto px-6">
          <div className="flex items-center justify-between">
            <div className="logo-section">
              <div className="logo-icon">🌊</div>
              <h1 className="logo-text">ORCA</h1>
              <p className="logo-subtitle">Marine Intelligence Command Center</p>
            </div>
            <button
              onClick={() => setIsAuthenticated(false)}
              className="btn-logout"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="dashboard-main">
        <div className="content-max-width">
          {/* Top Section - Query Input */}
          <div className="query-section">
            <QueryInput
              onSubmit={handleQuerySubmit}
              isLoading={uiState.loading}
              error={uiState.error}
            />
          </div>

          {/* Results Grid */}
          {uiState.response ? (
            <div className="results-grid">
              {/* Left Column - Map */}
              <div className="map-column">
                <Map
                  response={uiState.response}
                  selectedZoneId={uiState.selectedZoneId}
                  onZoneSelect={handleZoneSelect}
                  candidates={candidates}
                />
              </div>

              {/* Right Column - Analysis */}
              <div className="analysis-column space-y-6">
                <RecommendationCard response={uiState.response} />

                {candidates.length > 1 && (
                  <CandidateZonesPanel
                    candidates={candidates.slice(1)}
                    selectedZoneId={uiState.selectedZoneId}
                    onZoneSelect={handleZoneSelect}
                    loading={uiState.loading}
                  />
                )}

                <EvidenceDisplay response={uiState.response} />
              </div>
            </div>
          ) : (
            <div className="empty-state">
              <div className="empty-state-content">
                <div className="empty-icon">🎯</div>
                <h2>Ready for Analysis</h2>
                <p>Submit a query above to see marine intelligence, map visualization, and supporting evidence.</p>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="dashboard-footer">
        <p>ORCA — Marine Ecosystem Reasoning with Collaborative Agents | LLM PLANS. CODE CALCULATES. SAFETY VALIDATES.</p>
      </footer>
    </div>
  );
};

export default App;
