# Lab Hours Tracker

A small Django web app that lets students log lab/study sessions and visualize weekly study patterns on a Chart.js dashboard. Originally built for a CS algorithms study group; now Dockerized for one-command local runs and ready to deploy to Render's free tier.

## Features

- Email + password auth (Django's `auth_user`)
- Start/stop study sessions with optional notes
- Dashboard with a Chart.js bar chart of hours-by-weekday over the last 8 weeks
- CSV export of all your sessions (UTC ISO timestamps)
- Timezone-aware: stores UTC, renders in the configured `TIME_ZONE`
- Postgres in production (free tier on Render), SQLite fallback if no `DATABASE_URL` is set

## Local dev with Docker Compose

```bash
git clone <repo>
cd lab-hours-tracker
docker compose up --build
```

The web service waits for Postgres's healthcheck before running `migrate` and starting Gunicorn. App is at <http://localhost:8000>.

To create a superuser:

```bash
docker compose exec web python manage.py createsuperuser
```

## Local dev without Docker

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then edit DATABASE_URL if you have a local Postgres
python manage.py migrate
python manage.py runserver
```

If `DATABASE_URL` is unset, Django falls back to SQLite (`db.sqlite3`). The partial unique index migration is wrapped in `RunSQL(... IF NOT EXISTS)` so it's a no-op on SQLite (which silently parses but doesn't enforce partial indexes). That's fine for dev, but use Postgres for any real testing of the open-session constraint.
