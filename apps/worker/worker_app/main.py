import argparse
import json
import sys

from worker_app.config import settings
from worker_app.database import SessionLocal
from worker_app.ingest import ingest_claims_file
from worker_app.rss_ingest import ingest_rss_feeds


def run_ingest(file_path: str) -> int:
    with SessionLocal() as db:
        result = ingest_claims_file(db, file_path=file_path)
    print(json.dumps(result, indent=2))
    return 0


def run_ingest_rss(*, dry_run: bool = False) -> int:
    with SessionLocal() as db:
        result = ingest_rss_feeds(db, dry_run=dry_run)
    print(json.dumps(result, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Watchers worker CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_cmd = subparsers.add_parser("ingest-sample", help="Ingest local sample claims JSON")
    ingest_cmd.add_argument("--file", default=settings.sample_claims_path, help="Path to raw claims JSON file")

    subparsers.add_parser("ingest-rss", help="Ingest live claims from configured RSS feeds")
    subparsers.add_parser("dry-run-rss", help="Fetch and parse RSS feeds without writing to the DB")

    args = parser.parse_args()

    if args.command == "ingest-sample":
        return run_ingest(file_path=args.file)
    if args.command == "ingest-rss":
        return run_ingest_rss()
    if args.command == "dry-run-rss":
        return run_ingest_rss(dry_run=True)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
