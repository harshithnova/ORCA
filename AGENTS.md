# AGENTS.md — ORCA AI Coding Agent Constitution

This file is mandatory for every AI coding agent working on ORCA.

## 1. Project identity

Project: ORCA — Marine EcOsystem Reasoning with Collaborative Agents  
SIH Problem Statement: SIH26176

## 2. Non-negotiable principle

**LLM PLANS. CODE CALCULATES. SAFETY VALIDATES.**

AI agents may:
- interpret natural-language queries
- create structured plans
- choose which data/agent is needed
- summarize evidence
- explain already-calculated results

AI agents must NOT:
- invent marine/weather measurements
- invent source attribution
- calculate safety decisions through free-form reasoning
- override deterministic safety rules
- treat missing critical data as safe
- present cached data as live data
- call external providers directly from reasoning agents
- hard-code API keys or credentials

## 3. Source integrity

Never invent:
- API endpoints
- dataset IDs
- scientific measurements
- official thresholds
- official partnerships
- research results
- source URLs

Verify external sources against `DATA_SOURCES.md`.

## 4. Data policy

Primary MVP mode:
**CACHED OFFICIAL DATA**

Architecture:
Official provider → adapter → raw/cache → normalization → PostgreSQL/PostGIS → agents/reasoning.

Synthetic fixtures are only for:
- safety tests
- missing-data tests
- restricted-zone tests
- replanning tests
- offline/fallback demonstrations

Synthetic records must be explicitly labelled `SIMULATED_MVP`.

## 5. Safety

Safety decisions must be deterministic and auditable.

Examples:
- restricted area → BLOCK
- explicit official blocking warning → BLOCK
- severe hazard → BLOCK
- critical safety data missing/stale → fail safe
- risk above configured limit → BLOCK

If a candidate is blocked, the system may replan to another candidate and must run the safety checks again.

If no candidate passes:
`NO_SAFE_RECOMMENDATION`

## 6. Ownership

- Person 1: Frontend + Map
- Person 2: LLM + Planner + LangGraph
- Person 3: Marine + Weather Data Providers
- Person 4: GIS + Reasoning + Safety
- Person 5: Backend + Database + Integration
- Person 6: Product + Research + QA + Demo

See `TEAM_ROLES.md`.

## 7. Contract-first development

Before changing shared structures, review:
- `DATA_CONTRACT.md`
- `API_CONTRACT.md`
- `ARCHITECTURE.md`

Do not silently change field names, enum values, response shapes, or safety statuses.

## 8. Coding rules

- Keep modules small and testable.
- Prefer deterministic Python functions for calculations.
- Keep provider HTTP code inside provider/adaptor modules.
- Keep secrets in environment variables.
- Add tests for meaningful logic.
- Do not add unnecessary frameworks or services.
- Preserve provenance and timestamps.
- Make failure states explicit.

## 9. Before opening a PR

Confirm:
- tests pass
- no secrets committed
- no fake source/data
- contracts are still compatible
- safety behavior is unchanged unless explicitly reviewed
- `main` remains runnable
- documentation is updated if behavior changed
