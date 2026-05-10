# SQLMesh PoC for MatchPrism

A self-contained proof-of-concept showing what SQLMesh actually does and how it
would slot into a Snowflake + Dagster pipeline. Runs entirely locally against
DuckDB so no cloud account is required.

## What this PoC contains

```
poc/sqlmesh/
├── generate_sample_data.py   # Synthesizes 8 Cricsheet-shaped match JSONs
├── raw/ipl/*.json            # Generated raw input (gitignored if you want)
├── config.yaml               # SQLMesh project config (duckdb gateway)
├── models/
│   ├── raw_matches.py        # Python model: reads JSON files into DuckDB
│   ├── stg_matches.sql       # Staging: one row per match
│   ├── stg_deliveries.sql    # Staging: one row per ball (explodes JSON)
│   ├── venue_stats.sql       # Mart: per-venue aggregates
│   └── player_batting_daily.sql  # Mart: INCREMENTAL_BY_TIME_RANGE
└── matchprism.duckdb         # The DuckDB file (created by `sqlmesh plan`)
```

## How to run from scratch

```bash
cd poc/sqlmesh
python3 -m venv .venv
.venv/bin/pip install "sqlmesh[duckdb]"
.venv/bin/python generate_sample_data.py     # writes 8 JSON files
.venv/bin/sqlmesh plan --auto-apply          # builds all 5 models
```

To inspect the result:

```bash
.venv/bin/python -c "
import duckdb
con = duckdb.connect('matchprism.duckdb', read_only=True)
con.sql('USE matchprism.matchprism')
print(con.sql('SELECT * FROM venue_stats').df())
"
```

## What I built / what runs

| Layer    | Model                  | Kind                        | Rows |
|----------|------------------------|-----------------------------|------|
| raw      | raw_matches            | FULL (Python model)         | 8    |
| staging  | stg_matches            | FULL                        | 8    |
| staging  | stg_deliveries         | FULL                        | 1907 |
| mart     | venue_stats            | FULL                        | 5    |
| mart     | player_batting_daily   | INCREMENTAL_BY_TIME_RANGE   | 85   |

Audits attached to models (run on every materialization):

- `stg_matches`: `not_null(match_id, match_date, venue)`, `unique_values(match_id)`
- `stg_deliveries`: `not_null(match_id, innings_num, over_num, ball_num, batter, bowler)`
- `venue_stats`: `not_null(venue, matches_played)`, `unique_values(venue)`
- `player_batting_daily`: `not_null(batter, match_date)`

All 6 audits pass on first run.

## What was actually demonstrated

### 1. DAG resolution from `ref()`-style table references

SQLMesh parses the SQL and figures out the dependency graph itself. We never
declared "stg_matches depends on raw_matches" — it inferred this from the
`FROM matchprism.raw_matches` clause and ran them in the right order.

### 2. Incremental materialization

`player_batting_daily` is `INCREMENTAL_BY_TIME_RANGE` keyed on `match_date`.
On first run, SQLMesh built it in **29 monthly batches** from `2024-01-01` to
today. On the next run with new data only the affected partitions rebuild —
this is the bit that's tedious to hand-roll in raw SQL.

### 3. Audits as first-class objects

Audits are declared in the `MODEL (...)` block and run automatically after
each materialization. A failing audit blocks the plan. Equivalent to dbt's
schema tests, just inline.

### 4. Virtual environments — the killer feature

I modified `venue_stats` to add a `six_pct` column and ran:

```bash
sqlmesh plan dev --auto-apply --include-unmodified
```

What happened:

- Only `venue_stats` was physically rebuilt.
- A new schema `matchprism__dev` was created with views for all 5 models.
- The dev views for the **4 unchanged models** point to the same physical
  tables that prod uses. Zero compute, zero storage cost.
- The dev view for `venue_stats` points to a **new physical table** with the
  new column.
- Prod is completely untouched.

Inspect the physical layer:

```
sqlmesh__matchprism.matchprism__raw_matches__2709213814      <- shared by prod + dev
sqlmesh__matchprism.matchprism__stg_matches__1000506358      <- shared
sqlmesh__matchprism.matchprism__stg_deliveries__2894050514   <- shared
sqlmesh__matchprism.matchprism__player_batting_daily__3131664048  <- shared
sqlmesh__matchprism.matchprism__venue_stats__3855576195      <- PROD points here
sqlmesh__matchprism.matchprism__venue_stats__1300148675      <- DEV points here (new)
```

The hash suffix is a content-addressed identifier derived from the model SQL
and its upstream hashes. Promoting `dev` to `prod` would be a metadata-only
operation that flips the prod views to the new physical tables — instant, no
data movement.

**This is the thing dbt fundamentally cannot do.** dbt's `--defer` flag gets
partway there but requires manual `manifest.json` artifact management. SQLMesh
makes it the default workflow.

### 5. Table diff for code review

```bash
sqlmesh table_diff prod:dev matchprism.venue_stats --on venue
```

Output:

```
Schema Diff Between 'PROD' and 'DEV':
└── Added Columns:
    └── six_pct (DOUBLE)

Row Counts:
└──  FULL MATCH: 5 rows (100.0%)

COMMON ROWS column comparison stats:
                         pct_match
matches_played               100.0
avg_first_innings_score      100.0
avg_run_rate                 100.0
```

A PR reviewer can see exactly what a model change does to the data without
spinning up a dev environment themselves.

### 6. Python and SQL models in the same project

`raw_matches.py` is a Python model that reads JSON files and returns a
pandas DataFrame. SQLMesh inserts it into DuckDB and downstream SQL models
treat it as a regular table. No glue code, no separate orchestrator step.

In production this Python model would be replaced by an ingestion tool
(Airbyte/Fivetran/custom Snowflake task) landing data into Snowflake. The
boundary between "data engineering" and "analytics engineering" lives at
exactly this seam.

## What did not work the first time

Two SQL errors that are worth knowing about for the Snowflake migration:

1. **`UNNEST ... WITH ORDINALITY AS t(value, idx)` is Postgres syntax, not
   DuckDB.** DuckDB names the ordinality column `ordinality` and you can't
   alias it inline. I rewrote using `json_each()` which is cleaner anyway.
2. **DuckDB JSON `json_each` returns keys as VARCHAR** — needed `CAST(... AS
   INTEGER)` before arithmetic. Snowflake's `LATERAL FLATTEN` returns
   `INDEX` as a number directly, so this specific cast wouldn't be needed
   there.

Both errors surfaced immediately at `sqlmesh plan` time. The audits also
caught nothing because the schema errors blocked materialization before any
audit could run.

## What this PoC does NOT show

Things SQLMesh can do that I didn't exercise here:

- **Snapshots (SCD2)** — would be the right kind for tracking changing
  player team assignments over time.
- **Macros** — `@some_macro()` Jinja-style for reusable SQL fragments.
- **CI/CD integration** — `sqlmesh plan ci_branch` against a PR builds an
  isolated env, runs audits and table_diffs, posts results as a PR comment.
- **The VS Code extension** — column-level lineage as you edit, live SQL
  preview. The standalone browser UI (`sqlmesh ui`) is being phased out in
  favor of this.
- **dagster-sqlmesh integration** — the production fit. Dagster orchestrates
  ingestion, kicks off `sqlmesh run`, and treats every SQLMesh model as a
  Dagster asset for observability.
- **Snowflake gateway** — same code, swap `type: duckdb` for `type: snowflake`
  in `config.yaml` plus connection details. The models above would mostly
  work as-is; the JSON `json_each` would become Snowflake's `LATERAL FLATTEN`.

## Honest assessment

**What clicked:**

- Plan-then-apply is the right mental model. Every change shows a diff
  before it touches data. No "oh no the run broke prod" surprises.
- Virtual environments are genuinely cheap. Adding a column to one model
  cost ~0.07s of compute against ~2,000 rows. At Snowflake scale this is
  the difference between iterating freely and rationing dev runs.
- The audit DSL is more terse than dbt's YAML (`not_null(columns := (...))`
  inline beats a separate `schema.yml`).
- DAG inference from SQL `FROM` clauses means no `ref()` macro — the SQL
  you write is the SQL that runs. No Jinja compile step to debug.

**What was friction:**

- DuckDB SQL is close to but not identical to Snowflake SQL. The JSON
  exploding logic will need to be rewritten when porting. Not a SQLMesh
  problem, but a real cost of the "develop locally, deploy to Snowflake"
  story.
- The Python model surface is more verbose than I expected (`@model(...)`
  decorator + explicit columns dict). For one-off ingestion this is fine;
  for many Python models you'd want a helper.
- `sqlmesh ui` is being deprecated, so the visual canvas story is moving
  to the VS Code extension. If your team isn't on VS Code, that's a gap.
- Error messages are SQL-engine-native (DuckDB BinderException above).
  Surfaced through SQLMesh's CLI but not noticeably nicer than raw SQL
  errors.

**Bottom line:** SQLMesh delivers on its core promise — virtual environments
and column-level lineage that dbt doesn't have. For a Snowflake + Dagster
shop coming from an Alteryx background, it's a meaningfully better fit than
dbt for the iterative-development half of the story. It does **not** solve
the "live visual canvas" gap (no orchestrator-shaped tool does), but it
narrows the iteration loop enough that the missing canvas hurts less.

## Next steps if continuing

1. Add a `dagster-sqlmesh` integration in a sibling `poc/dagster/` directory
   to see the full orchestration story.
2. Swap the DuckDB gateway for a Snowflake gateway against a trial account
   and port the JSON-exploding SQL to `LATERAL FLATTEN`.
3. Try the VS Code extension and see whether column-level lineage during
   editing actually changes the dev loop in practice.
4. Wire up `ydata-profiling` inside the Python model to attach per-asset
   profile reports — that's the Alteryx-style "click and inspect" piece that
   neither SQLMesh nor Dagster gives you out of the box.
