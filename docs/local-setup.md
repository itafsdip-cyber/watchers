# Local Setup

## 1. Bootstrap
```bash
cd /Users/mr.nobody/Documents/Project-Watchers/Watchers
cp .env.example .env
make up
```

## 2. API
```bash
cd /Users/mr.nobody/Documents/Project-Watchers/Watchers/apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

## 3. Seed API Demo (optional)
```bash
curl -X POST http://localhost:8000/demo/seed
```

## 4. Worker Ingestion
```bash
cd /Users/mr.nobody/Documents/Project-Watchers/Watchers/apps/worker
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m worker_app.main ingest-sample --file ../../data/samples/raw_claims.json
```

## 5. Web Dashboard
```bash
cd /Users/mr.nobody/Documents/Project-Watchers/Watchers/apps/web
npm install
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

Open `http://localhost:3000`.
