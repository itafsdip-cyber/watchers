# apps/worker

Sample ingestion worker for Watchers MVP.

## Run
```bash
cd apps/worker
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m worker_app.main ingest-sample --file ../../data/samples/raw_claims.json
```

## Ingest live RSS incidents
```bash
cd apps/worker
source .venv/bin/activate
python -m worker_app.main ingest-rss
```

The RSS command pulls incidents from:
- https://news.google.com/rss/search?q=incident
- https://feeds.bbci.co.uk/news/world/rss.xml
