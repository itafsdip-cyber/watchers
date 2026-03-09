import datetime as dt

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from worker_app.database import Base
from worker_app.main import main
from worker_app.models import Incident
from worker_app.rss_ingest import TITLE_MAX_LENGTH, ingest_rss_feeds, parse_rss_items

SAMPLE_RSS = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<rss version=\"2.0\">
  <channel>
    <title>Incident Feed</title>
    <link>https://example.com/feed</link>
    <item>
      <title>Major fire in London</title>
      <description>Emergency services responded.</description>
      <pubDate>Wed, 04 Sep 2024 10:00:00 GMT</pubDate>
      <source url=\"https://bbc.example/news/1\">BBC News</source>
    </item>
    <item>
      <title>Major fire in London.</title>
      <description>Follow-up report from responders.</description>
      <pubDate>Wed, 04 Sep 2024 12:00:00 GMT</pubDate>
      <source url=\"https://bbc.example/news/2\">BBC News</source>
    </item>
  </channel>
</rss>
"""


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)()


def test_parse_rss_items_extracts_claim_fields() -> None:
    claims = parse_rss_items(
        SAMPLE_RSS,
        fallback_source_name="https://example.com/fallback",
        fallback_source_url="https://example.com/fallback",
    )

    assert len(claims) == 2
    assert claims[0].title == "Major fire in London"
    assert claims[0].summary == "Emergency services responded."
    assert claims[0].source_name == "BBC News"
    assert claims[0].source_url == "https://bbc.example/news/1"
    assert claims[0].timestamp == dt.datetime(2024, 9, 4, 10, 0, tzinfo=dt.UTC)


def test_parse_rss_items_sanitizes_and_truncates_content() -> None:
    long_title = "T" * (TITLE_MAX_LENGTH + 20)
    xml = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<rss version=\"2.0\">
  <channel>
    <item>
      <title>  {long_title}  </title>
      <description>  &lt;p&gt;First line&lt;/p&gt;\n&lt;p&gt;Second &amp;amp; third&lt;/p&gt;  </description>
      <pubDate>Wed, 04 Sep 2024 10:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""

    claims = parse_rss_items(
        xml,
        fallback_source_name="https://example.com/fallback",
        fallback_source_url="https://example.com/fallback",
    )

    assert len(claims) == 1
    assert len(claims[0].title) == TITLE_MAX_LENGTH
    assert claims[0].title == long_title[:TITLE_MAX_LENGTH]
    assert claims[0].summary == "First line Second & third"


def test_ingest_rss_feeds_inserts_and_skips_duplicates(monkeypatch) -> None:
    db = _session()
    monkeypatch.setattr("worker_app.rss_ingest.fetch_rss_content", lambda _: SAMPLE_RSS)

    result = ingest_rss_feeds(db, feed_urls=("https://example.com/rss",))

    incidents = db.scalars(select(Incident)).all()
    assert result == {"inserted": 1, "skipped": 1, "total": 2}
    assert len(incidents) == 1
    assert incidents[0].credibility_score > 0
    assert len(incidents[0].sources) == 2
    assert any(entry.event_type == "additional_source_attached" for entry in incidents[0].timeline_entries)


def test_main_ingest_rss_command(monkeypatch) -> None:
    monkeypatch.setattr("worker_app.main.run_ingest_rss", lambda: 0)
    monkeypatch.setattr("sys.argv", ["worker", "ingest-rss"])

    assert main() == 0


def test_ingest_rss_feeds_dry_run_does_not_write(monkeypatch) -> None:
    db = _session()
    monkeypatch.setattr("worker_app.rss_ingest.fetch_rss_content", lambda _: SAMPLE_RSS)

    result = ingest_rss_feeds(db, feed_urls=("https://example.com/rss",), dry_run=True)

    incidents = db.scalars(select(Incident)).all()
    assert result == {"inserted": 1, "skipped": 1, "total": 2}
    assert incidents == []


def test_main_dry_run_rss_command(monkeypatch) -> None:
    monkeypatch.setattr("worker_app.main.run_ingest_rss", lambda dry_run=False: 0 if dry_run else 1)
    monkeypatch.setattr("sys.argv", ["worker", "dry-run-rss"])

    assert main() == 0
