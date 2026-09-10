# SAFETY SPEC

Safety is a deterministic gate after reasoning.

## Core rule

**The LLM cannot override the Safety Engine.**

## Hard safety overrides

Examples:

1. Candidate lies in a restricted/geofenced area → `BLOCK`
2. Explicit official blocking warning applies → `BLOCK`
3. Severe cyclone/hazard condition applies → `BLOCK`
4. Critical safety data is missing → fail safe
5. Critical safety data is stale → fail safe
6. Configured risk limit is exceeded → `BLOCK`

The exact implementation must preserve provenance for authoritative warnings.

## Missing data

Never interpret:
- null
- unavailable
- provider failure

as zero risk.

For critical safety information, missing data means the system must not claim safety.

## Replanning

```text
Candidate A
   ↓
Safety check → BLOCK
   ↓
Candidate B
   ↓
Recalculate
   ↓
Safety check again
   ↓
SAFE/CAUTION or BLOCK
```

Never reuse Candidate A's safety result for Candidate B.

## All candidates blocked

Return:

`NO_SAFE_RECOMMENDATION`

The system should explain the blocking evidence rather than inventing an alternative.

## Official thresholds

Any official safety threshold must come from a verified authoritative source.

ORCA prototype thresholds are internal heuristics and must not be described as official standards.

## Future extension

INCOIS Small Vessel Advisory / Boat Safety Index concepts may inform future work, but do not claim that ORCA implements an official INCOIS safety index unless actually integrated and verified.
