# REASONING SPEC

All core scores are deterministic prototype heuristics.

They are **not official safety standards, scientific guarantees, or species-specific predictions**.

## Suitability

Prototype weighted model:

```text
Suitability =
0.35 × PFZ signal
+ 0.20 × chlorophyll
+ 0.15 × SST
+ 0.15 × wave suitability
+ 0.15 × weather suitability
```

Clamp to 0–100.

### Classes

- 0–20: POOR
- 21–40: FAIR
- 41–60: GOOD
- 61–80: VERY GOOD
- 81–100: EXCELLENT

If an official PFZ signal is unavailable, do not invent one. The implementation must define a documented fallback or omit that factor.

## Risk

Prototype weighted model:

```text
Risk =
0.30 × wave risk
+ 0.25 × wind risk
+ 0.20 × lightning risk
+ 0.15 × rain risk
+ 0.10 × hazard risk
```

Clamp to 0–100.

### Classes

- 0–20: LOW
- 21–40: MODERATE
- 41–60: ELEVATED
- 61–80: HIGH
- 81–100: SEVERE

## Confidence

Prototype model:

```text
Confidence =
0.50 × freshness
+ 0.40 × completeness
+ 0.10 × source score
```

Clamp to 0–1.

Confidence indicates confidence in the data-supported recommendation, not probability of fishing success.

## Candidate ranking

Recommended order:

1. Remove hard-blocked candidates.
2. Calculate scores for remaining candidates.
3. Rank by suitability and acceptable risk.
4. Apply final Safety Engine.
5. Return best valid candidate.
6. If blocked, replan and repeat.

## Important

Do not turn these prototype formulas into claims that ORCA has scientifically validated prediction accuracy.
