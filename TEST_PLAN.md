# TEST PLAN

## T1 — Normal safe case

Input:
safe cached forecast + valid candidate.

Expected:
`SAFE` or `CAUTION` according to configured logic, with evidence.

## T2 — High risk

Input:
high wave/wind/hazard conditions.

Expected:
risk increases and Safety Engine blocks when configured threshold is exceeded.

## T3 — Restricted zone

Input:
candidate geometry intersects restricted zone.

Expected:
`BLOCK` regardless of suitability score.

## T4 — Official severe warning

Input:
authoritative blocking warning overlaps candidate validity period/area.

Expected:
safety override → `BLOCK`.

## T5 — Missing critical data

Input:
critical safety parameter unavailable.

Expected:
fail safe; no false `SAFE`.

## T6 — Stale critical data

Input:
critical safety record outside configured freshness window.

Expected:
fail safe or block according to configured policy.

## T7 — Replan

Input:
best candidate is blocked.

Expected:
system evaluates next valid candidate and reruns safety checks.

## T8 — All candidates blocked

Expected:
`NO_SAFE_RECOMMENDATION`.

## T9 — Forecast validity

Input:
future query.

Expected:
only forecast data valid for requested time is selected.

Observation data must not be used as a future forecast.

## T10 — Provenance

Every recommendation evidence item should identify source and validity information where available.

## T11 — Synthetic fixture labeling

Any synthetic record must contain:
`data_mode=SIMULATED_MVP`

No UI or explanation may imply it is official live data.

## T12 — Determinism

Given the same cached inputs and configuration, deterministic calculations should return the same results.
