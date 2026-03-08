import datetime as dt
import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from worker_app.models import Incident, IncidentSource, IncidentTimelineEntry, SourceProfile
from worker_app.scoring import score_claim


def parse_dt(value: str | None) -> dt.datetime:
    if not value:
        return dt.datetime.now(dt.UTC)
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def _upsert_source_profile(db: Session, source_name: str, reliability: float) -> None:
    profile = db.scalar(select(SourceProfile).where(SourceProfile.source_name == source_name))
    if profile is None:
        db.add(
            SourceProfile(
                source_name=source_name,
                platform="open",
                historical_accuracy=reliability,
                reliability_baseline=reliability,
            )
        )
        return
    profile.historical_accuracy = round((profile.historical_accuracy + reliability) / 2, 3)
    profile.reliability_baseline = round((profile.reliability_baseline + reliability) / 2, 3)


def ingest_claims_file(db: Session, file_path: str) -> dict[str, int]:
    path = Path(file_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Sample claims file not found: {path}")

    claims = json.loads(path.read_text(encoding="utf-8"))
    inserted = 0
    skipped = 0

    for claim in claims:
        title = str(claim.get("title", "Untitled incident")).strip()
        occurred_at = parse_dt(claim.get("reported_at"))

        existing = db.scalar(
            select(Incident).where(Incident.title == title, Incident.occurred_at == occurred_at)
        )
        if existing is not None:
            skipped += 1
            continue

        score_result = score_claim(claim)

        incident = Incident(
            title=title,
            summary=str(claim.get("summary", "No summary available")),
            status=score_result.status,
            credibility_score=score_result.final_score,
            latitude=claim.get("location", {}).get("lat"),
            longitude=claim.get("location", {}).get("lon"),
            occurred_at=occurred_at,
            updated_at=dt.datetime.now(dt.UTC),
        )

        source_rows: list[IncidentSource] = []
        for src in claim.get("sources", []):
            reliability = float(src.get("reliability", 0.5))
            source_name = str(src.get("name", "unknown-source"))
            source_rows.append(
                IncidentSource(
                    source_name=source_name,
                    source_url=src.get("url"),
                    source_type=str(src.get("type", "open")),
                    reliability_score=reliability,
                    captured_at=dt.datetime.now(dt.UTC),
                )
            )
            _upsert_source_profile(db, source_name=source_name, reliability=reliability)

        timeline_rows: list[IncidentTimelineEntry] = [
            IncidentTimelineEntry(
                event_type="report_received",
                description="Worker ingested raw claim from local sample dataset.",
                timestamp=occurred_at,
            ),
            IncidentTimelineEntry(
                event_type="credibility_scored",
                description=(
                    f"Score={score_result.final_score}, status={score_result.status}, "
                    f"dimensions={score_result.dimensions}"
                ),
                timestamp=dt.datetime.now(dt.UTC),
            ),
        ]

        for event in claim.get("timeline", []):
            timeline_rows.append(
                IncidentTimelineEntry(
                    event_type=str(event.get("event_type", "update")),
                    description=str(event.get("description", "timeline update")),
                    timestamp=parse_dt(event.get("timestamp")),
                )
            )

        incident.sources = source_rows
        incident.timeline_entries = timeline_rows
        db.add(incident)
        inserted += 1

    db.commit()
    return {"inserted": inserted, "skipped": skipped, "total": len(claims)}
