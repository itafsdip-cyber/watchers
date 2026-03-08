import datetime as dt
from dataclasses import dataclass
from difflib import SequenceMatcher

from sqlalchemy import select
from sqlalchemy.orm import Session

from worker_app.models import Incident, IncidentSource

SIMILARITY_THRESHOLD = 0.9
DUPLICATE_TIME_WINDOW_HOURS = 6


def normalize_title(text: str) -> str:
    return " ".join(text.casefold().split())


@dataclass
class DuplicateMatch:
    incident: Incident
    reason: str


def find_duplicate_incident(
    db: Session,
    *,
    title: str,
    occurred_at: dt.datetime,
    source_url: str | None = None,
    similarity_threshold: float = SIMILARITY_THRESHOLD,
    time_window_hours: int = DUPLICATE_TIME_WINDOW_HOURS,
) -> DuplicateMatch | None:
    if source_url:
        for pending in db.new:
            if not isinstance(pending, Incident):
                continue
            for source in pending.sources:
                if source.source_url and source.source_url == source_url:
                    return DuplicateMatch(incident=pending, reason="source_url_match")

        existing_source = db.scalar(
            select(IncidentSource).where(IncidentSource.source_url == source_url).order_by(IncidentSource.id.desc())
        )
        if existing_source is not None:
            incident = db.get(Incident, existing_source.incident_id)
            if incident is not None:
                return DuplicateMatch(incident=incident, reason="source_url_match")

    window_start = occurred_at - dt.timedelta(hours=time_window_hours)
    window_end = occurred_at + dt.timedelta(hours=time_window_hours)

    nearby_incidents = db.scalars(
        select(Incident)
        .where(Incident.occurred_at >= window_start, Incident.occurred_at <= window_end)
        .order_by(Incident.occurred_at.desc(), Incident.id.desc())
    ).all()
    for pending in db.new:
        if isinstance(pending, Incident) and pending.occurred_at and window_start <= pending.occurred_at <= window_end:
            nearby_incidents.append(pending)

    normalized_title = normalize_title(title)
    best_match: Incident | None = None
    best_similarity = 0.0
    for incident in nearby_incidents:
        similarity = SequenceMatcher(None, normalized_title, normalize_title(incident.title)).ratio()
        if similarity >= similarity_threshold and similarity > best_similarity:
            best_similarity = similarity
            best_match = incident

    if best_match is None:
        return None

    return DuplicateMatch(incident=best_match, reason="title_time_match")
