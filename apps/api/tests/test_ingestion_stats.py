import datetime as dt

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Incident, IncidentSource, IncidentTimelineEntry, IngestRun


def test_ingestion_stats_endpoint_returns_expected_counts() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
    Base.metadata.create_all(bind=engine)

    now = dt.datetime.now(dt.UTC)
    yesterday = now - dt.timedelta(days=1)

    with SessionLocal() as db:
        today_incident = Incident(
            title="Today incident",
            summary="summary",
            status="developing",
            credibility_score=0.5,
            occurred_at=now,
            created_at=now,
            updated_at=now,
        )
        today_incident.sources = [
            IncidentSource(
                source_name="Source A",
                source_type="rss",
                reliability_score=0.7,
                captured_at=now,
            )
        ]
        today_incident.timeline_entries = [
            IncidentTimelineEntry(
                event_type="additional_source_attached",
                description="duplicate merge",
                timestamp=now,
            )
        ]

        yesterday_incident = Incident(
            title="Yesterday incident",
            summary="summary",
            status="developing",
            credibility_score=0.4,
            occurred_at=yesterday,
            created_at=yesterday,
            updated_at=yesterday,
        )

        db.add_all(
            [
                today_incident,
                yesterday_incident,
                IngestRun(
                    source="rss",
                    dry_run=False,
                    total_claims=3,
                    inserted=2,
                    duplicates_merged=1,
                    started_at=now - dt.timedelta(minutes=2),
                    completed_at=now - dt.timedelta(minutes=1),
                ),
            ]
        )
        db.commit()

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    response = client.get("/ingestion/stats")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_incidents"] == 2
    assert payload["incidents_created_today"] == 1
    assert payload["duplicate_claims_merged_today"] == 1
    assert payload["latest_ingest_run_timestamp"] is not None
