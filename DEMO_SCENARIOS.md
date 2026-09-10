# DEMO SCENARIOS

## Scenario 1 — Safe recommendation

Query:
> Find a suitable and safe fishing zone near Kochi tomorrow morning.

Show:
- planner interpretation
- cached INCOIS/IMD evidence
- candidate zones
- suitability/risk/confidence
- selected zone
- map
- evidence panel

## Scenario 2 — Safety override

Use a controlled fixture or verified warning condition.

Show:
- candidate may have good suitability
- safety rule overrides it
- status becomes `BLOCK`
- explanation identifies the blocking evidence

## Scenario 3 — Missing critical data

Remove a critical safety input.

Show:
- confidence decreases or safety fails
- system refuses to claim safety
- clear explanation

## Scenario 4 — Replanning

Candidate A:
- high suitability
- blocked by safety

Candidate B:
- slightly lower suitability
- passes safety

Show:
- A blocked
- system replans
- B recalculated and revalidated
- B returned if valid

## Scenario 5 — All unsafe

All candidates violate hard safety conditions.

Expected:
`NO_SAFE_RECOMMENDATION`

Do not invent a safe location.

## Demo wording

Use:
- cached official data
- ORCA candidate zone
- prototype score
- deterministic safety rule

Avoid:
- guaranteed catch
- officially certified safe
- official PFZ when it is an ORCA candidate
- live data unless actually live
