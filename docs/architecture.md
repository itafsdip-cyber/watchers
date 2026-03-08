# Watchers Architecture

## Scope
Watchers is a local-first incident intelligence MVP for public awareness using open/public data only.

## Monorepo Services
- `apps/api`: FastAPI service for incidents, credibility details, and provider configuration.
- `apps/worker`: Python ingestion worker that reads local sample claims, computes credibility, and writes to PostgreSQL.
- `apps/web`: Next.js dashboard with map, feed, and incident details.

## Data Flow
1. Worker reads `data/samples/raw_claims.json`.
2. Worker computes transparent credibility dimensions and status.
3. Worker writes incidents/sources/timeline entries to PostgreSQL.
4. API serves incidents and credibility explanation.
5. Web UI fetches API data and renders live map/feed/details.

## Storage and Infra
- PostgreSQL + PostGIS: primary data store
- Redis: cache/event buffer placeholder for next iterations
- Docker Compose: local orchestration

## Safety Constraints
- Public/open data only
- No private surveillance
- No individual targeting
- Uncertainty is always shown via status + score dimensions
