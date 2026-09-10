# ORCA — Marine EcOsystem Reasoning with Collaborative Agents

## SIH 2026 — Problem Statement SIH26176

ORCA is a safety-first, multi-agent decision-support system for marine/fishing queries. A user asks a natural-language question such as:

> Find a suitable and safe fishing zone near Kochi tomorrow morning.

The system plans the request, retrieves authoritative cached marine/weather/geospatial data, performs deterministic spatial and scoring calculations, validates safety constraints, and returns an explainable recommendation with evidence and a map.

## Core principle

**LLM PLANS. CODE CALCULATES. SAFETY VALIDATES.**

## MVP architecture

User Query → Planner Agent → Marine/Weather/Geo Agents → Validation/Normalization → Deterministic Reasoning → Safety Engine → Replan if required → Evidence → FastAPI → React/Leaflet

## MVP data mode

**Cached official data is the primary MVP data source.**

Official-source data should be retrieved, cached, normalized, and stored in PostgreSQL/PostGIS.

Small synthetic fixtures are allowed only for controlled safety tests/fallback and must be clearly labelled `SIMULATED_MVP`.

## Technology stack

- Frontend: React + Vite + TypeScript + Leaflet
- Backend: Python + FastAPI + Pydantic
- AI/orchestration: LLM API + LangGraph
- GIS: GeoPandas + Shapely + Haversine
- Database: PostgreSQL + PostGIS
- Data formats: JSON / CSV / GeoJSON
- Sources: INCOIS / IMD / authoritative geospatial sources

## Primary demo queries

1. Find a suitable and safe fishing zone near Kochi tomorrow morning.
2. Is it safe to go fishing near Kochi tomorrow morning?

Optional route-related functionality comes only after the primary flow is stable.

## Important terminology

Candidate zones are ORCA-evaluated sea-area patches. They are **not automatically official INCOIS PFZs**.

Forecast data must be used for future-time queries. Historical/current observations must not be presented as future forecasts.

## Read first

Every contributor and every coding AI agent must read:

1. `AGENTS.md`
2. `PROJECT_CONTEXT.md`
3. `TEAM_ROLES.md`
4. `ARCHITECTURE.md`
5. `DATA_CONTRACT.md`
6. `API_CONTRACT.md`
7. `REASONING_SPEC.md`
8. `SAFETY_SPEC.md`
9. `MVP_SCOPE.md`
10. `DEVELOPMENT_WORKFLOW.md`

## Repository rule

Keep `main` always runnable. Role-specific work happens on feature branches and is integrated by the Backend/Integration owner.
