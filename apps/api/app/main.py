import datetime as dt

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from typing import Optional
from app.config import settings
from app.credibility import build_explanation
from app.database import get_db
from app.models import Incident, IncidentSource, IncidentTimelineEntry
from app.schemas import IncidentRead
from app.providers import get_provider_registry
from app.schemas import CredibilityExplanation, HealthRead, IncidentDetailRead, IncidentRead

app = FastAPI(title=settings.app_name)
provider_registry = get_provider_registry()

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
