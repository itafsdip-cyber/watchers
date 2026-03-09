import datetime as dt

from pydantic import BaseModel, ConfigDict


class IncidentSourceRead(BaseModel):
    id: int
    source_name: str
    source_url: str | None
    source_type: str
    reliability_score: float
    captured_at: dt.datetime

    model_config = ConfigDict(from_attributes=True)


class IncidentTimelineEntryRead(BaseModel):
    id: int
    event_type: str
    description: str
    timestamp: dt.datetime

    model_config = ConfigDict(from_attributes=True)


class IncidentRead(BaseModel):
    id: int
    title: str
    summary: str
    status: str
    credibility_score: float
    latitude: float | None
    longitude: float | None
    occurred_at: dt.datetime | None
    updated_at: dt.datetime

    model_config = ConfigDict(from_attributes=True)


class IncidentDetailRead(IncidentRead):
    sources: list[IncidentSourceRead]
    timeline_entries: list[IncidentTimelineEntryRead]


class CredibilityExplanation(BaseModel):
    incident_id: int
    final_score: float
    dimensions: dict[str, float]
    notes: list[str]


class HealthRead(BaseModel):
    status: str
    app_env: str


class IngestionStatsRead(BaseModel):
    total_incidents: int
    incidents_created_today: int
    duplicate_claims_merged_today: int
    latest_ingest_run_timestamp: dt.datetime | None
