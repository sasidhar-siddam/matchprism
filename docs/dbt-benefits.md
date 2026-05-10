# dbt: What It Gives You

dbt (data build tool) is a SQL-based transformation framework. It runs against a SQL warehouse — it does not extract or load data, only transforms what is already there. Below is what you get, with the trade-offs.

## Core Capabilities

### 1. Transformations as version-controlled code
Models are `.sql` files in a git repo. Each model is a `SELECT` statement; dbt wraps it in `CREATE TABLE` or `CREATE VIEW` based on a `materialized` config. Result: data logic goes through pull requests, code review, and branch-based environments like application code.

### 2. Automatic DAG resolution
You reference upstream models with `{{ ref('model_name') }}`. dbt parses the refs, builds a DAG, and runs models in dependency order in parallel where possible. You do not write an Airflow DAG or shell script to orchestrate run order.

### 3. Materialization strategies
A single config switch changes how a model is built:
- `view` — recomputed on every read, no storage cost
- `table` — full rebuild on each `dbt run`
- `incremental` — only new rows appended, defined by an `is_incremental()` filter
- `ephemeral` — inlined as a CTE, never persisted
- `snapshot` — SCD Type 2 history with `valid_from` / `valid_to` columns

Switching strategies is a config change, not a rewrite.

### 4. Testing
Two kinds, both first-class:
- **Schema tests** in YAML: `unique`, `not_null`, `accepted_values`, `relationships` (foreign-key style).
- **Data tests** as SQL: any query that returns rows is a failing test.

`dbt test` runs them all. Tests can block CI on a PR or fail a production run.

### 5. Sources and freshness
Declare raw input tables in `sources.yml` with optional freshness thresholds (`warn_after`, `error_after`). `dbt source freshness` reports stale data before you run downstream models on it.

### 6. Documentation and lineage
YAML descriptions + `dbt docs generate` produces a static site with column-level descriptions, the full DAG, and click-through lineage. The lineage is computed from `ref()` calls — it cannot drift from the code.

### 7. Macros (Jinja)
Reusable SQL fragments. Common uses: surrogate keys, date spines, conditional logic across warehouses, generating columns from a list. Replaces copy-pasted SQL snippets.

### 8. Environments via targets
One `profiles.yml` defines `dev`, `ci`, `prod`. Same model code writes to different schemas/databases. No code branching for environment.

### 9. Package ecosystem
`dbt_utils` (date spines, surrogate keys, pivot helpers), `dbt_expectations` (Great Expectations-style assertions), warehouse-specific packages. Installed via `packages.yml`.

## What dbt Does Not Do

- **No extraction or loading.** You need Fivetran, Airbyte, a Python script, or `COPY` to get data into the warehouse first.
- **No general-purpose Python transforms.** Python models exist (Snowpark, BigQuery, DuckDB) but are second-class. If your transform is genuinely procedural, dbt is the wrong tool.
- **No real-time / streaming.** Batch only.
- **No orchestration outside dbt.** It runs the DAG it owns. Cross-system orchestration needs Airflow, Dagster, or dbt Cloud's scheduler.
- **Requires a SQL warehouse.** BigQuery, Snowflake, Redshift, Postgres, Databricks, DuckDB, etc. dbt does not transform flat files directly.

## When dbt Pays Off

- You have ≥10 transformation steps with dependencies between them.
- More than one person edits transformation logic.
- You need to test data quality continuously.
- Stakeholders ask "where does this column come from?"
- You run the same logic in dev and prod and want them identical.

## When dbt Is Overkill

- A handful of independent scripts that each produce one output.
- No SQL warehouse and no plan to adopt one.
- Transforms are primarily procedural (parsing, ML feature engineering, API calls).
- Output is static JSON with no warehouse in the loop.

## Relevance to MatchPrism

Current pipeline: Python scripts read Cricsheet JSON, compute stats, write `data/processed/*.json` consumed by the Next.js frontend. dbt does not slot into this directly because there is no warehouse.

It becomes relevant if you adopt **DuckDB + dbt-duckdb**:
1. Python ingest loads ball-by-ball Cricsheet into a DuckDB file.
2. dbt models compute venue stats, player form, head-to-head, win-probability inputs as SQL on that DuckDB.
3. A small export step writes selected models out to JSON for the static frontend.

Costs you would pay: DuckDB file in the repo or build artifact, dbt as a dev dependency, learning curve for whoever writes models. Benefits you would get: tested transformations, lineage docs for the stats logic, incremental rebuilds when only new matches arrive, parallel dev/prod schemas in the same DuckDB.

The decision is whether the stats pipeline is complex enough — and shared across enough people — to justify it. For a single-developer project with <20 transformation steps, plain Python is fine. For a growing pipeline with multiple sports and contributors, dbt-on-DuckDB is the cheapest way to get the discipline without a cloud warehouse bill.
