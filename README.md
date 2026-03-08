# Watchers

Watchers is a local-first, open-source incident intelligence platform for public awareness.

## Safety Rules
- Public/open data only
- No private surveillance
- No targeting individuals
- Uncertainty must be visible
- Credibility must be transparent
- Public awareness use only

## Quick Start

```bash
cp .env.example .env
make up
```

### API (manual)

```bash
cd apps/api
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Worker (manual)

```bash
cd apps/worker
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
python -m worker_app.main ingest-rss
```

## Duplicate incident merging

Worker ingestion now performs deterministic duplicate matching before creating a new incident:

1. **Exact source URL match**: if an incoming claim source URL already exists, it is treated as a duplicate.
2. **Near title + time proximity**: if normalized titles are highly similar and `occurred_at` is within the configured window, it is treated as a duplicate.

When a duplicate is detected, Watchers:
- does **not** create a new incident,
- attaches incoming source(s) as `IncidentSource`,
- appends an `IncidentTimelineEntry` with `event_type="additional_source_attached"`,
- updates `updated_at` so live clients receive the change.

## Live incident updates (SSE)

The API exposes `GET /incidents/stream` as a Server-Sent Events stream.

- The dashboard subscribes with `EventSource`.
- On `incident_changed`, frontend re-fetches incidents and refreshes KPI cards, map, and feed without page reload.
- Keepalive comments are emitted to keep local connections warm.

## Map clustering

The dashboard map uses MapLibre GeoJSON clustering:
- nearby incidents render as clusters,
- clicking a cluster zooms into that cluster,
- unclustered points retain status-based styling and popups.

## Local testing

```bash
# API
cd apps/api && pytest

# Worker
cd apps/worker && pytest

# Web lint
cd apps/web && npm run lint
```
