import datetime as dt
import email.utils
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from difflib import SequenceMatcher

from sqlalchemy import select
from sqlalchemy.orm import Session

from worker_app.models import Incident, IncidentSource, IncidentTimelineEntry, SourceProfile
from worker_app.scoring import score_claim

GOOGLE_INCIDENTS_RSS_URL = "https://news.google.com/rss/search?q=incident"
BBC_WORLD_RSS_URL = "https://feeds.bbci.co.uk/news/world/rss.xml"
DEFAULT_RSS_FEEDS = (GOOGLE_INCIDENTS_RSS_URL, BBC_WORLD_RSS_URL)

SIMILARITY_THRESHOLD = 0.9
DUPLICATE_TIME_WINDOW_HOURS = 6
REQUEST_TIMEOUT_SECONDS = 10


@dataclass
class RSSClaim:
    title: str
    summary: str
    source_name: str
    source_url: str | None
    timestamp: dt.datetime


def _normalize(text: str) -> str:
    return " ".join(text.casefold().split())


def _tag_name(elem: ET.Element) -> str:
    return elem.tag.rsplit("}", 1)[-1]


def _get_child_text(item: ET.Element, *names: str) -> str | None:
    targets = {name.casefold() for name in names}
    for child in item:
        if _tag_name(child).casefold() in targets:
            if child.text:
                return child.text.strip()
    return None


def _parse_rss_timestamp(raw_value: str | None) -> dt.datetime:
    if not raw_value:
        return dt.datetime.now(dt.UTC)

    parsed = email.utils.parsedate_to_datetime(raw_value)
    if parsed is None:
        return dt.datetime.now(dt.UTC)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=dt.UTC)
    return parsed.astimezone(dt.UTC)


def fetch_rss_content(feed_url: str) -> str:
    request = urllib.request.Request(feed_url, headers={"User-Agent": "watchers-worker/1.0"})
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:  # noqa: S310
        return response.read().decode("utf-8", errors="replace")


def parse_rss_items(xml_content: str, fallback_source_name: str, fallback_source_url: str) -> list[RSSClaim]:
    root = ET.fromstring(xml_content)

    feed_title = _get_child_text(root, "title")
    feed_link = _get_child_text(root, "link")

    claims: list[RSSClaim] = []
    for item in root.findall(".//item"):
        title = (_get_child_text(item, "title") or "Untitled incident").strip()
        summary = (_get_child_text(item, "description", "summary") or "No summary available").strip()
        timestamp = _parse_rss_timestamp(_get_child_text(item, "pubDate", "published", "updated"))

        source_name = fallback_source_name
        source_url = fallback_source_url
        for child in item:
            if _tag_name(child).casefold() == "source":
                source_name = (child.text or source_name).strip()
                source_url = child.attrib.get("url", source_url)
                break

        if feed_title:
            source_name = source_name or feed_title
        if feed_link:
            source_url = source_url or feed_link

        claims.append(
            RSSClaim(
                title=title,
                summary=summary,
                source_name=source_name or "unknown-source",
                source_url=source_url,
                timestamp=timestamp,
            )
        )

    return claims


def _upsert_source_profile(db: Session, source_name: str, reliability: float) -> None:
    for pending in db.new:
        if isinstance(pending, SourceProfile) and pending.source_name == source_name:
            pending.historical_accuracy = round((pending.historical_accuracy + reliability) / 2, 3)
            pending.reliability_baseline = round((pending.reliability_baseline + reliability) / 2, 3)
            return

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


def is_duplicate_incident(
    db: Session,
    title: str,
    occurred_at: dt.datetime,
    similarity_threshold: float = SIMILARITY_THRESHOLD,
    time_window_hours: int = DUPLICATE_TIME_WINDOW_HOURS,
) -> bool:
    window_start = occurred_at - dt.timedelta(hours=time_window_hours)
    window_end = occurred_at + dt.timedelta(hours=time_window_hours)

    nearby_incidents = db.scalars(
        select(Incident).where(Incident.occurred_at >= window_start, Incident.occurred_at <= window_end)
    ).all()
    for pending in db.new:
        if isinstance(pending, Incident) and pending.occurred_at is not None and window_start <= pending.occurred_at <= window_end:
            nearby_incidents.append(pending)

    normalized_title = _normalize(title)

    for incident in nearby_incidents:
        similarity = SequenceMatcher(None, normalized_title, _normalize(incident.title)).ratio()
        if similarity >= similarity_threshold:
            return True

    return False


def _reliability_for_source(source_name: str) -> float:
    if "bbc" in source_name.casefold():
        return 0.8
    if "google" in source_name.casefold():
        return 0.65
    return 0.6


def claim_to_incident(db: Session, claim: RSSClaim) -> Incident:
    reliability = _reliability_for_source(claim.source_name)
    scoring_claim = {
        "title": claim.title,
        "summary": claim.summary,
        "sources": [{"name": claim.source_name, "url": claim.source_url, "type": "rss", "reliability": reliability}],
        "independent_reports": 1,
        "evidence_count": 1,
        "cross_platform_hits": 1,
    }
    score_result = score_claim(scoring_claim)

    incident = Incident(
        title=claim.title,
        summary=claim.summary,
        status=score_result.status,
        credibility_score=score_result.final_score,
        occurred_at=claim.timestamp,
        updated_at=dt.datetime.now(dt.UTC),
        sources=[
            IncidentSource(
                source_name=claim.source_name,
                source_url=claim.source_url,
                source_type="rss",
                reliability_score=reliability,
                captured_at=dt.datetime.now(dt.UTC),
            )
        ],
        timeline_entries=[
            IncidentTimelineEntry(
                event_type="report_received",
                description="Worker ingested raw claim from RSS feed.",
                timestamp=claim.timestamp,
            ),
            IncidentTimelineEntry(
                event_type="credibility_scored",
                description=(
                    f"Score={score_result.final_score}, status={score_result.status}, "
                    f"dimensions={score_result.dimensions}"
                ),
                timestamp=dt.datetime.now(dt.UTC),
            ),
        ],
    )

    _upsert_source_profile(db, source_name=claim.source_name, reliability=reliability)
    return incident


def ingest_rss_feeds(db: Session, feed_urls: tuple[str, ...] = DEFAULT_RSS_FEEDS) -> dict[str, int]:
    parsed_claims: list[RSSClaim] = []
    for feed_url in feed_urls:
        xml_content = fetch_rss_content(feed_url)
        parsed_claims.extend(parse_rss_items(xml_content, fallback_source_name=feed_url, fallback_source_url=feed_url))

    inserted = 0
    skipped = 0

    for claim in parsed_claims:
        if is_duplicate_incident(db, title=claim.title, occurred_at=claim.timestamp):
            skipped += 1
            continue

        db.add(claim_to_incident(db, claim))
        inserted += 1

    db.commit()

    return {"inserted": inserted, "skipped": skipped, "total": len(parsed_claims)}
