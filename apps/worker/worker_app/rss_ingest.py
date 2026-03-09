import datetime as dt
import email.utils
import html
import json
import logging
import re
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from worker_app.deduplication import find_duplicate_incident
from worker_app.models import Incident, IncidentSource, IncidentTimelineEntry, IngestRun, SourceProfile
from worker_app.scoring import score_claim

GOOGLE_INCIDENTS_RSS_URL = "https://news.google.com/rss/search?q=incident"
BBC_WORLD_RSS_URL = "https://feeds.bbci.co.uk/news/world/rss.xml"
DEFAULT_RSS_FEEDS = (GOOGLE_INCIDENTS_RSS_URL, BBC_WORLD_RSS_URL)

REQUEST_TIMEOUT_SECONDS = 10
TITLE_MAX_LENGTH = 255

HTML_TAG_RE = re.compile(r"<[^>]+>")
logger = logging.getLogger(__name__)


@dataclass
class RSSClaim:
    title: str
    summary: str
    source_name: str
    source_url: str | None
    timestamp: dt.datetime


def _log_structured(event: str, **payload: object) -> None:
    logger.info(json.dumps({"event": event, **payload}, default=str))


def _normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def _strip_html_tags(text: str) -> str:
    without_tags = HTML_TAG_RE.sub(" ", text)
    return html.unescape(without_tags)


def _sanitize_title(title: str) -> str:
    normalized = _normalize_whitespace(title)
    if not normalized:
        normalized = "Untitled incident"
    return normalized[:TITLE_MAX_LENGTH]


def _sanitize_summary(summary: str) -> str:
    cleaned = _normalize_whitespace(_strip_html_tags(summary))
    return cleaned or "No summary available"


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
        title = _sanitize_title(_get_child_text(item, "title") or "Untitled incident")
        summary = _sanitize_summary(_get_child_text(item, "description", "summary") or "No summary available")
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


def ingest_rss_feeds(db: Session, feed_urls: tuple[str, ...] = DEFAULT_RSS_FEEDS, *, dry_run: bool = False) -> dict[str, int]:
    run_started_at = dt.datetime.now(dt.UTC)
    parsed_claims: list[RSSClaim] = []
    for feed_url in feed_urls:
        xml_content = fetch_rss_content(feed_url)
        feed_claims = parse_rss_items(xml_content, fallback_source_name=feed_url, fallback_source_url=feed_url)
        parsed_claims.extend(feed_claims)
        _log_structured("rss_feed_parsed", feed_url=feed_url, claim_count=len(feed_claims), dry_run=dry_run)

    inserted = 0
    skipped = 0

    for claim in parsed_claims:
        duplicate = find_duplicate_incident(
            db,
            title=claim.title,
            occurred_at=claim.timestamp,
            source_url=claim.source_url,
        )
        if duplicate is not None:
            _log_structured(
                "rss_claim_deduplicated",
                title=claim.title,
                source_url=claim.source_url,
                reason=duplicate.reason,
                dry_run=dry_run,
            )
            reliability = _reliability_for_source(claim.source_name)
            duplicate.incident.sources.append(
                IncidentSource(
                    source_name=claim.source_name,
                    source_url=claim.source_url,
                    source_type="rss",
                    reliability_score=reliability,
                    captured_at=dt.datetime.now(dt.UTC),
                )
            )
            duplicate.incident.timeline_entries.append(
                IncidentTimelineEntry(
                    event_type="additional_source_attached",
                    description=(
                        f"Attached additional source '{claim.source_name}' via duplicate merge "
                        f"({duplicate.reason})."
                    ),
                    timestamp=dt.datetime.now(dt.UTC),
                )
            )
            duplicate.incident.updated_at = dt.datetime.now(dt.UTC)
            _upsert_source_profile(db, source_name=claim.source_name, reliability=reliability)
            skipped += 1
            continue

        _log_structured("rss_claim_new_incident", title=claim.title, source_url=claim.source_url, dry_run=dry_run)
        db.add(claim_to_incident(db, claim))
        inserted += 1

    run_completed_at = dt.datetime.now(dt.UTC)
    run_result = {"inserted": inserted, "skipped": skipped, "total": len(parsed_claims)}

    if dry_run:
        db.rollback()
    else:
        db.add(
            IngestRun(
                source="rss",
                dry_run=False,
                total_claims=run_result["total"],
                inserted=inserted,
                duplicates_merged=skipped,
                started_at=run_started_at,
                completed_at=run_completed_at,
            )
        )
        db.commit()

    _log_structured("rss_ingest_run_completed", **run_result, dry_run=dry_run, completed_at=run_completed_at.isoformat())
    return run_result
