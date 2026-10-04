# Finance Hub — Claude Code brief

Oct 2, 2026 · @Travis

## Purpose and scope

The hub answers two questions every month: did money go where the plan said, and where does the plan land. It tracks planned flows against actual flows across all buckets, simulates the plan forward at a weekly tick, and tracks expenses by category plus a lumpy calendar.

It is not a trading tool. The covered-call engine stays in the Rotation Dashboard, which publishes one number to the hub. It is not a bank aggregator: transactions arrive by monthly CSV.

Done for v1: a month closes with every planned flow showing plan, actual, and gap; every sensor has a color; the simulate screen redraws from live balances when a lever moves.

All figures are the owner's own rail (bank checking, Schwab hub, brokerage, Ameritas policy, Roth, 401k). The household rail is out of scope for v1.

## Stack and repo

Separate app, same stack as the Rotation Dashboard: FastAPI + SQLAlchemy + Postgres backend, Angular frontend, deployed on Fly.io. New repo `finance-hub`, own database, own Fly app. If the dashboard uses a different ORM, chart library, or auth pattern, copy it rather than introduce a second one.

- Backend: FastAPI, Pydantic v2, SQLAlchemy 2, Alembic migrations, Postgres. One scheduled job (daily) that pulls the engine number from the dashboard API.
- Frontend: Angular, standalone components, signals for state, one chart library (whatever the dashboard uses; otherwise Chart.js). Mobile-first layout: two columns max, grain toggle at the top of every data view.
- Auth: single user. Reuse the dashboard's auth approach; a shared bearer token is enough for the dashboard-to-hub call.
- Money: integer cents in the database, decimal in the API, formatted only in the UI. Dates are ISO weeks for the ledger (year-week), calendar dates for events.
- Tests: pytest on the simulation engine first. The engine is pure functions over the ledger; it must be testable without a database.

## Data model

Nine tables carry the whole app. The ledger is the spine: the simulator writes forecast rows into it, imports and manual entries write actual rows, and every screen is a query over it.

| Table | Key fields | Notes |
| --- | --- | --- |
| `bucket` | id, name, kind (checking, hub, policy_cv, policy_loan, runway, lumpy_reserve, engine, roth, ira, k401), floor_cents, target_cents, balance_source (manual, dashboard, derived) | One row per place money sits. Policy loan is a negative bucket. |
| `planned_flow` | id, name, from_bucket, to_bucket, amount_cents or amount_rule (sweep_above_floor, remainder), cadence (per_paycheck, monthly_on_day, annual_on_date, weekly), anchor_date, stop_rule (bucket_reaches_target, headroom_zero, date), redirect_to_bucket, active | The Plan screen edits these rows. Stop rule plus redirect is how runway rolls into engine. |
| `ledger_entry` | id, iso_week, date, from_bucket, to_bucket, amount_cents, planned_flow_id, kind (forecast, actual), scenario_id (null = base), source (sim, csv, manual, dashboard) | Forecast rows for a week are deleted and rewritten on every sim run; actual rows are never touched by the sim. |
| `balance_snapshot` | bucket_id, date, balance_cents, source | Entered monthly for manual buckets, daily for dashboard buckets. The latest snapshot plus later actuals gives the live balance. |
| `transaction` | id, date, amount_cents, description, account (wf_checking, wf_card, capone_card), category_id, import_batch_id, hash | Hash of date+amount+description prevents duplicate imports. |
| `category` | id, name, monthly_target_cents, kind (recurring, lumpy, transfer, ignore) | Transfers between own buckets are categorized `transfer` so they never count as spend. |
| `lumpy_item` | id, name, amount_cents, cadence (months), next_due, category_id | Accrual per month = amount / cadence. Feeds the lumpy calendar and the reserve sensor. |
| `scenario` | id, name, levers (json), created | Levers: engine_return_pct, fpur_annual_cents, monthly_burn_cents, new_income_cents, new_income_start, retirement_age, inflation_pct, surplus_override_cents. |
| `engine_metric` | date, deployed_cents, reserve_cents, extrinsic_week_cents, mtm_week_cents, return_26wk_pct, after_tax_26wk_pct | Written by the daily pull from the Rotation Dashboard. |

Policy mechanics live in a small `policy` config row rather than a table: base premium, FPUR schedule, 7-pay limit and cumulative paid, loan rate, loan balance, anniversary date. The sim reads it; the Now screen's headroom sensor reads it.

## Simulation engine

The simulator is a pure function: `simulate(start_balances, planned_flows, lumpy_items, policy, levers, horizon_weeks) -> ledger rows + weekly balances`. It runs at the ISO-week tick from the Monday after today to the horizon (default: age 60). History is locked; the sim never rewrites weeks before today.

1. Build the event calendar. Each planned flow expands to its weeks: per-paycheck flows land on paycheck weeks from the anchor date (confirm 26 vs 24 checks); monthly flows land on the week containing their day; annual flows on the week containing their date; lumpy items on the week of `next_due` then every `cadence` months.
2. Step each week in order. Apply inflows first, then rule-based flows (sweep above floor, remainder), then fixed flows, then stop-rule checks. A flow whose stop rule has fired is skipped; if it has `redirect_to_bucket`, its amount goes there instead.
3. Grow balances. Engine bucket grows at `engine_return_pct / 52` per week on deployed balance; Roth, IRA, 401k, runway use their own configured rates; policy cash value follows the illustration curve (store the illustrated CV by policy year and interpolate) plus FPUR paid; loan balance accrues at the loan rate, interest due at anniversary.
4. Apply levers after the plan. `monthly_burn_cents` replaces the checking outflow; `new_income_cents` from `new_income_start` is an inflow to the hub; `fpur_annual_cents` overrides the FPUR flow; `inflation_pct` deflates every nominal balance for the real-dollar view; `retirement_age` sets where the W-2 inflows stop and the drawdown stack begins.
5. Compute the outputs: weekly balance per bucket, freedom date (first week where portfolio × withdrawal rate ≥ burn, or durable income + withdrawals ≥ burn), bridge funded % (accessible assets at retirement age vs five years of burn), ladder funded % (IRA at retirement vs required real value at 59½).

Roll-ups are queries, not separate sims: weekly rows group to monthly, quarterly, yearly. A scenario is a saved lever set; the chart overlays up to three scenarios plus the base plan. Base plan recomputes nightly and on any plan edit; scenarios recompute on lever change (debounced, under 200 ms for a 30-year horizon, so keep it in Python with numpy or plain loops, no pandas per call).

## Screens

Four tabs, one data model. Every data view carries the grain toggle (weekly, monthly, quarterly, yearly) and a real/nominal switch. Mobile layout: two columns max, metric cards 20px numbers, hairline-bordered rows for lists.

**Now.** Grid of bucket cards (balance, floor or target line, status color). Below it the current period's flow table: one row per planned flow with plan, actual, gap, colored green at zero, amber within 10%, red beyond. Rows whose date has not arrived show the date instead of a gap. Below that, the sensor strip (next section). Tapping a flow row opens a sheet to record the actual (amount, date) or mark it skipped with a reason.

**Plan.** The `planned_flow` table grouped by cadence (per paycheck, monthly, annual), each row showing from → to, amount or rule, and stop rule in small text. Add and edit via a form sheet. Saving a change triggers a base-plan resim and returns to Now with the diff highlighted for a few seconds.

**Simulate.** Line chart of total portfolio (and per-bucket on tap) from today to the horizon, today marked with a dashed line, the freedom number as a horizontal rule, the retirement age as a dot. Two metric cards under it: freedom date with delta vs base, bridge funded %. Lever panel: engine return (5–20%), FPUR per year ($9,250–37,000), monthly burn, new income per month, income start year, retirement age (45–55), inflation. Save as scenario; scenario chips above the chart toggle overlays. Opportunity card: plain-sentence summary of what the active lever change buys, computed from the two sims (months moved, portfolio replaced). At weekly grain the chart switches to cash reserve for the next 13 weeks and the list below becomes the week's actions.

**Expenses.** Two metric cards (recurring spend vs target, 3-month average). Category table: target, actual, trend arrow from the 3-month slope. Tapping a category lists its transactions with a recategorize action. Lumpy calendar: next twelve months of `lumpy_item` due dates with amounts, accrual per month in the header, and the reserve-coverage sensor underneath. CSV import button lives here.

## Sensors

Each sensor is a function of current state returning green, amber, or red plus a one-line label. They render on Now and in the quarterly roll-up.

| Sensor | Green | Amber | Red |
| --- | --- | --- | --- |
| Checking floor | balance ≥ $7,500 | within $500 below | more than $500 below |
| Flow gap (per planned flow, current period) | gap = 0 | within 10% | beyond 10% or missed past date |
| FPUR year-to-date vs schedule | on pace for the policy year | 1 month behind | 2+ months behind |
| 7-pay headroom | paid ≤ cumulative limit − $2,000 | within $2,000 | at or over limit (MEC risk) |
| Loan to cash value | ≤ 60% | 60–80% | over 80% |
| Runway progress | at target or on pace | 1 month behind pace | 2+ months behind |
| Lumpy reserve coverage | reserve ≥ next 12 months of accruals | ≥ 50% | under 50% |
| Roth window | funded for the tax year | open, under 60 days to April 15 | open, under 30 days |
| Engine 26-week net | ≥ 26 weeks of data and within or above the 8–15% band | fewer than 26 weeks | 26+ weeks and below 8% |
| Engine sidelined | deployed in last 4 weeks | out 2–4 weeks | out 4+ weeks (repay loan principal) |

Thresholds live in a `sensor_config` table so they can be tuned without a deploy.

## CSV ingestion and categorization

Monthly upload of three files: Wells Fargo checking, Wells Fargo card, Capital One card. Each bank has its own column layout, so the importer has one parser per `account` that maps to (date, amount, description). Store the raw row too.

1. Parse, normalize amounts to signed cents (outflows negative), hash date+amount+description, skip hashes already present.
2. Match against a `category_rule` table: ordered rows of (pattern, match_kind: contains or regex, category_id). First match wins. Unmatched rows land in an Uncategorized queue on the Expenses screen.
3. Transfers between own accounts (card payment from checking, hub transfers, Ameritas premium, Schwab deposits) match rules that assign the `transfer` kind, and the importer also writes the matching `ledger_entry` actual row when the description maps to a planned flow (a `planned_flow.match_pattern` field).
4. Recategorizing a transaction offers to create a rule from its description, so the queue shrinks each month.

Targets per category start as the 3-month average and are edited in place. The recurring-spend metric sums categories of kind `recurring`; lumpy spend is reported separately and checked against the lumpy calendar.

## Rotation Dashboard integration

The dashboard owns the engine; the hub only reads. Add one endpoint to the dashboard, `GET /api/hub/metrics`, returning the latest row of its engine tracker: deployed, cash reserve, this week's extrinsic, this week's mark-to-market, rolling 4/13/26-week net return, after-tax 26-week annualized, weeks of data, in-or-out flag. Bearer token shared by environment variable.

The hub's daily job stores it in `engine_metric`, updates the engine bucket's balance snapshot, and feeds the two engine sensors. The simulator's default `engine_return_pct` is the after-tax 26-week number once 26 weeks exist; until then it uses 10%, the middle of the plan band.

Nothing flows the other way. Deposits to the brokerage are hub ledger entries; the dashboard sees them as cash arriving in the Schwab account.

## Build order

Ship in five phases; each one is usable on its own and the next builds on its tables.

1. **Skeleton and Plan.** Repo, migrations for all tables, Plan screen with full CRUD on `planned_flow` and `bucket`. Done when the current routine can be entered from scratch and edited on a phone.
2. **Now.** Balance snapshots entry, flow table with plan/actual/gap, record-actual sheet, sensors with the thresholds above. Done when October closes with every row filled.
3. **Simulator.** Pure engine with pytest coverage (paycheck expansion, stop rules, redirect, policy curve, levers), base-plan nightly run, Simulate screen with chart, levers, scenarios, opportunity card, grain toggle. Done when moving the new-income lever changes the freedom date live.
4. **Expenses.** CSV parsers for the three accounts, dedupe, rule matching, uncategorized queue, category table, lumpy calendar and reserve sensor. Done when September's three CSVs import clean and the Dining row shows red.
5. **Dashboard feed.** Endpoint on the Rotation Dashboard, daily pull job, engine sensors live, simulator default rate switches to the measured number at 26 weeks.

Skip for v1: household rail, multi-user, bank API pulls, drawdown-phase detail beyond the freedom-date rule, notifications.

## Starting data and open items

No seed script. The app ships empty and the owner enters every bucket, flow, balance, category, and lumpy item through the UI, so the forms get tested on real data from day one. Every screen needs a usable empty state that says what to add first.

Entry order the empty states should steer toward: buckets with floors and targets, then paycheck flows, then monthly and annual flows, then a balance snapshot per bucket, then the policy config, then categories and lumpy items. The Now screen is blank until a snapshot exists; Simulate is blank until at least one flow and one snapshot exist.

For automated tests, use fixtures in pytest only (a small synthetic plan with two paycheck flows, one sweep, one stop rule, one lumpy item); never load them into the real database.

- [ ] Confirm the Rotation Dashboard's exact stack and auth before scaffolding
- [ ] Confirm Alan Wire pay frequency (26 vs 24) for the paycheck expansion
- [ ] Pull one month of CSVs from each account to write the parsers against real headers
- [ ] Get the illustrated cash value by policy year from the Ameritas PDF into the policy config
- [ ] Decide the FPUR send amount ($15,000 or $22,000) before entering the first policy snapshot
