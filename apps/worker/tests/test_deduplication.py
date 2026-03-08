import datetime as dt

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from worker_app.database import Base
from worker_app.deduplication import find_duplicate_incident
from worker_app.models import Incident, IncidentSource


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)()


def _seed_incident(db: Session, *, title: str, occurred_at: dt.datetime, source_url: str | None = None) -> Incident:
    incident = Incident(
        title=title,
        summary="summary",
        status="developing",
        credibility_score=0.5,
        occurred_at=occurred_at,
    )
    if source_url:
        incident.sources = [
            IncidentSource(
                source_name="Source",
                source_url=source_url,
                source_type="rss",
                reliability_score=0.7,
            )
        ]
    db.add(incident)
    db.commit()
    return incident


def test_find_duplicate_by_exact_source_url() -> None:
    db = _session()
    now = dt.datetime(2024, 9, 4, 10, 0, tzinfo=dt.UTC)
    original = _seed_incident(
        db,
        title="Airport disruption reported",
        occurred_at=now,
        source_url="https://example.com/a",
    )

    duplicate = find_duplicate_incident(
        db,
        title="Different title",
        occurred_at=now + dt.timedelta(hours=12),
        source_url="https://example.com/a",
    )

    assert duplicate is not None
    assert duplicate.incident.id == original.id
    assert duplicate.reason == "source_url_match"


def test_find_duplicate_by_similar_title_and_time_window() -> None:
    db = _session()
    now = dt.datetime(2024, 9, 4, 10, 0, tzinfo=dt.UTC)
    original = _seed_incident(db, title="Major fire in London city center", occurred_at=now)

    duplicate = find_duplicate_incident(
        db,
        title="Major fire in London city centre",
        occurred_at=now + dt.timedelta(hours=1),
    )

    assert duplicate is not None
    assert duplicate.incident.id == original.id
    assert duplicate.reason == "title_time_match"


def test_similar_wording_but_different_event_not_duplicate() -> None:
    db = _session()
    now = dt.datetime(2024, 9, 4, 10, 0, tzinfo=dt.UTC)
    _seed_incident(db, title="Fire near central train station", occurred_at=now)

    duplicate = find_duplicate_incident(
        db,
        title="Fire drill near central train station",
        occurred_at=now + dt.timedelta(hours=8),
    )

    assert duplicate is None
