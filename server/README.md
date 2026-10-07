# Qriously server

Django + DRF backend. See `../docs/ARCHITECTURE.md`, `../docs/DATA-MODEL.md`,
`../docs/API.md`, `../docs/PLAN.md`.

## Setup

```bash
cd server
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
docker compose up -d db
python manage.py migrate
python manage.py runserver
```

ASGI (needed for SSE streaming later): `uvicorn config.asgi:application --reload`.

## Checks

```bash
ruff check .
pytest
```

## Health

- `GET /health` — liveness
- `GET /health/ready` — readiness (checks the database)
