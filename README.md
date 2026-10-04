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

## Deploy (Fly.io, entirely from GitHub Actions)

Nothing needs flyctl on a laptop. Two workflows in `.github/workflows/`:

- `fly-bootstrap.yml` (run by hand, once): creates the Fly app and a Fly Postgres, attaches it
  (which sets `DATABASE_URL`), pushes the `HUB_BASIC_AUTH` secret, and runs the first deploy.
  Every step checks before acting, so re-running it is harmless.
- `ci.yml` (automatic): backend and frontend tests on every push and pull request; on a passing
  push to `main`, `flyctl deploy --remote-only`. Fly builds the root `Dockerfile` (Angular build
  copied into the API image), runs `alembic upgrade head` as the release command, and switches
  traffic once `/api/health` passes. The deploy job skips with a warning until bootstrap has run.

Setup:

1. Fly dashboard → Account → Access Tokens → create an **org** token (app-scoped deploy tokens
   cannot create apps). Copy it once.
2. GitHub → repo Settings → Secrets and variables → Actions:
   - secret `FLY_API_TOKEN`: the token from step 1
   - secret `HUB_BASIC_AUTH`: `you:a-long-password`, the browser login (without it the app is public)
   - variable `FLY_APP` (optional): only if `finance-hub` is taken on Fly; the workflows and
     `fly.toml`'s `app` should agree, so change both
3. GitHub → Actions → **Fly bootstrap (one time)** → Run workflow. Defaults: org `personal`,
   region `ord`, smallest Postgres. Watch the log; the last step prints the URL.

After that, merging to `main` deploys. `make deploy` runs the same `flyctl deploy` by hand.

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
