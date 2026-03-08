# Credibility Engine (MVP)

## Dimensions
- `source_reliability`
- `independence`
- `evidence_strength`
- `temporal_consistency`
- `geographic_consistency`
- `cross_platform_consistency`
- `historical_source_accuracy`
- `contradiction_penalty`
- `manipulation_penalty`

## Final Score
Worker computes:
- weighted positive signals
- minus contradiction/manipulation penalties
- clamped to `[0.0, 1.0]`

## Status Mapping
Penalty overrides:
- `false` if contradiction or manipulation penalty `>= 0.7`
- `disputed` if contradiction or manipulation penalty `>= 0.4`

Score thresholds:
- `< 0.20` -> `noise`
- `< 0.35` -> `rumor`
- `< 0.50` -> `developing`
- `< 0.65` -> `likely`
- `< 0.78` -> `credible`
- `< 0.90` -> `confirmed`
- `>= 0.90` -> `officially_confirmed`

## Transparency
API endpoint `/incidents/{id}/credibility` exposes dimensions and notes so users can inspect confidence logic directly.
