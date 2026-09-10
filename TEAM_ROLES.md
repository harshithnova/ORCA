# TEAM ROLES

## Person 1 — Frontend + Map

### Owns
- React/Vite/TypeScript
- Leaflet map
- query input
- loading/progress UI
- candidate markers
- recommendation cards
- risk/suitability display
- evidence panel
- map layer controls

### Must not
- calculate safety/risk independently
- call INCOIS/IMD directly
- duplicate backend reasoning logic

### Depends on
API response contract from Person 5.

---

## Person 2 — LLM + Planner + LangGraph

### Owns
- natural-language query interpretation
- structured planner output
- LangGraph orchestration
- marine/weather/geo agent coordination
- LLM explanation layer

### Must not
- invent data
- make deterministic safety decisions
- replace safety engine
- call providers directly if an adapter exists

---

## Person 3 — Marine + Weather Data

### Owns
- INCOIS adapters
- IMD adapters
- source verification
- retrieval
- caching
- normalization
- timestamps and provenance
- forecast/observation distinction

### First milestone
Retrieve a small real Kochi-area sample from an official source and make it available through the common schema.

### Must not
- hide source failures
- invent unavailable fields
- label observations as forecasts

---

## Person 4 — GIS + Reasoning + Safety

### Owns
- candidate zone generation
- spatial filtering
- GeoPandas/Shapely/Haversine logic
- PostGIS spatial checks
- suitability score
- risk score
- confidence score
- Safety Engine
- replan logic
- unit/logic validation tests

### Core flow

Candidate generation → spatial hard filters → suitability/risk/confidence → Safety Engine → replan if blocked → recheck.

### Must not
- call external providers directly
- let LLM override safety
- treat prototype thresholds as official standards

---

## Person 5 — Backend + Database + Integration

### Owns
- FastAPI
- Pydantic models
- PostgreSQL/PostGIS
- API contracts
- integration
- application wiring
- main/release branch

### Responsibility
Keep the full application runnable while integrating the role branches.

---

## Person 6 — Product + Research + QA + Demo

### Owns
- official-source verification
- test scenarios
- evidence/provenance review
- adversarial testing
- demo flow
- documentation
- pitch/demo consistency

### Must test
- safe case
- high-risk case
- restricted case
- official warning override
- missing critical data
- stale critical data
- replan
- all candidates blocked
- forecast validity
