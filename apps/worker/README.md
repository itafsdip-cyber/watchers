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
