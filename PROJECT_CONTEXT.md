# PROJECT CONTEXT

## Problem

Marine decision-making involves multiple heterogeneous data sources such as ocean conditions, weather warnings and geospatial restrictions. ORCA combines these through collaborative agents and deterministic reasoning.

## User experience

A user can ask a natural-language marine/fishing question.

Example:
> Find a suitable and safe fishing zone near Kochi tomorrow morning.

ORCA should return:
- candidate zones
- suitability score
- risk score
- confidence
- safety status
- explanation
- evidence/source information
- map visualization

## Design philosophy

The LLM is not the scientific calculator and is not the safety authority.

The architecture separates:
1. Planning
2. Data retrieval
3. Validation/normalization
4. Deterministic calculation
5. Safety validation
6. Explanation

## Current MVP decision

Use **cached official data** as the primary MVP source.

Use synthetic fixtures only for controlled testing and fallback.

## Forecast rule

If the requested time is in the future, the system must use forecast data valid for that time. Observation data must not be relabelled as forecast.

Forecast records should preserve:
- `issued_at`
- `valid_from`
- `valid_to`
- `data_type=FORECAST`

## Kochi

Kochi is the primary demonstration region. The architecture must remain location-independent so other coastal regions can be supported later.

## Non-goals

- national-scale live satellite processing
- raw satellite image processing
- species-specific prediction
- full navigation/route optimization
- production safety certification
- unnecessarily large multi-agent systems
- unsupported live API claims
