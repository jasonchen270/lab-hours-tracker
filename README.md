# Lab Hours Tracker

A small Django web app that lets students log lab/study sessions and visualize weekly study patterns on a Chart.js dashboard. Originally built for a CS algorithms study group; now Dockerized for one-command local runs.

## Prerequisites

- Python 3.12
- Docker
- Postgres 16

## Installation

With Docker Compose:

```bash
git clone <repo>
cd lab-hours-tracker
docker compose up --build
```

The web service waits for Postgres's healthcheck before running `migrate` and starting Gunicorn. App is at <http://localhost:8000>.

Without Docker:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then edit DATABASE_URL if you have a local Postgres
python manage.py migrate
python manage.py runserver
```

If `DATABASE_URL` is unset, Django falls back to SQLite (`db.sqlite3`). The partial unique index migration is wrapped in `RunSQL(... IF NOT EXISTS)` so it's a no-op on SQLite (which silently parses but doesn't enforce partial indexes). That's fine for dev, but use Postgres for any real testing of the open-session constraint.

## Usage

To create a superuser when running under Docker:

```bash
docker compose exec web python manage.py createsuperuser
```
