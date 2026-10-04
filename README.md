# Finance Hub

Did money go where the plan said, and where does the plan land. Planned flows vs actual flows
across buckets, a weekly-tick simulator, and expenses by category. See `BRIEF.md` for the full
design; this repo is at **phase 1: skeleton and Plan**.

## Stack

- `backend/` FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, Postgres 16. Money is integer cents in
  the database and decimal dollars in the API.
- `frontend/` Angular 21, standalone components, signals, zoneless. Mobile-first, two columns max.
- `docker-compose.yml` runs Postgres only; the API and the Angular dev server run on the host.

## Run it

```sh
make install        # backend/.venv (uv or venv) + npm install
make dev            # docker compose up db, alembic upgrade head, API on :8000, UI on :4200
```

Open http://localhost:4200. The app ships empty by design; the Plan screen walks you through
buckets first, then paycheck flows, then monthly and annual flows.

Other targets: `make migrate`, `make revision m="..."`, `make downgrade`, `make test`
(`make test-backend` / `make test-frontend`), `make lint`, `make db-down`.

Configuration is read from `HUB_*` environment variables or `backend/.env`
(see `backend/.env.example`). Defaults match the compose file.

## Deploy (Fly.io, launched from GitHub)

Fly's GitHub integration owns deploys: in the Fly dashboard choose **Launch from GitHub**, pick
this repository and the `main` branch, and Fly builds the root `Dockerfile` (Angular build copied
into the API image) on every push to `main`. `fly.toml` supplies the rest: `alembic upgrade head`
runs as the release command before traffic switches, and `/api/health` is the health check.

During the launch flow, add a **Postgres** database; Fly attaches it and sets `DATABASE_URL`,
which the app reads directly. If you give the app a name other than `finance-hub`, change `app`
in `fly.toml` to match on your next push.

After the first deploy, set the login under the app's **Secrets**:

| Secret | Value |
| --- | --- |
| `HUB_BASIC_AUTH` | `you:a-long-password`. Without it the app is public. |

GitHub Actions (`.github/workflows/ci.yml`) is the test gate: backend lint and pytest against a
Postgres service, frontend tests and a production build, on every push and pull request. It does
not deploy. `make deploy` runs `fly deploy --remote-only` by hand if ever needed.

## Backend layout

```
backend/app/models/     one module per table (12 tables, see BRIEF.md data model)
backend/app/schemas/    Pydantic request/response models; money.py does cents <-> decimal
backend/app/routers/    /api/buckets, /api/planned-flows (CRUD), /api/health
backend/alembic/        migrations; env.py reads the URL from settings or -x db_url=...
backend/tests/          pytest; migrates finance_hub_test up and down on every run
```

API docs are served at http://localhost:8000/docs while the backend runs.

## Phase status

1. **Skeleton and Plan** — done: migrations for every table, bucket and planned_flow CRUD, four-tab
   shell, Plan screen (grouped by cadence, add/edit via form sheet, empty states).
2. Now — balance snapshots, flow table, sensors.
3. Simulator — pure engine with pytest, Simulate screen.
4. Expenses — CSV import, rules, categories, lumpy calendar.
5. Dashboard feed — engine metrics from the Rotation Dashboard.
