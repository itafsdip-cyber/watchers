import datetime as dt
import json
import logging
import time
from collections.abc import Iterator
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.credibility import build_explanation
from app.database import get_db
from app.models import Incident, IncidentSource, IncidentTimelineEntry, IngestRun
from app.providers import get_provider_registry
from app.schemas import (
    CredibilityExplanation,
    HealthRead,
    IncidentDetailRead,
    IncidentRead,
    IngestionStatsRead,
)

app = FastAPI(title=settings.app_name)
provider_registry = get_provider_registry()
logger = logging.getLogger(__name__)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthRead)
def health() -> HealthRead:
    return HealthRead(status="ok", app_env=settings.app_env)


@app.get("/providers/active", response_model=dict[str, str])
def active_providers() -> dict[str, str]:
    return provider_registry.active_names()


@app.get("/incidents", response_model=list[IncidentRead])
def list_incidents(
    status: Optional[str] = None,
    min_score: Optional[float] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Incident)

    if status is not None:
        query = query.filter(Incident.status == status)

    if min_score is not None:
        query = query.filter(Incident.credibility_score >= min_score)

    incidents = query.order_by(Incident.occurred_at.desc(), Incident.id.desc()).all()
    return incidents


@app.get("/ingestion/stats", response_model=IngestionStatsRead)
def ingestion_stats(db: Session = Depends(get_db)) -> IngestionStatsRead:
    now_utc = dt.datetime.now(dt.UTC)
    start_of_day = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)

    total_incidents = db.scalar(select(func.count(Incident.id))) or 0
    incidents_created_today = db.scalar(select(func.count(Incident.id)).where(Incident.created_at >= start_of_day)) or 0
    duplicate_claims_merged_today = (
        db.scalar(
            select(func.count(IncidentTimelineEntry.id)).where(
                IncidentTimelineEntry.event_type == "additional_source_attached",
                IncidentTimelineEntry.timestamp >= start_of_day,
            )
        )
        or 0
    )
    latest_ingest_run_timestamp = db.scalar(select(func.max(IngestRun.completed_at)).where(IngestRun.source == "rss"))

    return IngestionStatsRead(
        total_incidents=int(total_incidents),
        incidents_created_today=int(incidents_created_today),
        duplicate_claims_merged_today=int(duplicate_claims_merged_today),
        latest_ingest_run_timestamp=latest_ingest_run_timestamp,
    )


def _incident_updates_stream(db: Session) -> Iterator[str]:
    last_seen: dt.datetime | None = None

    while True:
        db.expire_all()
        latest_incident = db.scalar(select(Incident).order_by(Incident.updated_at.desc(), Incident.id.desc()).limit(1))
        if latest_incident is not None:
            current_updated_at = latest_incident.updated_at
            if last_seen is None:
                last_seen = current_updated_at
                payload = {"event": "connected", "updated_at": current_updated_at.isoformat()}
                logger.info(json.dumps({"event": "incident_stream_connected", **payload}))
                yield f"event: connected\ndata: {json.dumps(payload)}\n\n"
            elif current_updated_at > last_seen:
                last_seen = current_updated_at
                payload = {
                    "event": "incident_changed",
                    "incident_id": latest_incident.id,
                    "updated_at": current_updated_at.isoformat(),
                }
                logger.info(json.dumps({"event": "incident_stream_incident_changed", **payload}))
                yield f"event: incident_changed\ndata: {json.dumps(payload)}\n\n"

        yield ": keepalive\n\n"
        time.sleep(1)


@app.get("/incidents/stream")
def stream_incident_updates(db: Session = Depends(get_db)) -> StreamingResponse:
    return StreamingResponse(_incident_updates_stream(db), media_type="text/event-stream")


@app.get("/incidents/{incident_id}", response_model=IncidentDetailRead)
def get_incident(incident_id: int, db: Session = Depends(get_db)) -> Incident:
    stmt = (
        select(Incident)
        .where(Incident.id == incident_id)
        .options(selectinload(Incident.sources), selectinload(Incident.timeline_entries))
    )
    incident = db.scalar(stmt)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@app.get("/incidents/{incident_id}/credibility", response_model=CredibilityExplanation)
def incident_credibility(incident_id: int, db: Session = Depends(get_db)) -> CredibilityExplanation:
    stmt = (
        select(Incident)
        .where(Incident.id == incident_id)
        .options(selectinload(Incident.sources), selectinload(Incident.timeline_entries))
    )
    incident = db.scalar(stmt)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    dimensions, notes = build_explanation(incident)
    return CredibilityExplanation(
        incident_id=incident.id,
        final_score=incident.credibility_score,
        dimensions=dimensions,
        notes=notes,
    )


@app.post("/demo/seed", response_model=dict[str, int])
def seed_demo(db: Session = Depends(get_db)) -> dict[str, int]:
    incident_count = db.scalar(select(func.count(Incident.id))) or 0
    if incident_count > 0:
        return {"incidents": int(incident_count)}

    incident = Incident(
        title="Airport operations disruption report",
        summary="Multiple open reports indicate temporary service interruption at a major airport.",
        status="developing",
        credibility_score=0.58,
        latitude=25.2532,
        longitude=55.3657,
        occurred_at=dt.datetime.now(dt.UTC) - dt.timedelta(minutes=45),
    )
    incident.sources = [
        IncidentSource(
            source_name="Local News Desk",
            source_url="https://example.org/local-news",
            source_type="news",
            reliability_score=0.78,
        ),
        IncidentSource(
            source_name="Open Transit Channel",
            source_url="https://example.org/transit-feed",
            source_type="open_feed",
            reliability_score=0.62,
        ),
    ]
    incident.timeline_entries = [
        IncidentTimelineEntry(
            event_type="report_received",
            description="First cluster of public disruption reports observed.",
            timestamp=dt.datetime.now(dt.UTC) - dt.timedelta(minutes=40),
        ),
        IncidentTimelineEntry(
            event_type="corroboration",
            description="Independent source reported matching conditions.",
            timestamp=dt.datetime.now(dt.UTC) - dt.timedelta(minutes=20),
        ),
    ]

    db.add(incident)
    db.commit()

    return {"incidents": 1}
