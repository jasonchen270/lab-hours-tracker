# Lab Hours Tracker

A small Django web app that lets students log lab/study sessions and visualize weekly study patterns on a Chart.js dashboard. Originally built for a CS algorithms study group; now Dockerized for one-command local runs and ready to deploy to Render's free tier.

## Features

- Email + password auth (Django's `auth_user`)
- Start/stop study sessions with optional notes
- Dashboard with a Chart.js bar chart of hours-by-weekday over the last 8 weeks
- CSV export of all your sessions (UTC ISO timestamps)
- Timezone-aware: stores UTC, renders in the configured `TIME_ZONE`
- Postgres in production (free tier on Render), SQLite fallback if no `DATABASE_URL` is set

## Schema design notes

Sessions are modeled as a **half-open interval `[start_at, end_at)`**. `end_at` is NULL while a session is in progress. This makes "currently open" trivially queryable (`WHERE end_at IS NULL`) and avoids the off-by-one ambiguity at midnight boundaries.

Two database-level guarantees back the model:

1. **`CheckConstraint(end_at IS NULL OR end_at > start_at)`** rejects backwards or zero-duration intervals at insert time, regardless of which layer wrote the row (Django ORM, admin, or `psql`).
2. **Partial unique index** `WHERE end_at IS NULL` enforces "at most one open session per user" without any application-level locking. See `sessions_app/migrations/0001_initial.py`:

   ```sql
   CREATE UNIQUE INDEX one_open_session_per_user
   ON sessions_app_session (user_id) WHERE end_at IS NULL;
   ```

   This works because Postgres treats partial-index uniqueness like any other unique constraint, but only for rows matching the `WHERE`. Open a second session and the database rejects it (`IntegrityError`), which the view translates to a 400 response.

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

## Deploying to Render (free tier)

1. **Create a new Postgres instance** on Render (free tier, 1GB). Copy the internal Database URL.
2. **Create a Web Service** pointing to this repo. Build/start commands:
   - Environment: Python 3
   - Build command: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - Start command: `python manage.py migrate --noinput && gunicorn config.wsgi:application`
3. **Environment variables:**
   - `DJANGO_SECRET_KEY`: generate one (`python -c 'import secrets; print(secrets.token_urlsafe(60))'`)
   - `DJANGO_DEBUG` = `0`
   - `DJANGO_ALLOWED_HOSTS` = `your-app.onrender.com`
   - `DATABASE_URL`: paste the internal URL from step 1
   - `CSRF_TRUSTED_ORIGINS` = `https://your-app.onrender.com`
   - `TIME_ZONE` = whatever fits your users (e.g., `America/Los_Angeles`)
4. **First deploy** will run migrations automatically via the start command. Visit the URL and sign up.

> The free Render web service spins down after 15 min of inactivity. First request after a sleep takes ~30s; that's a free-tier characteristic, not a bug.

## Project layout

```
config/             Django project (settings, urls, wsgi)
sessions_app/       The app: model, views, migrations, admin
templates/          base.html, dashboard.html, login.html, signup.html
Dockerfile          python:3.12-slim, gunicorn
docker-compose.yml  web + postgres:16 with healthcheck
requirements.txt    Django 5.1, psycopg3, gunicorn, whitenoise, dotenv, dj-database-url
```

## Known behaviors and gotchas

- **Timezone fix:** Aggregating hours by weekday must `.astimezone(current_tz)` before `.weekday()`. Otherwise a Sunday 11pm Pacific session shows up under Monday in UTC. Fixed in `sessions_app/views.py::dashboard`.
- **CSV exports UTC.** Localized timestamps in CSVs invite reinterpretation bugs downstream; we export ISO 8601 UTC and let the consumer (Pandas, Excel) localize.
- **Partial index, not a unique constraint.** Postgres unique constraints treat each NULL as distinct, so a vanilla `UniqueConstraint(user, end_at)` lets multiple open sessions through. The partial index is the right tool.
